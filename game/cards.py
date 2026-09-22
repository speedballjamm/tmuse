"""Lesson cards: short explanations shown in a tmux popup before new ideas.

Markup: `keys` become key chips, **bold** is bold. Keep lines under ~74 chars.
"""
from . import progress

CARDS = {
    "welcome": {
        "title": "Welcome to tmuse",
        "body": """\
**tmux** is a **terminal multiplexer**: one terminal window that holds many
shells, split side by side, in tabs, and still running after you walk away.

  ┌─ the tmux **server** (runs in the background) ────────────────────┐
  │  **session** "work"               **session** "play"              │
  │   ├─ **window** 0 "code"  ┌──────┬──────┐                         │
  │   │                  │ pane │ pane │  ← **panes** = splits        │
  │   │                  └──────┴──────┘                              │
  │   └─ **window** 1 "logs"   (windows are like browser tabs)        │
  └───────────────────────────────────────────────────────────────────┘

**You are inside a real tmux right now.** Look at the bottom of the screen:
  • the top two coloured lines are the **game** (your mission and tips)
  • the last line is **tmux's own status bar** (sessions and windows)

The game watches what you do and cheers when you get it right.
Stuck? Type these in the shell:  `tmuse hint`  `tmuse skip`  `tmuse show`
  (`tmuse card` re-opens a lesson card, `tmuse reset` restarts a step)
""",
    },
    "prefix": {
        "title": "The prefix key",
        "body": """\
Every tmux shortcut starts with the **prefix**: `C-b`

  `C-b` means: **hold Ctrl, tap b, then let go of both.**

Then you press the command key **on its own**. So `C-b %` is two moves:

   1. Ctrl+b   (let go!)        2. %   (that's Shift+5)

The prefix tells tmux "the next key is for you, not the shell". Without
it, keys go straight to the program in the pane, as normal.

While tmux is waiting for that second key, the game shows a yellow
 PREFIX  badge in the status bar. Watch for it.

Common beginner slip: holding Ctrl for the second key too.
`C-b` then `o` is different from `C-b` then `C-o`!
""",
    },
    "panes": {
        "title": "World 1: Panes",
        "body": """\
A **pane** is a rectangle with its own shell. Split one pane into two:

   `C-b %`  side by side         `C-b "`  top / bottom
   ┌─────┬─────┐                 ┌───────────┐
   │     │     │                 │           │
   │     │     │                 ├───────────┤
   │     │     │                 │           │
   └─────┴─────┘                 └───────────┘

Memory trick: **%** has two circles side by side with a line between them.
**"** is the other one. After ten splits you won't need the trick.

Only one pane is **active** (it has the cursor and a green border).
Move around with `C-b ←` `C-b →` `C-b ↑` `C-b ↓`,
cycle with `C-b o`, or jump back to the last one with `C-b ;`.
""",
    },
    "kill": {
        "title": "Closing panes",
        "body": """\
Two ways to close a pane:

  • `C-b x`  asks  "kill-pane? (y/n)"  → press `y`
  • type `exit` (or press `C-d`) in the shell. When a pane's program
    ends, the pane closes.

If you close the **last** pane of the **last** window, the session ends
and tmux sends you back to your normal terminal. (Don't worry: the game
will explain how to get back in.)
""",
    },
    "pane_power": {
        "title": "World 2: Pane power",
        "body": """\
Now you can split. Next, **control** your panes:

  `C-b z`          zoom: the active pane fills the window. Again to undo.
                   (a Z appears in the status bar while zoomed)
  `C-b C-→`        resize: hold Ctrl, tap b, keep holding, tap → → →
  `C-b {` `C-b }`  swap this pane with the previous / next one
  `C-b C-o`        rotate every pane one spot
  `C-b Space`      cycle through 5 preset layouts
  `C-b !`          break this pane out into its own window

Zoom is one of the most useful keys in tmux: work in a tiny pane,
zoom it to full screen, then zoom back out.
""",
    },
    "resize": {
        "title": "Resizing (and a Mac gotcha)",
        "body": """\
`C-b C-→` moves the border by 1 cell. It's **repeatable**: after one
prefix you can keep tapping arrows (within half a second) without
pressing `C-b` again. Easiest way: hold Ctrl the whole time:

      Ctrl held:  b  →  →  →  →  →

**Mac gotcha:** macOS uses Ctrl+←/→ to switch desktops (Spaces), so
the keys never reach tmux. Two fixes:
  • the command prompt: `C-b :` then type  resize-pane -R 10  Enter
    (-L -R -U -D = left right up down). Always works.
  • get the keys back: System Settings → Keyboard → Keyboard Shortcuts
    → Mission Control, untick "Move left/right a space".
""",
    },
    "layouts": {
        "title": "Layouts by name",
        "body": """\
`C-b Space` cycles layouts. To pick one directly, use Meta (Option) keys:

  `C-b M-1`  even-horizontal   ┃┃┃  all side by side
  `C-b M-2`  even-vertical     ☰   all stacked
  `C-b M-3`  main-horizontal   one big on top, rest below
  `C-b M-4`  main-vertical     one big on the left, rest on the right
  `C-b M-5`  tiled             a neat grid

**Mac:** Option needs to act as Meta. Terminal.app: Settings → Profiles →
Keyboard → "Use Option as Meta key". iTerm2: Profiles → Keys →
Left Option key → "Esc+".  No luck? `C-b :` then  select-layout tiled
""",
    },
    "blueprint": {
        "title": "Boss: Blueprint",
        "body": """\
Build this layout, starting from a single pane:

        ┌──────────────────┬─────────┐
        │                  │    B    │
        │                  ├─────────┤
        │        A         │    C    │
        │                  ├─────────┤
        │                  │    D    │
        └──────────────────┴─────────┘

Then make A **wider than half** the screen, and finally
**zoom the bottom-right pane (D)**.

Any route counts: splits, layouts, resizing. It's timed, so go!
(`tmuse card` shows this blueprint again.)
""",
    },
    "windows": {
        "title": "World 3: Windows",
        "body": """\
A **window** is a full screen of panes: think browser **tabs**.
The status bar lists them:   0:zsh  1:logs*  2:vim-
   * = the current window     - = the last (previous) window

  `C-b c`        create a window
  `C-b n` / `p`  next / previous window
  `C-b 0`…`9`    jump to window number N
  `C-b l`        lowercase L: the last window you were on (great for flipping)
  `C-b ,`        rename the window (it's pre-filled; delete first)
  `C-b &`        kill the window (y to confirm)
  `C-b w`        a tree of every window; arrows + Enter to pick

Naming windows ("code", "server", "logs") makes the status bar a map.
""",
    },
    "sessions": {
        "title": "World 4: Sessions: tmux's superpower",
        "body": """\
A **session** is a whole workspace of windows. The trick:

  **Sessions keep running when you leave.**

`C-b d` **detaches**: tmux disappears, you're back in your plain terminal,
but everything inside keeps running: builds, servers, SSH jobs.
Later (even after your laptop disconnects from an SSH server!) you
**attach** again and it's all exactly as you left it.

From a normal shell (outside tmux):
  tmux ls                  list sessions
  tmux attach   / tmux a   attach to the most recent one
  tmux a -t work           attach to the session named "work"
  tmux new -s work         start a new session called "work"
  tmux kill-session -t work

Inside:  `C-b $` rename,  `C-b s` chooser,  `C-b (` `C-b )` prev/next
""",
    },
    "detach": {
        "title": "Detaching for real",
        "body": """\
You're about to detach with `C-b d`.

tmux will vanish and you'll see a plain prompt: that's the
"outside world" (your normal terminal). The game gives you a small
practice prompt there that understands real tmux commands.

Your session, and the counter running in it, keeps going.
Get back in with:   tmux attach
""",
    },
    "copy_mode": {
        "title": "World 5: Copy mode & scrollback",
        "body": """\
Output scrolled off the top? In tmux you don't use the mouse wheel
(yet). You use **copy mode**:

  `C-b [`          enter copy mode (a position counter appears top-right)
  `PgUp` `PgDn`    page up / down    (Mac laptop: Fn+↑ / Fn+↓)
  `↑` `↓` or `k` `j`  line by line    `C-u` `C-d`  half a page
  `g` / `G`        very top / very bottom of the history
  `q`              leave copy mode

Search (the game uses **vi** keys, which most tmux users use):
  `?`  search **up** (older)       `/`  search **down** (newer)
  `n`  next match                  `N`  previous match

Shortcut: `C-b PgUp` enters copy mode and scrolls up in one go.
""",
    },
    "copy_select": {
        "title": "Copy & paste, the tmux way",
        "body": """\
Inside copy mode (vi keys):

  1. move the cursor to the start of the text
        `w` next word   `b` back a word   `0` line start   `$` line end
  2. `Space`   start selecting
  3. move to the end of the text (the selection highlights)
  4. `Enter`   copy it and leave copy mode

Then in any pane:   `C-b ]`   pastes it.

Everything you copy is saved in a **paste buffer** list.
`C-b =` shows them all so you can paste an older one.

Handy: `V` selects the whole line. `v` switches to rectangle selection.
""",
    },
    "commands": {
        "title": "World 6: The command prompt",
        "body": """\
Every key binding is just a shortcut for a **tmux command**:

   `C-b %`  runs  split-window -h        `C-b c`  runs  new-window
   `C-b z`  runs  resize-pane -Z         `C-b d`  runs  detach-client

`C-b :` opens a prompt in the status bar where you can type **any**
command, with options the keys can't reach:

   new-window -n build          a window that's already named
   split-window -h -p 30        a split taking 30%
   select-layout tiled
   setw synchronize-panes on    type into every pane at once

Tab completes command names. The same commands work in scripts,
in your config file, and from the shell as  tmux <command>.
""",
    },
    "sync": {
        "title": "Synchronized panes",
        "body": """\
With **synchronize-panes** on, whatever you type goes to **every pane
in the window at once**. Sysadmins use it to run the same command on
several servers.

   `C-b :`  setw synchronize-panes on
   `C-b :`  setw synchronize-panes off

(setw = set-window-option. It's per window, so other windows aren't
affected.)
""",
    },
    "mouse": {
        "title": "Mouse mode",
        "body": """\
tmux ignores the mouse by default. Turn it on with:

   `C-b :`  set -g mouse on

Then you can:  • click a pane to select it
               • drag a border to resize
               • scroll the wheel to enter copy mode and scroll
               • click a window name in the status bar

With the mouse on, your terminal's normal text selection needs a
modifier: hold **Option** (Terminal.app / iTerm2) or **Shift** (most
Linux terminals) while dragging.
""",
    },
    "config": {
        "title": "World 7: Make it yours",
        "body": """\
tmux reads **~/.tmux.conf** when the server starts. It's just a list
of the same commands you type at `C-b :`, one per line:

   set -g mouse on                 # set an option (-g = global)
   setw -g mode-keys vi            # set a window option
   bind r source-file ~/.tmux.conf # bind prefix+r to a command
   unbind C-b                      # remove a binding

Changes don't apply by themselves: reload with
   `C-b :`  source-file ~/.tmux.conf

In this world you'll edit a **practice** config:
   ~/.tmuse/sandbox.tmux.conf
At the end you can copy it to your real ~/.tmux.conf if you like.
""",
    },
    "editor": {
        "title": "Editing a file with nano",
        "body": """\
**nano** is the friendliest terminal editor:

   nano ~/.tmuse/sandbox.tmux.conf

  • just type: arrow keys move, Backspace deletes
  • `C-o` then `Enter`  saves ("Write Out")
  • `C-x`             exits

Already know vim? Use it, the game doesn't mind:
   vim ~/.tmuse/sandbox.tmux.conf     (i to type, Esc :wq to save & quit)

Mistyped the path? `tmuse edit` opens the same file for you.

Tip: split the window first (`C-b %`) so you can keep a shell next
to your editor. That's the whole point of tmux!
""",
    },
    "prefix_change": {
        "title": "Changing the prefix",
        "body": """\
Lots of people move the prefix to `C-a` (easier to reach, and GNU
screen's old default). Three lines:

   set -g prefix C-a
   unbind C-b
   bind C-a send-prefix      # press C-a twice to send a real Ctrl-a

After you reload, **every** shortcut starts with `C-a` instead.
The game will switch all its instructions to your new prefix.

(Heads up: `C-a` is also "go to start of line" in the shell. That's
what send-prefix is for: `C-a C-a` still gets it through.)
""",
    },
    "final": {
        "title": "Final Boss: A Day in the Life",
        "body": """\
Time to use everything, like a real work day:

  1. Start a session called **day**
  2. Set up windows: **editor**, **server**, **logs**
  3. Split the server window side by side
  4. An incident hits the logs! Find the **first ERROR**, copy its req id
  5. Paste it into the editor window
  6. Go home: detach.  Next morning: reattach to **day**
  7. Zoom in on a server pane and get to work

It's timed. No new keys, just you and tmux. Good luck!
""",
    },
    "graduation": {
        "title": "You're a Multiplexer Master",
        "body": """\
You've learned panes, windows, sessions, copy mode, commands and config:
more tmux than most people who use it every day.

Keep it sharp:
  • ./tmuse → **Review**: spaced repetition brings back shaky keys
  • ./tmuse → **Dojo**: 60-second speed drills; beat your high score
  • ./tmuse cheat: a printable cheat sheet

Now go use it for real: open a terminal, type  tmux new -s work
and start splitting.
""",
    },
}


def height_of(card):
    return card["body"].count("\n") + 3


def world_complete(world, data, worlds):
    stars = sum(data["missions"].get(m.id, {}).get("stars", 0) for m in world.missions)
    total = 3 * len(world.missions)
    nxt = worlds[world.num + 1].title if world.num + 1 < len(worlds) else "the end!"
    return {
        "title": f"World {world.num} complete!",
        "body": f"""\
  ★ **{world.title}** cleared!

  New rank:  **{progress.rank(data, worlds)}**
  Stars:     {stars} / {total}
  Total XP:  {data['xp']}

  Up next:   {nxt}

  Bonus missions you skipped are waiting in the World menu.
""",
    }
