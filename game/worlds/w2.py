from .common import (MAC_ARROWS, Mission, Step, World, active_id, fresh, grid, is_main_vertical, label, npanes, panes_h,
                     reset, select, snap, split, win)


def zoomed(c):
    return bool(win(c) and win(c).zoomed)


def labelled(n, sel="left"):
    def setup(c):
        reset(c)
        split(c, n, "h")
        label(c, "ABCD"[:n])
        s = snap(c)
        ordered = sorted(s.window.panes, key=lambda p: p.left)
        c.mem["ids"] = {name: p.id for name, p in zip("ABCD", ordered)}
        select(c, sel)
    return setup


def leftmost_is(name):
    return lambda c: bool(win(c) and win(c).leftmost().id == c.mem["ids"][name])


def resize_setup(c):
    panes_h(2, sel="left")(c)
    snap(c)
    c.mem["w0"] = win(c).leftmost().width


def left_width(c):
    return win(c).leftmost().width if win(c) else 0


def seen_layouts(c):
    seen = c.mem.setdefault("layouts", set())
    w = win(c)
    if w and not w.zoomed:
        seen.add(w.layout.split(",", 1)[-1])
    return len(seen) >= 4


def main_vertical_ok(c):
    return is_main_vertical(win(c), 4)


def wide_left(c):
    w = win(c)
    return is_main_vertical(w, 4) and w.leftmost().width > w.width / 2 + 1


def zoom_br(c):
    w = win(c)
    if not w:
        return False
    if not w.zoomed:
        c.mem["br"] = w.corner("br").id
        return False
    if active_id(c) == c.mem.get("br"):
        return True
    c.say("That's not the bottom-right pane. Unzoom (`C-b z`), move to D, and zoom again.")
    return False


def broke_out(c):
    return c.did("break-pane") or (len(c.s.swindows()) > len(c.base.swindows()))


