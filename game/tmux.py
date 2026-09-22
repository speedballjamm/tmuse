"""Thin wrapper for running tmux commands against the game's private server."""
import subprocess

from . import paths


class ServerGone(Exception):
    pass


class Tmux:
    def __init__(self, socket=None):
        self.socket = socket or paths.SOCKET
        self.base = ["tmux", "-L", self.socket]

    def run(self, *args, timeout=5):
        try:
            return subprocess.run(
                self.base + [str(a) for a in args],
                capture_output=True, text=True, errors="replace", timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(args, 124, "", "timeout")

    def ok(self, *args):
        return self.run(*args).returncode == 0

    def out(self, *args):
        r = self.run(*args)
        return r.stdout if r.returncode == 0 else ""

    def seq(self, *commands):
        """Run several commands in one tmux invocation: seq(["set", "x", "1"], ["refresh-client", "-S"])."""
        args = []
        for i, c in enumerate(commands):
            if i:
                args.append(";")
            args.extend(c)
        return self.run(*args)

    def alive(self):
        r = self.run("list-sessions", "-F", "x")
        if r.returncode == 0:
            return True
        err = r.stderr.lower()
        return not ("no server running" in err or "error connecting" in err or "no such file" in err)

    def option(self, name, window=False):
        flags = "-gwv" if window else "-gv"
        return self.out("show", flags, name).strip()

    def capture(self, target, history=False, join=True):
        args = ["capture-pane", "-p", "-t", target] + (["-J"] if join else [])
        if history:
            args += ["-S", "-"]
        return self.out(*args)
