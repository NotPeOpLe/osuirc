import asyncio
from .objects.message import Message
import re
from logging import Logger
from typing import TYPE_CHECKING, Coroutine, Dict, Pattern

from .utils.errors import LoginFailError
from .utils.regex import *

if TYPE_CHECKING:
    from .client import IrcClient

class IrcHandler:
    def __init__(self, client: "IrcClient") -> None:
        self.client: "IrcClient" = client
        self.log: Logger = self.client.log

        self.events: Dict[Pattern[str], Coroutine] = {
            WELCOME: self.on_welcome,
               MOTD: self.on_motd,
               PING: self.on_ping,
               QUIT: self.on_quit,
               JOIN: self.on_join,
               PART: self.on_part,
               MODE: self.on_mode,
            PRIVMSG: self.on_message,
            CHTOPIC: self.on_chtopic,
            CHCTIME: self.on_chtime,
            CHUSERS: self.on_chusers,
            CHENDNA: self.on_endofnames,
        }

    async def __call__(self, payload: str) -> None:
        return await self.handler(payload)
    
    async def handler(self, payload: str):
        for pattern in self.events:
            if m := re.match(pattern, payload):
                return await self.events[pattern](*m.groups())
        
        self.log.debug(f'NOT PROCESSED: {payload=}') # 無處理方式的訊息


    async def nothing(self, *_):
        return


    async def on_welcome(self):
        self.client.events.welcome.set()
        asyncio.create_task(self.on_ready())


    async def on_motd(self, code: str, message: str):
        self.log.debug(message)
        if code == '375':
            self.client.events.motd_start.set()
        elif code == '376':
            self.client.events.motd_end.set()
        else:
            pass


    async def on_ready(self):
        await self.client.events.welcome.wait()
        await self.client.events.motd_start.wait()
        await self.client.events.motd_end.wait()
        self.log.debug('ON_READY.')
        asyncio.create_task(self.client.on_ready())
        
        
    async def on_login_fail(self, message: str):
        self.log.debug(f'ON_LOGIN_FAIL: {message=}')
        raise LoginFailError()


    async def on_ping(self, content: str):
        self.log.debug(f'ON_PING: {content=}')
        await self.client.send_command(f'PONG {content}')
        asyncio.create_task(self.client.on_ping(content))


    async def on_quit(self, user: str, reason: str):
        asyncio.create_task(self.client.on_quit(user, reason))


    async def on_join(self, user: str, channel_name: str):
        self.log.debug(f'ON_JOIN: {user=} {channel_name=}')
        channel = self.client.channels.get(channel_name)
        if not channel:
            channel = self.client.create_channel(channel_name)
        channel.users.add(user)
        asyncio.create_task(self.client.on_join(user, channel))


    async def on_part(self, user: str, channel_name: str):
        self.log.debug(f'ON_PART: {user=} {channel_name=}')
        channel = self.client.channels[channel_name]
        channel.users.discard(user)
        if user.lower() == self.client.nickname.lower():
            channel.joined = False
        asyncio.create_task(self.client.on_part(user, channel))


    async def on_message(self, sender: str, target: str, content: str):
        self.log.debug(f'ON_MESSAGE: {sender=} {target=} {content=}')
        context = Message(self.client, sender, target, content)
        if sender == self.client.nickname:
            if content.startswith(':'):
                await self.client.send_command(content[1:])
        asyncio.create_task(self.client.on_message(context))
        
        
    async def on_mode(self, admin: str, channel_name: str, mode: str, user: str):
        self.log.debug(f'ON_MODE: {admin=} {channel_name=} {mode=} {user=}')


    async def on_chtopic(self, channel_name: str, topic: str):
        self.log.debug(f'ON_CHANNEL_TOPIC: {channel_name=} {topic=}')
        channel = self.client.channels[channel_name]
        if m := re.match(MP_GAMEID, topic):
            game_id = int(m.group(1))
            channel.game_id = game_id


    async def on_chtime(self, channel_name: str, time: int):
        self.log.debug(f'ON_CHANNEL_CREATED_TIME: {channel_name=} {time=}')
        channel = self.client.channels[channel_name]
        channel.created_time = float(time)

    async def on_chusers(self, channel_name: str, users: str):
        self.log.debug(f'ON_CHANNEL_USERS: {channel_name=} {users=}')
        channel = self.client.channels[channel_name]
        channel.users = set((u[1:] for u in users.split()))
        
    
    async def on_endofnames(self, channel_name: str):
        channel = self.client.channels[channel_name]
        self.log.debug(f'ON_ENDOFNAMES: {channel_name=}')
        self.log.debug(f'channel={channel.__dict__}')