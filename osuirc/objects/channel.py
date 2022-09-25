from typing import TYPE_CHECKING, Set

from osuirc.objects.osu import Beatmap

from .enums import Mods, ScoreMode, TeamMode
from ..objects.slot import Slots
from ..utils.errors import NotInChannel

if TYPE_CHECKING:
    from ..client import IrcClient


class Channel(object):
    def __init__(self, client: "IrcClient", name: str) -> None:
        self.name: str = name
        self.__client: "IrcClient" = client
        self.joined: bool = True

        # 創建後更新
        self.topic: str = ""
        self.created_time: float = 0.0
        self.users: Set[str] = set()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name}>"

    def __str__(self) -> str:
        return self.name

    @property
    def is_mutiplayer(self):
        return self.name[:4] == "#mp_"

    async def send(
        self, content: str, *, action: bool = False, ignore_limit: bool = False
    ) -> None:
        if not self.joined:
            raise NotInChannel(f"無法將訊息傳送到'{self.name}'，因為你已離開頻道。")

        await self.__client.send(
            self.name, content, action=action, ignore_limit=ignore_limit
        )

    async def part(self) -> None:
        await self.__client.send_command(f"PART {self.name}")


class MpChannel(Channel):
    def __init__(self, client: "IrcClient", name: str) -> None:
        super().__init__(client, name)
        self._mp_id: int = int(self.name[4:])
        self.game_id: int = 0
        self.room_name: str = None
        self.has_password: bool = True
        self.size: int = 16
        self.slots: Slots = Slots()
        self.score_mode: ScoreMode = ScoreMode.Score
        self.team_mode: TeamMode = TeamMode.HeadToHead
        self.game_mode: int = 0
        self.active_mods: Mods = Mods.NoMod
        self.freemod: bool = False
        self.current_map: Beatmap | None = None
        self.host: str = None
        self.started: bool = False
        self.locked: bool = False
        self.player_count: int = 0
        self.refs: set = {}

    @property
    def mp_id(self):
        return self._mp_id
