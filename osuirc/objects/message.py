from typing import TYPE_CHECKING, Union

from ..objects.user import User


if TYPE_CHECKING:
    from ..client import IrcClient
    from ..objects.channel import Channel, MpChannel


class Message(object):
    def __init__(self, client: "IrcClient", author: str, target: str, content: str) -> None:
        self.__client: "IrcClient" = client
        self.__author: User = User(client, author)
        self.__target: str = target
        self.__content: str = content
        # 如果訊息類類型私人，那頻道將會是 client.nickname
        self.__channel = self.__client.channels.get(target)
        if not self.__channel:
            self.__channel = self.__client.create_channel(target)
        self.__private = target[0] != '#'

    @property
    def author(self) -> User:
        return self.__author

    @property
    def channel(self) -> Union["Channel", "MpChannel"]:
        return self.__channel

    @property
    def content(self) -> str:
        return self.__content

    @property
    def is_private(self) -> bool:
        return self.__private

    async def reply(self, content: str, *, action: bool = False, ignore_limit: bool = False):
        """
        快速回復，如果發送者(sender)是在頻道上發言，則會回覆在頻道；發送者(sender)是用私人訊息，則會回覆給發送者
        """
        target = self.author.username if self.is_private else self.channel.name
        await self.__client.send(target, content, action=action, ignore_limit=ignore_limit)
