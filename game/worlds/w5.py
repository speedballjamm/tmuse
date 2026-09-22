import random

from .common import (Mission, Step, World, answered, buffer_has, rand_code, reset, run_in, select, snap, split,
                     visible_in_copy)


def log_setup(line_fmt, key="code"):
    def setup(c):
        reset(c, clear_buffers=True)
        c.mem[key] = rand_code()
        run_in(c, snap(c).pane.id, "log", random.randint(1, 10 ** 6), line_fmt.format(c.mem[key]), 220, 60)
    return setup


def search_setup(c):
    reset(c)
    run_in(c, snap(c).pane.id, "search", random.randint(1, 10 ** 6), "PASSWORD", 3)


def first_match(c):
    p = c.s.pane
    if p and p.mode == "copy-mode" and p.search and "PASSWORD" in p.cursor_line:
        c.mem["first"] = p.cursor_line
        return True
    return False


def next_match(c):
    p = c.s.pane
    return bool(p and p.mode == "copy-mode" and "PASSWORD" in p.cursor_line
                and p.cursor_line != c.mem.get("first"))


def copied(key):
    def goal(c):
        if buffer_has(c, c.mem[key]):
            return True
        b = c.s.newest_buffer
        if b and c.just("copy"):
            c.say(f"You copied '{b.sample[:30]}', which doesn't include the code. Try again!")
        return False
    return goal


def paste_setup(c):
    reset(c, clear_buffers=True)
    split(c, 2, "h")
    c.mem["code"] = rand_code()
    s = snap(c)
    left, right = s.window.leftmost(), s.window.rightmost()
    c.mem["right"] = right.id
    run_in(c, left.id, "log", random.randint(1, 10 ** 6), f"ACCESS CODE: {c.mem['code']}", 120, 60)
    select(c, "left")


def pasted_right(c):
    return c.mem["code"] in c.capture(c.mem["right"])


def buffers_setup(c):
    reset(c, clear_buffers=True)
    for fruit in ("apple", "banana", "cherry"):
        c.tmux.run("set-buffer", fruit)


def pasted_banana(c):
    text = c.capture(c.s.pane.id)
    if "banana" in text:
        return True
    if "cherry" in text or "apple" in text:
        c.say("That's the wrong fruit. Clear the line (C-u) and pick **banana** in `C-b =`.")
    return False


def incident_setup(c):
    reset(c, clear_buffers=True)
    split(c, 2, "h")
    s = snap(c)
    left, right = s.window.leftmost(), s.window.rightmost()
    rid = lambda: "req-" + "".join(random.choice("0123456789abcdef") for _ in range(6))
    c.mem["id"], c.mem["decoys"] = rid(), [rid(), rid(), rid()]
    c.mem["right"] = right.id
    run_in(c, right.id, "banner", "TICKET #4521: paste the req id of the FIRST error below")
    run_in(c, left.id, "incident", random.randint(1, 10 ** 6), c.mem["id"], ",".join(c.mem["decoys"]), 0.03)
    select(c, "left")


def ticket_filed(c):
    text = c.capture(c.mem["right"])
    if c.mem["id"] in text:
        return True
    if any(d in text for d in c.mem["decoys"]):
        c.say("That's an ERROR, but not the FIRST one. Scroll further up! (C-u clears the line)")
    return False


