"""All worlds, in order."""
from . import w0, w1, w2, w3, w4, w5, w6, w7, w8

WORLDS = [w0.WORLD, w1.WORLD, w2.WORLD, w3.WORLD, w4.WORLD, w5.WORLD, w6.WORLD, w7.WORLD, w8.WORLD]
ORDER = [m for w in WORLDS for m in w.missions]
BY_ID = {m.id: m for m in ORDER}


def mission_index(mid):
    for i, m in enumerate(ORDER):
        if m.id == mid:
            return i
    return 0
