from .common import Mission, Step, World, active_id, fresh, grid, npanes, panes_h, win

SPLIT_V_NOT_H = (lambda c: c.just("split-v"),
                 'That was `C-b "` (top/bottom). For side by side use `C-b %` (Shift+5). `C-b x` y removes a pane.')
SPLIT_H_NOT_V = (lambda c: c.just("split-h"),
                 "That was `C-b %` (side by side). For top/bottom use `C-b \"`. `C-b x` y removes a pane.")


def corner_is(which):
    return lambda c: bool(win(c) and not win(c).zoomed and active_id(c) == win(c).corner(which).id)


def visit_all(c):
    seen = c.mem.setdefault("seen", set())
    seen.add(active_id(c))
    return len(npanes_ids(c) - seen) == 0


def npanes_ids(c):
    return {p.id for p in win(c).panes}


def went_right(c):
    w = win(c)
    if active_id(c) == w.rightmost().id:
        a = c.last("select-pane")
        c.mem["back"] = a.info["old"] if a else c.base.pane.id
        return True
    return False


def went_left(c):
    return bool(win(c) and active_id(c) == win(c).leftmost().id)


def went_right_simple(c):
    return bool(win(c) and active_id(c) == win(c).rightmost().id)


WORLD = World(1, "Panes 101", card="panes", missions=[
    Mission("1.1", "Side by side", xp=50, par=20, steps=[
        Step("Split this pane into left | right: `C-b %`",
             setup=fresh,
             goal=lambda c: c.did("split-h") and npanes(c) >= 2,
             mistakes=[SPLIT_V_NOT_H], expect=["split-h"],
             hints=["Prefix first (Ctrl+b, let go), then the percent sign.", "`C-b` then Shift+5 (%)"],
             keys=["split-h"], demo=[["split-window", "-h"]],
             done="Two shells, side by side. Each pane is its own terminal."),
    ]),
    Mission("1.2", "Stacked", xp=50, par=20, steps=[
        Step('Split this pane top / bottom: `C-b "`',
             setup=fresh,
             goal=lambda c: c.did("split-v") and npanes(c) >= 2,
             mistakes=[SPLIT_H_NOT_V], expect=["split-v"],
             hints=["Prefix, then the double-quote key.", '`C-b` then Shift+\' (")'],
             keys=["split-v"], demo=[["split-window", "-v"]],
             done="Top and bottom. % and \" are the two splits; that's all there is."),
    ]),
    Mission("1.3", "Hop around", xp=50, par=25, steps=[
        Step("The active pane has the green border. Move LEFT: `C-b ←`",
             setup=panes_h(2, sel="right"),
             goal=went_left,
             hints=["Prefix, then the left arrow key.", "`C-b` then ←"],
             keys=["pane-nav"], demo=[["select-pane", "-L"]]),
        Step("And back RIGHT: `C-b →`",
             goal=went_right_simple,
             hints=["`C-b` then →"]),
    ]),
    Mission("1.4", "Four corners", xp=60, par=40, steps=[
        Step("Four panes! Go to the TOP-LEFT one: `C-b` + arrow keys",
             setup=grid(sel="br"),
             goal=corner_is("tl"),
             hints=["One prefix, then an arrow. Arrows repeat: `C-b ↑ ←` quickly works too.",
                    "From bottom-right: `C-b ↑` then `C-b ←`"],
             keys=["pane-nav"]),
        Step("Now the BOTTOM-RIGHT pane.", goal=corner_is("br"), hints=["`C-b ↓` then `C-b →`"]),
        Step("Now the TOP-RIGHT pane.", goal=corner_is("tr"), hints=["`C-b ↑`"]),
        Step("And finally BOTTOM-LEFT.", goal=corner_is("bl"), hints=["`C-b ↓` then `C-b ←`"],
             done="Tip: arrows are repeatable: after one `C-b` you can tap arrows quickly."),
    ]),
    Mission("1.5", "Round robin", xp=50, par=25, steps=[
        Step("Visit every pane using `C-b o` (next pane). Press it a few times.",
             setup=panes_h(3, sel="left"),
             goal=visit_all,
             hints=["Prefix, then the letter o. Repeat it.", "`C-b o`, `C-b o`, `C-b o`"],
             keys=["pane-next"], demo=[["select-pane", "-t", ":.+"]],
             done="`C-b o` cycles through panes in order: great when you don't care about direction."),
    ]),
    Mission("1.6", "Ping-pong", xp=50, par=30, steps=[
        Step("Go to the right-most pane (arrows or `C-b o`).",
             setup=panes_h(3, sel="left"),
             goal=went_right, hints=["`C-b →` twice, or `C-b o` twice."]),
        Step("Now jump straight back to the pane you were just in: `C-b ;`",
             goal=lambda c: active_id(c) == c.mem.get("back"),
             hints=["Prefix, then the semicolon key.", "`C-b ;` means last-pane: the one you were on before."],
             keys=["pane-last"], demo=[["last-pane"]],
             done="`C-b ;` flips between two panes, however far apart they are."),
    ]),
    Mission("1.7", "Clean up", xp=50, par=30, card="kill", steps=[
        Step("Close the active pane: `C-b x`, then `y` to confirm.",
             setup=panes_h(3),
             goal=lambda c: npanes(c) == 2,
             hints=["Prefix, x. tmux asks 'kill-pane? (y/n)' in the status bar: press y.",
                    "`C-b x` then y"],
             expect=["kill-pane"], keys=["kill-pane"], demo=[["kill-pane"]]),
        Step("Close another the shell way: type **exit** and press Enter.",
             goal=lambda c: npanes(c) == 1,
             hints=["Type exit in the active pane and press Enter."],
             keys=["exit"], done="When the program in a pane ends, the pane closes."),
    ]),
    Mission("1.8", "Numbered panes", xp=60, par=30, bonus=True, steps=[
        Step("Press `C-b q` to flash pane numbers, then quickly press **3** to jump to pane 3.",
             setup=grid(sel=0),
             goal=lambda c: bool(c.s.pane and c.s.pane.index == 3),
             hints=["The big numbers only show for about 1 second. `C-b q` then 3 straight away!",
                    "`C-b q` 3"],
             keys=["pane-numbers"], demo=[["select-pane", "-t", ":.3"]],
             done="In World 7 you can set display-panes-time to make the numbers stay longer."),
    ]),
    Mission("1.9", "BOSS: The Quad", xp=150, par=60, boss=True, steps=[
        Step("BOSS! Build a 2×2 grid of four panes. The clock is ticking!",
             setup=fresh,
             goal=lambda c: bool(win(c) and win(c).is_grid(2, 2) and not win(c).zoomed),
             hints=["Split side by side, then split each half top/bottom.",
                    '`C-b %`, then `C-b "`, then `C-b ←` and `C-b "`'],
             mistakes=[(lambda c: npanes(c) > 4, "Too many panes! Close extras with `C-b x` y.")]),
        Step("Visit ↖ TOP-LEFT", goal=corner_is("tl")),
        Step("Visit ↘ BOTTOM-RIGHT", goal=corner_is("br")),
        Step("Visit ↗ TOP-RIGHT", goal=corner_is("tr")),
        Step("Visit ↙ BOTTOM-LEFT", goal=corner_is("bl")),
    ]),
])
