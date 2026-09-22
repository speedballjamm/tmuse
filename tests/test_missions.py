"""End-to-end: play every mission with real keystrokes and check each one clears.

    python3 tests/test_missions.py            # all worlds, in parallel
    python3 tests/test_missions.py 1 5        # just worlds 1 and 5
"""
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import Game  # noqa: E402


def step(g, n, total):
    g.wait_hud(f"({n}/{total})")


def mission(g, mid):
    g.wait_hud(f"▶ {mid} ")


def cmd(g, text):
    """Run a tmux command from the C-b : prompt."""
    g.keys("C-b", ":")
    g.type(text, delay=0.5)


def rename(g, key, name):
    g.keys("C-b", key)
    g.keys("C-u")
    g.type(name, delay=0.5)


def pane_ids(g):
    return g.inner_out("list-panes", "-F", "#{pane_id}").split()


def find_in_history(g, pattern, pane=None):
    target = ["-t", pane] if pane else []
    text = g.inner_out("capture-pane", "-p", "-J", "-S", "-", *target)
    m = re.search(pattern, text)
    return m.group(1) if m else None


def nano_add(g, conf, *lines):
    g.type(f"nano {conf}", delay=1.2)
    for _ in range(40):
        g.keys("Down", delay=0.02)
    for line in lines:
        g.type(line, delay=0.2)
    g.keys("C-o", delay=0.6)
    g.keys("Enter", delay=0.6)
    g.keys("C-x", delay=0.8)


# ------------------------------------------------------------------------------ worlds

def world0(g):
    g.close_card()  # welcome
    mission(g, "0.1")
    g.type("echo hello")
    g.wait_done("0.1")
    g.close_card()  # prefix
    mission(g, "0.2")
    g.keys("C-b")
    step(g, 2, 3)
    g.keys("?")
    step(g, 3, 3)
    g.keys("q")
    g.wait_done("0.2")
    mission(g, "0.3")
    g.keys("C-b")
    step(g, 2, 2)
    g.keys("Escape")
    g.wait_done("0.3")
    mission(g, "0.4")
    g.keys("C-b", "t")
    step(g, 2, 2)
    g.keys("q")
    g.wait_done("0.4")


def world1(g):
    g.close_card()  # panes
    mission(g, "1.1")
    g.keys("C-b", "%")
    g.wait_done("1.1")
    mission(g, "1.2")
    g.keys("C-b", '"')
    g.wait_done("1.2")
    mission(g, "1.3")
    g.keys("C-b", "Left")
    step(g, 2, 2)
    g.keys("C-b", "Right")
    g.wait_done("1.3")
    mission(g, "1.4")
    g.keys("C-b", "Up", "C-b", "Left")
    step(g, 2, 4)
    g.keys("C-b", "Down", "C-b", "Right")
    step(g, 3, 4)
    g.keys("C-b", "Up")
    step(g, 4, 4)
    g.keys("C-b", "Down", "C-b", "Left")
    g.wait_done("1.4")
    mission(g, "1.5")
    g.keys("C-b", "o", "C-b", "o", "C-b", "o")
    g.wait_done("1.5")
    mission(g, "1.6")
    g.keys("C-b", "Right", "C-b", "Right")
    step(g, 2, 2)
    g.keys("C-b", ";")
    g.wait_done("1.6")
    g.close_card()  # kill
    mission(g, "1.7")
    g.keys("C-b", "x", "y")
    step(g, 2, 2)
    g.type("exit")
    g.wait_done("1.7")
    mission(g, "1.8")
    g.keys("C-b", "q", "3", delay=0.1)
    g.wait_done("1.8")
    mission(g, "1.9")
    g.keys("C-b", "%", "C-b", '"', "C-b", "Left", "C-b", '"')
    step(g, 2, 5)
    g.keys("C-b", "Up")
    step(g, 3, 5)
    g.keys("C-b", "Down", "C-b", "Right")
    step(g, 4, 5)
    g.keys("C-b", "Up")
    step(g, 5, 5)
    g.keys("C-b", "Down", "C-b", "Left")
    g.wait_done("1.9")