WORLD = World(5, "Copy Mode & Scrollback", card="copy_mode", missions=[
    Mission("5.1", "Scrollback", xp=60, par=60, steps=[
        Step("A secret scrolled off the top! Enter copy mode: `C-b [`",
             setup=log_setup("SECRET: {}"),
             goal=lambda c: c.s.mode == "copy-mode",
             hints=["Prefix, then [ (left square bracket).", "`C-b [`"],
             expect=["copy-mode"], keys=["copy-mode"], demo=[["copy-mode"]]),
        Step("Scroll up (PgUp, or ↑ / k) until the **SECRET:** line is on screen.",
             goal=lambda c: visible_in_copy(c, "SECRET:"),
             hints=["It's about 60 lines up. PgUp a few times (Mac laptop: Fn+↑).",
                    "Try `C-u` (half page up) or just hold ↑."], keys=["copy-scroll"]),
        Step("Memorise it, then leave copy mode: `q`",
             goal=lambda c: c.s.mode != "copy-mode", hints=["Press q."]),
        Step("Prove it: type  **tmuse answer THE-SECRET**  in the shell.",
             goal=lambda c: answered(c, c.mem["code"]),
             hints=["Forgot it? `C-b [` and scroll back up. It looks like WORD-123."],
             done="Copy mode is how you read anything that scrolled away."),
    ]),
    Mission("5.2", "Search", xp=60, par=60, steps=[
        Step("Search UP for PASSWORD: `C-b [` then `?`, type PASSWORD, Enter.",
             setup=search_setup, goal=first_match,
             hints=["In copy mode, ? searches upwards (older). A prompt appears in the status bar.",
                    "`C-b [`  ?  PASSWORD  Enter"],
             keys=["copy-search"]),
        Step("Press `n` to jump to the next (older) match.", goal=next_match,
             hints=["Just n. N goes the other way."]),
        Step("Keep pressing `n` until you land on the OLDEST one.",
             goal=lambda c: bool(c.s.pane and "OLDEST" in c.s.pane.cursor_line),
             hints=["n, n… the line says (the OLDEST one)."]),
        Step("Leave copy mode: `q`", goal=lambda c: c.s.mode != "copy-mode",
             done="? searches up, / searches down, n / N move between matches."),
    ]),
    Mission("5.3", "Copy", xp=70, par=90, card="copy_select", steps=[
        Step("Enter copy mode and scroll up to the **ACCESS CODE:** line.",
             setup=log_setup("ACCESS CODE: {}"),
             goal=lambda c: visible_in_copy(c, "ACCESS CODE:"),
             hints=["`C-b [` then PgUp. Or search: ?ACCESS Enter"]),
        Step("Copy just the code: move to its start, `Space`, move to the end (`$`), `Enter`.",
             goal=copied("code"),
             hints=["Put the cursor on the line (↑↓). `0` = line start, `w` = next word.",
                    "`0` `w` `w` (to the code), `Space`, `$`, `Enter`"],
             keys=["copy-select"],
             done="Copied into a tmux paste buffer!"),
    ]),
    Mission("5.4", "Paste", xp=70, par=90, steps=[
        Step("Copy the ACCESS CODE from the left pane (`C-b [` … `Space` … `Enter`).",
             setup=paste_setup, goal=copied("code"),
             hints=["Search for it: `C-b [` ?ACCESS Enter, then `w` `w`, `Space`, `$`, `Enter`."]),
        Step("Move to the right pane and paste it: `C-b ]`",
             goal=pasted_right,
             hints=["`C-b →` to move, then `C-b ]` to paste.", "Paste = prefix + ]"],
             keys=["paste"], done="Copy with [ … Enter, paste with ]. Works across panes and windows."),
    ]),
    Mission("5.5", "Paste history", xp=60, par=40, bonus=True, steps=[
        Step("You've copied apple, banana, cherry. Paste **banana**: `C-b =`, pick it, Enter.",
             setup=buffers_setup, goal=pasted_banana,
             hints=["`C-b =` lists every paste buffer, newest first.", "`C-b =` ↓ Enter"],
             keys=["choose-buffer"]),
    ]),
    Mission("5.6", "Quick scroll", xp=50, par=30, bonus=True, steps=[
        Step("Enter copy mode AND scroll up a page in one move: `C-b PgUp`",
             setup=log_setup("nothing to see here: {}"),
             goal=lambda c: bool(c.s.pane and c.s.pane.mode == "copy-mode" and c.s.pane.scroll > 0),
             hints=["Prefix, then Page Up (Mac laptop: Fn+↑)."], keys=["copy-pgup"],
             demo=[["copy-mode", "-u"]]),
        Step("Jump to the very top of history: `g`. Then leave with `q`.",
             goal=lambda c: c.did("mode-exit") and c.s.mode != "copy-mode",
             hints=["g = top, G = bottom, q = quit"]),
    ]),
    Mission("5.7", "BOSS: Log Detective", xp=150, par=150, boss=True, steps=[
        Step("BOSS! Find the req id of the FIRST ERROR (left log) & paste it in the ticket (right).",
             setup=incident_setup, goal=ticket_filed,
             hints=["Wait for the stream to end, `C-b [`, then search: ?ERROR Enter, n… to the oldest.",
                    "Copy the req-xxxxxx with Space…Enter, `C-b →`, `C-b ]`."]),
    ]),
])
