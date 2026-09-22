# tmuse: a game that teaches tmux

> Learn tmux by using real tmux. Instructions sit in the status bar and the
> game watches what you do.

Status: **Built.** See §10 for where the build differs from the original draft.

---

## 1. Goals

| Goal | What it means in practice |
|---|---|
| **Assume zero knowledge** | Level 1 covers "what is a terminal multiplexer?" and "hold Ctrl, press b, let go, then press %". |
| **Real skills, not trivia** | You press real keys in a **real tmux**, so the muscle memory carries straight over to daily use. |
| **Comprehensive** | Covers panes, windows, sessions, copy mode and scrollback, the command prompt, layouts, and configuration. That's every default binding a normal user needs, plus the CLI (`tmux ls`, `attach`, …). |
| **Fun** | Missions, XP, ranks, streaks, boss levels, timed drills, and hidden secrets to dig out of the scrollback. |
| **Sticky** | Spaced-repetition review brings back the keys you fumbled. |
| **Safe** | Runs on an isolated tmux server. It never touches your own sessions or `~/.tmux.conf` unless you explicitly agree. |

Non-goals: teaching shell scripting, tmux plugin managers (TPM), or tmux internals.

---

## 2. Core idea and architecture

A simulated tmux would teach the wrong reflexes and couldn't cover the long tail
of behavior. So the game **drives real tmux** and **checks real tmux state**.

```
 ┌─────────────────────────── your terminal ───────────────────────────┐
 │  tmux client (socket: -L tmuse)                                     │
 │  ┌──────────────────────────┬──────────────────────────┐            │
 │  │ pane: shell              │ pane: shell              │  sandbox:  │
 │  │ (you do whatever you     │                          │  yours to  │
 │  │  like here)              │                          │  wreck     │
 │  └──────────────────────────┴──────────────────────────┘            │
 │ ▶ 1.2 Stacked │ Split this pane top / bottom:  C-b "                 │ ← status line 1 (mission)
 │ PREFIX  » Hint: prefix, then the double-quote key   Pane Apprentice · 340 XP │ ← status line 2 (feedback)
 │ [tmuse] 0:zsh*  1:logs-                            "mac" 17:12      │ ← status line 3 (normal tmux bar)
 └─────────────────────────────────────────────────────────────────────┘
          ▲                                          ▲
          │ polls state every ~100ms                 │ lesson cards shown with
          │ (list-panes / display -p / hooks)        │ tmux display-popup
   ┌──────┴────────────────────────────────┐         │
   │ tmuse engine (Python background process)│───────┘
   │ • runs the lesson state machine         │
   │ • checks mission predicates             │
   │ • writes status lines and popups        │
   │ • saves progress to ~/.tmuse/           │
   └─────────────────────────────────────────┘
```

### Key decisions

1. **Isolated server.** Everything runs on `tmux -L tmuse -f <game.conf>`. The game config
   keeps **stock default key bindings** (prefix `C-b`), so everything you learn applies
   to a fresh tmux anywhere. It changes only what the game needs: a multi-line status bar
   and hooks.
2. **The HUD is the status bar, not a pane.** The whole screen is your sandbox. You can
   kill every pane, and the game survives and says "nice, now make a new one."
3. **The engine runs outside the panes.** It's a detached background process that talks to
   the server over the socket. If you kill all your panes or detach, the engine keeps
   running (or resumes).
4. **Lesson cards use `display-popup`** (tmux ≥ 3.2): short, illustrated explanations
   with ASCII diagrams, shown before each new concept. Press Enter to close.
5. **Verification is state-based, backed by hooks.** Every mission has a predicate over
   tmux state, for example:
   - pane count and geometry (`#{pane_left}`, `#{pane_top}`, `#{pane_width}`) tell a
     `%` split apart from a `"` split
   - `#{window_zoomed_flag}`, `#{pane_in_mode}`, `#{pane_mode}`, `#{client_prefix}`,
     `#{session_name}`, `#{window_name}`, `#{window_layout}`, `#{pane_synchronized}`
   - `list-buffers` / `show-buffer` for copy-and-paste missions
   - `show-options` for config missions
   - hooks (`after-split-window`, `after-select-pane`, `after-resize-pane`,
     `after-copy-mode`, `client-detached`, `session-renamed`, …) for things that don't
     leave lasting state, such as "you cycled panes with `o`"
