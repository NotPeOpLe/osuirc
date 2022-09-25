from asyncio import Event
from dataclasses import dataclass

from osuirc.objects.channel import MpChannel
from osuirc.objects.enums import GameMode, Mods, ScoreMode, TeamMode, TeamType
from osuirc.objects.osu import Beatmap


class ClientEvents:
    def __init__(self) -> None:
        self.welcome = Event()
        self.motd_start = Event()
        self.motd_end = Event()


@dataclass
class BaseMatchEvent:
    channel: MpChannel


@dataclass
class MatchLockChanged(BaseMatchEvent):
    old: bool
    new: bool


@dataclass
class MatchSizeChanged(BaseMatchEvent):
    old: bool
    new: bool


@dataclass
class MatchTeamModeChanged(BaseMatchEvent):
    old: TeamMode
    new: TeamMode


@dataclass
class MatchScoreModeChanged(BaseMatchEvent):
    old: ScoreMode
    new: ScoreMode


@dataclass
class MatchGameModeChanged(BaseMatchEvent):
    old: GameMode
    new: GameMode


@dataclass
class MatchHostChanged(BaseMatchEvent):
    old: str
    new: str


@dataclass
class MatchPasswordChanged(BaseMatchEvent):
    has_password: bool


@dataclass
class MatchModsChanged(BaseMatchEvent):
    old_mods: Mods
    new_mods: Mods
    old_freemod: bool
    new_freemod: bool


@dataclass
class MatchPlayerCountChanged(BaseMatchEvent):
    old: int
    new: int


@dataclass
class MatchMapChanged(BaseMatchEvent):
    old: Beatmap | None
    new: Beatmap | None


@dataclass
class MatchStarted(BaseMatchEvent):
    pass


@dataclass
class MatchFinished(BaseMatchEvent):
    pass


@dataclass
class MatchAborted(BaseMatchEvent):
    pass


@dataclass
class MatchRefereeAdded(BaseMatchEvent):
    ref: str


@dataclass
class MatchRefereeRemoved(BaseMatchEvent):
    ref: str


@dataclass
class MatchTimerStarted(BaseMatchEvent):
    time: int


@dataclass
class MatchTimerStopped(BaseMatchEvent):
    pass


@dataclass
class MatchTimerAborted(BaseMatchEvent):
    pass


@dataclass
class MatchCreated(BaseMatchEvent):
    pass


@dataclass
class MatchClosed(BaseMatchEvent):
    pass


@dataclass
class MatchRoomNameChanged(BaseMatchEvent):
    old: str
    new: str


@dataclass
class PlayerJoined(BaseMatchEvent):
    user: str
    slot: int
    team: TeamType = TeamType.Neutral


@dataclass
class PlayerLeft(BaseMatchEvent):
    user: str


@dataclass
class PlayerKicked(BaseMatchEvent):
    user: str


@dataclass
class PlayerBanned(BaseMatchEvent):
    user: str


@dataclass
class PlayerSlotChanged(BaseMatchEvent):
    user: str
    old: int
    new: int


@dataclass
class PlayerTeamChanged(BaseMatchEvent):
    user: str
    old: TeamType
    new: TeamType


@dataclass
class PlayerModsChanged(BaseMatchEvent):
    user: str
    old: Mods
    new: Mods


@dataclass
class PlayerFinished(BaseMatchEvent):
    user: str
    score: int
    passed: bool


@dataclass
class SlotUpdated(BaseMatchEvent):
    slot_number: int
    username: str
    user_id: int
    status: str
    is_host: bool
    team: TeamType
    enabled_mods: Mods


@dataclass
class AllPlayerReady(BaseMatchEvent):
    pass
