"""Run the real game inside an 'outer' tmux, so tests can type real keystrokes into it
and capture exactly what the player would see (status bar, popups and all)."""
import json
import os
import shutil
import subprocess
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Game:
    def __init__(self, name, args=("play",), cols=120, rows=40, home=None):
        self.outer = f"tmuse-outer-{name}"
        self.inner = f"tmuse-test-{name}"
        self.home = home or tempfile.mkdtemp(prefix=f"tmuse-{name}-")
        self._own_home = home is None
        self.run_outer("kill-server")
        self.run_inner("kill-server")
        self.real_conf = os.path.join(self.home, "real.tmux.conf")
        cmd = (f"env -u TMUX TMUSE_HOME={self.home} TMUSE_SOCKET={self.inner} TMUSE_REAL_CONF={self.real_conf} "
               f"{ROOT}/tmuse {' '.join(args)}; sleep 30")
        self.run_outer("-f", "/dev/null", "new-session", "-d", "-x", str(cols), "-y", str(rows), cmd)
        self.run_outer("set", "-g", "status", "off")

    # --- plumbing
    def run_outer(self, *a):
        return subprocess.run(["tmux", "-L", self.outer, *a], capture_output=True, text=True)

    def run_inner(self, *a):
        return subprocess.run(["tmux", "-L", self.inner, *a], capture_output=True, text=True)

    def inner_out(self, *a):
        return self.run_inner(*a).stdout

    # --- input
    def keys(self, *keys, delay=0.25):
        for k in keys:
            # a lone ";" is tmux's command separator, even as an argument
            self.run_outer("send-keys", "-t", ":0.0", "\\;" if k == ";" else k)
            time.sleep(delay)

    def type(self, text, enter=True, delay=0.3):
        self.run_outer("send-keys", "-t", ":0.0", "-l", text)
        if enter:
            self.run_outer("send-keys", "-t", ":0.0", "Enter")
        time.sleep(delay)

    def mouse(self, x, y, button=0, release=True):
        """SGR mouse press (+release) at 1-based cell x, y."""
        seq = f"\x1b[<{button};{x};{y}M"
        if release:
            seq += f"\x1b[<{button};{x};{y}m"
        self.run_outer("send-keys", "-t", ":0.0", "-l", seq)
        time.sleep(0.3)

    def drag(self, x1, y1, x2, y2):
        self.run_outer("send-keys", "-t", ":0.0", "-l", f"\x1b[<0;{x1};{y1}M")
        for x in range(x1, x2, 1 if x2 > x1 else -1):
            self.run_outer("send-keys", "-t", ":0.0", "-l", f"\x1b[<32;{x};{y1}M")
            time.sleep(0.02)
        self.run_outer("send-keys", "-t", ":0.0", "-l", f"\x1b[<0;{x2};{y2}m")
        time.sleep(0.3)

    # --- output
    def screen(self):
        return self.run_outer("capture-pane", "-p", "-t", ":0.0").stdout

    def hud(self):
        return self.inner_out("show", "-gv", "@tmuse_al").strip()

    def msg(self):
        return self.inner_out("show", "-gv", "@tmuse_bl").strip()

    def progress(self):
        try:
            with open(os.path.join(self.home, "progress.json")) as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def stars(self, mid):
        return self.progress().get("missions", {}).get(mid, {}).get("stars", 0)

    def fmt(self, f):
        return self.inner_out("display", "-p", f).strip()

    def engine_log(self):
        try:
            with open(os.path.join(self.home, "engine.log")) as f:
                return f.read()
        except OSError:
            return ""

    # --- waiting
    def wait(self, pred, timeout=15, what="condition"):
        end = time.time() + timeout
        while time.time() < end:
            try:
                if pred():
                    return True
            except Exception:
                pass
            time.sleep(0.15)
        raise AssertionError(f"timed out waiting for {what}\nHUD: {self.hud()}\nMSG: {self.msg()}\n"
                             f"SCREEN:\n{self.screen()}\nLOG:\n{self.engine_log()[-2000:]}")

    def wait_hud(self, text, timeout=15):
        return self.wait(lambda: text in self.hud(), timeout, f"HUD to contain {text!r}")

    def wait_screen(self, text, timeout=15):
        return self.wait(lambda: text in self.screen(), timeout, f"screen to contain {text!r}")

    def wait_done(self, mid, timeout=20):
        return self.wait(lambda: self.stars(mid) > 0, timeout, f"mission {mid} to complete")

    def close_card(self, timeout=10):
        self.wait_screen("Press Enter to continue", timeout)
        self.keys("Enter")

    def close(self):
        self.run_inner("kill-server")
        self.run_outer("kill-server")
        if self._own_home:
            shutil.rmtree(self.home, ignore_errors=True)
