"""Show a lesson card (runs inside a tmux popup).

    python3 -m game.card CARD_ID [--prefix C-b]
    python3 -m game.card --file card.json
"""
import json
import os
import shutil
import sys
import termios
import tty

from . import markup
from .cards import CARDS

TITLE = "\x1b[1;38;5;255;48;5;24m"
DIM = "\x1b[38;5;244m"
RESET = "\x1b[0m"


def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = os.read(fd, 8)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch


def show(card, prefix="C-b"):
    cols, rows = shutil.get_terminal_size((80, 24))
    lines = card["body"].rstrip("\n").split("\n")
    page = max(3, rows - 4)
    pos = 0
    while True:
        sys.stdout.write("\x1b[2J\x1b[H")
        sys.stdout.write(f"{TITLE} {markup.plain(card['title'], prefix):<{cols - 1}}{RESET}\n\n")
        for line in lines[pos:pos + page]:
            sys.stdout.write(" " + markup.to_ansi(line, prefix) + "\n")
        more = pos + page < len(lines)
        sys.stdout.write("\n" + DIM + (" Space/↓ = more   Enter = done" if more else " Press Enter to continue")
                         + RESET)
        sys.stdout.flush()
        ch = getch()
        if more and ch in (b" ", b"\x1b[B", b"j", b"\x1b[6~"):
            pos += page - 1
        elif ch in (b"\x1b[A", b"k", b"\x1b[5~") and pos:
            pos = max(0, pos - page + 1)
        elif ch in (b"\r", b"\n", b"q", b"\x1b", b"\x03"):
            if more and ch in (b"\r", b"\n"):
                pos += page - 1
                continue
            return


def main(argv):
    prefix = "C-b"
    if "--prefix" in argv:
        i = argv.index("--prefix")
        prefix = argv[i + 1]
        del argv[i:i + 2]
    if argv and argv[0] == "--file":
        with open(argv[1]) as f:
            card = json.load(f)
    else:
        card = CARDS[argv[0]]
    try:
        show(card, prefix)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main(sys.argv[1:])