6. **Wrong-move coaching.** The engine spots common mistakes and names them, for example:
   - You split side by side when the mission wanted top/bottom: "That was `%`
     (vertical line). You wanted `"`."
   - The prefix went active, then a key did nothing: "You pressed `C-b` but the next key
     wasn't bound. Remember: let go of Ctrl before pressing the second key."
   - An unexpected pane closed: "Oops, `x` kills a pane. Here's one back."
7. **Detach and attach are taught for real.** On detach, the launcher gets the terminal
   back and shows a mini "outside tmux" prompt. You type real commands (`tmux ls`,
   `tmux attach`, `tmux a -t work`, `tmux new -s scratch`), which get routed to the
   game socket. Anything else is explained, not executed.

### Tech

- **Python 3.9+, standard library only** (macOS ships with 3.9, so nothing to install).
- **Needs tmux ≥ 3.2** (you have 3.7c). The launcher checks the version.
- Entry point: `./tmuse`.
- Progress file: `~/.tmuse/progress.json`.
- Tests run the whole game inside an outer tmux, type real keystrokes into it, and read
  the rendered screen, so every mission is tested end to end.

---

## 3. Notation taught in-game

The game teaches this in Level 0 and uses it everywhere after:

| Written | Means |
|---|---|
| `C-b` | Hold **Ctrl**, press **b**, let go of both. This is the **prefix**. |
| `C-b %` | Prefix, *then* press `%` (Shift+5). Two separate steps. |
| `C-b C-o` | Prefix, then Ctrl+o. |
| `M-1` | Meta/Option + 1. **macOS note:** needs "Use Option as Meta" (Terminal.app) or "Esc+" (iTerm2). The game detects whether it works and shows how to set it up. |
| `C-b` … `↑ ↑ ↑` | Repeatable keys: after one prefix, you can press some keys again quickly. |

---

## 4. Curriculum

Each **World** is a set of **Missions**. Each mission is either a *lesson* (lesson
card, then a guided task) or a *challenge* (task only). Every world ends with a
**Boss**. Keys marked **(core)** are required. **(bonus)** keys give extra XP and
count toward 100% completion.

### World 0: Hello, Multiplexer (orientation)
- Lesson card: what tmux is (the **server → sessions → windows → panes** mental model,
  with a diagram), and why people use it (sessions survive disconnects; split screens).
- M0.1 **Feel the prefix**: press `C-b` and see the prefix indicator in the status bar
  light up. Detected via `#{client_prefix}`.
- M0.2 **The panic button**: `C-b ?` lists every key binding; `q` exits it. Verified via
  `pane_mode`.
- M0.3 **Type in tmux**: run `echo hello` in the pane. This shows tmux is "just a
  terminal".

### World 1: Panes 101
- `C-b %` split left/right (core)
- `C-b "` split top/bottom (core)
- `C-b ←↑→↓` move between panes (core)
- `C-b o` cycle to the next pane (core)
- `C-b ;` jump to the last-used pane (core)
- `C-b x` then `y` kill a pane (core); typing `exit` also closes a pane (core)
- `C-b q` show pane numbers, then press a number to jump to that pane (bonus)
- **Boss: "The Quad."** Build a 2×2 grid, then visit every pane in a given order
  (↖ ↘ ↗ ↙). The engine tracks the active-pane sequence.

### World 2: Pane Power
- `C-b z` zoom/unzoom a pane (core)
- `C-b C-↑↓←→` resize by 1 cell (repeatable) (core); `C-b M-↑↓←→` resize by 5 (bonus)
- `C-b {` / `C-b }` swap a pane with the previous/next one (core)
- `C-b C-o` / `C-b M-o` rotate panes (bonus)
- `C-b Space` cycle preset layouts (core)
- `C-b M-1…M-5` jump to a specific layout: even-horizontal, even-vertical, main-horizontal,
  main-vertical, tiled (bonus)
