from typing import TYPE_CHECKING, Any, Dict


if TYPE_CHECKING:
    from ..client import IrcClient


class User(object):
    def __init__(
        self,
        client: "IrcClient",
        username: str,
        user_id: int = None,
        country: str = None,
        level: float = None,
        pp_rank: int = None,
        pp_raw: float = None,
        pp_country_rank: int = None
    ) -> None:
        self.__client = client
        self.username = username
        self.user_id = user_id
        self.country = country
        self.level = level
        self.pp_rank = pp_rank
        self.pp_raw = pp_raw
        self.pp_country_rank = pp_country_rank

    def __getattribute__(self, __name: str) -> Any:
        attr = super(User, self).__getattribute__(__name)
        if attr:
            return attr
        self.load()
        return super(User, self).__getattribute__(__name)

    async def send(self, message: str, *, action: bool = False, ignore_limit: bool = False):
        await self.__client.send(self.username, message, action=action, ignore_limit=ignore_limit)

    def get_data(self, api_key, username: str) -> Dict[str, str]:
        if not api_key:
            raise ValueError("api_key required")

        import httpx
        with httpx.Client() as http:
            resp = http.get("https://osu.ppy.sh/api/get_user",
                            params=dict(k=api_key, u=username, type="string"))
            resp.raise_for_status()

        return resp.json()[0]

    def load(self):
        result = self.get_data(self.__client.api_key, self.username)
        self.user_id = int(result['user_id'])
        self.country = result['country']
        self.level = float(result['level']) if result['level'] else None,
        self.pp_rank = int(result['pp_rank']) if result['pp_rank'] else None,
        self.pp_raw = float(result['pp_raw']) if result['pp_raw'] else None,
        self.pp_country_rank = int(
            result['pp_country_rank']) if result['pp_country_rank'] else None
