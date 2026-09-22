# tmuse

Learn tmux by playing it. No prior knowledge needed.

```
./tmuse
```

You play inside a **real tmux**, and the game watches what you do. Your mission shows in
the status bar at the bottom. Press the right keys and you clear it, earning XP, stars and
ranks. Everything you learn works in any stock tmux.

## Requirements

- tmux 3.2 or newer (`brew install tmux`)
- Python 3.9+ (the one that ships with macOS is fine). No packages to install.
- A terminal of at least 80×24. 100×30 or bigger is nicer.

Run it from a plain terminal, not from inside another tmux.

## What's in it

| | |
|---|---|
| **Campaign** | 9 worlds, 64 missions: the prefix, panes, pane power (zoom, resize, layouts), windows, sessions (detach and attach for real), copy mode and scrollback, the command prompt, configuration, and a final boss. |
| **Dojo** | 60-second speed drills with combos. Beat your high score. |
| **Review** | Spaced repetition: keys you fumbled come back sooner. |
| **Sandbox** | Free play. The status bar names every key you press and the command it ran. |
| **Cheat sheet** | `./tmuse cheat` (or `./tmuse cheat --all`). |

## While playing

Type these in any shell pane inside the game:

```
tmuse task      reprint the task here           tmuse card    re-open the lesson card
tmuse hint      a hint (the first is free)      tmuse reset   set the step up again
tmuse show      watch it done, then try         tmuse edit    open the World 7 config
tmuse skip      skip this mission               tmuse menu    back to the title screen
```

When you detach (`C-b d`) you land on a practice prompt that understands real tmux
commands: `tmux ls`, `tmux attach`, `tmux new -s NAME`, and so on.

## Safety

The game runs its own tmux server (`tmux -L tmuse`), so it can't see or touch your own
sessions. Progress lives in `~/.tmuse/`. The only other file it ever writes is
`~/.tmux.conf`, at the end of World 7, and only if you say yes (any existing file is
backed up first).

## Mac notes

- **Ctrl+←/→** may switch desktops instead of reaching tmux. The resize missions show
  alternatives.
- **Option as Meta** (for `M-1`…`M-5`): in Terminal.app, go to Settings → Profiles →
  Keyboard → "Use Option as Meta key". In iTerm2, go to Profiles → Keys → Left Option key
  → Esc+.

## Development

```
python3 -m unittest tests/test_units.py     # fast, no tmux
python3 tests/test_missions.py              # plays every mission with real keystrokes (~75s, parallel)
python3 tests/test_modes.py                 # sandbox, dojo, review, hints, menu, detach…
```

The design is in [SPEC.md](SPEC.md). Missions are data in `game/worlds/`. Each step has
a setup, a goal function over a snapshot of tmux's state, hints, and mistake detectors.
