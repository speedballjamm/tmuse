"""Fast unit tests (no tmux needed): python3 -m unittest tests/test_units.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game import actions, markup, progress  # noqa: E402
from game.hud import visible_len, wrap  # noqa: E402
from game.keylog import LINE, new_count  # noqa: E402
from game.state import Client, Pane, Snapshot, Window  # noqa: E402
from game.worlds import ORDER, WORLDS  # noqa: E402


class Markup(unittest.TestCase):
    def test_tmux_escapes_hash_and_percent(self):
        out = markup.to_tmux("press `C-b %` for #1", "fg=white")
        self.assertIn(" C-b %% ", out)
        self.assertIn("##1", out)

    def test_prefix_swap(self):
        self.assertEqual(markup.plain("`C-b c` new", "C-a"), "C-a c new")
        self.assertEqual(markup.plain("unbind C-b", "C-a"), "unbind C-a")

    def test_wrap_never_splits_chips(self):
        raw = "Split this pane into left and right with `C-b %` please now"
        first, rest = wrap(raw, 45)
        self.assertLessEqual(visible_len(first), 45)
        self.assertEqual(first.count("`") % 2, 0)
        self.assertEqual((first + " " + rest).split(), raw.split())


class KeyLog(unittest.TestCase):
    def test_new_count(self):
        self.assertEqual(new_count(["b", "a"], ["c", "b", "a"]), 1)
        self.assertEqual(new_count(["o", "x"], ["o", "o", "x"]), 1)
        self.assertEqual(new_count(["o", "x"], ["o", "o", "o", "x"]), 2)
        self.assertEqual(new_count(["a"], ["a"]), 0)
        self.assertEqual(new_count([], ["a", "b"]), 2)

    def test_line_format(self):
        m = LINE.match("17:54: /dev/ttys005 key /: list-keys -1N z")
        self.assertEqual(m.group(2, 3), ("/", "list-keys -1N z"))


def pane(pid, left, top, w, h, active=False, mode=""):
    return Pane("s", "@1", pid, 0, left, top, w, h, active, mode, 0, False, 0, "zsh", False, "")


def snap(panes, zoomed=False, layout="x,80x24,0,0,1"):
    w = Window("s", "@1", 0, "zsh", True, zoomed, layout, len(panes), False, 80, 24, False, panes=panes)
    s = Snapshot([Client("c", "s", False, "root", 80, 24, 1)], [], [w], panes, [], {})
    s.client, s.session = s.clients[0], "s"
    return s


class Classify(unittest.TestCase):
    def kinds(self, a, b):
        return [x.kind for x in actions.classify(a, b)]

    def test_split_h(self):
        a = snap([pane("%1", 0, 0, 80, 24, True)])
        b = snap([pane("%1", 0, 0, 40, 24), pane("%2", 41, 0, 39, 24, True)])
        self.assertIn("split-h", self.kinds(a, b))

    def test_split_v(self):
        a = snap([pane("%1", 0, 0, 80, 24, True)])
        b = snap([pane("%1", 0, 0, 80, 12), pane("%2", 0, 13, 80, 11, True)])
        self.assertIn("split-v", self.kinds(a, b))

    def test_select_direction(self):
        a = snap([pane("%1", 0, 0, 40, 24), pane("%2", 41, 0, 39, 24, True)])
        b = snap([pane("%1", 0, 0, 40, 24, True), pane("%2", 41, 0, 39, 24)])
        acts = actions.classify(a, b)
        sel = [x for x in acts if x.kind == "select-pane"][0]
        self.assertEqual(sel.info["dir"], "left")

    def test_swap(self):
        a = snap([pane("%1", 0, 0, 40, 24, True), pane("%2", 41, 0, 39, 24)])
        b = snap([pane("%1", 41, 0, 39, 24, True), pane("%2", 0, 0, 40, 24)])
        self.assertIn("swap", self.kinds(a, b))

    def test_zoom(self):
        a = snap([pane("%1", 0, 0, 40, 24, True), pane("%2", 41, 0, 39, 24)])
        b = snap([pane("%1", 0, 0, 80, 24, True), pane("%2", 41, 0, 39, 24)], zoomed=True)
        self.assertEqual(self.kinds(a, b), ["zoom"])

    def test_copy_mode(self):
        a = snap([pane("%1", 0, 0, 80, 24, True)])
        b = snap([pane("%1", 0, 0, 80, 24, True, mode="copy-mode")])
        self.assertIn("copy-mode", self.kinds(a, b))


class Content(unittest.TestCase):
    def test_mission_ids_unique(self):
        ids = [m.id for m in ORDER]
        self.assertEqual(len(ids), len(set(ids)))

    def test_keys_exist(self):
        from game.keys import BY_ID
        for m in ORDER:
            for k in m.keys:
                self.assertIn(k, BY_ID, f"{m.id} practises unknown key {k}")

    def test_cards_exist(self):
        from game.cards import CARDS
        for w in WORLDS:
            if w.card:
                self.assertIn(w.card, CARDS)
            for m in w.missions:
                for c in [m.card] + [s.card for s in m.steps]:
                    if c:
                        self.assertIn(c, CARDS, m.id)

    def test_every_world_ends_in_a_boss(self):
        for w in WORLDS[1:]:
            self.assertTrue(w.missions[-1].boss or w.missions[-1].id == "7.8", w.title)

    def test_leitner(self):
        d = progress.default()
        progress.learn_key(d, "zoom", ok=True, fresh=True)
        self.assertEqual(d["keys"]["zoom"]["box"], 2)
        progress.learn_key(d, "zoom", ok=True)
        self.assertEqual(d["keys"]["zoom"]["box"], 3)
        progress.learn_key(d, "zoom", ok=False)
        self.assertEqual(d["keys"]["zoom"]["box"], 1)


if __name__ == "__main__":
    unittest.main()
