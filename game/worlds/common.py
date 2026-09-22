"""Shared building blocks for mission files."""
import os
import plistlib
import random
import re
import subprocess
import sys
from shlex import quote as shlex_quote  # noqa: F401

from .. import paths
from ..model import Mission, Step, World  # noqa: F401  (re-exported for world files)
from ..setups import label, reset, run_in, select, settle, snap, split  # noqa: F401

EDITORS = {"nano", "pico", "vim", "vi", "nvim", "emacs", "micro", "hx", "helix", "kak", "joe", "ne", "mg"}
WORDS = ["ORCA", "LYNX", "OTTER", "FALCON", "BADGER", "HERON", "IBEX", "MARTEN", "OCELOT", "PUFFIN",
         "TAPIR", "WOMBAT", "GECKO", "KESTREL", "NARWHAL", "QUOKKA"]


def mac_steals_ctrl_arrows():
    """True when macOS grabs Ctrl+←/→ for "Move left/right a space" (hotkeys 79/81).

    Those shortcuts are on by default and never reach the terminal, so tmux's
    `C-b C-→` resize binding silently does nothing.
    """
    if sys.platform != "darwin":
        return False
    try:
        raw = subprocess.run(["defaults", "export", "com.apple.symbolichotkeys", "-"],
                             capture_output=True, timeout=3).stdout
        keys = plistlib.loads(raw).get("AppleSymbolicHotKeys", {})
    except Exception:
        return True  # can't tell; assume the macOS default
    return any(keys.get(k, {}).get("enabled", True) for k in ("79", "81"))


MAC_ARROWS = mac_steals_ctrl_arrows()


# --- quick state readers -------------------------------------------------------

def win(c):
    return c.s.window


def npanes(c):
    w = c.s.window
    return len(w.panes) if w else 0


def active(c):
    return c.s.pane


def active_id(c):
    p = c.s.pane
    return p.id if p else None


def mode(c):
    return c.s.mode


def names(c, session=None):
    return [w.name for w in c.s.swindows(session)]


def cur_name(c):
    w = c.s.window
    return w.name if w else None


def session(c):
    return c.s.session


def attached(c):
    return c.s.attached


def is_main_vertical(w, n):
    if not w or len(w.panes) != n or w.zoomed:
        return False
    left = w.leftmost()
    rest = [p for p in w.panes if p.id != left.id]
    return (left.height == w.height and len({p.left for p in rest}) == 1
            and rest[0].left > left.left and len({p.top for p in rest}) == n - 1)


def lines_of(text):
    return [l.rstrip() for l in text.splitlines()]


def pane_has_line(c, pane_id, text):
    return any(l.strip() == text for l in lines_of(c.capture(pane_id)))


def pane_contains(c, pane_id, text):
    return text in c.capture(pane_id)


def visible_in_copy(c, needle):
    """Is a line containing `needle` on screen while the active pane is in copy mode?"""
    p = c.s.pane
    if not p or p.mode != "copy-mode":
        return False
    full = c.capture(p.id, history=True, join=False).split("\n")
    idx = [i for i, l in enumerate(full) if needle in l]
    if not idx:
        return False
    top = p.history - p.scroll
    return any(top <= i < top + p.height for i in idx)


def buffer_has(c, text):
    b = c.s.newest_buffer
    return bool(b and text in b.sample)


def answered(c, expected, strip=("SECRET:", "CODE:")):
    a = c.answer()
    if a is None:
        return False
    got = a.strip().upper()
    for s in strip:
        got = got.replace(s, "").strip()
    if got == expected.upper():
        return True
    c.say(f"'{a}' isn't it. Look again!")
    return False


def rand_code(prefix=""):
    return f"{prefix}{random.choice(WORDS)}-{random.randint(100, 999)}"


# --- config helpers (World 7) -----------------------------------------------------

CONF_HEADER = """\
# My tmux config (practice copy, made in tmuse).
# Lines starting with # are comments.
"""


def conf_path():
    return paths.SANDBOX_CONF


def conf_shown():
    return paths.SANDBOX_CONF_TILDE


def ensure_conf():
    paths.ensure()
    if not os.path.exists(conf_path()):
        with open(conf_path(), "w") as f:
            f.write(CONF_HEADER)


def conf_lines():
    try:
        with open(conf_path()) as f:
            return [l.strip() for l in f.read().splitlines() if l.strip() and not l.strip().startswith("#")]
    except OSError:
        return []


def conf_has(pattern):
    rx = re.compile(pattern)
    return any(rx.search(l) for l in conf_lines())


def in_editor(c):
    p = c.s.pane
    return bool(p and p.command in EDITORS)


def binding(c, key, table="prefix"):
    """The command bound to `key`, or "". (Listing a single key shows it on the
    client's status line instead of printing it, so list the table and filter.)"""
    for line in c.tmux.out("list-keys", "-T", table).splitlines():
        parts = line.split()
        try:
            i = parts.index("-T")
        except ValueError:
            continue
        if len(parts) > i + 2 and parts[i + 2] in (key, "\\" + key):
            return " ".join(parts[i + 3:])
    return ""


def opt(c, name, window=False):
    return c.tmux.option(name, window)


# --- common setups ------------------------------------------------------------------

def fresh(c):
    reset(c)


def panes_h(n, sel=None):
    def setup(c):
        reset(c)
        split(c, n, "h")
        if sel is not None:
            select(c, sel)
    return setup


def panes_v(n, sel=None):
    def setup(c):
        reset(c)
        split(c, n, "v")
        if sel is not None:
            select(c, sel)
    return setup


def grid(sel=None):
    def setup(c):
        reset(c)
        split(c, 4, "tiled")
        if sel is not None:
            select(c, sel)
    return setup


def windows(*wnames, active=0, session="tmuse", tags=False):
    """`tags` puts a big WINDOW N name tag in each window so switching is visible."""
    def setup(c):
        ids = reset(c, session=session, windows=len(wnames), names=list(wnames))
        if tags:
            for i, (wid, name) in enumerate(zip(ids, wnames)):
                run_in(c, f"{wid}.0", "winlabel", i, *([name] if name else []))
        c.tmux.run("select-window", "-t", ids[active])
        c.mem["wids"] = ids
        snap(c)
    return setup


def sessions(*snames, current=None):
    """Sessions with the client on `current` (default: the first)."""
    current = current or snames[0]

    def setup(c):
        reset(c, session=current)
        for n in snames:
            if n != current:
                c.tmux.run("new-session", "-d", "-s", n)
        snap(c)
    return setup


def chain(*fns):
    def setup(c):
        for f in fns:
            f(c)
    return setup