- `C-b !` break a pane out into its own window (core)
- **Boss: "Blueprint."** The game shows an ASCII target layout, for example a big pane on
  the left and three stacked on the right with the top-right one zoomed. You rebuild it.
  The engine compares a normalized `#{window_layout}` within a tolerance.

### World 3: Windows (tabs)
- `C-b c` create a window (core)
- `C-b n` / `C-b p` next/previous window (core)
- `C-b 0…9` go to window N (core)
- `C-b l` last window (core)
- `C-b ,` rename a window (core)
- `C-b &` kill a window (confirm with `y`) (core)
- `C-b w` tree chooser: navigate with arrows, Enter to pick (core)
- `C-b '` go to window by index prompt (bonus)
- `C-b f` find a window by text (bonus)
- `C-b .` move/renumber a window (bonus)
- **Boss: "Mission Control."** Create windows named `code`, `server`, and `logs`, in that
  order. Then the game fires rapid requests ("go to server!", "back to the last one!",
  "rename logs to tail!") with a timer.

### World 4: Sessions: tmux's superpower
- Lesson card: detaching means your work keeps running, which is why SSH users love tmux.
- `C-b d` detach (core). This is taught with the real outside-tmux prompt:
  `tmux ls` (core), `tmux attach` / `tmux a` (core), `tmux a -t NAME` (core),
  `tmux new -s NAME` (core), `tmux kill-session -t NAME` (bonus)
- `C-b $` rename a session (core)
- `C-b s` session chooser (core)
- `C-b (` / `C-b )` previous/next session (core)
- `C-b L` last session (bonus)
- **Boss: "Survive the Disconnect."** A long-running countdown is going in a pane. Detach,
  prove it kept running (`tmux ls` shows the session), reattach to the right session,
  and read the number it reached.

### World 5: Copy Mode & Scrollback
The game prints output into your pane with a **secret code buried 300 lines up**.
- `C-b [` enter copy mode (core); `q` exit (core)
- `PgUp` / `PgDn` and arrows scroll (core)
- Search backwards / forwards (core)
- Start a selection, move, and copy (core)
- `C-b ]` paste the most recent buffer (core)
- `C-b =` choose from buffer history (bonus)
- `C-b PgUp` enter copy mode and scroll up in one step (bonus)
- Missions: *find* the secret (type it in to prove it), *copy* it (verified with
  `show-buffer`), *paste* it into the other pane.
- **Boss: "Log Detective."** A fake incident log streams by. Find the request ID of the
  first `ERROR`, copy it, and paste it into the "ticket" pane.
- Copy-mode keys differ between **vi** and **emacs** mode. See open question Q1.

### World 6: The Command Prompt & Extras
- `C-b :` command prompt (core). Missions: `new-window -n build`,
  `split-window -h`, `select-layout tiled`, `rename-session work`
- `:setw synchronize-panes on` types into every pane at once (core, and a fun one:
  "deploy" the same command to 4 "servers" simultaneously)
- `C-b t` big clock (bonus, easter egg)
- `C-b i` window info, `C-b ~` message log (bonus)
- `:list-keys` and `C-b ?` revisited: how to look anything up yourself (core)
- Mouse mode: `:set -g mouse on`, then click panes, drag borders, and scroll (core)
- **Boss: "Fleet Commander."** Using only the command prompt, build a tiled 4-pane window
  named `fleet` with synchronized input, and run `hostname` in all of them in one go.

### World 7: Make It Yours (configuration)
- Lesson card: `~/.tmux.conf`, `source-file`, what `set -g` / `setw` / `bind` / `unbind` mean.
- The player edits a **sandbox** config (`~/.tmuse/sandbox.tmux.conf`) in a pane using
  their editor of choice (nano is suggested for beginners), then runs
  `:source-file ~/.tmuse/sandbox.tmux.conf`. The engine verifies with `show-options`.
- Missions: turn mouse on; start numbering at 1 (`base-index`, `pane-base-index`); add
  a `C-b r` reload binding; add intuitive split keys (`|` and `-`) (bonus); change the
  prefix to `C-a` (bonus); switch copy mode to vi keys (bonus); increase
  `history-limit`.
