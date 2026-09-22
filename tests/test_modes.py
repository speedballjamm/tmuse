"""End-to-end tests for everything that isn't a campaign mission.

    python3 tests/test_modes.py            # all, in parallel
    python3 tests/test_modes.py sandbox    # one
"""
import json
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import ROOT, Game  # noqa: E402
from test_missions import mission, step  # noqa: E402


def test_sandbox():
    g = Game("sandbox", ("sandbox",))
    try:
        g.wait_hud("SANDBOX")
        time.sleep(1)
        g.keys("C-b", "%")
        g.wait(lambda: "split-window -h" in g.msg(), what="sandbox narration of C-b %")
        assert "C-b %" in g.msg().replace("%%", "%"), g.msg()
        g.keys("C-b", "z")
        g.wait(lambda: "resize-pane -Z" in g.msg(), what="narration of zoom")
    finally:
        g.close()


def test_hint_show_skip():
    g = Game("hints", ("play", "1.1"))
    try:
        g.close_card()
        mission(g, "1.1")
        g.type("tmuse hint")
        g.wait(lambda: "Prefix first" in g.msg(), what="first hint")
        g.type("tmuse show")
        g.wait(lambda: "Now you try" in g.msg(), timeout=10, what="demo finished")
        g.wait(lambda: len(g.inner_out("list-panes").splitlines()) == 1, what="step reset after demo")
        g.keys("C-b", "%")
        g.wait_done("1.1")
        assert g.stars("1.1") == 1, g.progress()
        assert g.progress()["missions"]["1.1"]["xp"] == 0
        mission(g, "1.2")
        g.type("tmuse skip")
        mission(g, "1.3")
        m = g.progress()["missions"]["1.2"]
        assert m["stars"] == 0 and m["skipped"], m
        g.keys("C-b", "Left")
        step(g, 2, 2)
        g.type("tmuse reset")
        g.wait(lambda: "(1/2)" in g.hud(), what="reset back to step 1")
    finally:
        g.close()


def test_coaching():
    g = Game("coach", ("play", "1.1"))
    try:
        g.close_card()
        mission(g, "1.1")
        time.sleep(0.5)
        g.keys("C-b", '"')
        g.wait(lambda: "top/bottom" in g.msg(), what="wrong-split coaching")
        g.keys("C-b", "c")
        g.wait(lambda: "That did: New window" in g.msg(), what="generic coaching")
    finally:
        g.close()


def test_detach_and_last_pane():
    g = Game("detach", ("play", "1.1"))
    try:
        g.close_card()
        mission(g, "1.1")
        time.sleep(0.5)
        g.keys("C-b", "d")
        g.wait_screen("outside tmux")
        g.wait_screen("tmux attach")
        g.type("ls -la", delay=0.5)
        g.wait_screen("only tmux commands work")
        g.type("tmux attach", delay=1.2)
        g.wait(lambda: g.inner_out("list-clients").strip() != "", what="reattached")
        # close the only pane: the session ends, the server stays up
        g.type("exit", delay=1.5)
        g.wait_screen("Your last session ended")
        g.type("tmux new", delay=1.5)
        g.wait(lambda: g.inner_out("list-clients").strip() != "", what="attached to new session")
        g.keys("C-b", "%")
        g.wait_done("1.1")
        mission(g, "1.2")
        # quit to the menu from inside
        g.type("tmuse menu", delay=1)
        g.wait_screen("Progress saved")
    finally:
        g.close()


def test_attach_too_early():
    """The outside banner shows the next step (not 'tmux attach'), and attaching early says how to get out."""
    g = Game("early", ("play", "4.2"))
    try:
        g.close_card()
        mission(g, "4.2")
        time.sleep(0.5)
        g.keys("C-b", "d")
        g.wait_screen("Type:  tmux ls")
        g.type("tmux attach", delay=1.2)
        g.wait(lambda: g.inner_out("list-clients").strip() != "", what="reattached")
        g.wait(lambda: "This step happens outside tmux" in g.msg(), what="detach nudge")
        g.keys("C-b", "d")
        g.wait_screen("you@outside")
        g.type("tmux ls", delay=0.8)
        g.wait(lambda: "(3/5)" in g.hud(), what="step 3")
    finally:
        g.close()


KEYS_FOR = [
    ("Split side by side", ["C-b", "%"]),
    ("Split top / bottom", ["C-b", '"']),
    ("Move one pane LEFT", ["C-b", "Left"]),
    ("Move one pane RIGHT", ["C-b", "Right"]),
    ("Move one pane UP", ["C-b", "Up"]),
    ("Move one pane DOWN", ["C-b", "Down"]),
    ("Unzoom", ["C-b", "z"]),
    ("Zoom", ["C-b", "z"]),
    ("New window", ["C-b", "c"]),
    ("Next window", ["C-b", "n"]),
    ("Kill a pane", ["C-b", "x", "y"]),
]


