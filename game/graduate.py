"""Offer to install the practice config as the real ~/.tmux.conf (runs in a popup)."""
import os
import shutil
import sys
import time

from . import paths

REAL = os.path.expanduser(os.environ.get("TMUSE_REAL_CONF", "~/.tmux.conf"))
B = "\x1b[1m"
DIM = "\x1b[38;5;244m"
GREEN = "\x1b[38;5;78m"
R = "\x1b[0m"


def rewrite(text):
    """Point reload bindings at the real config file."""
    return text.replace(paths.SANDBOX_CONF_TILDE, "~/.tmux.conf").replace(paths.SANDBOX_CONF, "~/.tmux.conf")


def main():
    try:
        with open(paths.SANDBOX_CONF) as f:
            text = rewrite(f.read())
    except OSError:
        print("No practice config found. Nothing to install.")
        input("\nPress Enter…")
        return
    print(f"{B}Your tmux config{R}\n")
    for line in text.rstrip().splitlines():
        print(f"  {DIM if line.strip().startswith('#') else ''}{line}{R}")
    print()
    exists = os.path.exists(REAL)
    if exists:
        print(f"You already have {B}~/.tmux.conf{R}. It will be backed up first.")
    ans = input(f"Install this as {B}~/.tmux.conf{R}? [y/N] ").strip().lower()
    if ans not in ("y", "yes"):
        print("\nNo problem. It stays at " + paths.SANDBOX_CONF_TILDE)
        time.sleep(1.5)
        return
    if exists:
        backup = REAL + time.strftime(".bak-%Y%m%d-%H%M%S")
        shutil.copy2(REAL, backup)
        print(f"Backed up the old one to {backup}")
    with open(REAL, "w") as f:
        f.write(text)
    print(f"\n{GREEN}Installed!{R} New tmux servers will use it.")
    print("Inside an already-running tmux:  tmux source-file ~/.tmux.conf")
    input("\nPress Enter…")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)
