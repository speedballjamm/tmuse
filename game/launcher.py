"""Title menu, starting the game's tmux server, and the outside-tmux practice prompt."""
import curses
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time

from . import cli, paths, progress
from .tmux import Tmux

LOGO = r"""
  _
 | |_ _ __ ___  _   _ ___  ___
 | __| '_ ` _ \| | | / __|/ _ \
 | |_| | | | | | |_| \__ \  __/
  \__|_| |_| |_|\__,_|___/\___|
""".strip("\n")

B = "\x1b[1m"
Y = "\x1b[38;5;214m"
C = "\x1b[38;5;117m"
G = "\x1b[38;5;78m"
DIM = "\x1b[38;5;244m"
R = "\x1b[0m"

OUTSIDE_TMUX = {"ls", "list-sessions", "a", "at", "attach", "attach-session", "new", "new-session",
                "kill-session", "has-session", "has", "rename-session", "rename", "kill-server",
                "list-windows", "lsw", "list-clients", "lsc", "info", "-V"}
ATTACHING = {"a", "at", "attach", "attach-session", "new", "new-session", ""}


# ------------------------------------------------------------------ checks

def tmux_version():
    try:
        out = subprocess.run(["tmux", "-V"], capture_output=True, text=True).stdout
    except OSError:
        return None
    m = re.search(r"(\d+)\.(\d+)", out)
    return (int(m.group(1)), int(m.group(2))) if m else (99, 0)


def preflight():
    v = tmux_version()
    if v is None:
        print("tmux isn't installed. On a Mac:  brew install tmux")
        return False
    if v < (3, 2):
        print(f"tmuse needs tmux 3.2 or newer (you have {v[0]}.{v[1]}). Try: brew upgrade tmux")
        return False
    cols, rows = shutil.get_terminal_size((80, 24))
    if cols < 80 or rows < 24:
        print(f"{Y}Your terminal is {cols}×{rows}. tmuse works best at 100×30 or larger.{R}")
        print("Make the window bigger (or zoom out), then press Enter…")
        input()
    if os.environ.get("TMUX"):
        print(f"{Y}You're already inside tmux!{R} Running tmux inside tmux (\"nesting\") works, but every")
        print("key would go to the OUTER tmux first. You'd have to press the prefix twice (C-b C-b).")
        print("Best: quit this tmux (or open a plain terminal window) and run ./tmuse there.")
        if input("Continue anyway? [y/N] ").strip().lower() != "y":
            return False
    return True


# ------------------------------------------------------------------ playing

def game_env():
    env = dict(os.environ)
    env.pop("TMUX", None)
    env.pop("TMUX_PANE", None)
    env["PATH"] = paths.ROOT + os.pathsep + env.get("PATH", "")
    env["TMUSE_GAME"] = "1"
    env["PYTHONPATH"] = paths.ROOT
    return env


def play(mode="campaign", start=None):
    if not preflight():
        return
    paths.ensure()
    t = Tmux()
    t.run("kill-server")
    env = game_env()
    cols, rows = shutil.get_terminal_size((100, 30))
    subprocess.run(["tmux", "-L", t.socket, "-f", paths.CONF, "new-session", "-d", "-s", "tmuse",
                    "-x", str(cols), "-y", str(rows - 1)], env=env, cwd=os.path.expanduser("~"))
    for f in (paths.RUNTIME, paths.EVENTS):
        try:
            os.remove(f)
        except OSError:
            pass
    args = [sys.executable, "-m", "game.engine", mode] + ([start] if start else [])
    log = open(paths.ENGINE_LOG, "a")
    # the engine's cwd becomes the start directory of windows it creates
    engine = subprocess.Popen(args, env=env, cwd=os.path.expanduser("~"), stdout=log, stderr=log,
                              start_new_session=True)
    # give the engine a moment to install the HUD
    for _ in range(30):
        if t.out("show", "-gv", "status-format[0]").find("@tmuse") >= 0:
            break
        time.sleep(0.1)
    subprocess.call(["tmux", "-L", t.socket, "attach"], env=env)
    while t.alive():
        if outside_prompt(t, env) == "quit":
            break
    t.run("kill-server")
    try:
        engine.wait(timeout=3)
    except subprocess.TimeoutExpired:
        engine.kill()
    print(f"\n{G}Progress saved.{R} Run ./tmuse to play again.\n")


