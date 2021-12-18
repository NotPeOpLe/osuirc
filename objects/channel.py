from ..utils.errors import NotInChannel
from typing import TYPE_CHECKING, Dict, Set
if TYPE_CHECKING:
    from ..client import IrcClient

class Channel(object):
    def __init__(self, client: "IrcClient", name: str) -> None:
        self.name: str = name
        self._client: "IrcClient" = client
        self._joined: bool = True

        # 創建後更新
        self.topic: str = ''        
        self.created_time: float = 0.0
        self.users: Set[str] = set()

        # mutiplayer settings
        self._mp_id: int = int(self.name.removeprefix('#mp_'))
        self.game_id: int = 0
        self.room_name: str = None
        self.password: str = None
        self.size: int = 16
        self.slots: Dict[int, dict] = {}
        self.score_mode: int = 0
        self.team_mode: int = 0
        self.game_mode: int = 0
        self.active_mods: int = 0
        self.current_map: int = 0
        self.host: str = None
        self.started: bool = False
        self.players: int = 0


    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name}>"


    @property
    def is_mutiplayer(self):
        return True if self.name.startswith('#mp_') else False


    @property
    def mp_id(self):
        return self._mp_id


    async def send(self, content: str, ignore_limit: bool = False) -> None:
        if not self._joined:
            raise NotInChannel(f"無法將訊息傳送到'{self.name}'，因為你已離開頻道。")
        
        await self._client.send(self.name, content, ignore_limit)


    async def part(self) -> None:
        await self._client.send_command(f'PART {self.name}')


    def all_ready(self) -> bool:
        pass