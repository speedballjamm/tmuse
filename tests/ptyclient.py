"""Drive a real tmux client inside a pseudo-terminal, typing real keystrokes."""
import fcntl
import os
import pty
import select
import struct
import termios
import threading
import time


class PtyClient:
    def __init__(self, argv, cols=120, rows=40, env=None):
        pid, fd = pty.fork()
        if pid == 0:
            e = dict(os.environ if env is None else env)
            e.pop("TMUX", None)
            e["TERM"] = "xterm-256color"
            os.execvpe(argv[0], argv, e)
        self.pid, self.fd = pid, fd
        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        self.output = bytearray()
        self._alive = True
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        while self._alive:
            try:
                r, _, _ = select.select([self.fd], [], [], 0.1)
                if r:
                    data = os.read(self.fd, 65536)
                    if not data:
                        break
                    self.output.extend(data)
            except OSError:
                break

    def type(self, data, delay=0.15):
        if isinstance(data, str):
            data = data.encode()
        os.write(self.fd, data)
        time.sleep(delay)

    def keys(self, *seq, delay=0.15):
        """keys('C-b', '%') -> prefix then %."""
        for k in seq:
            self.type(encode_key(k), delay)

    def exited(self):
        try:
            pid, _ = os.waitpid(self.pid, os.WNOHANG)
            return pid != 0
        except ChildProcessError:
            return True

    def close(self):
        self._alive = False
        try:
            os.kill(self.pid, 9)
            os.waitpid(self.pid, 0)
        except (OSError, ChildProcessError):
            pass
        try:
            os.close(self.fd)
        except OSError:
            pass


SPECIAL = {
    "Enter": b"\r", "Escape": b"\x1b", "Space": b" ", "Tab": b"\t", "BSpace": b"\x7f",
    "Up": b"\x1b[A", "Down": b"\x1b[B", "Right": b"\x1b[C", "Left": b"\x1b[D",
    "PageUp": b"\x1b[5~", "PageDown": b"\x1b[6~",
    "C-Up": b"\x1b[1;5A", "C-Down": b"\x1b[1;5B", "C-Right": b"\x1b[1;5C", "C-Left": b"\x1b[1;5D",
    "M-Up": b"\x1b[1;3A", "M-Down": b"\x1b[1;3B", "M-Right": b"\x1b[1;3C", "M-Left": b"\x1b[1;3D",
}


def encode_key(k):
    if k in SPECIAL:
        return SPECIAL[k]
    if k.startswith("C-") and len(k) == 3:
        return bytes([ord(k[2].lower()) & 0x1F])
    if k.startswith("M-") and len(k) == 3:
        return b"\x1b" + k[2].encode()
    return k.encode()