def runtime():
    try:
        with open(paths.RUNTIME) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def outside_banner(t):
    rt = runtime()
    sessions = t.out("list-sessions", "-F", "#{session_name}").split()
    print()
    print(f"{C}──────────────────────── outside tmux ────────────────────────{R}")
    if sessions:
        print(f"You've {B}detached{R}. tmux is still running in the background with")
        print(f"your session{'s' if len(sessions) > 1 else ''}: {B}{', '.join(sessions)}{R}")
    else:
        print(f"Your last session ended (the last pane closed). The tmux {B}server{R} is still up,")
        print(f"but has no sessions. Start one with:  {B}tmux new{R}")
    print(f"{DIM}This is a practice prompt: it understands tmux commands like your real shell.{R}")
    if rt.get("prompt"):
        print(f"\n{Y}▶ {rt.get('title', '')}{R}  {rt['prompt']}")
    if rt.get("outside"):
        print(f"  {B}{rt['outside']}{R}")
    elif sessions:
        print(f"  To go back in:  {B}tmux attach{R}")
    print(f"{DIM}  (type menu to quit to the title screen){R}")


def await_engine(timeout=1.5):
    """After a detach, give the engine a moment to notice and move to the next step,
    so the banner doesn't show the step that was just finished."""
    try:
        seen = os.stat(paths.RUNTIME).st_mtime
    except OSError:
        return
    end = time.time() + timeout
    while time.time() < end:
        time.sleep(0.1)
        try:
            if os.stat(paths.RUNTIME).st_mtime != seen:
                time.sleep(0.1)
                return
        except OSError:
            return


def outside_prompt(t, env):
    """The practice shell shown while detached. Returns 'quit' when the player leaves."""
    await_engine()
    outside_banner(t)
    last_prompt = runtime().get("prompt")
    while True:
        if not t.alive():
            print("\nThe tmux server has stopped (kill-server ends every session). Back to the menu!")
            time.sleep(1.5)
            return "quit"
        rt = runtime()
        if rt.get("prompt") != last_prompt:
            last_prompt = rt.get("prompt")
            print(f"\n{G}✔{R} {Y}▶ {rt.get('title', '')}{R}  {rt.get('prompt', '')}")
            if rt.get("outside"):
                print(f"  {B}{rt['outside']}{R}")
        try:
            line = input(f"{G}you@outside{R} $ ").strip()
        except EOFError:
            return "quit"
        if not line:
            continue
        try:
            argv = shlex.split(line)
        except ValueError:
            print("Couldn't parse that (unbalanced quotes?).")
            continue
        if argv[0] in ("menu", "quit", "exit", "q"):
            ans = input("Quit to the title menu? Progress is saved. [Y/n] ").strip().lower()
            if ans in ("", "y", "yes"):
                return "quit"
            continue
        if argv[0] == "clear":
            print("\x1b[2J\x1b[H", end="")
            continue
        if argv[0] == "help":
            print("Try: tmux ls · tmux attach · tmux a -t NAME · tmux new -s NAME · "
                  "tmux kill-session -t NAME · menu")
            continue
        if argv[0] == "tmuse":
            cli.send({"type": "cmd", "cmd": argv[1]} if len(argv) > 1 and argv[1] in cli.GAME_CMDS
                     else {"type": "answer", "text": " ".join(argv[2:])} if len(argv) > 2 and argv[1] == "answer"
                     else {"type": "noop"})
            print("Sent.")
            continue
        if argv[0] != "tmux":
            print(f"{DIM}(practice prompt) In a real shell that would run {argv[0]}. Here, only tmux "
                  f"commands work, e.g. tmux ls, tmux attach. Type menu to quit.{R}")
            continue
        sub = argv[1] if len(argv) > 1 else ""
        if sub not in OUTSIDE_TMUX and sub not in ATTACHING:
            print(f"{DIM}(practice prompt) That tmux command isn't supported here. Try tmux ls, tmux attach, "
                  f"tmux new -s NAME, tmux kill-session -t NAME.{R}")
            continue
        cli.send({"type": "outside", "argv": argv})
        time.sleep(0.25)  # let the engine see it before an attach takes over the screen
        subprocess.call(["tmux", "-L", t.socket] + argv[1:], env=env)
        if sub in ATTACHING and t.alive() and not t.out("list-clients").strip():
            # we were attached and the player detached again (or the attach failed)
            await_engine()
            outside_banner(t)
            last_prompt = runtime().get("prompt")


