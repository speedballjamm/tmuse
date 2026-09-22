"""Work out what the player just did by diffing two snapshots."""
from dataclasses import dataclass, field

MODE_ACTIONS = {
    "copy-mode": "copy-mode",
    "view-mode": "view-mode",
    "tree-mode": "tree-mode",
    "clock-mode": "clock-mode",
    "buffer-mode": "buffer-mode",
    "client-mode": "client-mode",
}


@dataclass
class Action:
    kind: str
    info: dict = field(default_factory=dict)

    def __repr__(self):
        return f"Action({self.kind}, {self.info})"


def classify(p, c):
    """Return the list of Actions that turn snapshot p into snapshot c."""
    out = []
    if p is None or c is None:
        return out
    add = lambda kind, **info: out.append(Action(kind, info))

    # clients
    if p.client is None and c.client is not None:
        add("attach", session=c.session)
    elif p.client is not None and c.client is None:
        add("detach")
        return out
    if c.client and not (p.client and p.client.prefix) and c.client.prefix:
        add("prefix")

    # sessions
    pids = {s.id: s for s in p.sessions}
    cids = {s.id: s for s in c.sessions}
    for sid, s in cids.items():
        if sid not in pids:
            add("new-session", name=s.name)
        elif pids[sid].name != s.name:
            add("rename-session", old=pids[sid].name, new=s.name)
    for sid, s in pids.items():
        if sid not in cids:
            add("kill-session", name=s.name)
    if p.client and c.client and p.session != c.session and p.session in [s.name for s in c.sessions]:
        # same session id renamed doesn't count as a switch
        renamed = any(a.kind == "rename-session" and a.info["old"] == p.session for a in out)
        if not renamed:
            add("switch-session", old=p.session, new=c.session)

    # windows (only within the current session, which is what the player sees)
    pw = {w.id: w for w in p.swindows(p.session)}
    cw = {w.id: w for w in c.swindows(c.session)}
    same_session = p.session == c.session or any(a.kind == "rename-session" for a in out)
    if same_session:
        for wid, w in cw.items():
            if wid not in pw:
                old_ids = {x.id for x in p.panes}
                if len(w.panes) == 1 and w.panes[0].id in old_ids:
                    add("break-pane", window=w.name)
                else:
                    add("new-window", index=w.index, name=w.name)
        for wid, w in pw.items():
            if wid not in cw:
                add("kill-window", index=w.index, name=w.name)
        for wid in set(pw) & set(cw):
            if pw[wid].name != cw[wid].name and not cw[wid].auto_name:
                # (automatic-rename stays on unless a person renamed the window)
                add("rename-window", old=pw[wid].name, new=cw[wid].name)
            if pw[wid].index != cw[wid].index:
                add("move-window", old=pw[wid].index, new=cw[wid].index)
        pwin, cwin = p.window, c.window
        if pwin and cwin and pwin.id != cwin.id and cwin.id in pw:
            add("select-window", old=pwin.index, new=cwin.index, name=cwin.name)

    # panes in the current window
    pwin, cwin = p.window, c.window
    if pwin and cwin and pwin.id == cwin.id:
        out.extend(_pane_actions(p, pwin, cwin))
    elif pwin and cwin and pwin.id != cwin.id:
        # pane may have been joined/moved; still report mode changes
        pass

    # modes of the active pane
    pp, cp = p.pane, c.pane
    if pp and cp and pp.id == cp.id and pp.mode != cp.mode:
        if cp.mode:
            add(MODE_ACTIONS.get(cp.mode, cp.mode))
        else:
            add("mode-exit", mode=pp.mode)
    elif cp and cp.mode and (not pp or pp.id != cp.id):
        add(MODE_ACTIONS.get(cp.mode, cp.mode))
    if pp and cp and pp.id == cp.id and cp.mode == "copy-mode":
        if cp.search and not pp.search:
            add("copy-search")
        if cp.selection and not pp.selection:
            add("copy-select")
        if cp.scroll != pp.scroll:
            add("copy-scroll", pos=cp.scroll)

    # buffers
    pb, cb = p.newest_buffer, c.newest_buffer
    if cb and (not pb or (cb.name, cb.created, cb.sample) != (pb.name, pb.created, pb.sample)):
        add("copy", sample=cb.sample)

    # options
    for opt in ("mouse", "prefix"):
        if p.options.get(opt) != c.options.get(opt):
            add("option", name=opt, value=c.options.get(opt))
    return out


