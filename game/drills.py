"""Dojo (60-second speed drills) and Review (spaced repetition).

Each drill is a quick prompt ("Zoom!") with a setup that nudges the sandbox
into a state where the prompt makes sense, and a goal to detect success.
"""
import random
import time

from . import progress, state
from .keys import BY_ID as KEYS
from .model import Ctx
from .setups import reset, snap

WORDS = ["api", "db", "notes", "build", "logs", "docs", "tests", "web", "vim", "htop"]
BASICS = ["split-h", "split-v", "pane-nav", "zoom", "new-window", "next-window", "kill-pane"]
ROUND_SECS = 60


class Drill:
    def __init__(self, kid, prompt, goal, setup=None):
        self.kid, self.prompt, self.goal, self.setup = kid, prompt, goal, setup


# --- sandbox helpers ----------------------------------------------------------------

def norm(c):
    """Leave modes, unzoom, desync, and keep things from growing without bound."""
    t = c.tmux
    s = snap(c)
    if s is None or not s.window or not s.session:
        reset(c)
        return snap(c)
    p = s.pane
    if p and p.mode in ("copy-mode", "view-mode"):
        t.run("send-keys", "-t", p.id, "-X", "cancel")
    elif p and p.mode:
        t.run("send-keys", "-t", p.id, "q")
    if s.window.zoomed:
        t.run("resize-pane", "-Z", "-t", s.window.id)
    if s.window.sync:
        t.run("setw", "-t", s.window.id, "synchronize-panes", "off")
    if len(s.swindows()) > 5 or len(s.window.panes) > 5 or s.window.panes and min(
            p.width for p in s.window.panes) < 12:
        reset(c)
    return snap(c)


def need_panes(c, n):
    s = norm(c)
    for _ in range(n - len(s.window.panes)):
        c.tmux.run("split-window", "-d", "-h", "-t", s.window.id)
        c.tmux.run("select-layout", "-t", s.window.id, "tiled")
    return snap(c)


def need_windows(c, n):
    s = norm(c)
    for _ in range(n - len(s.swindows())):
        c.tmux.run("new-window", "-d", "-t", f"{s.session}:")
    return snap(c)


def neighbour_dirs(w, a):
    dirs = {}
    for p in w.panes:
        if p.id == a.id:
            continue
        vo = p.top < a.bottom and a.top < p.bottom
        ho = p.left < a.right and a.left < p.right
        if vo and p.right < a.left + 1:
            dirs["LEFT"] = "←"
        if vo and p.left >= a.right:
            dirs["RIGHT"] = "→"
        if ho and p.bottom < a.top + 1:
            dirs["UP"] = "↑"
        if ho and p.top >= a.bottom:
            dirs["DOWN"] = "↓"
    return dirs


# --- the drills ---------------------------------------------------------------------

def d_split(kid, how, word):
    def setup(c):
        norm(c)
    return Drill(kid, f"Split {word}!", lambda c: c.did(how), setup)


def d_nav(rng):
    def setup(c):
        s = need_panes(c, 2)
        dirs = neighbour_dirs(s.window, s.pane)
        d = rng.choice(sorted(dirs))
        c.mem["dir"] = d.lower()
        c.mem["prompt"] = f"Move one pane {d}!  ({dirs[d]})"
    d = Drill("pane-nav", "", lambda c: any(a.kind == "select-pane" and a.info["dir"] == c.mem["dir"]
                                            for a in c.actions), setup)
    return d


def d_simple(kid, prompt, goal, panes=1, windows=1):
    def setup(c):
        need_panes(c, panes)
        if windows > 1:
            need_windows(c, windows)
    return Drill(kid, prompt, goal, setup)


def d_last_pane():
    def setup(c):
        s = need_panes(c, 2)
        c.mem["back"] = s.pane.id
        other = [p for p in s.window.panes if p.id != s.pane.id][0]
        c.tmux.run("select-pane", "-t", other.id)
    return Drill("pane-last", "Back to the previous pane!", lambda c: c.s.pane.id == c.mem["back"], setup)


