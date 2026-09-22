import subprocess

from .common import Mission, Step, World, active_id, fresh, pane_has_line, panes_h, reset, win


def all_panes_show(text):
    def goal(c):
        w = win(c)
        return bool(w and w.panes and all(pane_has_line(c, p.id, text) for p in w.panes))
    return goal


def sync_on(c):
    return bool(win(c) and win(c).sync)


def described(c):
    if c.just("view-mode"):
        c.say("That's the full list (`C-b ?`). Press q, then try `C-b /` followed by z.", "hint")
    return any(a.kind == "key" and a.info["cmd"].startswith("list-keys -1N") for a in c.actions)


def mouse_setup(c):
    c.tmux.run("set", "-g", "mouse", "off")
    panes_h(2, sel="left")(c)


def fleet_setup(c):
    reset(c)
    try:
        c.mem["host"] = subprocess.run(["hostname"], capture_output=True, text=True).stdout.strip()
    except OSError:
        c.mem["host"] = ""


def fleet_built(c):
    w = win(c)
    return bool(w and w.name == "fleet" and w.is_grid(2, 2))


def fleet_ran(c):
    return fleet_built(c) and all_panes_show(c.mem["host"])(c)


WORLD = World(6, "The Command Prompt", card="commands", missions=[
    Mission("6.1", "Command prompt", xp=60, par=45, steps=[
        Step("Open the prompt with `C-b :` then type  **new-window -n build**  and Enter.",
             setup=fresh,
             goal=lambda c: bool(c.s.find_window("build")),
             hints=["The prompt appears in the status bar. Type the command, press Enter.",
                    "`C-b :`  new-window -n build  Enter   (Tab completes command names)"],
             keys=["command-prompt"], demo=[["new-window", "-n", "build"]],
             done="A window, already named. Keys can't do that!"),
    ]),
    Mission("6.2", "Keys are commands", xp=50, par=40, steps=[
        Step("Split side by side WITHOUT `%`: `C-b :` then  **split-window -h**",
             setup=fresh,
             goal=lambda c: c.did("split-h"),
             mistakes=[(lambda c: c.just("split-v"), "That's -v (top/bottom). You want split-window -h.")],
             hints=["`C-b :` split-window -h Enter"],
             done="That's exactly what `C-b %` runs. Check with `C-b ?`."),
    ]),
    Mission("6.3", "Layout by name", xp=50, par=40, steps=[
        Step("Stack these panes: `C-b :` then  **select-layout even-vertical**",
             setup=panes_h(3),
             goal=lambda c: bool(win(c) and win(c).orientation() == "top-bottom"),
             hints=["`C-b :` select-layout even-vertical Enter"],
             done="Also: even-horizontal, main-horizontal, main-vertical, tiled."),
    ]),
    Mission("6.4", "Synchronize", xp=70, par=60, card="sync", steps=[
        Step("Turn on synchronized input: `C-b :` then  **setw synchronize-panes on**",
             setup=panes_h(3), goal=sync_on,
             hints=["`C-b :` setw synchronize-panes on Enter"], keys=["sync"],
             demo=[["setw", "synchronize-panes", "on"]]),
        Step("Now type  **echo deploy**  and Enter ONCE. Watch every pane.",
             goal=all_panes_show("deploy"),
             hints=["Just type in the active pane; tmux copies your keys to the others."]),
        Step("Turn it off: `C-b :` then  **setw synchronize-panes off**",
             goal=lambda c: not sync_on(c),
             hints=["`C-b :` setw synchronize-panes off Enter"],
             done="Great for running one command on several servers at once."),
    ]),
    Mission("6.5", "Describe a key", xp=50, par=40, steps=[
        Step("Ask tmux what a key does: press `C-b /` then `z`. Read the status bar.",
             setup=fresh, goal=described,
             hints=["Prefix, then /. It prompts 'key': press z.", "`C-b /` z"],
             keys=["describe-key"],
             done="`C-b /` any key tells you what it does. `C-b ?` lists them all."),
    ]),
    Mission("6.6", "Message log", xp=40, par=30, bonus=True, steps=[
        Step("Show tmux's recent messages: `C-b ~`",
             setup=fresh,
             goal=lambda c: c.s.mode == "view-mode",
             hints=["Prefix, then ~ (tilde, Shift+`)."], keys=["messages"], demo=[["show-messages"]]),
        Step("Press `q` to leave.", goal=lambda c: c.s.mode != "view-mode"),
    ]),
    Mission("6.7", "Mouse mode", xp=70, par=90, card="mouse", steps=[
        Step("Turn on the mouse: `C-b :` then  **set -g mouse on**",
             setup=mouse_setup,
             goal=lambda c: c.s.options.get("mouse") == "on",
             hints=["`C-b :` set -g mouse on Enter"], keys=["mouse"],
             demo=[["set", "-g", "mouse", "on"]]),
        Step("Click the RIGHT pane to select it.",
             goal=lambda c: bool(win(c) and active_id(c) == win(c).rightmost().id),
             hints=["Just click anywhere inside the right-hand pane."]),
        Step("Drag the border between the panes to resize them.",
             goal=lambda c: c.did("resize", "layout"),
             hints=["Press on the vertical line between the panes and drag sideways."]),
        Step("Scroll UP with the wheel/trackpad over a pane (it enters copy mode).",
             goal=lambda c: c.did("copy-mode"),
             hints=["Scroll up. The yellow position counter means you're in copy mode."]),
        Step("Leave copy mode with `q` (or scroll back to the bottom).",
             goal=lambda c: c.s.mode != "copy-mode",
             done="Mouse stays on for now. Want it off? `C-b :` set -g mouse off"),
    ]),
    Mission("6.8", "BOSS: Fleet Commander", xp=150, par=150, boss=True, steps=[
        Step("BOSS! Make a window named **fleet** with 4 panes in a tiled 2×2 grid.",
             setup=fleet_setup, goal=fleet_built,
             hints=["new-window -n fleet, split-window (×3), select-layout tiled",
                    "All via `C-b :`. Or keys: `C-b c`, `C-b ,`, splits, `C-b Space` to tiled."]),
        Step("Turn on synchronize-panes in fleet.", goal=lambda c: fleet_built(c) and sync_on(c),
             hints=["`C-b :` setw synchronize-panes on"]),
        Step("Run  **hostname**  in all four panes at once.", goal=fleet_ran),
        Step("Turn synchronize-panes off again.", goal=lambda c: not sync_on(c)),
    ]),
])
