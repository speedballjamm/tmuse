import sys
import time

from .. import paths
from .common import (Mission, Step, World, binding, conf_has, conf_shown, ensure_conf, in_editor, opt, reset,
                     shlex_quote)

CONF = conf_shown()
SOURCE = f"`C-b :` then  **source-file {CONF}**"
SET = r"^set(-option)?\s+(-\w*g\w*\s+)?"
SETW = r"^(setw|set-window-option|set(-option)?\s+-\w*w\w*)\s+(-\w*g\w*\s+)?"


def conf_setup(c):
    reset(c)
    ensure_conf()
    c.tmux.run("set", "-g", "mouse", "off")


# What the shell says when the path was typed on its own, or typed wrong.
RAN_IT = ("permission denied", "command not found", "is a directory")
NOT_THERE = ("no such file or directory", "does not exist", "directory does not exist")


def opened_editor(c):
    """The editor is open. Two slips are common and both look like a dead end, so read
    the shell's complaint back to the player instead of leaving them guessing."""
    if in_editor(c):
        return True
    p = c.s.pane
    if p:
        # Newest complaint wins: an earlier one is still on screen after a retry, and
        # explaining that one instead would send the player back down the wrong path.
        for line in reversed(c.capture(p.id).strip().splitlines()[-6:]):
            line = line.lower()
            if any(e in line for e in RAN_IT):
                c.say(f"That's the path on its own, so the shell tried to *run* it. "
                      f"Put the editor in front:  nano {CONF}")
                break
            if any(e in line for e in NOT_THERE):
                c.say("Check the dots: sandbox.tmux.conf is one filename, not a folder. "
                      "Or type  tmuse edit  and the game opens it for you.")
                break
    return False


def base_index_ok(c):
    return opt(c, "base-index") == "1" and opt(c, "pane-base-index", window=True) == "1"


def reload_bound(c):
    return "source-file" in binding(c, "r")


def status_changed(c):
    return opt(c, "status-style") not in ("", "bg=green,fg=black")


def graduate(c):
    """Offer to install the config for real, in a popup. Runs from the goal so the
    step's prompt is already on screen."""
    if not c.s.client:
        return False
    time.sleep(1)
    cmd = "PYTHONPATH={} {} -m game.graduate".format(shlex_quote(paths.ROOT), shlex_quote(sys.executable))
    c.tmux.run("display-popup", "-c", c.s.client.name, "-w", "86", "-h", "30", "-E", cmd, timeout=None)
    return True


WORLD = World(7, "Make It Yours", card="config", missions=[
    Mission("7.1", "Your config file", xp=70, par=120, card="editor", steps=[
        Step(f"Open the practice config in an editor: type  **nano {CONF}**",
             setup=conf_setup, goal=opened_editor,
             hints=["Type it in the shell and press Enter — the word nano first, then the path. (vim works too.)",
                    "Careful with the dots: sandbox.tmux.conf is one filename, not a folder. "
                    "Stuck? `tmuse edit` opens it for you."]),
        Step("Add the line  **set -g mouse on**  then save & exit (nano: `C-o` Enter, then `C-x`).",
             goal=lambda c: conf_has(SET + r"mouse\s+on") and not in_editor(c),
             hints=["Type the line on its own row. `C-o` Enter saves, `C-x` quits.",
                    "Saved but the game didn't notice? Check the spelling: set -g mouse on — and "
                    "that you're editing " + CONF + " (quit the editor and run `tmuse edit` to be sure)."],
             keys=["conf-set"]),
        Step(f"The file does nothing until tmux reads it. Load it: {SOURCE}",
             goal=lambda c: c.s.options.get("mouse") == "on",
             hints=["Tab completes paths in the prompt too."], keys=["source"],
             done="Loaded! The mouse is on. Configs are just commands, one per line."),
    ]),
    Mission("7.2", "Count from 1", xp=60, par=120, steps=[
        Step("Windows start at 0, far from the 1 key. Add  **set -g base-index 1**  and  "
             "**setw -g pane-base-index 1**",
             setup=conf_setup,
             goal=lambda c: conf_has(SET + r"base-index\s+1") and conf_has(SETW + r"pane-base-index\s+1")
             and not in_editor(c),
             hints=[f"nano {CONF}, add both lines, `C-o` Enter `C-x`."]),
        Step(f"Load it: {SOURCE}", goal=base_index_ok,
             done="New windows now count from 1. (Existing ones keep their numbers.)"),
    ]),
    Mission("7.3", "A reload key", xp=70, par=150, steps=[
        Step(f"Typing source-file is tedious. Add  **bind r source-file {CONF}**  and load it once.",
             setup=conf_setup, goal=reload_bound,
             hints=[f"Add the line, save, then `C-b :` source-file {CONF}"], keys=["conf-bind"]),
        Step("Test it: add  **set -g status-style bg=colour22**  (any colour 0-255), save, press `C-b r`",
             goal=status_changed,
             hints=["Save the file, leave the editor (or use another pane), then `C-b r`."],
             done="Edit, save, `C-b r`: your new config loop."),
    ]),
    Mission("7.4", "More history", xp=50, par=90, steps=[
        Step("tmux remembers 2000 lines per pane. Add  **set -g history-limit 50000**, save, `C-b r`",
             setup=lambda c: ensure_conf(),
             goal=lambda c: int(c.s.options.get("history-limit", "0") or 0) >= 10000,
             hints=["Same routine: edit, save, `C-b r`."],
             done="More scrollback for copy mode. Applies to new panes."),
    ]),
    Mission("7.5", "Friendlier splits", xp=60, par=120, bonus=True, steps=[
        Step("Add  **bind | split-window -h**  and  **bind - split-window -v**, save, `C-b r`",
             setup=lambda c: ensure_conf(),
             goal=lambda c: "split-window" in binding(c, "|") and "split-window" in binding(c, "-"),
             hints=["Two lines, save, reload with `C-b r`."]),
        Step("Try your new key: `C-b |`", goal=lambda c: c.did("split-h"),
             done="| looks like a vertical split, - like a horizontal one. Easier to remember!"),
    ]),
    Mission("7.6", "vi-style copying", xp=60, par=120, bonus=True, steps=[
        Step("Add  **bind -T copy-mode-vi v send -X begin-selection**  and  "
             "**bind -T copy-mode-vi y send -X copy-selection-and-cancel**, reload",
             setup=lambda c: ensure_conf(),
             goal=lambda c: "begin-selection" in binding(c, "v", "copy-mode-vi")
             and "copy-selection" in binding(c, "y", "copy-mode-vi"),
             hints=["Copy mode now works like vim's visual mode: v to select, y to yank."]),
    ]),
    Mission("7.7", "A new prefix", xp=70, par=150, bonus=True, card="prefix_change", steps=[
        Step("Add  **set -g prefix C-a**,  **unbind C-b**,  **bind C-a send-prefix**, then reload",
             setup=lambda c: ensure_conf(),
             goal=lambda c: c.s.options.get("prefix") == "C-a",
             hints=["Three lines. Reload with `C-b r` (the old prefix works until the reload finishes)."]),
        Step("Your prefix is now C-a! Make a window with it: C-a then c",
             goal=lambda c: c.did("new-window"),
             done="The game now shows your new prefix everywhere."),
    ]),
    Mission("7.8", "Take it home", xp=50, par=600, steps=[
        Step("Your config is ready. Want it in your real ~/.tmux.conf? (a popup will ask)",
             goal=graduate),
    ]),
])
