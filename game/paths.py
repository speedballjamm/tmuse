"""Where things live. Overridable with env vars so tests can run in isolation."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME = os.path.expanduser(os.environ.get("TMUSE_HOME", "~/.tmuse"))
SOCKET = os.environ.get("TMUSE_SOCKET", "tmuse")

CONF = os.path.join(ROOT, "game", "game.conf")
PROGRESS = os.path.join(HOME, "progress.json")
RUN_DIR = os.path.join(HOME, "run")
EVENTS = os.path.join(RUN_DIR, "events.jsonl")
RUNTIME = os.path.join(RUN_DIR, "runtime.json")
ENGINE_LOG = os.path.join(HOME, "engine.log")
SANDBOX_CONF = os.path.join(HOME, "sandbox.tmux.conf")
SANDBOX_CONF_TILDE = "~/.tmuse/sandbox.tmux.conf" if "TMUSE_HOME" not in os.environ else SANDBOX_CONF


def ensure():
    os.makedirs(RUN_DIR, exist_ok=True)
