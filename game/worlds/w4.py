import random

from .common import WORDS, Mission, Step, World, answered, attached, reset, run_in, session, sessions, snap

OUT_LS = "Type:  tmux ls        (short for tmux list-sessions)"
OUT_ATTACH = "Type:  tmux attach    (or just: tmux a)"


def detached(c):
    return not attached(c)


def on_session(name):
    return lambda c: attached(c) and session(c) == name and not c.s.mode


def ticking(name, secs=3600, code="-"):
    def setup(c):
        reset(c, session=name)
        run_in(c, snap(c).pane.id, "ticker", secs, code)
    return setup


def boss_setup(c):
    c.mem["code"] = random.choice(WORDS)
    ticking("ops", 15, c.mem["code"])(c)


def remember_back(target):
    def goal(c):
        if on_session(target)(c):
            a = c.last("switch-session")
            c.mem["back"] = a.info["old"] if a else c.base.session
            return True
        return False
    return goal


def rename_to(target):
    def goal(c):
        if session(c) == target:
            return True
        a = c.last("rename-session")
        if a and a.info["new"] != target:
            c.say(f"Renamed to '{a.info['new']}', we want exactly **{target}**. Try `C-b $` again.")
        return False
    return goal


WORLD = World(4, "Sessions", card="sessions", missions=[
    Mission("4.1", "Name your session", xp=50, par=40, steps=[
        Step("Rename this session to **work**: `C-b $`, type work, Enter. (See the bottom-left.)",
             setup=lambda c: reset(c, session="tmuse"),
             goal=rename_to("work"),
             hints=["Prefix, then $ (Shift+4). Clear the old name first (C-u).", "`C-b $` C-u work Enter"],
             keys=["rename-session"], demo=[["rename-session", "work"]],
             done="[work] in the bottom-left: that's your session name."),
    ]),
    Mission("4.2", "The great escape", xp=80, par=90, card="detach", steps=[
        Step("A counter is running. Detach from tmux: `C-b d`",
             setup=ticking("work"),
             goal=detached,
             hints=["Prefix, then d.", "`C-b d`"], keys=["detach"]),
        Step("You're outside! List your sessions: tmux ls",
             goal=lambda c: c.ran_outside("ls", "list-sessions"), outside=OUT_LS, keys=["tmux-ls"]),
        Step("Now get back in: tmux attach",
             goal=attached, outside=OUT_ATTACH, keys=["tmux-attach"],
             done="Welcome back! The counter kept counting while you were gone."),
        Step("Detach again: `C-b d`", goal=detached),
        Step("This time attach by name: tmux a -t work",
             goal=lambda c: attached(c) and c.ran_outside("a", "at", "attach", "attach-session", flag="-t"),
             outside="Type:  tmux a -t work     (-t = target session)", keys=["tmux-attach-t"],
             done="With many sessions, -t picks which one."),
    ]),
    Mission("4.3", "A second session", xp=60, par=60, steps=[
        Step("Detach: `C-b d`", setup=lambda c: reset(c, session="work"), goal=detached),
        Step("Create a second session named **play**: tmux new -s play",
             goal=on_session("play"),
             outside="Type:  tmux new -s play     (new-session, -s = session name)",
             keys=["tmux-new"],
             done="Two sessions now. Each has its own windows and panes."),
    ]),
    Mission("4.4", "Session tree", xp=50, par=40, steps=[
        Step("Three sessions exist. Open the session chooser: `C-b s`",
             setup=sessions("work", "play", "music"),
             goal=lambda c: c.s.mode == "tree-mode",
             hints=["Prefix, then s.", "`C-b s`"], keys=["session-tree"], demo=[["choose-tree", "-Zs"]]),
        Step("Pick **music** and press Enter.", goal=on_session("music"),
             hints=["Arrow down to 'music', then Enter.",
                    "Shortcut: press the number shown in (brackets) next to it."],
             done="`C-b s` for sessions, `C-b w` for windows: same tree, different starting view."),
    ]),
    Mission("4.5", "Hop between sessions", xp=50, par=30, steps=[
        Step("Sessions alpha, beta, gamma. Go to the next session: `C-b )`",
             setup=sessions("alpha", "beta", "gamma"), goal=on_session("beta"),
             hints=["Prefix, then ) (Shift+0).", "`C-b )`"], keys=["session-cycle"],
             demo=[["switch-client", "-n"]]),
        Step("Next again: `C-b )`", goal=on_session("gamma"), hints=["`C-b )`"]),
        Step("Back one: `C-b (`", goal=on_session("beta"), hints=["`C-b (`"]),
    ]),
    Mission("4.6", "Last session", xp=50, par=40, bonus=True, steps=[
        Step("Go to session **gamma** any way you like.",
             setup=sessions("alpha", "beta", "gamma"), goal=remember_back("gamma"),
             hints=["`C-b s` and pick it, or `C-b )` twice."]),
        Step("Jump back to the session you were in just before: `C-b L`",
             goal=lambda c: on_session(c.mem.get("back"))(c),
             hints=["Prefix, then capital L (Shift+l).", "`C-b L`"], keys=["session-last"],
             demo=[["switch-client", "-l"]]),
    ]),
    Mission("4.7", "Clean up sessions", xp=60, par=60, bonus=True, steps=[
        Step("Detach: `C-b d`", setup=sessions("work", "play"), goal=detached),
        Step("Kill the **play** session from outside: tmux kill-session -t play",
             goal=lambda c: not c.s.has_session("play"),
             outside="Type:  tmux kill-session -t play", keys=["tmux-kill"]),
        Step("Check it's gone: tmux ls", goal=lambda c: c.ran_outside("ls", "list-sessions"), outside=OUT_LS),
        Step("And back in: tmux a", goal=attached, outside=OUT_ATTACH),
    ]),
    Mission("4.8", "BOSS: Survive the disconnect", xp=150, par=90, boss=True, steps=[
        Step("BOSS! A 15-second job is running in session **ops**. Detach right now: `C-b d`",
             setup=boss_setup, goal=detached),
        Step("Prove the job is still alive out there: tmux ls",
             goal=lambda c: c.ran_outside("ls", "list-sessions"), outside=OUT_LS),
        Step("Give it 15 seconds, then attach to ops by name.",
             goal=on_session("ops"), outside="Wait ~15s, then type:  tmux a -t ops"),
        Step("The job printed a code word. Tell me: type  **tmuse answer WORD**",
             goal=lambda c: answered(c, c.mem["code"]),
             hints=["Look in the pane for 'The code word is'. Not there yet? Wait a few seconds."]),
    ]),
])
