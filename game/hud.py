"""The heads-up display: extra lines at the bottom of tmux's status bar.

    ▶ 2.3 Swap │ Swap the panes so A ends up on the right: [C-b }]       ← mission
      (continuation, only when the prompt doesn't fit)                  ← optional
    PREFIX ✔ feedback / hints                         rank · XP · clock   ← messages
    [tmuse] 0:zsh*                                         (normal tmux bar)
"""
import re

from . import markup

A_STYLE = "fg=colour255,bg=colour24"
B_STYLE = "fg=colour252,bg=colour236"
MSG_STYLES = {
    "": B_STYLE,
    "ok": "fg=colour16,bg=colour78",
    "bad": "fg=colour255,bg=colour131",
    "hint": "fg=colour16,bg=colour222",
    "info": "fg=colour16,bg=colour117",
}
MSG_ICONS = {"ok": "✔ ", "bad": "✘ ", "hint": "» ", "info": "• "}

LINE_A = f"#[fill=colour24 {A_STYLE}]#[align=left]#{{E:@tmuse_al}}"
LINE_A2 = f"#[fill=colour24 {A_STYLE}]#[align=left]#{{E:@tmuse_a2}}"
PREFIX_BADGE = ("#{?client_prefix,#[fg=colour16#,bg=colour214#,bold] PREFIX: now press a key "
                f"#[{B_STYLE.replace(',', '#,')}#,nobold] ,}}")
LINE_B = (f"#[fill=colour236 {B_STYLE}]#[align=left]{PREFIX_BADGE}#{{E:@tmuse_bl}}"
          f"#[align=right]#{{E:@tmuse_br}}")

TOKEN = re.compile(r"`[^`]+`|\*\*[^*]+\*\*|\S+|\s+")


def visible_len(raw):
    """Width of marked-up text once rendered (chips get a space either side)."""
    n = 0
    for tok in TOKEN.findall(raw):
        if tok.startswith("`"):
            n += len(tok) - 2 + 2
        elif tok.startswith("**"):
            n += len(tok) - 4
        else:
            n += len(tok)
    return n


def wrap(raw, width):
    """Split marked-up text into (first, rest) at a word boundary, never inside markup."""
    if visible_len(raw) <= width:
        return raw, ""
    used, cut = 0, 0
    toks = TOKEN.findall(raw)
    for i, tok in enumerate(toks):
        w = visible_len(tok)
        if used + w > width:
            break
        used += w
        if tok.isspace():
            cut = i
    if cut == 0:
        return raw, ""
    return "".join(toks[:cut]), "".join(toks[cut:]).strip()


class Hud:
    def __init__(self, tmux):
        self.tmux = tmux
        self.prefix = "C-b"
        self.width = 80
        self.lines = 3
        self.raw = {"title": "", "prompt": "", "right": ""}
        self.values = {"al": "", "a2": "", "bl": "", "br": ""}
        self.pushed = {}

    def install(self, width=None):
        """Put the HUD into the status bar, keeping tmux's normal bar as the last line."""
        t = self.tmux
        if width:
            self.width = width
        default0 = t.out("show", "-gv", "status-format[0]").strip()
        if "@tmuse" in default0 or not default0:
            t.run("set", "-gu", "status-format")
            default0 = t.out("show", "-gv", "status-format[0]").strip()
        self.default0 = default0
        self.lines = 0
        self.pushed = {}
        self._layout()
        self.push()

    def _layout(self):
        want = 4 if self.values["a2"] else 3
        if want == self.lines:
            return
        self.lines = want
        fmts = [LINE_A, LINE_A2, LINE_B] if want == 4 else [LINE_A, LINE_B]
        cmds = [["set", "-g", "status", str(want)]]
        cmds += [["set", "-g", f"status-format[{i}]", f] for i, f in enumerate(fmts)]
        cmds.append(["set", "-g", f"status-format[{len(fmts)}]", self.default0])
        self.tmux.seq(*cmds)

    def healthy(self, snap):
        return snap.options.get("status") in ("3", "4")

    def resize(self, width):
        if width and width != self.width:
            self.width = width
            self._render_prompt()
            self.push()

    def _render_prompt(self):
        title, prompt = self.raw["title"], self.raw["prompt"]
        head = f"#[bold] ▶ {title} #[nobold]│ " if title else " "
        head_len = len(title) + 5 if title else 1
        first, rest = wrap(prompt, max(20, self.width - head_len - 1))
        self.values["al"] = head + markup.to_tmux(first, A_STYLE, self.prefix)
        self.values["a2"] = (" " * min(head_len, 12) + markup.to_tmux(rest, A_STYLE, self.prefix)) if rest else ""

    def set(self, title=None, prompt=None, right=None, msg=None, kind=""):
        if title is not None:
            self.raw["title"] = title
        if prompt is not None:
            self.raw["prompt"] = prompt
        if title is not None or prompt is not None:
            self._render_prompt()
        if right is not None:
            self.raw["right"] = right
        if right is not None:
            self.values["br"] = markup.to_tmux(self.raw["right"], B_STYLE, self.prefix) + " "
        if msg is not None:
            style = MSG_STYLES.get(kind, B_STYLE)
            icon = MSG_ICONS.get(kind, "")
            if msg:
                self.values["bl"] = f"#[{style}] {icon}{markup.to_tmux(msg, style, self.prefix)} #[{B_STYLE}]"
            else:
                self.values["bl"] = ""
        self.push()

    def rerender(self):
        """Re-render everything (e.g. after the prefix changed)."""
        self._render_prompt()
        self.values["br"] = markup.to_tmux(self.raw["right"], B_STYLE, self.prefix) + " "
        self.pushed = {}
        self.push()

    def push(self):
        self._layout()
        cmds = [["set", "-g", f"@tmuse_{k}", v] for k, v in self.values.items() if self.pushed.get(k) != v]
        if not cmds:
            return
        cmds.append(["refresh-client", "-S"])
        self.tmux.seq(*cmds)
        self.pushed = dict(self.values)
