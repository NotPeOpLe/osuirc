from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ..client import IrcClient

class User(object):
    def __init__(self, client: IrcClient, username: str) -> None:
        self.username = username
        self.__client = client

    async def send(self, message: str, action: bool = False):
        await self.__client.send(self.username, message, action)