def world2(g):
    g.close_card()  # pane power
    mission(g, "2.1")
    g.keys("C-b", "z")
    step(g, 2, 2)
    g.keys("C-b", "z")
    g.wait_done("2.1")
    g.close_card()  # resize
    mission(g, "2.2")
    for _ in range(7):
        g.keys("C-b", "C-Right", delay=0.1)
    step(g, 2, 2)
    for _ in range(15):
        g.keys("C-b", "C-Left", delay=0.1)
    g.wait_done("2.2")
    mission(g, "2.3")
    g.keys("C-b", "}")
    g.wait_done("2.3")
    mission(g, "2.4")
    g.keys("C-b", "C-o")
    step(g, 2, 2)
    g.keys("C-b", "C-o", "C-b", "C-o")
    g.wait_done("2.4")
    mission(g, "2.5")
    g.keys("C-b", "Space", "C-b", "Space", "C-b", "Space", "C-b", "Space")
    step(g, 2, 2)
    for _ in range(10):
        if g.stars("2.5"):
            break
        g.keys("C-b", "Space", delay=0.6)
    g.wait_done("2.5")
    g.close_card()  # layouts
    mission(g, "2.6")
    g.keys("C-b", "M-2")
    step(g, 2, 2)
    g.keys("C-b", "M-4")
    g.wait_done("2.6")
    mission(g, "2.7")
    g.keys("C-b", "!")
    g.wait_done("2.7")
    g.close_card()  # blueprint
    mission(g, "2.8")
    g.keys("C-b", "%", "C-b", '"', "C-b", '"')
    step(g, 2, 3)
    g.keys("C-b", "Left")
    cmd(g, "resize-pane -R 15")
    step(g, 3, 3)
    cmd(g, "select-pane -t '{bottom-right}'")
    g.keys("C-b", "z")
    g.wait_done("2.8")


def world3(g):
    g.close_card()  # windows
    mission(g, "3.1")
    g.keys("C-b", "c")
    g.wait_done("3.1")
    mission(g, "3.2")
    g.keys("C-b", "n")
    step(g, 2, 3)
    g.keys("C-b", "n")
    step(g, 3, 3)
    g.keys("C-b", "p")
    g.wait_done("3.2")
    mission(g, "3.3")
    g.keys("C-b", "3")
    step(g, 2, 2)
    g.keys("C-b", "1")
    g.wait_done("3.3")
    mission(g, "3.4")
    rename(g, ",", "code")
    g.wait_done("3.4")
    mission(g, "3.5")
    g.keys("C-b", "2")
    step(g, 2, 3)
    g.keys("C-b", "l")
    step(g, 3, 3)
    g.keys("C-b", "l")
    g.wait_done("3.5")
    mission(g, "3.6")
    g.keys("C-b", "w")
    step(g, 2, 2)
    g.keys("Down", "Enter")
    g.wait_done("3.6")
    mission(g, "3.7")
    g.keys("C-b", "&", "y")
    g.wait_done("3.7")
    mission(g, "3.8")
    g.keys("C-b", "f")
    g.type("TREASURE", delay=0.8)
    g.keys("Down", "Enter")
    g.wait_done("3.8")
    mission(g, "3.9")
    g.keys("C-b", ".")
    g.type("5")
    g.wait_done("3.9")
    mission(g, "3.10")
    g.keys("C-b", "'")
    g.type("12")
    g.wait_done("3.10")
    mission(g, "3.11")
    rename(g, ",", "code")
    g.keys("C-b", "c")
    rename(g, ",", "server")
    g.keys("C-b", "c")
    rename(g, ",", "logs")
    step(g, 2, 6)
    g.keys("C-b", "1")
    step(g, 3, 6)
    g.keys("C-b", "2")
    step(g, 4, 6)
    g.keys("C-b", "l")
    step(g, 5, 6)
    g.keys("C-b", "2")
    rename(g, ",", "tail")
    step(g, 6, 6)
    g.keys("C-b", "0", "C-b", "&", "y")
    g.wait_done("3.11")