def _pane_actions(p, pwin, cwin):
    out = []
    add = lambda kind, **info: out.append(Action(kind, info))
    if pwin.zoomed != cwin.zoomed:
        add("zoom" if cwin.zoomed else "unzoom")
    if pwin.sync != cwin.sync:
        add("sync-on" if cwin.sync else "sync-off")
    pp = {x.id: x for x in pwin.panes}
    cp = {x.id: x for x in cwin.panes}
    new = [cp[i] for i in cp if i not in pp]
    gone = [pp[i] for i in pp if i not in cp]
    for n in new:
        # the pane that was split is the old active pane; compare with it
        was = pwin.active_pane
        after = cp.get(was.id) if was else None
        if after and after.top == n.top and after.height == n.height:
            add("split-h")
        elif after and after.left == n.left and after.width == n.width:
            add("split-v")
        elif after and after.width < was.width:
            add("split-h")
        else:
            add("split-v")
    for g in gone:
        add("kill-pane")
    pa, ca = pwin.active_pane, cwin.active_pane
    if pa and ca and pa.id != ca.id and ca.id in pp:
        add("select-pane", old=pa.id, new=ca.id, dir=_direction(pa, ca))
    if not new and not gone and pwin.zoomed == cwin.zoomed and not cwin.zoomed:
        if pwin.width != cwin.width or pwin.height != cwin.height:
            return out  # terminal resized
        prects = {i: pp[i].rect for i in pp}
        crects = {i: cp[i].rect for i in cp}
        if prects != crects:
            if sorted(prects.values()) == sorted(crects.values()):
                add("swap")
            elif pwin.shape != cwin.shape:
                add("layout")
            else:
                changed = [i for i in prects if prects[i] != crects[i]]
                delta = sum(abs(a - b) for i in changed for a, b in zip(prects[i], crects[i]))
                if delta <= 12 * max(1, len(changed)) and len(changed) <= len(prects):
                    add("resize")
                else:
                    add("layout")
    return out


def _direction(a, b):
    if b.right <= a.left:
        return "left"
    if b.left >= a.right:
        return "right"
    if b.bottom <= a.top:
        return "up"
    if b.top >= a.bottom:
        return "down"
    return ""


# How the sandbox narrates each action: (key id, text)
NARRATION = {
    "prefix": ("prefix", "Prefix is active: now press a command key"),
    "split-h": ("split-h", "Split side by side (split-window -h)"),
    "split-v": ("split-v", "Split top/bottom (split-window -v)"),
    "kill-pane": ("kill-pane", "A pane closed (C-b x, or exit in the shell)"),
    "select-pane": ("pane-nav", "Moved to another pane (arrows, C-b o, C-b ; or C-b q N)"),
    "zoom": ("zoom", "Zoomed in (C-b z again to unzoom)"),
    "unzoom": ("zoom", "Unzoomed"),
    "resize": ("resize", "Resized a pane"),
    "swap": ("swap", "Panes moved around (swap or rotate)"),
    "layout": ("layout-next", "Layout changed"),
    "break-pane": ("break-pane", "Pane broken out into its own window"),
    "new-window": ("new-window", "New window created"),
    "kill-window": ("kill-window", "A window closed"),
    "select-window": ("select-window", "Switched window (n, p, l, 0-9, or the tree)"),
    "rename-window": ("rename-window", "Window renamed"),
    "move-window": ("move-window", "Window moved to a new index"),
    "new-session": ("tmux-new", "New session created"),
    "kill-session": ("tmux-kill", "A session ended"),
    "rename-session": ("rename-session", "Session renamed"),
    "switch-session": ("session-cycle", "Switched session"),
    "detach": ("detach", "Detached (everything keeps running)"),
    "attach": ("tmux-attach", "Attached"),
    "copy-mode": ("copy-mode", "Copy mode: scroll, search, select. q leaves"),
    "view-mode": ("list-keys", "Viewing a list (q leaves)"),
    "tree-mode": ("window-tree", "Tree chooser: arrows move, Enter picks, q leaves"),
    "clock-mode": ("clock", "Clock mode, very handy for impressing people"),
    "buffer-mode": ("choose-buffer", "Buffer chooser: Enter pastes"),
    "copy": ("copy-select", "Copied text into a paste buffer"),
    "copy-search": ("copy-search", "Searching in copy mode (n = next match)"),
    "copy-select": ("copy-select", "Selecting: move, then Enter copies"),
    "sync-on": ("sync", "Synchronized input ON: typing goes to every pane"),
    "sync-off": ("sync", "Synchronized input off"),
}
