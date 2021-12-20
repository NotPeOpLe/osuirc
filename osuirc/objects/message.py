from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ..client import IrcClient
    from ..objects.channel import Channel


class Message(object):
    def __init__(self, client: "IrcClient", author: str, target: str, content: str) -> None:
        self._client: "IrcClient" = client
        self._author: str = author
        self._target: str = target
        self._content: str = content
        
        if target.startswith("#"):
            self._channel = self._client.channels.get(target)
            if not self._channel:
                self._channel = self._client.create_channel(target)
            self._private = False
            
            
    @property
    def author(self) -> str:
        return self._author
    
    @property
    def channel(self) -> "Channel":
        return self._channel
    
    @property
    def content(self) -> str:
        return self._content
    
    @property
    def is_private(self) -> bool:
        return self._private
    
    
    async def reply(self, content: str, ignore_limit: bool = False):
        """快速回復，如果發送者(sender)是在頻道上發言，則會回覆在頻道；發送者(sender)是用私人訊息，則會回覆給發送者
        """
        target = self.channel or self.author
        await self._client.send(target, content, ignore_limit)