def world4(g):
    g.close_card()  # sessions
    mission(g, "4.1")
    rename(g, "$", "work")
    g.wait_done("4.1")
    g.close_card()  # detach
    mission(g, "4.2")
    time.sleep(0.5)
    g.keys("C-b", "d")
    g.wait_screen("you@outside")
    g.wait(lambda: "(2/5)" in g.hud(), what="step 2")
    g.type("tmux ls", delay=0.8)
    step(g, 3, 5)
    g.type("tmux attach", delay=1)
    step(g, 4, 5)
    g.keys("C-b", "d")
    g.wait_screen("you@outside")
    step(g, 5, 5)
    g.type("tmux a -t work", delay=1)
    g.wait_done("4.2")
    mission(g, "4.3")
    g.keys("C-b", "d")
    step(g, 2, 2)
    g.type("tmux new -s play", delay=1)
    g.wait_done("4.3")
    mission(g, "4.4")
    g.keys("C-b", "s")
    step(g, 2, 2)
    g.keys("2")
    g.wait_done("4.4")
    mission(g, "4.5")
    g.keys("C-b", ")")
    step(g, 2, 3)
    g.keys("C-b", ")")
    step(g, 3, 3)
    g.keys("C-b", "(")
    g.wait_done("4.5")
    mission(g, "4.6")
    g.keys("C-b", ")")
    time.sleep(0.4)
    g.keys("C-b", ")")
    step(g, 2, 2)
    g.keys("C-b", "L")
    g.wait_done("4.6")
    mission(g, "4.7")
    g.keys("C-b", "d")
    step(g, 2, 4)
    g.type("tmux kill-session -t play", delay=0.8)
    step(g, 3, 4)
    g.type("tmux ls", delay=0.8)
    step(g, 4, 4)
    g.type("tmux a", delay=1)
    g.wait_done("4.7")
    mission(g, "4.8")
    g.keys("C-b", "d")
    step(g, 2, 4)
    g.type("tmux ls", delay=0.8)
    step(g, 3, 4)
    time.sleep(16)
    g.type("tmux a -t ops", delay=1.5)
    step(g, 4, 4)
    code = find_in_history(g, r"The code word is: (\w+)")
    g.type(f"tmuse answer {code}")
    g.wait_done("4.8")


def world5(g):
    g.close_card()  # copy mode
    mission(g, "5.1")
    time.sleep(0.5)
    g.keys("C-b", "[")
    step(g, 2, 4)
    for _ in range(20):
        if "(3/4)" in g.hud():
            break
        g.keys("PageUp", delay=0.3)
    step(g, 3, 4)
    g.keys("q")
    step(g, 4, 4)
    code = find_in_history(g, r"SECRET: (\S+)")
    g.type(f"tmuse answer {code}")
    g.wait_done("5.1")
    mission(g, "5.2")
    time.sleep(0.5)
    g.keys("C-b", "[", "?")
    g.type("PASSWORD")
    step(g, 2, 4)
    g.keys("n")
    step(g, 3, 4)
    for _ in range(4):
        if "(4/4)" in g.hud():
            break
        g.keys("n", delay=0.4)
    step(g, 4, 4)
    g.keys("q")
    g.wait_done("5.2")

    def copy_code(code):
        g.keys("C-b", "[", "?")
        g.type(code, delay=0.5)
        g.keys("Space", "$", "Enter")

    g.close_card()  # copy_select
    mission(g, "5.3")
    time.sleep(0.6)
    code = find_in_history(g, r"ACCESS CODE: (\S+)")
    g.keys("C-b", "[", "?")
    g.type("ACCESS CODE")
    step(g, 2, 2)
    g.keys("w", "w", "w", "Space", "$", "Enter")
    g.wait_done("5.3")
    mission(g, "5.4")
    time.sleep(0.6)
    left = g.inner_out("display", "-p", "#{pane_id}").strip()
    code = find_in_history(g, r"ACCESS CODE: (\S+)", left)
    copy_code(code)
    step(g, 2, 2)
    g.keys("C-b", "Right", "C-b", "]")
    g.wait_done("5.4")
    mission(g, "5.5")
    g.keys("C-b", "=", "Down", "Enter")
    g.wait_done("5.5")
    mission(g, "5.6")
    time.sleep(0.5)
    g.keys("C-b", "PageUp")
    step(g, 2, 2)
    g.keys("g", "q")
    g.wait_done("5.6")
    mission(g, "5.7")
    left = g.inner_out("display", "-p", "#{pane_id}").strip()
    g.wait(lambda: "stream ended" in g.inner_out("capture-pane", "-p", "-t", left), 30, "stream end")
    rid = find_in_history(g, r"charge failed: upstream timeout req=(req-\w+)", left)
    copy_code(rid)
    g.keys("C-b", "Right", "C-b", "]")
    g.wait_done("5.7")


