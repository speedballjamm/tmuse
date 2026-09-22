"""Helpers missions use to arrange the sandbox before a step."""
import os
import shlex
import sys
import time

from . import paths, state

LIVE_SESSION = "tmuse"


def snap(ctx):
    s = state.take(ctx.tmux)
    ctx.s = s
    return s


def client(ctx):
    s = ctx.s or snap(ctx)
    return s.client.name if s and s.client else None


def reset(ctx, session=LIVE_SESSION, windows=1, names=None, keep=(), clear_buffers=False):
    """One session (plus `keep`), `windows` fresh single-pane windows, client on the first.
    Returns the list of window ids."""
    t = ctx.tmux
    s = snap(ctx)
    if s is None:
        return []
    # get out of any mode so nothing is left half-done
    if s.pane and s.pane.mode:
        t.run("send-keys", "-t", s.pane.id, "-X", "cancel")
    if not s.has_session(session):
        if s.client and s.session and s.session not in keep:
            t.run("rename-session", "-t", s.session, session)
        else:
            t.run("new-session", "-d", "-s", session)
    names = list(names or [])
    wids = []
    for i in range(windows):
        args = ["new-window", "-d", "-P", "-F", "#{window_id}", "-t", f"{session}:"]
        if i < len(names) and names[i]:
            args += ["-n", names[i]]
        wids.append(t.out(*args).strip())
    c = client(ctx)
    if c:
        t.run("switch-client", "-c", c, "-t", session)
    t.run("select-window", "-t", wids[0])
    s = snap(ctx)
    for w in s.swindows(session):
        if w.id not in wids:
            t.run("kill-window", "-t", w.id)
    for other in s.sessions:
        if other.name != session and other.name not in keep:
            t.run("kill-session", "-t", other.id)
    t.run("move-window", "-r", "-t", session)
    t.run("select-window", "-t", wids[0])
    if clear_buffers:
        for b in s.buffers:
            t.run("delete-buffer", "-b", b.name)
    t.run("setw", "-gu", "synchronize-panes")
    snap(ctx)
    return wids


def split(ctx, n, how="h", target=None):
    """Grow the current window to n panes. how: h, v, tiled, main-vertical, grid."""
    t = ctx.tmux
    s = snap(ctx)
    w = s.window
    target = target or w.id
    for _ in range(n - len(w.panes)):
        flag = "-v" if how == "v" else "-h"
        t.run("split-window", "-d", flag, "-t", target)
        t.run("select-layout", "-t", target, _layout(how))
    t.run("select-layout", "-t", target, _layout(how))
    snap(ctx)


def _layout(how):
    return {"h": "even-horizontal", "v": "even-vertical", "tiled": "tiled", "grid": "tiled",
            "main-vertical": "main-vertical"}.get(how, "tiled")


def select(ctx, which):
    """Select a pane in the current window: 'tl', 'tr', 'bl', 'br', 'left', 'right' or an index."""
    s = snap(ctx)
    w = s.window
    if which == "left":
        p = w.leftmost()
    elif which == "right":
        p = w.rightmost()
    elif isinstance(which, int):
        p = sorted(w.panes, key=lambda x: x.index)[which]
    else:
        p = w.corner(which)
    ctx.tmux.run("select-pane", "-t", p.id)
    snap(ctx)
    return p.id


def run_in(ctx, pane, program, *args, keep_shell=True):
    """Respawn a pane running one of game/panes.py's programs, then a shell."""
    cmd = "PYTHONPATH={} {} -m game.panes {} {}".format(
        shlex.quote(paths.ROOT), shlex.quote(sys.executable), program, " ".join(shlex.quote(str(a)) for a in args))
    if keep_shell:
        cmd += '; exec "${SHELL:-/bin/sh}"'
    ctx.tmux.run("clear-history", "-t", pane)
    ctx.tmux.run("respawn-pane", "-k", "-t", pane, cmd)


def label(ctx, labels):
    """Put a big name tag in each pane of the current window, in index order."""
    s = snap(ctx)
    panes = sorted(s.window.panes, key=lambda p: p.index)
    for p, name in zip(panes, labels):
        run_in(ctx, p.id, "label", name)
    time.sleep(0.2)


def settle(ctx, secs=0.3):
    time.sleep(secs)
    return snap(ctx)


def pane_env():
    env = dict(os.environ)
    env["PYTHONPATH"] = paths.ROOT
    return env