WORLD = World(2, "Pane Power", card="pane_power", missions=[
    Mission("2.1", "Zoom", xp=50, par=20, steps=[
        Step("Zoom the active pane to full size: `C-b z`",
             setup=panes_h(3, sel=1),
             goal=zoomed, expect=["zoom"],
             hints=["Prefix, then z.", "`C-b z`"], keys=["zoom"], demo=[["resize-pane", "-Z"]]),
        Step("The other panes are hidden, not gone (see the Z in the status bar). Unzoom: `C-b z`",
             goal=lambda c: not zoomed(c), hints=["Same key again: `C-b z`"],
             done="Zoom is a favourite: focus on one pane, then pop back out."),
    ]),
    Mission("2.2", "Resize", xp=60, par=40, card="resize", steps=[
        Step("Make the LEFT pane wider: `C-b :` then type  resize-pane -R 10  Enter"
             if MAC_ARROWS else
             "Make the LEFT pane wider: `C-b C-→` (hold Ctrl, tap → several times)",
             setup=resize_setup,
             goal=lambda c: left_width(c) >= c.mem["w0"] + 5,
             hints=["macOS uses Ctrl+←/→ to switch Spaces, so `C-b C-→` never gets to tmux. Use the command prompt:"
                    " `C-b :` resize-pane -R 10 Enter",
                    "`C-b :`  resize-pane -R 10  Enter.  (-R means move the border right)"]
             if MAC_ARROWS else
             ["Hold Ctrl, tap b, keep holding Ctrl and tap → five or more times.",
              "Nothing happening? Your OS may be taking Ctrl+→. Use `C-b :` resize-pane -R 10"],
             keys=["resize"], demo=[["resize-pane", "-R", "10"]]),
        Step("Now make it narrower than it started: `C-b :` resize-pane -L 15"
             if MAC_ARROWS else
             "Now make it narrower than it started: `C-b C-←`",
             goal=lambda c: left_width(c) <= c.mem["w0"] - 3,
             hints=["`C-b :` then  resize-pane -L 15  Enter.  (-L = left)"]
             if MAC_ARROWS else
             ["Hold Ctrl: b ← ← ← ← ← ← ← ←", "Or `C-b :` resize-pane -L 15"],
             done="-L -R -U -D work for resize-pane in any direction."
                  + ("  To get `C-b C-→` back: System Settings → Keyboard → Keyboard Shortcuts → Mission Control,"
                     " untick Move left/right a space." if MAC_ARROWS else "")),
    ]),
    Mission("2.3", "Swap", xp=50, par=25, steps=[
        Step("Swap the panes so A ends up on the right: `C-b }` (or `C-b {`)",
             setup=labelled(2),
             goal=lambda c: bool(win(c) and win(c).rightmost().id == c.mem["ids"]["A"]),
             hints=["Prefix, then the curly brace } (Shift+]).", "`C-b }` swaps with the next pane."],
             keys=["swap"], demo=[["swap-pane", "-D"]],
             done="The panes swapped places. Their contents came along."),
    ]),
    Mission("2.4", "Rotate", xp=50, par=30, bonus=True, steps=[
        Step("Rotate all three panes one spot: `C-b C-o`",
             setup=labelled(3),
             goal=lambda c: bool(win(c) and not leftmost_is("A")(c)),
             hints=["Hold Ctrl for both: Ctrl+b then Ctrl+o.", "`C-b C-o`"],
             keys=["rotate"], demo=[["rotate-window"]]),
        Step("Keep rotating (`C-b C-o`, or `C-b M-o` backwards) until A is on the left again.",
             goal=leftmost_is("A"), hints=["`C-b C-o` again, and again."]),
    ]),
    Mission("2.5", "Layouts", xp=60, par=40, steps=[
        Step("Cycle through the preset layouts with `C-b Space`. Try it 4 times.",
             setup=panes_h(4),
             goal=seen_layouts,
             hints=["Prefix, then the space bar. Repeat.", "`C-b Space` ×4"],
             keys=["layout-next"], demo=[["next-layout"]]),
        Step("Keep pressing `C-b Space` until you get the neat 2×2 grid (tiled).",
             goal=lambda c: bool(win(c) and win(c).is_grid(2, 2)),
             hints=["Five layouts in a loop: keep going."],
             done="Layouts rearrange panes without closing anything."),
    ]),
    Mission("2.6", "Layouts by name", xp=60, par=40, bonus=True, card="layouts", steps=[
        Step("Stack every pane top-to-bottom: `C-b M-2` (even-vertical)",
             setup=grid(),
             goal=lambda c: bool(win(c) and win(c).orientation() == "top-bottom"),
             hints=["M- means Option/Meta. See the card for Mac settings (`tmuse card`).",
                    "No Meta key? `C-b :` select-layout even-vertical"],
             keys=["layout-pick"], demo=[["select-layout", "even-vertical"]]),
        Step("Now one big pane on the left: `C-b M-4` (main-vertical)",
             goal=main_vertical_ok,
             hints=["`C-b M-4`, or `C-b :` select-layout main-vertical"]),
    ]),
    Mission("2.7", "Break out", xp=50, par=25, steps=[
        Step("Move the active pane into its own brand-new window: `C-b !`",
             setup=panes_h(2),
             goal=broke_out,
             hints=["Prefix, then ! (Shift+1).", "`C-b !`"],
             keys=["break-pane"], demo=[["break-pane"]],
             done="New window! See it in the status bar? Windows are World 3."),
    ]),
    Mission("2.8", "BOSS: Blueprint", xp=150, par=120, boss=True, card="blueprint", steps=[
        Step("BOSS! Build it: big pane A on the left, B C D stacked on the right. (`tmuse card`)",
             setup=fresh,
             goal=main_vertical_ok,
             hints=['`C-b %`, then in the right pane `C-b "` twice.',
                    "Or make 4 panes and pick main-vertical with `C-b M-4` / select-layout."],
             mistakes=[(lambda c: npanes(c) > 4, "Too many panes: `C-b x` y to close one.")]),
        Step("Make A wider than half the window (resize!)",
             goal=wide_left,
             hints=["Go to A and `C-b :` resize-pane -R 10" if MAC_ARROWS else "Go to A and `C-b C-→`, or `C-b :` resize-pane -R 10"]),
        Step("Finally zoom the bottom-right pane (D).",
             goal=zoom_br,
             hints=["Move to D with arrows, then `C-b z`."]),
    ]),
])