def solve_prompts(g, until, seen):
    last = None
    while time.time() < until:
        hud = g.hud()
        for text, keys in KEYS_FOR:
            if text in hud and hud != last:
                seen.add(text)
                g.keys(*keys, delay=0.2)
                last = hud
                break
        time.sleep(0.2)


def test_dojo():
    g = Game("dojo", ("dojo",))
    try:
        g.close_card()
        g.wait_hud("DOJO")
        seen = set()
        solve_prompts(g, time.time() + 62, seen)
        g.wait_screen("Score:", timeout=20)
        best = g.progress().get("dojo_best", 0)
        assert best >= 500, (best, seen)
        g.keys("Enter")
        g.wait_hud("tmuse again")
    finally:
        g.close()


def test_review():
    home = tempfile.mkdtemp(prefix="tmuse-review-")
    past = time.time() - 10
    with open(os.path.join(home, "progress.json"), "w") as f:
        json.dump({"xp": 100, "keys": {k: {"box": 2, "due": past} for k in ("split-h", "new-window", "zoom")},
                   "missions": {}}, f)
    g = Game("review", ("review",), home=home)
    try:
        g.close_card()
        g.wait_hud("REVIEW")
        seen = set()
        end = time.time() + 40
        while time.time() < end and "Review done" not in g.screen():
            solve_prompts(g, time.time() + 2, seen)
        g.wait_screen("Review done", timeout=15)
        boxes = {k: v["box"] for k, v in g.progress()["keys"].items()}
        assert boxes == {"split-h": 3, "new-window": 3, "zoom": 3}, boxes
    finally:
        g._own_home = True
        g.close()


def test_menu():
    g = Game("menu", ())
    try:
        g.wait_screen("learn tmux by playing it")
        g.wait_screen("Continue: 0.1 Just a terminal")
        g.keys("Down", "Enter")               # World select
        g.wait_screen("Choose a world")
        g.keys("Down", "Enter")               # World 1: locked
        g.wait_screen("Locked")
        g.keys("Escape")
        time.sleep(0.5)
        g.keys("Up", "Enter")                 # back on main, Continue
        g.close_card()
        mission(g, "0.1")
        g.type("tmuse menu", delay=1.5)
        g.wait_screen("learn tmux by playing it")
        g.keys("q")
        g.wait(lambda: "learn tmux" not in g.screen(), what="menu to exit")
    finally:
        g.close()


def test_conf_slips():
    """World 7.1: running the config path as a command, or mistyping it. Both look like
    a dead end, so the game must explain — and the explanation has to survive in the
    pane, since the player is reading their own shell error while they retype."""
    g = Game("confslips", ("play", "7.1"))
    try:
        g.close_card()  # config
        g.close_card()  # editor
        mission(g, "7.1")
        conf = os.path.join(g.home, "sandbox.tmux.conf")
        time.sleep(0.5)
        g.type(conf, delay=1.2)  # the path on its own: the shell tries to run it
        g.wait(lambda: "the shell tried to" in g.msg(), what="rescue for running the path")
        g.type(os.path.join(g.home, "sandbox", "tmux.conf"), delay=1.2)  # dots as a folder
        g.wait(lambda: "one filename, not a folder" in g.msg(), what="rescue for the wrong path")
        g.type("tmuse task", delay=1.5)
        screen = g.screen()
        assert "the shell tried to" in screen, screen
        assert "one filename, not a folder" in screen, screen
    finally:
        g.close()


def test_cheat_sheet():
    out = subprocess.run([os.path.join(ROOT, "tmuse"), "cheat", "--all"], capture_output=True, text=True,
                         env=dict(os.environ, TMUSE_HOME=tempfile.mkdtemp())).stdout
    for needle in ("C-b %", "Split pane left | right", "tmux a -t NAME", "Copy mode", "synchronize-panes"):
        assert needle in out, needle


TESTS = {name[5:]: fn for name, fn in globals().items() if name.startswith("test_")}


def main(argv):
    if len(argv) == 1:
        t0 = time.time()
        try:
            TESTS[argv[0]]()
            print(f"PASS {argv[0]} ({time.time() - t0:.0f}s)")
        except AssertionError as e:
            print(f"FAIL {argv[0]}: {e}")
            sys.exit(1)
        return
    names = argv or list(TESTS)
    procs = {n: subprocess.Popen([sys.executable, __file__, n]) for n in names}
    failed = [n for n, p in procs.items() if p.wait() != 0]
    print("\nALL PASSED" if not failed else f"\nFAILED: {failed}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