- **Graduation:** the game shows your finished config and *offers* (you type y/N) to copy
  it to `~/.tmux.conf`, backing up any existing file first.

### Final Boss: "A Day in the Life"
A chained scenario that uses everything: start a named session, lay out an editor, server,
and logs workspace, find an error in the scrollback, copy it to a notes window, detach
("go home"), reattach ("next morning"), and zoom into the fix. Scored on time, hints used,
and keystroke efficiency.

---

## 5. Game systems

### Progression
- **XP** per mission. Bonus for no hints, first-try success, and speed.
- **Ranks:** Tmux Tadpole → Pane Apprentice → Window Wrangler → Session Keeper →
  Scrollback Sleuth → Command Crafter → Multiplexer Master.
- **Streak** 🔥: consecutive missions cleared without a hint.
- Worlds unlock in order. Bonus keys can be skipped and revisited later.
- **Stars** per mission (1 to 3): cleared / no hints / under par time.

### Hints (tiered)
1. After ~15s idle or a wrong move: a conceptual nudge ("panes are split with the prefix
   plus a symbol that looks like a divider").
2. Press `C-b ?`, or wait ~30s: the exact key, which costs half the mission's XP.
3. Show-me: the engine performs the action itself so you can watch, and you then redo
   it. You get no XP, but the mission can still be cleared.

### Modes (main menu)
1. **Campaign.** Worlds 0–7 plus the final boss, as above.
2. **Dojo (speed drills).** Random prompts from unlocked keys against the clock ("Zoom!",
   "New window!", "Pane left!"). 60-second rounds, personal bests, combo multiplier.
3. **Review (spaced repetition).** Each binding has a Leitner-box score. Keys you missed,
   hinted, or were slow on come back more often. The game suggests "5 keys due for
   review" at launch.
4. **Sandbox.** Free play in the game's tmux with the HUD showing live feedback on every
   key you use ("that was `C-b z`: zoom").
5. **Cheat Sheet.** A generated reference of everything you've learned, grouped by world.
   Also available from the shell as `./tmuse cheat` (plain text you can print or pin).

### Menus and flow
- `./tmuse` shows a title screen (a curses menu outside tmux) with Continue, Campaign,
  Dojo, Review, Sandbox, Cheat Sheet, Settings, and Quit.
- Starting play launches the isolated tmux server and attaches.
- Leave anytime with `C-b d` (which is also a lesson) or with `:kill-server`. Progress
  saves after every mission.
- **Settings:** reset progress, copy-mode key style, hint timing, sound (terminal bell
  on success, on/off), and "Meta key test".

---

## 6. Robustness and safety
- Uses its own socket (`-L tmuse`), so your own tmux sessions can't be seen or affected.
- The only writes are to `~/.tmuse/`, plus `~/.tmux.conf` if you explicitly agree
  (with a backup) at graduation.
- If you wreck the sandbox (kill the session, close all panes, change a critical option),
  the engine notices and offers to reset the mission.
- If the engine crashes, the status bar says so, and `./tmuse` resumes from the last save.
- Terminal checks at launch: size (at least 80×24, and warns if too small for 2×2
  missions), 256-color support, and Meta key.
- Running `./tmuse` from inside another tmux: the launcher warns you and explains
  nesting (prefix twice: `C-b C-b`). By default it asks you to run it from a plain
  terminal.

---

## 7. Code layout

```
tmuse                    # launcher script: ./tmuse
game/
  cli.py                 # `tmuse` subcommands (inside and outside the game)
  launcher.py            # title menu (curses), server start/attach, outside-tmux prompt
  engine.py              # background daemon: mission state machine, polling loop, modes
  tmux.py  state.py      # run tmux commands; one-call snapshot of the whole server
  actions.py             # diff two snapshots -> what the player did (split-h, zoom, …)
  keylog.py              # exact keys pressed, read from tmux's message log
  hud.py  markup.py      # status-line HUD (wraps long prompts), key-chip markup
  cards.py  card.py      # lesson card text; popup viewer
  model.py  setups.py    # Mission/Step/Ctx; sandbox arrangement helpers
  worlds/w0.py … w8.py   # the curriculum, as data plus goal functions
  drills.py              # Dojo + Review
  progress.py            # save file, XP, ranks, Leitner boxes
  panes.py               # programs run inside panes (fake logs, ticker, labels)
  graduate.py            # installs your config to ~/.tmux.conf (with backup)
  game.conf              # stock bindings + HUD settings
tests/
  test_units.py          # fast, no tmux
  test_missions.py       # every mission solved with real keystrokes
  test_modes.py          # sandbox, dojo, review, hints, coaching, menu, detach
  harness.py             # runs the game inside an outer tmux; types keys, reads the screen
```

A mission is declared as data:

```python
Mission("1.2", "Stacked", xp=50, par=20, steps=[
    Step('Split this pane top / bottom: `C-b "`',
         setup=fresh,
         goal=lambda c: c.did("split-v") and npanes(c) >= 2,
         mistakes=[SPLIT_H_NOT_V], expect=["split-v"],
         hints=["Prefix, then the double-quote key.", '`C-b` then Shift+\' (")'],
         keys=["split-v"], demo=[["split-window", "-v"]]),
])
```

## 8. Build plan (milestones)
1. **Skeleton:** launcher, isolated server, engine daemon, HUD in the status bar, save file.
   World 0 playable.
2. **Worlds 1–3** (panes and windows) with coaching and bosses. pty test harness.
3. **World 4** (sessions and the outside-tmux prompt) and **World 5** (copy mode).
4. **Worlds 6–7**, the final boss, and graduation config export.
5. **Dojo, Review, Sandbox, Cheat Sheet** modes. Polish: title art, ranks, sounds.

---

## 9. Decisions (were open questions)

- **Q1. Copy-mode keys: vi.** *(decided)* tmux defaults to *emacs* keys unless `$EDITOR`
  contains "vi". **My recommendation:** teach **vi** keys (`v` select, `y` copy, `/`
  search, `hjkl`) and set `mode-keys vi` in the game, because that's what most tmux users
  and guides use. World 7 then shows you how to set it in your own config. Plain arrows
  and PgUp/PgDn work in both modes.
- **Q2. Prefix:** stock `C-b`; remapping to `C-a` is a World 7 bonus. *(decided)*
- **Q3. Mouse:** off until World 6. *(decided)*
- **Q4. Scope:** everything was built. *(decided)*

---

## 10. As built: differences from the draft

- **HUD position.** The game lines sit at the bottom, in tmux's multi-line status bar:
  mission, then feedback, then tmux's own bar last. A long prompt wraps onto a fourth
  line. The PREFIX badge is at the far left of the feedback line, so it's always visible.
- **vi copy keys are stock tmux:** `Space` starts a selection and `Enter` copies. The
  popular `v` / `y` bindings are *not* tmux defaults, so World 7 teaches adding them.
- **No hooks.** Verification is state polling plus the message log (below), which covers
  everything the hooks were meant for.
- **tmux 3.7 gotcha:** `list-keys -T prefix KEY` with a single key shows its result on the
  attached client's status line instead of printing it. The game lists the whole table
  and filters.
- **Exact key detection.** Besides diffing state, the engine reads tmux's message log,
  which records every key binding that runs (`key %: split-window -h`). The sandbox
  uses it to name the exact key you pressed. The game config lowers `message-limit`
  to 100 to keep this quick.
- **Game-config deviations from stock tmux:** `mode-keys vi`, `exit-empty off` (closing
  your last pane doesn't kill the game), `status 3`, `message-limit 100`. All key
  bindings are stock.
- **Worlds 0 and 7 have no boss.** World 0 is orientation. World 7 ends with "Take it
  home", which offers to install your config.
- **Final boss** is scored on time and hints like other missions. Keystroke efficiency
  isn't measured.
- **Settings:** bell, unlock all worlds, reset progress. The in-menu "Meta key test" was
  dropped. Instead, the Meta-key missions explain the Mac setting and accept the
  `C-b :` command equivalent.
- **Hint timing:** a free nudge after 20s, then the exact key after 45s (which halves XP).
  `tmuse hint` skips the wait.
- **64 missions:** 49 core, 15 bonus.