# ------------------------------------------------------------------ menu

def world_unlocked(data, worlds, n):
    if data["settings"].get("unlock_all"):
        return True
    return progress.worlds_done(data, worlds) >= n


def continue_target(data, order):
    for m in order:
        if not progress.completed(data, m.id) and not m.bonus:
            return m
    return None


def menu():
    os.environ.setdefault("ESCDELAY", "25")  # curses waits 1s after Esc by default
    if not sys.stdout.isatty():
        print(cli.OUT_HELP)
        return
    while True:
        choice = curses.wrapper(_menu_screen)
        if choice is None:
            return
        kind, arg = choice
        if kind == "play":
            play(*arg)
        elif kind == "cheat":
            text = cli.cheat_sheet(show_all=True)
            pager = shutil.which("less")
            if pager:
                subprocess.run([pager, "-R"], input=text.encode())
            else:
                print(text)
                input("\nPress Enter…")


def _menu_screen(scr):
    from .worlds import ORDER, WORLDS
    curses.curs_set(0)
    curses.use_default_colors()
    curses.init_pair(1, 214, -1)   # orange
    curses.init_pair(2, 117, -1)   # cyan
    curses.init_pair(3, 78, -1)    # green
    curses.init_pair(4, 244, -1)   # grey
    curses.init_pair(5, 16, 214)   # selected
    ORANGE, CYAN, GREEN, GREY, SEL = (curses.color_pair(i) for i in range(1, 6))
    screen = "main"
    sel = 0
    world_sel = 0
    msg = ""
    while True:
        data = progress.load()
        due = len(progress.due_keys(data))
        scr.erase()
        h, w = scr.getmaxyx()

        def put(y, x, text, attr=0):
            if 0 <= y < h - 1 and x < w:
                try:
                    scr.addstr(y, x, text[:max(0, w - x - 1)], attr)
                except curses.error:
                    pass

        y = 1
        for line in LOGO.splitlines():
            put(y, 2, line, ORANGE | curses.A_BOLD)
            y += 1
        put(y, 3, "learn tmux by playing it", GREY)
        y += 2
        put(y, 3, f"Rank: {progress.rank(data, WORLDS)}", CYAN | curses.A_BOLD)
        put(y, 34, f"XP: {data['xp']}   Streak: {data['streak']}   Dojo best: {data['dojo_best']}", CYAN)
        y += 2
        if screen == "main":
            nxt = continue_target(data, ORDER)
            items = [
                ("play", ("campaign", nxt.id if nxt else None),
                 f"Continue: {nxt.id} {nxt.title}" if nxt else "Campaign complete! Replay from the start"),
                ("worlds", None, "World select"),
                ("play", ("dojo",), "Dojo: 60-second speed drills"),
                ("play", ("review",), f"Review: {due} key{'s' if due != 1 else ''} due"),
                ("play", ("sandbox",), "Sandbox: free play with live explanations"),
                ("cheat", None, "Cheat sheet"),
                ("settings", None, "Settings"),
                ("quit", None, "Quit"),
            ]
            for i, (_, _, label) in enumerate(items):
                put(y + i, 3, (" ▶ " if i == sel else "   ") + label + " ", SEL if i == sel else 0)
            y += len(items) + 1
            for wd in WORLDS:
                done = sum(progress.completed(data, m.id) for m in wd.missions)
                bar = "█" * done + "░" * (len(wd.missions) - done)
                lock = "" if world_unlocked(data, WORLDS, wd.num) else "  (locked)"
                put(y, 3, f"{wd.num} {wd.title:<24}", GREY if lock else 0)
                put(y, 30, bar, GREEN)
                put(y, 31 + len(bar), f"{done}/{len(wd.missions)}{lock}", GREY)
                y += 1
        elif screen == "worlds":
            put(y, 3, "Choose a world (Enter), Esc to go back", GREY)
            y += 1
            for i, wd in enumerate(WORLDS):
                ok = world_unlocked(data, WORLDS, wd.num)
                stars = sum(data["missions"].get(m.id, {}).get("stars", 0) for m in wd.missions)
                label = f"World {wd.num}: {wd.title:<26} ★ {stars}/{3 * len(wd.missions)}"
                put(y + i, 3, (" ▶ " if i == sel else "   ") + label + ("" if ok else "  locked") + " ",
                    SEL if i == sel else (GREY if not ok else 0))
            items = WORLDS
        elif screen == "missions":
            wd = WORLDS[world_sel]
            put(y, 3, f"World {wd.num}: {wd.title}. Enter plays from there, Esc goes back", GREY)
            y += 1
            items = wd.missions
            for i, m in enumerate(items):
                e = data["missions"].get(m.id, {})
                st = progress.stars_str(e.get("stars", 0))
                tag = " bonus" if m.bonus else ""
                best = f"  best {e['best']:.0f}s" if e.get("best") else ""
                label = f"{m.id:<5} {m.title:<30} {st}{tag}{best}"
                put(y + i, 3, (" ▶ " if i == sel else "   ") + label + " ", SEL if i == sel else 0)
        elif screen == "settings":
            items = [("bell", f"Bell on success: {'on' if data['settings'].get('bell', True) else 'off'}"),
                     ("unlock", f"Unlock all worlds: {'yes' if data['settings'].get('unlock_all') else 'no'}"),
                     ("reset", "Reset all progress"),
                     ("back", "Back")]
            for i, (_, label) in enumerate(items):
                put(y + i, 3, (" ▶ " if i == sel else "   ") + label + " ", SEL if i == sel else 0)
        if msg:
            put(h - 2, 3, msg, ORANGE)
        put(h - 1 if h > 1 else 0, 3, "↑↓ move · Enter choose · q quit", GREY)
        scr.refresh()
        k = scr.getch()
        msg = ""
        n = len(items)
        if k in (curses.KEY_UP, ord("k")):
            sel = (sel - 1) % n
        elif k in (curses.KEY_DOWN, ord("j")):
            sel = (sel + 1) % n
        elif k in (27, curses.KEY_BACKSPACE, 127, curses.KEY_LEFT) and screen != "main":
            back_to = {"missions": ("worlds", world_sel), "worlds": ("main", 1), "settings": ("main", 6)}
            screen, sel = back_to.get(screen, ("main", 0))
        elif k == ord("q") and screen == "main":
            return None
        elif k == ord("q"):
            screen, sel = {"worlds": ("main", 1), "settings": ("main", 6)}.get(screen, ("worlds", world_sel))
        elif k in (10, 13, curses.KEY_ENTER, curses.KEY_RIGHT):
            if screen == "main":
                kind, arg, _ = items[sel]
                if kind == "play":
                    return ("play", arg)
                if kind == "cheat":
                    return ("cheat", None)
                if kind == "quit":
                    return None
                screen, sel = kind, 0
            elif screen == "worlds":
                if world_unlocked(data, WORLDS, items[sel].num):
                    world_sel, screen, sel = sel, "missions", 0
                else:
                    msg = "Locked: finish the earlier worlds first (or Settings → Unlock all)."
            elif screen == "missions":
                return ("play", ("campaign", items[sel].id))
            elif screen == "settings":
                what = items[sel][0]
                if what == "bell":
                    data["settings"]["bell"] = not data["settings"].get("bell", True)
                    progress.save(data)
                elif what == "unlock":
                    data["settings"]["unlock_all"] = not data["settings"].get("unlock_all")
                    progress.save(data)
                elif what == "reset":
                    put(h - 2, 3, "Really erase all progress? Press y to confirm.", ORANGE | curses.A_BOLD)
                    scr.refresh()
                    if scr.getch() == ord("y"):
                        progress.save(progress.default())
                        msg = "Progress reset."
                else:
                    screen, sel = "main", 0