def d_unzoom():
    def setup(c):
        s = need_panes(c, 2)
        c.tmux.run("resize-pane", "-Z", "-t", s.window.id)
    return Drill("zoom", "Unzoom!", lambda c: c.s.window and not c.s.window.zoomed, setup)


def d_nextwin(kid, step, word):
    def setup(c):
        s = need_windows(c, 3)
        ws = s.swindows()
        i = [w.id for w in ws].index(s.window.id)
        c.mem["target"] = ws[(i + step) % len(ws)].id
    return Drill(kid, f"{word} window!", lambda c: c.s.window.id == c.mem["target"], setup)


def d_selwin(rng):
    def setup(c):
        s = need_windows(c, 3)
        choices = [w for w in s.swindows() if w.id != s.window.id and w.index <= 9]
        w = rng.choice(choices)
        c.mem["target"] = w.id
        c.mem["prompt"] = f"Go to window {w.index}!"
    return Drill("select-window", "", lambda c: c.s.window.id == c.mem["target"], setup)


def d_lastwin():
    def setup(c):
        s = need_windows(c, 2)
        c.mem["back"] = s.window.id
        other = [w for w in s.swindows() if w.id != s.window.id][0]
        c.tmux.run("select-window", "-t", other.id)
    return Drill("last-window", "Back to the last window!", lambda c: c.s.window.id == c.mem["back"], setup)


def d_rename_window(rng):
    word = rng.choice(WORDS)
    return Drill("rename-window", f"Rename this window to '{word}'!",
                 lambda c: c.s.window and c.s.window.name == word, lambda c: norm(c))


def d_rename_session(rng):
    word = rng.choice(WORDS)
    return Drill("rename-session", f"Rename this session to '{word}'!",
                 lambda c: c.s.session == word, lambda c: norm(c))


def d_prompt_window(rng):
    word = rng.choice(WORDS) + str(rng.randint(2, 99))
    return Drill("command-prompt", f"Use `C-b :` to make a window named '{word}'!",
                 lambda c: bool(c.s.find_window(word)), lambda c: norm(c))


def d_session_cycle():
    def setup(c):
        s = norm(c)
        if len(s.sessions) < 2:
            c.tmux.run("new-session", "-d", "-s", "side")
    return Drill("session-cycle", "Switch to the next session!", lambda c: c.did("switch-session"), setup)