def world6(g):
    g.close_card()  # commands
    mission(g, "6.1")
    cmd(g, "new-window -n build")
    g.wait_done("6.1")
    mission(g, "6.2")
    cmd(g, "split-window -h")
    g.wait_done("6.2")
    mission(g, "6.3")
    cmd(g, "select-layout even-vertical")
    g.wait_done("6.3")
    g.close_card()  # sync
    mission(g, "6.4")
    cmd(g, "setw synchronize-panes on")
    step(g, 2, 3)
    time.sleep(0.5)
    g.type("echo deploy")
    step(g, 3, 3)
    cmd(g, "setw synchronize-panes off")
    g.wait_done("6.4")
    mission(g, "6.5")
    g.keys("C-b", "/", "z")
    g.wait_done("6.5")
    mission(g, "6.6")
    g.keys("C-b", "~")
    step(g, 2, 2)
    g.keys("q")
    g.wait_done("6.6")
    g.close_card()  # mouse
    mission(g, "6.7")
    cmd(g, "set -g mouse on")
    step(g, 2, 5)
    width = int(g.inner_out("display", "-p", "-t", "{left}", "#{pane_width}").strip())
    g.mouse(width + 10, 8)
    step(g, 3, 5)
    g.drag(width + 1, 8, width + 12, 8)
    step(g, 4, 5)
    g.mouse(10, 8, button=64, release=False)
    g.mouse(10, 8, button=64, release=False)
    step(g, 5, 5)
    g.keys("q")
    g.wait_done("6.7")
    mission(g, "6.8")
    cmd(g, "new-window -n fleet")
    cmd(g, "split-window -h")
    cmd(g, "split-window -v")
    cmd(g, "split-window -v")
    cmd(g, "select-layout tiled")
    step(g, 2, 4)
    cmd(g, "setw synchronize-panes on")
    step(g, 3, 4)
    time.sleep(0.5)
    g.type("hostname")
    step(g, 4, 4)
    cmd(g, "setw synchronize-panes off")
    g.wait_done("6.8")


