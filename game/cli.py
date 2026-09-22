"""The `tmuse` command.

Outside the game:   tmuse [play [MISSION] | dojo | review | sandbox | cheat | status | help]
Inside the game:    tmuse task | hint | skip | show | reset | card | edit | answer WORD | again | menu | cheat
"""
import json
import os
import subprocess
import sys
import time

from . import paths, progress
from .keys import KEYS

IN_GAME_HELP = """\
tmuse, in-game commands (type them in any shell pane):

  tmuse task           reprint the current task (and hints so far) in this pane
  tmuse hint           a hint (the first is free, later ones halve the XP)
  tmuse show           watch the game do it, then try yourself
  tmuse skip           skip this mission (come back later from the menu)
  tmuse reset          set the current step up again
  tmuse card           re-open the lesson card
  tmuse edit           open the practice config (World 7) in your editor
  tmuse answer WORD    answer a question the game asked
  tmuse again          another Dojo round
  tmuse cheat          print your cheat sheet
  tmuse menu           quit to the title menu (progress is saved)
"""

OUT_HELP = """\
usage: ./tmuse [command]

  (nothing)        title menu
  play [ID]        jump straight into the campaign (optionally at a mission, e.g. 2.3)
  dojo             60-second speed drills
  review           spaced-repetition review of keys you've learned
  sandbox          free play with live explanations
  cheat [--all]    print your cheat sheet (--all includes keys you haven't learned yet)
  status           your progress
"""

GAME_CMDS = {"hint", "skip", "show", "reset", "card", "again"}


def in_game():
    return os.environ.get("TMUSE_GAME") == "1"


def runtime():
    try:
        with open(paths.RUNTIME) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def show_task(before=None, wait=0.0):
    """Print the current task (and any hints so far) here in the pane, where it stays
    on screen while you type. The status bar only ever shows the newest line."""
    r = runtime()
    if wait:
        deadline = time.time() + wait
        while time.time() < deadline and r.get("hints", []) == (before or []):
            time.sleep(0.1)
            r = runtime()
    b = (lambda s: f"\x1b[1m{s}\x1b[0m") if sys.stdout.isatty() else (lambda s: s)
    title, prompt = r.get("title", ""), r.get("prompt", "")
    if not prompt:
        return False
    print(f"\n{b('▶ ' + title if title else '▶ task')}\n  {prompt}")
    for h in r.get("hints", []):
        print(f"  {b('»')} {h}")
    print()
    return True


def send(event):
    paths.ensure()
    event["t"] = time.time()
    with open(paths.EVENTS, "a") as f:
        f.write(json.dumps(event) + "\n")


def cheat_sheet(show_all=False, color=True):
    data = progress.load()
    learned = set(data["keys"])
    b = (lambda s: f"\x1b[1;38;5;214m{s}\x1b[0m") if color else (lambda s: s)
    dim = (lambda s: f"\x1b[38;5;244m{s}\x1b[0m") if color else (lambda s: s)
    out = ["tmux cheat sheet" + ("" if show_all else "  (keys you've learned; --all for everything)"),
           "C-b = hold Ctrl, press b, let go. Then press the next key.", ""]
    group = None
    for k in KEYS:
        mark = k.id in learned
        if not show_all and not mark:
            continue
        if k.group != group:
            group = k.group
            out.append(b(f"── {group} " + "─" * (50 - len(group))))
        line = f"  {k.keys:<22} {k.desc}"
        out.append(line if mark or not show_all else dim(line))
    if len(out) == 3:
        out.append("Nothing learned yet! Play a few missions, or use --all.")
    return "\n".join(out)


def status():
    from .worlds import WORLDS
    d = progress.load()
    print(f"Rank: {progress.rank(d, WORLDS)}   XP: {d['xp']}   Best streak: {d['best_streak']}   "
          f"Dojo best: {d['dojo_best']}")
    for w in WORLDS:
        done = sum(progress.completed(d, m.id) for m in w.missions)
        print(f"  World {w.num}  {w.title:<24} {done}/{len(w.missions)}")
    print(f"Keys due for review: {len(progress.due_keys(d))}")


def main(argv):
    cmd = argv[0] if argv else ""
    if cmd in ("-h", "--help", "help"):
        print(IN_GAME_HELP if in_game() else OUT_HELP)
        return
    if cmd == "cheat":
        text = cheat_sheet("--all" in argv, color=sys.stdout.isatty())
        print(text)
        return
    if cmd == "status":
        status()
        return
    if in_game():
        if cmd == "edit":
            # Rescue hatch for World 7: open the practice config without retyping its path.
            from .worlds.common import conf_path, ensure_conf
            ensure_conf()
            editor = os.environ.get("EDITOR") or "nano"
            os.execvp(editor, [editor, conf_path()])
        if cmd == "task":
            if not show_task():
                print("No task right now.")
            return
        if cmd in GAME_CMDS:
            before = runtime().get("hints", [])
            send({"type": "cmd", "cmd": cmd})
            if cmd == "hint":
                if not show_task(before, wait=2.5):
                    print("Hint on its way: look at the status bar.")
                return
            print({"skip": "Skipping…", "show": "Watch the screen!", "reset": "Resetting…",
                   "card": "Opening the card…", "again": "Here we go!"}[cmd])
        elif cmd == "answer":
            send({"type": "answer", "text": " ".join(argv[1:])})
            print("Answer sent: look at the status bar.")
        elif cmd in ("menu", "quit"):
            print("Back to the menu. Progress is saved.")
            subprocess.run(["tmux", "-L", paths.SOCKET, "kill-server"])
        else:
            print(IN_GAME_HELP)
        return
    from . import launcher
    if cmd in ("", "menu"):
        launcher.menu()
    elif cmd in ("play", "campaign"):
        launcher.play("campaign", argv[1] if len(argv) > 1 else None)
    elif cmd in ("dojo", "review", "sandbox"):
        launcher.play(cmd)
    else:
        print(OUT_HELP)
