"""Tiny markup shared by the HUD and lesson cards.

    `C-b %`   -> a key chip
    **text**  -> bold
"""
import re

CHIP = re.compile(r"`([^`]+)`")
BOLD = re.compile(r"\*\*([^*]+)\*\*")


def swap_prefix(text, prefix):
    """Show the player's real prefix if they've changed it (World 7)."""
    if prefix and prefix != "C-b":
        text = re.sub(r"(?<![\w-])C-b(?=[ `]|$)", prefix, text)
    return text


def to_tmux(text, base, prefix="C-b"):
    """Render markup as a tmux status-line format. `base` is the line's style."""
    # '#' starts a tmux format and '%' a strftime code in status lines
    text = swap_prefix(text, prefix).replace("#", "##").replace("%", "%%")
    text = CHIP.sub(lambda m: f"#[fg=colour16,bg=colour214,bold] {m.group(1)} #[{base},nobold]", text)
    text = BOLD.sub(lambda m: f"#[bold]{m.group(1)}#[nobold]", text)
    return text


RESET = "\x1b[0m"


def to_ansi(text, prefix="C-b"):
    text = swap_prefix(text, prefix)
    text = CHIP.sub(lambda m: f"\x1b[1;30;48;5;214m {m.group(1)} {RESET}", text)
    text = BOLD.sub(lambda m: f"\x1b[1m{m.group(1)}{RESET}", text)
    return text


def plain(text, prefix="C-b"):
    text = swap_prefix(text, prefix)
    return BOLD.sub(r"\1", CHIP.sub(r"\1", text))
