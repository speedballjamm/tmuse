import random

from .common import (Mission, Step, World, attached, buffer_has, names, reset, run_in, session, snap)


def on_day(c):
    return attached(c) and session(c) == "day"


def has_windows(c):
    return all(n in names(c, "day") for n in ("editor", "server", "logs"))


def server_split(c):
    w = c.s.find_window("server", "day")
    return bool(w and len(w.panes) >= 2 and len({p.top for p in w.panes}) < len(w.panes))


def start_incident(c):
    rid = lambda: "req-" + "".join(random.choice("0123456789abcdef") for _ in range(6))
    c.mem["id"], c.mem["decoys"] = rid(), [rid(), rid()]
    w = snap(c).find_window("logs", "day")
    if w:
        run_in(c, w.panes[0].id, "incident", random.randint(1, 10 ** 6), c.mem["id"], ",".join(c.mem["decoys"]),
               0.02)


def copied_id(c):
    if buffer_has(c, c.mem["id"]):
        return True
    b = c.s.newest_buffer
    if b and c.just("copy") and any(d in b.sample for d in c.mem["decoys"]):
        c.say("That's a later ERROR. You need the FIRST one: scroll further up.")
    return False


def pasted_in_editor(c):
    w = c.s.find_window("editor", "day")
    return bool(w and any(c.mem["id"] in c.capture(p.id) for p in w.panes))


def zoomed_server(c):
    w = c.s.window
    return bool(on_day(c) and w and w.name == "server" and w.zoomed)


WORLD = World(8, "Final Boss", card="final", missions=[
    Mission("F", "BOSS: A Day in the Life", xp=300, par=360, boss=True, steps=[
        Step("Good morning! Start a new session named **day** (detach, then: tmux new -s day)",
             setup=lambda c: reset(c, session="tmuse"), goal=on_day,
             outside="Type:  tmux new -s day"),
        Step("Set up windows named **editor**, **server** and **logs** in session day.",
             goal=has_windows, hints=["`C-b ,` renames, `C-b c` creates."]),
        Step("Split the **server** window side by side.", goal=server_split,
             hints=["Go to server, `C-b %`."]),
        Step("ALERT! Incident in **logs**. Find the FIRST ERROR and copy its req id.",
             setup=start_incident, goal=copied_id,
             hints=["Go to logs, `C-b [`, search ?ERROR, n to older ones… Space … Enter"]),
        Step("Paste it into the **editor** window: `C-b ]`", goal=pasted_in_editor),
        Step("Home time! Detach: `C-b d`", goal=lambda c: not attached(c)),
        Step("Next morning: reattach to **day**.", goal=on_day, outside="Type:  tmux a -t day"),
        Step("Go to **server** and zoom one of its panes to focus: `C-b z`", goal=zoomed_server,
             done="THAT'S A WRAP! You are a tmux user now."),
    ]),
])