def make(kid, rng):
    n = lambda c: len(c.s.window.panes) if c.s.window else 0
    table = {
        "split-h": lambda: d_split("split-h", "split-h", "side by side"),
        "split-v": lambda: d_split("split-v", "split-v", "top / bottom"),
        "pane-nav": lambda: d_nav(rng),
        "pane-next": lambda: d_simple("pane-next", "Next pane (`C-b o`)!", lambda c: c.did("select-pane"), 3),
        "pane-last": d_last_pane,
        "kill-pane": lambda: d_simple("kill-pane", "Kill a pane!", lambda c: n(c) < len(c.base.window.panes), 3),
        "zoom": lambda: rng.choice([
            lambda: d_simple("zoom", "Zoom!", lambda c: c.s.window and c.s.window.zoomed, 2), d_unzoom])(),
        "resize": lambda: d_simple("resize", "Resize a pane!", lambda c: c.did("resize", "layout"), 2),
        "swap": lambda: d_simple("swap", "Swap two panes!", lambda c: c.did("swap"), 2),
        "rotate": lambda: d_simple("rotate", "Rotate the panes!", lambda c: c.did("swap"), 3),
        "layout-next": lambda: d_simple("layout-next", "Next layout!", lambda c: c.did("layout", "resize"), 3),
        "break-pane": lambda: d_simple("break-pane", "Break this pane out into a window!",
                                       lambda c: c.did("break-pane"), 2),
        "new-window": lambda: d_simple("new-window", "New window!", lambda c: c.did("new-window")),
        "next-window": lambda: d_nextwin("next-window", 1, "Next"),
        "prev-window": lambda: d_nextwin("prev-window", -1, "Previous"),
        "select-window": lambda: d_selwin(rng),
        "last-window": d_lastwin,
        "rename-window": lambda: d_rename_window(rng),
        "kill-window": lambda: d_simple("kill-window", "Kill this window!", lambda c: c.did("kill-window"), 1, 2),
        "window-tree": lambda: d_simple("window-tree", "Open the window tree!",
                                        lambda c: c.s.mode == "tree-mode"),
        "session-tree": lambda: d_simple("session-tree", "Open the session tree!",
                                         lambda c: c.s.mode == "tree-mode"),
        "rename-session": lambda: d_rename_session(rng),
        "session-cycle": d_session_cycle,
        "copy-mode": lambda: d_simple("copy-mode", "Enter copy mode!", lambda c: c.s.mode == "copy-mode"),
        "copy-pgup": lambda: d_simple("copy-pgup", "Copy mode + page up in one move!",
                                      lambda c: c.s.mode == "copy-mode" and c.s.pane.scroll > 0),
        "clock": lambda: d_simple("clock", "Show the clock!", lambda c: c.s.mode == "clock-mode"),
        "list-keys": lambda: d_simple("list-keys", "List all key bindings!", lambda c: c.s.mode == "view-mode"),
        "messages": lambda: d_simple("messages", "Show the message log!", lambda c: c.s.mode == "view-mode"),
        "command-prompt": lambda: d_prompt_window(rng),
        "sync": lambda: d_simple("sync", "Synchronize panes ON!", lambda c: c.s.window and c.s.window.sync, 2),
    }
    f = table.get(kid)
    return f() if f else None


DRILLABLE = ["split-h", "split-v", "pane-nav", "pane-next", "pane-last", "kill-pane", "zoom", "resize", "swap",
             "rotate", "layout-next", "break-pane", "new-window", "next-window", "prev-window", "select-window",
             "last-window", "rename-window", "kill-window", "window-tree", "session-tree", "rename-session",
             "session-cycle", "copy-mode", "copy-pgup", "clock", "list-keys", "messages", "command-prompt", "sync"]


# --- the loop -----------------------------------------------------------------------

def attempt(engine, drill, reveal_after, give_up_after, deadline=None):
    """Run one drill. Returns seconds taken, or None if it timed out / was revealed."""
    ctx = Ctx(engine.t, {})
    if drill.setup:
        drill.setup(ctx)
        time.sleep(0.1)
    s = state.take(engine.t)
    if s is None:
        from .engine import Quit
        raise Quit()
    engine.snap = ctx.s = ctx.base = s
    prompt = drill.prompt or ctx.mem.get("prompt", "")
    engine.hud.set(prompt=prompt)
    engine.msg("")
    start = time.time()
    revealed = False
    while True:
        s, acts, evs = engine.tick()
        ctx.new_tick(s, acts, evs)
        for e in evs:
            if e.get("type") == "cmd" and e.get("cmd") in ("skip", "hint", "show"):
                give_up_after = 0
        el = time.time() - start
        try:
            ok = drill.goal(ctx)
        except Exception:
            ok = False
        if ok:
            return (el, revealed)
        if not revealed and el > reveal_after:
            revealed = True
            engine.msg(f"The key: `{KEYS[drill.kid].keys}`", "hint")
        if el > give_up_after or (deadline and time.time() > deadline):
            return (None, True)


def run(engine, review=False, worlds=None):
    data = engine.data
    rng = random.Random()
    if review:
        return run_review(engine, data, rng)
    while True:
        pool = [k for k in data["keys"] if k in DRILLABLE] or []
        note = ""
        if len(pool) < 4:
            pool = BASICS
            note = " (warm-up set: finish more missions to unlock more)"
        run_dojo(engine, data, rng, pool, note)
        engine.hud.set(title="DOJO", prompt="Round over! Type  **tmuse again**  for another round.")
        engine.msg("Or `tmuse menu` to go back to the title screen.", "info")
        while True:
            _, _, evs = engine.tick()
            if any(e.get("type") == "cmd" and e.get("cmd") in ("again", "skip") for e in evs):
                break


