"""Which key bindings did the player just use?

tmux's message log (show-messages) records every command a key binding runs:
    17:54: /dev/ttys005 key /: list-keys -1N z
The log is newest-first, so new entries are the lines above what we saw last time.
"""
import re

LINE = re.compile(r"^\d\d:\d\d: (\S+) key (.+?): (.*)$")


class KeyLog:
    def __init__(self, tmux):
        self.tmux = tmux
        self.prev = None

    def poll(self):
        """Return [(key, command), ...] used since the last poll, oldest first."""
        lines = self.tmux.out("show-messages").splitlines()
        if self.prev is None:
            self.prev = lines
            return []
        n = new_count(self.prev, lines)
        self.prev = lines
        out = []
        for line in reversed(lines[:n]):
            m = LINE.match(line)
            if m:
                out.append((m.group(2), m.group(3)))
        return out


def new_count(prev, cur):
    """How many lines at the top of `cur` weren't in `prev`."""
    if not prev:
        return len(cur)
    for n in range(len(cur) + 1):
        rest = cur[n:]
        if rest == prev[:len(rest)]:
            return n
    return len(cur)


def describe(key, cmd, prefix="C-b"):
    """How to show a logged key to the player."""
    if key.startswith(("Mouse", "Wheel", "Double", "Triple")):
        return f"mouse ({key})"
    if cmd.startswith("send-keys -X") or cmd.startswith("send -X"):
        return f"{key} (in copy mode)"
    return f"{prefix} {key}"
