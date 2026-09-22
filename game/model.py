"""Missions, steps, and the context their goal functions see."""
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence, Tuple


@dataclass
class Step:
    prompt: str
    goal: Callable
    hints: Sequence[str] = ()          # hints[0] is a free nudge; the rest cost XP
    setup: Optional[Callable] = None
    mistakes: Sequence[Tuple[Callable, str]] = ()
    expect: Sequence[str] = ()          # action kinds that count as "on track"
    card: Optional[str] = None
    keys: Sequence[str] = ()            # key ids practised (for review)
    done: str = ""
    demo: Sequence[Sequence[str]] = ()  # tmux commands `tmuse show` runs
    outside: str = ""                   # extra help shown at the outside-tmux prompt
    timeout_hints: bool = True


@dataclass
class Mission:
    id: str
    title: str
    steps: List[Step]
    xp: int = 50
    par: int = 30
    bonus: bool = False
    boss: bool = False
    card: Optional[str] = None
    blurb: str = ""
    world: int = 0

    @property
    def keys(self):
        out = []
        for s in self.steps:
            for k in s.keys:
                if k not in out:
                    out.append(k)
        return out


@dataclass
class World:
    num: int
    title: str
    missions: List[Mission]
    card: Optional[str] = None
    blurb: str = ""

    def __post_init__(self):
        for m in self.missions:
            m.world = self.num

    @property
    def core(self):
        return [m for m in self.missions if not m.bonus]


class Ctx:
    """What a goal function can look at."""

    def __init__(self, tmux, mem):
        self.tmux = tmux
        self.mem = mem            # shared across all steps of a mission
        self.s = None             # current snapshot
        self.prev = None
        self.base = None          # snapshot right after the step's setup
        self.actions = []         # actions since the step started
        self.new = []             # actions from the latest tick
        self.events = []          # outside-prompt / tmuse-command events since step start
        self._captures = {}
        self.feedback = None      # (text, kind) a goal wants shown
        self._said = None
        self._saying = False

    def say(self, text, kind="bad"):
        """Goals call this to give feedback. The same message repeats every tick while
        the condition holds, so show it once — but say it again if it comes back after
        the player cleared it."""
        self._saying = True
        if text != self._said:
            self._said = text
            self.feedback = (text, kind)

    def did(self, *kinds):
        return any(a.kind in kinds for a in self.actions)

    def last(self, kind):
        for a in reversed(self.actions):
            if a.kind == kind:
                return a
        return None

    def just(self, *kinds):
        return any(a.kind in kinds for a in self.new)

    def capture(self, target, history=False, join=True):
        key = (target, history, join)
        if key not in self._captures:
            self._captures[key] = self.tmux.capture(target, history, join)
        return self._captures[key]

    def ran_outside(self, *subcommands, flag=None):
        """True if the player ran `tmux <subcommand>` at the outside prompt."""
        for e in self.events:
            if e.get("type") == "outside":
                argv = e.get("argv", [])
                if len(argv) >= 2 and argv[0] == "tmux" and argv[1] in subcommands:
                    if flag is None or flag in argv:
                        return True
        return False

    def answer(self):
        for e in reversed(self.events):
            if e.get("type") == "answer":
                return e.get("text", "")
        return None

    def new_tick(self, snap, actions, events):
        if not self._saying:
            self._said = None
        self._saying = False
        self.prev, self.s = self.s, snap
        self.new = actions
        self.actions.extend(actions)
        self.events.extend(events)
        self._captures = {}
