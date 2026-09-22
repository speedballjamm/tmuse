"""The game engine: a background process that watches tmux and runs the lessons.

    python3 -m game.engine campaign [MISSION_ID] [--once]
    python3 -m game.engine dojo | review | sandbox
"""
import json
import logging
import os
import shlex
import sys
import time

from . import actions, markup, paths, progress, state
from .hud import Hud
from .keylog import KeyLog, describe as describe_key
from .keys import BY_ID as KEYS
from .model import Ctx
from .tmux import Tmux

TICK = 0.1
NUDGE_AFTER = 20
HINT_AFTER = 45
FEEDBACK_SECS = 12
IGNORE = {"key", "prefix", "copy-scroll", "attach", "mode-exit", "option", "copy-search", "copy-select"}
IDLE_TIP = "stuck? type: tmuse hint   (tmuse task reprints it here; also: tmuse show, tmuse skip)"

log = logging.getLogger("tmuse")


class Quit(Exception):
    """The tmux server went away, or the player asked for the menu."""


class Skip(Exception):
    pass


class Reset(Exception):
    pass


class StepResult:
    def __init__(self, hinted=False, shown=False):
        self.hinted = hinted
        self.shown = shown


class Engine:
    def __init__(self, tmux, mode="campaign", start=None, once=False):
        self.t = tmux
        self.mode = mode
        self.start = start
        self.once = once
        self.hud = Hud(tmux)
        self.data = progress.load()
        self.snap = None
        self.keylog = KeyLog(tmux)
        self.flash_until = 0
        self.base_msg = ("", "")
        self.last_health = 0
        self.timer = None      # (start, par) when a clock is shown
        self.prompt = ("", "")  # (title, raw prompt) for re-rendering
        self.runtime = {}      # last runtime.json payload, so partial updates keep the rest
        self.hints_shown = []  # hints revealed on the current step, for `tmuse hint` to reprint
        paths.ensure()
        try:
            self.ev_pos = os.path.getsize(paths.EVENTS)
        except OSError:
            self.ev_pos = 0

    # ------------------------------------------------------------ plumbing

    def tick(self, sleep=True):
        if sleep:
            time.sleep(TICK)
        s = state.take(self.t)
        if s is None:
            raise Quit()
        acts = actions.classify(self.snap, s) if self.snap else []
        acts += [actions.Action("key", {"key": k, "cmd": c}) for k, c in self.keylog.poll()]
        self.snap = s
        evs = self.read_events()
        now = time.time()
        if now - self.last_health > 1:
            self.last_health = now
            self.health(s)
        if self.flash_until and now > self.flash_until:
            self.flash_until = 0
            self.hud.set(msg=self.base_msg[0], kind=self.base_msg[1])
        if self.timer:
            self.hud.set(right=self.right_text())
        return s, acts, evs

    def health(self, s):
        if s.client:
            self.hud.resize(s.client.width)
        if s.prefix_key != self.hud.prefix:
            self.hud.prefix = s.prefix_key
            self.hud.rerender()
        fmt0 = self.t.out("show", "-gv", "status-format[0]")
        if not self.hud.healthy(s) or "@tmuse" not in fmt0:
            log.info("HUD was overwritten; reinstalling")
            self.hud.install()

    def read_events(self):
        out = []
        try:
            size = os.path.getsize(paths.EVENTS)
            if size < self.ev_pos:
                self.ev_pos = 0
            if size == self.ev_pos:
                return out
            with open(paths.EVENTS) as f:
                f.seek(self.ev_pos)
                chunk = f.read()
                self.ev_pos = f.tell()
        except OSError:
            return out
        for line in chunk.splitlines():
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
        return out

    def msg(self, text, kind="", secs=None):
        if secs:
            self.flash_until = time.time() + secs
        else:
            self.base_msg = (text, kind)
            if self.flash_until:
                return
        self.hud.set(msg=text, kind=kind)

    def set_prompt(self, title, prompt, outside=""):
        self.prompt = (title, prompt)
        self.hints_shown = []
        self.hud.set(title=title, prompt=prompt, right=self.right_text())
        self.write_runtime(title=title, prompt=markup.plain(prompt, self.hud.prefix), outside=outside,
                           hints=[])

    def write_runtime(self, **kw):
        self.runtime.update(kw)
        self.runtime.update(mode=self.mode, pid=os.getpid(), socket=self.t.socket)
        tmp = paths.RUNTIME + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.runtime, f)
        os.replace(tmp, paths.RUNTIME)

    def show_hint(self, text, kind="hint", secs=None):
        """Reveal a hint: on the status bar, and in runtime.json so `tmuse hint`
        can print it in the pane, where it stays put while the player types."""
        if text not in self.hints_shown:
            self.hints_shown.append(text)
        self.msg(text, kind, secs)
        self.write_runtime(hints=[markup.plain(h, self.hud.prefix) for h in self.hints_shown])

    def notice(self, text, kind="bad"):
        """Feedback a goal asked for. It usually lands while the player is reading their
        own shell output, so keep it with the hints rather than only flashing it."""
        self.show_hint(text, kind, FEEDBACK_SECS)

    def right_text(self):
        from .worlds import WORLDS
        d = self.data
        bits = [progress.rank(d, WORLDS), f"{d['xp']} XP"]
        if d["streak"] > 1:
            bits.append(f"streak ×{d['streak']}")
        if self.timer:
            start, par = self.timer
            el = int(time.time() - start)
            clock = f"⏱ {el // 60}:{el % 60:02d}"
            if par:
                clock += f" / par {par // 60}:{par % 60:02d}"
            bits.append(clock)
        return " · ".join(bits)

    def bell(self):
        if not self.data["settings"].get("bell", True):
            return
        s = self.snap
        if s and s.client and s.client.name.startswith("/dev/"):
            try:
                with open(s.client.name, "w") as f:
                    f.write("\a")
            except OSError:
                pass

    def wait_attached(self):
        s = self.snap or state.take(self.t)
        if s and s.attached:
            return s
        while True:
            s, _, _ = self.tick()
            if s.attached:
                return s

    def show_card(self, card_id=None, text=None):
        from . import cards
        s = self.wait_attached()
        if text is not None:
            path = os.path.join(paths.RUN_DIR, "card.json")
            with open(path, "w") as f:
                json.dump(text, f)
            arg = "--file " + shlex.quote(path)
            lines = cards.height_of(text)
        else:
            arg = shlex.quote(card_id)
            lines = cards.height_of(cards.CARDS[card_id])
        c = s.client
        w = max(40, min(86, c.width - 4))
        h = max(10, min(lines + 6, c.height - 4))
        cmd = "PYTHONPATH={} {} -m game.card {} --prefix {}".format(
            shlex.quote(paths.ROOT), shlex.quote(sys.executable), arg, shlex.quote(self.hud.prefix))
        old = self.base_msg
        self.msg("Reading a lesson card: press Enter to continue", "info")
        self.t.run("display-popup", "-c", c.name, "-w", w, "-h", h, "-E", cmd, timeout=None)
        self.msg(*old)
        self.snap = state.take(self.t)
        if self.snap is None:
            raise Quit()

    def save(self):
        progress.save(self.data)

    # ------------------------------------------------------------ steps & missions

    def run_step(self, mission, idx, step, ctx, title):
        if step.card:
            self.show_card(step.card)
        if step.setup:
            step.setup(ctx)
            time.sleep(0.15)
        s = state.take(self.t)
        if s is None:
            raise Quit()
        self.snap = s
        self.keylog.poll()  # forget keys pressed during setup
        ctx.s, ctx.prev, ctx.base = s, None, s
        ctx.actions, ctx.events = [], []
        ctx._said = None
        self.set_prompt(title, step.prompt, step.outside)
        self.flash_until = 0
        self.msg(IDLE_TIP)
        start = time.time()
        tier, hinted, shown = 0, False, False
        nagged_inside = False
        while True:
            s, acts, evs = self.tick()
            ctx.new_tick(s, acts, evs)
            for e in evs:
                if e.get("type") != "cmd":
                    continue
                cmd = e.get("cmd")
                if cmd == "hint":
                    if tier < len(step.hints):
                        hinted |= tier >= 1 or len(step.hints) == 1
                        self.show_hint(step.hints[tier])
                        tier += 1
                    elif self.hints_shown:
                        # out of new hints: repeat what's been said rather than dead-ending
                        self.show_hint(self.hints_shown[-1])
                    else:
                        self.msg("No hint for this one. `tmuse show` will do it for you to watch.", "hint", 6)
                elif cmd == "skip":
                    raise Skip()
                elif cmd == "reset":
                    raise Reset()
                elif cmd == "show":
                    shown = True
                    self.demo(step, ctx)
                    if step.setup:
                        ctx.base = ctx.s
                        ctx.actions = []
                elif cmd == "card":
                    card = step.card or mission.card
                    if card:
                        self.show_card(card)
                    else:
                        self.msg("No lesson card for this mission.", "info", 4)
            try:
                ok = step.goal(ctx)
            except Exception:
                log.exception("goal crashed for %s step %d", mission.id, idx)
                ok = False
            if ctx.feedback:
                self.notice(ctx.feedback[0], ctx.feedback[1])
                ctx.feedback = None
            if ok:
                self.msg(step.done or "Nice!", "ok", 3)
                time.sleep(0.9)
                return StepResult(hinted, shown)
            if step.outside and s and s.attached:
                if not nagged_inside:
                    # an outside step, but they're in tmux (e.g. attached early): point the way out
                    self.msg("This step happens outside tmux. Press `C-b d` to detach first.", "bad", 30)
                    nagged_inside = True
            else:
                nagged_inside = False
            if acts:
                self.coach(step, ctx, acts)
            el = time.time() - start
            if step.timeout_hints and step.hints:
                if tier == 0 and el > NUDGE_AFTER:
                    self.show_hint(step.hints[0])
                    tier = 1
                elif tier == 1 and el > HINT_AFTER and len(step.hints) > 1:
                    self.show_hint(step.hints[1])
                    tier, hinted = 2, True

    def coach(self, step, ctx, acts):
        for pred, text in step.mistakes:
            try:
                if pred(ctx):
                    self.msg(text, "bad", 7)
                    return
            except Exception:
                log.exception("mistake predicate crashed")
        if not step.expect:
            return
        off = [a for a in acts if a.kind not in step.expect and a.kind not in IGNORE]
        if off:
            kid, text = actions.NARRATION.get(off[0].kind, (None, off[0].kind))
            key = f" `{KEYS[kid].keys}`" if kid in KEYS else ""
            self.msg(f"That did: {text}{key}. Not quite what this step wants; try again!", "bad", 6)

    def demo(self, step, ctx):
        if not step.demo:
            self.show_hint("No demo here. The answer: " + (step.hints[-1] if step.hints else step.prompt))
            return
        self.msg("Watch the screen…", "info")
        time.sleep(0.8)
        for cmd in step.demo:
            self.t.run(*cmd)
            time.sleep(0.8)
        self.msg("That's how! Now you try.", "info", 4)
        time.sleep(1.5)
        if step.setup:
            step.setup(ctx)
            time.sleep(0.2)
            s = state.take(self.t)
            if s is None:
                raise Quit()
            self.snap = ctx.s = s

    def play_mission(self, m):
        """Play one mission. Returns stars (0 = skipped)."""
        if m.card:
            self.show_card(m.card)
        mem = {}
        ctx = Ctx(self.t, mem)
        t0 = time.time()
        hinted = shown = False
        n = len(m.steps)
        self.timer = (t0, m.par) if m.boss else None
        i = 0
        while i < n:
            title = f"{m.id} {m.title}" + (f" ({i + 1}/{n})" if n > 1 else "")
            try:
                r = self.run_step(m, i, m.steps[i], ctx, title)
            except Skip:
                self.timer = None
                self.msg(f"Skipped {m.id}. Come back to it from the World menu any time.", "info", 4)
                progress.record_mission(self.data, m, 0, 0, 0, True)
                self.save()
                time.sleep(1.2)
                return 0
            except Reset:
                while i > 0 and m.steps[i].setup is None:
                    i -= 1
                if i == 0:
                    mem.clear()
                self.msg("Reset! Starting the step again.", "info", 3)
                continue
            hinted |= r.hinted
            shown |= r.shown
            i += 1
        secs = time.time() - t0
        self.timer = None
        if shown:
            stars, xp = 1, 0
        elif hinted:
            stars, xp = 1, m.xp // 2
        elif secs <= m.par:
            stars, xp = 3, int(m.xp * 1.25)
        else:
            stars, xp = 2, m.xp
        gained = progress.record_mission(self.data, m, stars, xp, round(secs, 1), hinted or shown)
        self.save()
        self.bell()
        extra = "" if stars == 3 else ("  (hints halve XP)" if hinted and not shown else
                                        "  (beat par for ★★★)" if stars == 2 else "")
        self.hud.set(right=self.right_text())
        self.msg(f"Mission complete! {progress.stars_str(stars)}  +{gained} XP  in {secs:.0f}s{extra}", "ok", 4)
        time.sleep(2.2)
        return stars

    # ------------------------------------------------------------ modes

    def campaign(self):
        from .worlds import WORLDS, ORDER, mission_index
        from . import cards
        idx = mission_index(self.start) if self.start else self.first_incomplete(ORDER)
        while idx < len(ORDER):
            m = ORDER[idx]
            world = WORLDS[m.world]
            if world.missions[0] is m and world.card:
                self.show_card(world.card)
            before = progress.worlds_done(self.data, WORLDS)
            self.play_mission(m)
            after = progress.worlds_done(self.data, WORLDS)
            if after > before:
                self.show_card(text=cards.world_complete(world, self.data, WORLDS))
            if self.once:
                return
            idx += 1
        if all(progress.completed(self.data, m.id) for m in ORDER if not m.bonus):
            self.show_card("graduation")
        self.sandbox(finished=True)

    def first_incomplete(self, order):
        for i, m in enumerate(order):
            if not progress.completed(self.data, m.id) and not m.bonus:
                return i
        return 0

    def sandbox(self, finished=False):
        from . import setups
        self.mode = "sandbox"
        self.timer = None
        title = "SANDBOX"
        prompt = ("You've finished the campaign! Free play: try anything and I'll name every key."
                  if finished else "Free play: try anything and I'll name every key you use.")
        self.set_prompt(title, prompt)
        self.msg("Tip: `C-b ?` lists every key. `tmuse cheat` prints your cheat sheet.", "info")
        if not finished:
            ctx = Ctx(self.t, {})
            setups.reset(ctx)
        while True:
            s, acts, evs = self.tick()
            pressed = [a for a in acts if a.kind == "key"]
            if pressed:
                a = pressed[-1]
                self.msg(f"`{describe_key(a.info['key'], a.info['cmd'], s.prefix_key)}`  runs:  "
                         f"{a.info['cmd'][:70]}", "info", 8)
            for a in acts:
                if a.kind in actions.NARRATION and a.kind not in ("attach", "prefix"):
                    kid, text = actions.NARRATION[a.kind]
                    if pressed:
                        self.hud.set(prompt=text)
                    else:
                        key = KEYS[kid].keys if kid in KEYS else ""
                        self.msg(f"`{key}`  {text}" if key else text, "info", 8)

    def drills(self, review=False):
        from . import drills
        from .worlds import WORLDS
        drills.run(self, review=review, worlds=WORLDS)

    def main(self):
        log.info("engine start mode=%s start=%s", self.mode, self.start)
        # wait for the server
        for _ in range(50):
            if self.t.alive():
                break
            time.sleep(0.1)
        self.hud.install()
        self.hud.set(title="tmuse", prompt="Loading…", right=self.right_text())
        try:
            self.wait_attached()
            if self.mode == "campaign":
                self.campaign()
            elif self.mode == "sandbox":
                self.sandbox()
            elif self.mode == "dojo":
                self.drills()
            elif self.mode == "review":
                self.drills(review=True)
        except Quit:
            log.info("server gone; engine exiting")
        except Exception:
            log.exception("engine crashed")
            try:
                self.hud.set(title="tmuse", prompt="The game engine crashed, sorry! Details: ~/.tmuse/engine.log",
                             msg="Detach with `C-b d` and run ./tmuse again to resume.", kind="bad")
            except Exception:
                pass
        finally:
            self.save()


def main(argv):
    paths.ensure()
    logging.basicConfig(filename=paths.ENGINE_LOG, level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    args = [a for a in argv if not a.startswith("--")]
    mode = args[0] if args else "campaign"
    start = args[1] if len(args) > 1 else None
    Engine(Tmux(), mode, start, once="--once" in argv).main()


if __name__ == "__main__":
    main(sys.argv[1:])