def run_dojo(engine, data, rng, pool, note):
    engine.mode = "dojo"
    engine.show_card(text={"title": "Dojo: 60-second drills", "body": f"""\
Prompts flash up in the status bar: **Zoom!**, **New window!**, **Split
top / bottom!** Do each one as fast as you can.

  • quick answers (under 4s) build a **combo** multiplier
  • stuck? after 5 seconds the key is shown (fewer points)
  • `tmuse skip` in a shell skips a prompt

Keys in play: {len(pool)}{note}
Best score so far: **{data.get('dojo_best', 0)}**
"""})
    reset(Ctx(engine.t, {}))
    score, combo, last = 0, 1, None
    end = time.time() + ROUND_SECS
    engine.timer = None
    engine.hud.set(title="DOJO")
    solved = 0
    while time.time() < end:
        kid = rng.choice([k for k in pool if k != last] or pool)
        last = kid
        drill = make(kid, rng)
        if not drill:
            continue
        left = lambda: max(0, int(end - time.time()))
        engine.hud.set(right=f"⏱ {left()}s · score {score} · combo ×{combo}")
        el, revealed = attempt(engine, drill, 5, 15, deadline=end)
        if el is None:
            combo = 1
            continue
        solved += 1
        pts = 25 if revealed else 100 * combo
        score += pts
        combo = min(8, combo + 1) if (el < 4 and not revealed) else 1
        engine.msg(f"+{pts}" + ("  COMBO!" if combo > 2 else ""), "ok", 1)
        engine.hud.set(right=f"⏱ {left()}s · score {score} · combo ×{combo}")
    best = data.get("dojo_best", 0)
    new_best = score > best
    data["dojo_best"] = max(best, score)
    data["xp"] += score // 50
    engine.save()
    engine.bell()
    engine.show_card(text={"title": "Time!", "body": f"""\
  Score:    **{score}**{'   NEW PERSONAL BEST!' if new_best else ''}
  Solved:   {solved} prompts
  Best:     {data['dojo_best']}
  XP:       +{score // 50}
"""})


def run_review(engine, data, rng):
    engine.mode = "review"
    due = [k for k in progress.due_keys(data) if k in DRILLABLE][:12]
    if not due:
        engine.show_card(text={"title": "Review", "body": """\
Nothing is due for review right now. Nice!

Keys come back for review after 1, 3, 7 and 21 days, sooner
if you fumbled them. Finish more missions to add keys.

Dropping you into the sandbox instead.
"""})
        return engine.sandbox()
    engine.show_card(text={"title": "Review", "body": f"""\
**{len(due)}** keys are due. For each prompt, do it from memory.

  • get it before the key is revealed (10s) and it moves up a box
    and comes back later
  • miss it and it drops to box 1 and comes back sooner
"""})
    reset(Ctx(engine.t, {}))
    engine.hud.set(title="REVIEW")
    right = 0
    for i, kid in enumerate(due):
        engine.hud.set(right=f"{i + 1} / {len(due)} · {right} right")
        drill = make(kid, rng)
        el, revealed = attempt(engine, drill, 10, 40)
        ok = el is not None and not revealed
        right += ok
        progress.learn_key(data, kid, ok=ok)
        engine.msg("Got it!" if ok else f"That one was `{KEYS[kid].keys}`: it'll come back soon.",
                   "ok" if ok else "hint", 2)
        time.sleep(0.8)
    engine.save()
    engine.show_card(text={"title": "Review done", "body": f"""\
  You knew **{right}** of {len(due)}.

  Missed keys come back tomorrow; known ones get spaced further out.
  Come back daily for a couple of minutes: that's how it sticks.
"""})
    engine.sandbox()
