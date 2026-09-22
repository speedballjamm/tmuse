"""Every key and command the game teaches. Drives the cheat sheet, sandbox
narration and spaced-repetition review."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Key:
    id: str
    keys: str       # how to press it, e.g. "C-b %"
    desc: str
    world: int
    cmd: str = ""   # the tmux command behind it
    group: str = ""


KEYS = [
    # World 0
    Key("prefix", "C-b", "The prefix: press it, let go, then press a command key", 0, "", "Basics"),
    Key("list-keys", "C-b ?", "List every key binding (q to leave)", 0, "list-keys", "Basics"),
    Key("clock", "C-b t", "Big clock (any key to leave)", 0, "clock-mode", "Basics"),
    # World 1
    Key("split-h", "C-b %", "Split pane left | right", 1, "split-window -h", "Panes"),
    Key("split-v", 'C-b "', "Split pane top / bottom", 1, "split-window -v", "Panes"),
    Key("pane-nav", "C-b ←↑→↓", "Move to the pane in that direction", 1, "select-pane -L/-U/-R/-D", "Panes"),
    Key("pane-next", "C-b o", "Cycle to the next pane", 1, "select-pane -t :.+", "Panes"),
    Key("pane-last", "C-b ;", "Jump to the previously active pane", 1, "last-pane", "Panes"),
    Key("kill-pane", "C-b x", "Kill the active pane (y to confirm)", 1, "kill-pane", "Panes"),
    Key("exit", "exit", "Typing exit (or C-d) in a shell closes its pane", 1, "", "Panes"),
    Key("pane-numbers", "C-b q", "Flash pane numbers; press one to jump there", 1, "display-panes", "Panes"),
    # World 2
    Key("zoom", "C-b z", "Zoom / unzoom the active pane", 2, "resize-pane -Z", "Pane power"),
    Key("resize", "C-b C-←↑→↓", "Resize by 1 cell (repeatable; hold Ctrl)", 2, "resize-pane -L/-U/-R/-D", "Pane power"),
    Key("resize5", "C-b M-←↑→↓", "Resize by 5 cells (Option/Meta)", 2, "resize-pane -L 5", "Pane power"),
    Key("swap", "C-b { / }", "Swap pane with previous / next", 2, "swap-pane -U / -D", "Pane power"),
    Key("rotate", "C-b C-o", "Rotate panes (M-o rotates the other way)", 2, "rotate-window", "Pane power"),
    Key("layout-next", "C-b Space", "Cycle through preset layouts", 2, "next-layout", "Pane power"),
    Key("layout-pick", "C-b M-1…M-5", "even-horizontal, even-vertical, main-horizontal, main-vertical, tiled", 2,
        "select-layout", "Pane power"),
    Key("break-pane", "C-b !", "Break the pane out into its own window", 2, "break-pane", "Pane power"),
    # World 3
    Key("new-window", "C-b c", "Create a new window", 3, "new-window", "Windows"),
    Key("next-window", "C-b n", "Next window", 3, "next-window", "Windows"),
    Key("prev-window", "C-b p", "Previous window", 3, "previous-window", "Windows"),
    Key("select-window", "C-b 0…9", "Go to window by number", 3, "select-window -t :N", "Windows"),
    Key("last-window", "C-b l", "Go to the previously active window (lowercase L)", 3, "last-window", "Windows"),
    Key("rename-window", "C-b ,", "Rename the current window", 3, "rename-window", "Windows"),
    Key("kill-window", "C-b &", "Kill the current window (y to confirm)", 3, "kill-window", "Windows"),
    Key("window-tree", "C-b w", "Choose a window from a tree (Enter picks)", 3, "choose-tree -Zw", "Windows"),
    Key("find-window", "C-b f", "Find a window by name or content", 3, "find-window", "Windows"),
    Key("move-window", "C-b .", "Move / renumber the current window", 3, "move-window -t N", "Windows"),
    Key("window-index", "C-b '", "Prompt for a window index (for 10+)", 3, "select-window -t :N", "Windows"),
    # World 4
    Key("detach", "C-b d", "Detach: leave tmux, everything keeps running", 4, "detach-client", "Sessions"),
    Key("tmux-ls", "tmux ls", "(outside) List sessions", 4, "list-sessions", "Sessions"),
    Key("tmux-attach", "tmux a", "(outside) Attach to the most recent session", 4, "attach", "Sessions"),
    Key("tmux-attach-t", "tmux a -t NAME", "(outside) Attach to a named session", 4, "attach -t", "Sessions"),
    Key("tmux-new", "tmux new -s NAME", "(outside) Start a new named session", 4, "new-session -s", "Sessions"),
    Key("tmux-kill", "tmux kill-session -t NAME", "(outside) Kill a session", 4, "kill-session -t", "Sessions"),
    Key("rename-session", "C-b $", "Rename the current session", 4, "rename-session", "Sessions"),
    Key("session-tree", "C-b s", "Choose a session from a tree", 4, "choose-tree -Zs", "Sessions"),
    Key("session-cycle", "C-b ( / )", "Previous / next session", 4, "switch-client -p / -n", "Sessions"),
    Key("session-last", "C-b L", "Last session", 4, "switch-client -l", "Sessions"),
    # World 5
    Key("copy-mode", "C-b [", "Enter copy mode (scroll the past; q leaves)", 5, "copy-mode", "Copy mode"),
    Key("copy-scroll", "PgUp PgDn ↑↓ k j", "Scroll / move in copy mode (g top, G bottom)", 5, "", "Copy mode"),
    Key("copy-search", "? and /", "Search up / down in copy mode (n next, N back)", 5, "search-backward", "Copy mode"),
    Key("copy-select", "Space … Enter", "Start a selection, move, Enter copies (vi keys)", 5, "begin-selection",
        "Copy mode"),
    Key("paste", "C-b ]", "Paste the most recent copy", 5, "paste-buffer", "Copy mode"),
    Key("choose-buffer", "C-b =", "Pick from everything you've copied", 5, "choose-buffer", "Copy mode"),
    Key("copy-pgup", "C-b PgUp", "Enter copy mode and scroll up in one go", 5, "copy-mode -u", "Copy mode"),
    # World 6
    Key("command-prompt", "C-b :", "Command prompt: type any tmux command", 6, "command-prompt", "Commands"),
    Key("sync", ":setw synchronize-panes", "Type into every pane at once", 6, "setw synchronize-panes on",
        "Commands"),
    Key("describe-key", "C-b /", "Describe what a key does", 6, "list-keys -1N", "Commands"),
    Key("mouse", ":set -g mouse on", "Mouse: click panes, drag borders, scroll", 6, "set -g mouse on",
        "Commands"),
    Key("info", "C-b i", "Show window info", 6, "display-message", "Commands"),
    Key("messages", "C-b ~", "Show recent tmux messages", 6, "show-messages", "Commands"),
    # World 7
    Key("source", ":source-file FILE", "Load a config file", 7, "source-file", "Config"),
    Key("conf-bind", "bind KEY CMD", "Config: add a key binding", 7, "bind-key", "Config"),
    Key("conf-set", "set -g OPTION VALUE", "Config: set an option", 7, "set-option", "Config"),
]

BY_ID = {k.id: k for k in KEYS}


def get(kid):
    return BY_ID[kid]
