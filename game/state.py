"""A snapshot of the whole tmux server, gathered in a single tmux call."""
import re
from dataclasses import dataclass, field
from typing import List, Optional

SEP = "\x1f"

CLIENT_F = SEP.join(["C", "#{client_name}", "#{client_session}", "#{client_prefix}",
                     "#{client_key_table}", "#{client_width}", "#{client_height}", "#{client_activity}"])
SESSION_F = SEP.join(["S", "#{session_id}", "#{session_name}", "#{session_windows}",
                      "#{session_attached}", "#{session_last_attached}"])
WINDOW_F = SEP.join(["W", "#{session_name}", "#{window_id}", "#{window_index}", "#{window_name}",
                     "#{window_active}", "#{window_zoomed_flag}", "#{window_layout}", "#{window_panes}",
                     "#{synchronize-panes}", "#{window_width}", "#{window_height}", "#{window_last_flag}",
                     "#{automatic-rename}"])
PANE_F = SEP.join(["P", "#{session_name}", "#{window_id}", "#{pane_id}", "#{pane_index}",
                   "#{pane_left}", "#{pane_top}", "#{pane_width}", "#{pane_height}", "#{pane_active}",
                   "#{pane_mode}", "#{scroll_position}", "#{search_present}", "#{history_size}",
                   "#{pane_current_command}", "#{selection_present}", "#{copy_cursor_line}"])
BUFFER_F = SEP.join(["B", "#{buffer_name}", "#{buffer_size}", "#{buffer_created}", "#{buffer_sample}"])
OPTS = ["prefix", "mouse", "status", "base-index", "history-limit"]


@dataclass
class Client:
    name: str
    session: str
    prefix: bool
    key_table: str
    width: int
    height: int
    activity: int


@dataclass
class Session:
    id: str
    name: str
    windows: int
    attached: int
    last_attached: int


@dataclass
class Pane:
    session: str
    window_id: str
    id: str
    index: int
    left: int
    top: int
    width: int
    height: int
    active: bool
    mode: str
    scroll: int
    search: bool
    history: int
    command: str
    selection: bool
    cursor_line: str

    @property
    def rect(self):
        return (self.left, self.top, self.width, self.height)

    @property
    def right(self):
        return self.left + self.width

    @property
    def bottom(self):
        return self.top + self.height


@dataclass
class Window:
    session: str
    id: str
    index: int
    name: str
    active: bool
    zoomed: bool
    layout: str
    npanes: int
    sync: bool
    width: int
    height: int
    last: bool
    auto_name: bool = False
    panes: List[Pane] = field(default_factory=list)

    @property
    def shape(self):
        """Layout nesting pattern without sizes, e.g. '{[]}'."""
        return re.sub(r"[^\[\]{}]", "", self.layout.split(",", 1)[-1])

    @property
    def active_pane(self):
        for p in self.panes:
            if p.active:
                return p
        return self.panes[0] if self.panes else None

    def orientation(self):
        """'left-right', 'top-bottom', 'mixed' or 'single'."""
        if len(self.panes) < 2:
            return "single"
        tops = {p.top for p in self.panes}
        lefts = {p.left for p in self.panes}
        if len(tops) == 1:
            return "left-right"
        if len(lefts) == 1:
            return "top-bottom"
        return "mixed"

    def is_grid(self, cols, rows):
        return (len(self.panes) == cols * rows
                and len({p.left for p in self.panes}) == cols
                and len({p.top for p in self.panes}) == rows)

    def corner(self, which):
        """Pane nearest a corner: 'tl', 'tr', 'bl', 'br'."""
        if not self.panes:
            return None
        def key(p):
            x = p.left if which[1] == "l" else -(p.right)
            y = p.top if which[0] == "t" else -(p.bottom)
            return (x + y, y)
        return min(self.panes, key=key)

    def leftmost(self):
        return min(self.panes, key=lambda p: (p.left, p.top))

    def rightmost(self):
        return max(self.panes, key=lambda p: (p.right, -p.top))

    def pane_order(self):
        return [p.id for p in sorted(self.panes, key=lambda p: p.index)]


@dataclass
class Buffer:
    name: str
    size: int
    created: int
    sample: str


