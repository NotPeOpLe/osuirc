import logging
from enum import Enum, IntEnum, IntFlag


class GameMode(IntEnum):
    Osu = 0
    Taiko = 1
    CatchTheBeat = 2
    OsuMania = 3


class TeamType(Enum):
    Neutral = None
    Blue = "blue"
    Red = "red"


class ScoreMode(IntEnum):
    Score = 0
    Accuracy = 1
    Combo = 2
    ScoreV2 = 3


class TeamMode(IntEnum):
    HeadToHead = 0
    TagCoop = 1
    TeamVs = 2
    TagTeamVs = 3


class Mods(IntFlag):
    NoMod = 0
    NoFail = 1
    Easy = 2
    TouchDevice = 4
    Hidden = 8
    HardRock = 16
    SuddenDeath = 32
    DoubleTime = 64
    Relax = 128
    HalfTime = 256
    Nightcore = 512
    Flashlight = 1024
    Autoplay = 2048
    SpunOut = 4096
    Relax2 = 8192
    Perfect = 16384
    Key4 = 32768
    Key5 = 65536
    Key6 = 131072
    Key7 = 262144
    Key8 = 524288
    FadeIn = 1048576
    Random = 2097152
    Cinema = 4194304
    Target = 8388608
    Key9 = 16777216
    KeyCoop = 33554432
    Key1 = 67108864
    Key3 = 134217728
    Key2 = 268435456
    ScoreV2 = 536870912
    Mirror = 1073741824
    KeyMod = Key1 | Key2 | Key3 | Key4 | Key5 | Key6 | Key7 | Key8 | Key9 | KeyCoop
    FreeMod = (
        NoFail
        | Easy
        | Hidden
        | HardRock
        | SuddenDeath
        | Flashlight
        | FadeIn
        | Relax
        | Relax2
        | SpunOut
        | KeyMod
    )
    ScoreIncreaseMods = Hidden | HardRock | DoubleTime | Flashlight | FadeIn

    @classmethod
    def from_str(cls, *mods: str):
        result = cls(0)
        for m in mods:
            try:
                if isinstance(m, str):
                    result |= cls._member_map_[m]
            except KeyError:
                logging.warning(f"{m} not in enum Mods")
                continue
        return result