def world7(g):
    conf = os.path.join(g.home, "sandbox.tmux.conf")
    g.close_card()  # config
    g.close_card()  # editor
    mission(g, "7.1")
    time.sleep(0.5)
    g.type(f"nano {conf}", delay=1.2)
    step(g, 2, 3)
    for _ in range(10):
        g.keys("Down", delay=0.02)
    g.type("set -g mouse on", delay=0.2)
    g.keys("C-o", delay=0.6)
    g.keys("Enter", delay=0.6)
    g.keys("C-x", delay=0.8)
    step(g, 3, 3)
    cmd(g, f"source-file {conf}")
    g.wait_done("7.1")
    mission(g, "7.2")
    time.sleep(0.5)
    nano_add(g, conf, "set -g base-index 1", "setw -g pane-base-index 1")
    step(g, 2, 2)
    cmd(g, f"source-file {conf}")
    g.wait_done("7.2")
    mission(g, "7.3")
    time.sleep(0.5)
    nano_add(g, conf, f"bind r source-file {conf}")
    cmd(g, f"source-file {conf}")
    step(g, 2, 2)
    nano_add(g, conf, "set -g status-style bg=colour22")
    g.keys("C-b", "r")
    g.wait_done("7.3")
    mission(g, "7.4")
    nano_add(g, conf, "set -g history-limit 50000")
    g.keys("C-b", "r")
    g.wait_done("7.4")
    mission(g, "7.5")
    nano_add(g, conf, "bind | split-window -h", "bind - split-window -v")
    g.keys("C-b", "r")
    step(g, 2, 2)
    g.keys("C-b", "|")
    g.wait_done("7.5")
    mission(g, "7.6")
    nano_add(g, conf, "bind -T copy-mode-vi v send -X begin-selection",
             "bind -T copy-mode-vi y send -X copy-selection-and-cancel")
    g.keys("C-b", "r")
    g.wait_done("7.6")
    g.close_card()  # prefix change
    mission(g, "7.7")
    nano_add(g, conf, "set -g prefix C-a", "unbind C-b", "bind C-a send-prefix")
    g.keys("C-b", "r")
    step(g, 2, 2)
    g.keys("C-a", "c")
    g.wait_done("7.7")
    mission(g, "7.8")
    g.wait_screen("Install this as")
    g.type("y", delay=1)
    g.keys("Enter")
    g.wait_done("7.8")
    with open(g.real_conf) as f:
        real = f.read()
    assert "~/.tmux.conf" in real and "sandbox" not in real, real
    assert "set -g prefix C-a" in real


def world8(g):
    g.close_card()  # final
    mission(g, "F")
    time.sleep(0.5)
    g.keys("C-b", "d")
    g.wait_screen("you@outside")
    g.type("tmux new -s day", delay=1.5)
    step(g, 2, 8)
    rename(g, ",", "editor")
    g.keys("C-b", "c")
    rename(g, ",", "server")
    g.keys("C-b", "c")
    rename(g, ",", "logs")
    step(g, 3, 8)
    g.keys("C-b", "1", "C-b", "%")
    step(g, 4, 8)
    logs = g.inner_out("list-panes", "-t", "day:logs", "-F", "#{pane_id}").split()[0]
    g.wait(lambda: "stream ended" in g.inner_out("capture-pane", "-p", "-t", logs), 30, "stream end")
    rid = find_in_history(g, r"charge failed: upstream timeout req=(req-\w+)", logs)
    g.keys("C-b", "2", "C-b", "[", "?")
    g.type(rid, delay=0.5)
    g.keys("Space", "$", "Enter")
    step(g, 5, 8)
    g.keys("C-b", "0", "C-b", "]")
    step(g, 6, 8)
    g.keys("C-b", "d")
    g.wait_screen("you@outside")
    step(g, 7, 8)
    g.type("tmux a -t day", delay=1.5)
    step(g, 8, 8)
    g.keys("C-b", "1", "C-b", "z")
    g.wait_done("F", timeout=30)


WORLDS = {0: ("0.1", world0), 1: ("1.1", world1), 2: ("2.1", world2), 3: ("3.1", world3),
          4: ("4.1", world4), 5: ("5.1", world5), 6: ("6.1", world6), 7: ("7.1", world7), 8: ("F", world8)}


def run_world(n):
    first, fn = WORLDS[n]
    g = Game(f"w{n}", ("play", first))
    t0 = time.time()
    try:
        fn(g)
        print(f"PASS world {n} ({time.time() - t0:.0f}s)")
        return True
    except AssertionError as e:
        print(f"FAIL world {n}: {e}")
        return False
    finally:
        g.close()


def main(argv):
    if len(argv) == 1:
        sys.exit(0 if run_world(int(argv[0])) else 1)
    worlds = [int(a) for a in argv] or list(WORLDS)
    procs = {n: subprocess.Popen([sys.executable, __file__, str(n)]) for n in worlds}
    failed = [n for n, p in procs.items() if p.wait() != 0]
    print("\nALL PASSED" if not failed else f"\nFAILED worlds: {failed}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
