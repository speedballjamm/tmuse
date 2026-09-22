from .common import Mission, Step, World, cur_name, fresh, names, reset, run_in, snap, windows


def nwin(c):
    return len(c.s.swindows())


def on_nth(k):
    """Active window is the k-th one created by the setup."""
    return lambda c: bool(c.s.window and c.s.window.id == c.mem["wids"][k])


def on(name):
    return lambda c: cur_name(c) == name and not c.s.mode


def rename_check(target):
    def goal(c):
        if cur_name(c) == target:
            return True
        a = c.last("rename-window")
        if a and a.info["new"] != target:
            c.say(f"Renamed to '{a.info['new']}', we want exactly **{target}**. `C-b ,` again "
                  "(Backspace or C-u clears the old name).")
        return False
    return goal


def treasure(c):
    windows("alpha", "bravo", "charlie")(c)
    bravo = snap(c).find_window("bravo")
    run_in(c, bravo.panes[0].id, "banner", "~~~ you found the TREASURE ~~~")


def far_window(c):
    reset(c)
    c.tmux.run("new-window", "-d", "-t", "tmuse:12", "-n", "far")
    snap(c)


def mission_control_goal(c):
    return names(c) == ["code", "server", "logs"]


WORLD = World(3, "Windows", card="windows", missions=[
    Mission("3.1", "New window", xp=50, par=20, steps=[
        Step("Create a new window: `C-b c`. Then look at the status bar at the very bottom.",
             setup=fresh,
             goal=lambda c: nwin(c) > len(c.base.swindows()),
             hints=["Prefix, then c (for create).", "`C-b c`"],
             expect=["new-window"], keys=["new-window"], demo=[["new-window"]],
             done="See 0:zsh 1:zsh*? The * marks the window you're in."),
    ]),
    Mission("3.2", "Next & previous", xp=50, par=30, steps=[
        Step("Three windows: 0 1 2 at the bottom, * = you. Go to the next: `C-b n`",
             setup=windows("", "", "", tags=True), goal=on_nth(1),
             hints=["Prefix, then n (next).", "`C-b n`"], keys=["next-window"], demo=[["next-window"]]),
        Step("Next again: `C-b n`", goal=on_nth(2), hints=["`C-b n`"]),
        Step("Now go back one: `C-b p` (previous)", goal=on_nth(1),
             hints=["`C-b p`"], keys=["prev-window"],
             done="n and p wrap around at the ends, too."),
    ]),
    Mission("3.3", "Jump by number", xp=50, par=25, steps=[
        Step("Four windows, numbered 0-3 in the status bar. Jump to window 3: `C-b 3`",
             setup=windows("", "", "", "", tags=True), goal=on_nth(3),
             hints=["Prefix, then the number key 3.", "`C-b 3`"],
             keys=["select-window"], demo=[["select-window", "-t", ":3"]]),
        Step("Now window 1: `C-b 1`", goal=on_nth(1), hints=["`C-b 1`"],
             done="Number keys are the fastest way around. Keep important stuff in 0-9!"),
    ]),
    Mission("3.4", "Name it", xp=50, par=40, steps=[
        Step("Rename this window to **code**: `C-b ,` then type code and press Enter.",
             setup=fresh, goal=rename_check("code"),
             hints=["The prompt is pre-filled with the old name. Delete it (Backspace, or C-u clears).",
                    "`C-b ,`  C-u  code  Enter"],
             keys=["rename-window"], demo=[["rename-window", "code"]],
             done="Named windows turn the status bar into a map."),
    ]),
    Mission("3.5", "Flip-flop", xp=50, par=30, steps=[
        Step("Go to **logs** (window 2): `C-b 2`",
             setup=windows("code", "server", "logs", tags=True), goal=on("logs"), hints=["`C-b 2`"]),
        Step("Flip back to the window you were just in: `C-b l` (lowercase L, for Last)", goal=on("code"),
             hints=["Prefix, then lowercase L (the letter, not the number 1).", "`C-b l`"], keys=["last-window"], demo=[["last-window"]]),
        Step("And flip again: `C-b l` (the letter L)", goal=on("logs"), hints=["`C-b l`, lowercase L"],
             done="The - in the status bar marks your 'last' window."),
    ]),
    Mission("3.6", "Window tree", xp=50, par=40, steps=[
        Step("Open the window tree: `C-b w`",
             setup=windows("code", "server", "logs"),
             goal=lambda c: c.s.mode == "tree-mode",
             hints=["Prefix, then w.", "`C-b w`"], keys=["window-tree"], demo=[["choose-tree", "-Zw"]]),
        Step("Use ↑ ↓ to highlight **server** and press Enter.",
             goal=on("server"),
             hints=["Windows are listed under the session. Arrow to 'server', Enter.",
                    "In the tree you can also press the number shown next to a window."],
             done="The tree shows every session and window, with previews."),
    ]),
    Mission("3.7", "Close a window", xp=50, par=25, steps=[
        Step("Kill the current window: `C-b &`, then `y`",
             setup=windows("one", "two", "three", tags=True),
             goal=lambda c: nwin(c) == 2,
             hints=["Prefix, then & (Shift+7). Confirm with y.", "`C-b &` y"],
             expect=["kill-window", "select-window"], keys=["kill-window"], demo=[["kill-window"]],
             done="Or close every pane in it: the window goes when its last pane does."),
    ]),
    Mission("3.8", "Treasure hunt", xp=60, par=45, bonus=True, steps=[
        Step("A window's screen says TREASURE. `C-b f`, type TREASURE, Enter, then ↓ to the match, Enter.",
             setup=treasure,
             goal=on("bravo"),
             hints=["find-window opens a tree showing only matching windows. Arrow down to it, Enter.",
                    "`C-b f` TREASURE Enter, ↓, Enter (the search is case-sensitive)"],
             keys=["find-window"],
             done="find-window searches window names and screen contents."),
    ]),
    Mission("3.9", "Reorder", xp=50, par=40, bonus=True, steps=[
        Step("Move this window to number 5: `C-b .` then type 5, Enter.",
             setup=windows("code", "server", "logs", active=2),
             goal=lambda c: bool(c.s.find_window("logs") and c.s.find_window("logs").index == 5),
             hints=["Prefix, then . (period). The prompt asks for a target index.", "`C-b .` 5 Enter"],
             keys=["move-window"], demo=[["move-window", "-t", ":5"]]),
    ]),
    Mission("3.10", "Beyond nine", xp=50, par=40, bonus=True, steps=[
        Step("Window 12 exists, but there's no 12 key! Use `C-b '` then type 12, Enter.",
             setup=far_window,
             goal=lambda c: bool(c.s.window and c.s.window.index == 12),
             hints=["Prefix, then the apostrophe '. It asks for an index.", "`C-b '` 12 Enter"],
             keys=["window-index"], demo=[["select-window", "-t", ":12"]]),
    ]),
    Mission("3.11", "BOSS: Mission Control", xp=150, par=120, boss=True, steps=[
        Step("BOSS! Make exactly 3 windows named **code**, **server**, **logs** (in that order).",
             setup=fresh, goal=mission_control_goal,
             hints=["`C-b ,` renames the current window, `C-b c` makes new ones.",
                    "Rename window 0 to code, `C-b c` + `C-b ,` server, `C-b c` + `C-b ,` logs"]),
        Step("Go to **server**!", goal=on("server")),
        Step("Go to **logs**!", goal=on("logs")),
        Step("Flip back to the last window!", goal=on("server"), hints=["`C-b l` (lowercase L)"]),
        Step("Rename **logs** to **tail**!",
             goal=lambda c: "tail" in names(c) and "logs" not in names(c),
             hints=["Go to logs first, then `C-b ,`"]),
        Step("Kill the **code** window!",
             goal=lambda c: "code" not in names(c) and len(names(c)) == 2,
             hints=["Go to code, then `C-b &` y"]),
    ]),
])