@dataclass
class Snapshot:
    clients: List[Client]
    sessions: List[Session]
    windows: List[Window]
    panes: List[Pane]
    buffers: List[Buffer]
    options: dict

    # derived
    client: Optional[Client] = None
    session: Optional[str] = None

    @property
    def attached(self):
        return self.client is not None

    @property
    def prefix_key(self):
        return self.options.get("prefix", "C-b")

    def session_names(self):
        return [s.name for s in self.sessions]

    def has_session(self, name):
        return any(s.name == name for s in self.sessions)

    def swindows(self, session=None):
        session = session or self.session
        return sorted([w for w in self.windows if w.session == session], key=lambda w: w.index)

    @property
    def window(self) -> Optional[Window]:
        for w in self.swindows():
            if w.active:
                return w
        return None

    @property
    def pane(self) -> Optional[Pane]:
        w = self.window
        return w.active_pane if w else None

    def find_window(self, name, session=None):
        for w in self.swindows(session):
            if w.name == name:
                return w
        return None

    def window_by_id(self, wid):
        for w in self.windows:
            if w.id == wid:
                return w
        return None

    def pane_by_id(self, pid):
        for p in self.panes:
            if p.id == pid:
                return p
        return None

    @property
    def newest_buffer(self):
        # tmux lists buffers newest first
        return self.buffers[0] if self.buffers else None

    @property
    def mode(self):
        p = self.pane
        return p.mode if p else ""


def _i(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def take(tmux) -> Optional[Snapshot]:
    """Gather everything. Returns None if the server is gone."""
    # list-panes -a errors when there are no sessions, and tmux stops at the
    # first error, so it goes last.
    cmds = [["list-clients", "-F", CLIENT_F],
            ["list-sessions", "-F", SESSION_F],
            ["list-buffers", "-F", BUFFER_F]]
    for o in OPTS:
        cmds.append(["show", "-g", o])
    cmds.append(["list-windows", "-a", "-F", WINDOW_F])
    cmds.append(["list-panes", "-a", "-F", PANE_F])
    r = tmux.seq(*cmds)
    if r.returncode != 0 and not tmux.alive():
        return None
    clients, sessions, windows, panes, buffers, options = [], [], [], [], [], {}
    for line in r.stdout.splitlines():
        f = line.split(SEP)
        tag = f[0]
        if tag == "C" and len(f) >= 8:
            clients.append(Client(f[1], f[2], f[3] == "1", f[4], _i(f[5]), _i(f[6]), _i(f[7])))
        elif tag == "S" and len(f) >= 6:
            sessions.append(Session(f[1], f[2], _i(f[3]), _i(f[4]), _i(f[5])))
        elif tag == "W" and len(f) >= 14:
            windows.append(Window(f[1], f[2], _i(f[3]), f[4], f[5] == "1", f[6] == "1", f[7], _i(f[8]),
                                  f[9] == "1", _i(f[10]), _i(f[11]), f[12] == "1", f[13] == "1"))
        elif tag == "P" and len(f) >= 17:
            panes.append(Pane(f[1], f[2], f[3], _i(f[4]), _i(f[5]), _i(f[6]), _i(f[7]), _i(f[8]),
                              f[9] == "1", f[10], _i(f[11]), f[12] == "1", _i(f[13]), f[14],
                              f[15] == "1", SEP.join(f[16:])))
        elif tag == "B" and len(f) >= 5:
            buffers.append(Buffer(f[1], _i(f[2]), _i(f[3]), SEP.join(f[4:])))
        elif " " in line and line.split(" ", 1)[0] in OPTS:
            k, v = line.split(" ", 1)
            options[k] = v.strip().strip('"')
    by_win = {}
    for w in windows:
        by_win.setdefault(w.id, []).append(w)
    for p in panes:
        for w in by_win.get(p.window_id, []):
            if w.session == p.session:
                w.panes.append(p)
    snap = Snapshot(clients, sessions, windows, panes, buffers, options)
    if clients:
        snap.client = max(clients, key=lambda c: c.activity)
        snap.session = snap.client.session
    elif sessions:
        snap.session = max(sessions, key=lambda s: s.last_attached).name
    return snap
