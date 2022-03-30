from typing import TYPE_CHECKING


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

    async def send(self, message: str, *, action: bool = False, ignore_limit: bool = False):
        await self.__client.send(self.username, message, action=action, ignore_limit=ignore_limit)

    @classmethod
    async def from_api(cls, client: "IrcClient", username: str):
        if not client.api_key:
            raise ValueError("api_key required")

        import httpx
        async with httpx.AsyncClient() as http:
            resp = await http.get("https://osu.ppy.sh/api/get_user", params=dict(k=client.api_key, u=username, type="string"))
            resp.raise_for_status()

        result = resp.json()[0]
        client.log.debug(f'{result=}')
        
        return cls(
            client = client,
            username = result['username'],
            user_id = int(result['user_id']),
            country = result['country'],
            level = float(result['level']) if result['level'] else None,
            pp_rank = int(result['pp_rank']) if result['pp_rank'] else None,
            pp_raw = float(result['pp_raw']) if result['pp_raw'] else None,
            pp_country_rank = int(result['pp_country_rank']) if result['pp_country_rank'] else None
        )
