"""Little programs the game runs inside your panes (logs to dig through, labels, a ticker).

    python3 -m game.panes label A
    python3 -m game.panes winlabel INDEX [NAME]
    python3 -m game.panes log SEED SECRET_LINE [BEFORE] [AFTER]
    python3 -m game.panes search SEED WORD N
    python3 -m game.panes incident SEED FIRST_ID DECOY1,DECOY2 [DELAY]
    python3 -m game.panes ticker SECS CODE
    python3 -m game.panes banner TEXT
"""
import random
import sys
import time

SERVICES = ["api", "auth", "db", "cache", "billing", "search", "queue", "cdn"]
MSGS = [
    "GET /v1/users/{n} 200 {ms}ms", "POST /v1/orders 201 {ms}ms", "cache hit ratio {pct}%",
    "worker {n} heartbeat ok", "rotated log segment {n}", "GET /healthz 200 1ms",
    "connection pool size={n}", "flushed {n} metrics", "scheduled job #{n} complete",
    "GET /v1/search?q=tmux 200 {ms}ms", "user {n} logged in", "TLS session resumed",
]
LEVELS = ["INFO"] * 6 + ["DEBUG"] * 3 + ["WARN"]


def fake_line(rng, i):
    msg = rng.choice(MSGS).format(n=rng.randint(1, 9999), ms=rng.randint(2, 400), pct=rng.randint(60, 99))
    h, m, s = 9 + i // 3600 % 12, (i // 60) % 60, i % 60
    return f"{h:02d}:{m:02d}:{s:02d} {rng.choice(LEVELS):<5} [{rng.choice(SERVICES):<7}] {msg}"


def label(name):
    print("\x1b[2J\x1b[H")
    print()
    print(f"      \x1b[1;30;48;5;117m            \x1b[0m")
    print(f"      \x1b[1;30;48;5;117m   PANE {name:<3} \x1b[0m")
    print(f"      \x1b[1;30;48;5;117m            \x1b[0m")
    print()


WIN_COLOURS = [117, 150, 217, 222, 183, 116, 210, 186]


def winlabel(index, name=""):
    """A big coloured tag so switching windows visibly changes the screen."""
    bg = WIN_COLOURS[int(index) % len(WIN_COLOURS)]
    text = f"WINDOW {index}" + (f": {name}" if name else "")
    pad = " " * (len(text) + 6)
    print("\x1b[2J\x1b[H")
    print()
    print(f"      \x1b[1;30;48;5;{bg}m{pad}\x1b[0m")
    print(f"      \x1b[1;30;48;5;{bg}m   {text}   \x1b[0m")
    print(f"      \x1b[1;30;48;5;{bg}m{pad}\x1b[0m")
    print()
    print(f"      In the status bar at the bottom, the * is next to {index}: that's this window.")
    print()


def log(seed, secret, before=220, after=60):
    rng = random.Random(seed)
    before, after = int(before), int(after)
    for i in range(before):
        print(fake_line(rng, i))
    print(f"\x1b[1m{secret}\x1b[0m")
    for i in range(after):
        print(fake_line(rng, before + i + 1))
    sys.stdout.flush()


def search(seed, word, n):
    """`n` lines containing `word`, spread through a long log; the oldest says it's the oldest."""
    rng = random.Random(seed)
    n = int(n)
    marks = sorted(rng.sample(range(20, 260), n))
    k = n
    for i in range(300):
        if i in marks:
            tag = " (the OLDEST one)" if k == n else ""
            print(f"{fake_line(rng, i)}  {word} hint #{n - k + 1}{tag}")
            k -= 1
        else:
            print(fake_line(rng, i))
    sys.stdout.flush()


def incident(seed, first_id, decoys, delay=0.02):
    rng = random.Random(seed)
    decoys = [d for d in decoys.split(",") if d]
    delay = float(delay)
    first_at = rng.randint(50, 80)
    later = sorted(rng.sample(range(first_at + 30, 240), len(decoys)))
    print("=== incident stream: payments-api (prod) ===")
    for i in range(260):
        if i == first_at:
            line = f"{i:05d} ERROR [billing] charge failed: upstream timeout req={first_id}"
        elif i in later:
            line = f"{i:05d} ERROR [billing] retry failed req={decoys[later.index(i)]}"
        else:
            line = f"{i:05d} " + fake_line(rng, i)[9:]
        print(line, flush=True)
        time.sleep(delay)
    print("=== stream ended: find the FIRST error ===", flush=True)


def ticker(secs, code):
    secs = int(secs)
    for i in range(secs + 1):
        print(f"\r  ⏱  working… {i:3d}s / {secs}s", end="", flush=True)
        time.sleep(1)
    print(f"\n\n  ✅ Job finished. The code word is: \x1b[1m{code}\x1b[0m\n", flush=True)


def banner(text):
    print()
    print(f"   {text}")
    print()


def main(argv):
    if not argv:
        print(__doc__)
        return
    cmd, args = argv[0], argv[1:]
    {"label": label, "winlabel": winlabel, "log": log, "search": search, "incident": incident,
     "ticker": ticker, "banner": banner}[cmd](*args)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        pass
