import asyncio
import logging
from .objects.command import Command, MsgCommand
from .objects.message import Message
import re
from typing import Any, Coroutine, Dict, List, Optional, Pattern, Set, Union

from .handler import IrcHandler
from .objects.channel import Channel, MpChannel
from .utils.errors import EmptyError
from .utils.events import Events


class IrcClient:
    def __init__(self, nickname: str, password: str, *, debug: bool = False, prefix: str = '!') -> None:
        # static
        self.host: str = 'cho.ppy.sh'
        self.port: int = 6667
        self.encoding: str = 'UTF-8'
        self.nickname: str = nickname
        self.password: str = password
        self.prefix: str = prefix
        self.debug: bool = debug
        self.limit: float = 1.0
        self.running: bool = False
        self.log: logging.Logger = logging.getLogger('IrcClient')
        self.log.setLevel(logging.DEBUG if self.debug else logging.INFO)

        self.channels: Dict[str, Union[Channel, MpChannel]] = {}
        self.users: Set[str] = set()
        self.commands: Dict[str, Command] = {}
        self.messages: Dict[Pattern[str], MsgCommand] = {}

        self.handler = IrcHandler(self)

    
    def run(self):
        self.running = True
        
        try:
            asyncio.run(self.main())
        except KeyboardInterrupt:
            self.stop()
        finally:
            self.log.info('Closed')
        

    def stop(self):
        self.running = False


    async def main(self):
        self.loop = asyncio.get_event_loop()
        self.events = Events(self.loop)
        self.sendmsg_queue = asyncio.Queue(loop=self.loop)
            
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            
        await self.send_command(f'PASS {self.password}')
        await self.send_command(f'NICK {self.nickname}')
            
        await asyncio.gather(
            self.listen(),
            self.sender()
        )


    async def send_command(self, content: str):
        self.writer.write((content + '\r\n').encode(self.encoding))
        self.log.debug(f'{content}')


    async def send(self, target, content: str, *, action: bool = False, ignore_limit: bool = False):
        _content = f'\x01ACTION {content}\x01' if action else content
        task = self.send_command(f'PRIVMSG {target} :{_content}')

        if not ignore_limit:
            self.sendmsg_queue.put_nowait(task)
        else:
            await task
            
            
    async def join(self, channel: Union[Channel, str]):
        if isinstance(channel, Channel):
            channel_name = channel.name
        elif isinstance(channel, str):
            channel_name = '#' + channel if not channel.startswith('#') else channel
        else:
            raise ValueError('channel 參數只支援 Channel、str 類別')
            
        await self.send_command(f'JOIN {channel_name}')
        
    
    async def part(self, channel: Union[Channel, str]):
        if isinstance(channel, Channel):
            channel_name = channel.name
        elif isinstance(channel, str):
            channel_name = '#' + channel if not channel.startswith('#') else channel
        else:
            raise ValueError('channel 參數只支援 Channel、str 類別')

        await self.send_command(f'PART {channel_name}')


    async def listen(self):        
        while self.running:
            if raw := await self.reader.readline():
                payload = raw.decode(self.encoding).strip()
                asyncio.create_task(self.handler(payload))
            else:
                raise EmptyError('空資料')
            
    
    async def sender(self):
        while self.running:
            task = await self.sendmsg_queue.get()
            await task
            await asyncio.sleep(self.limit)


    def create_channel(self, channel_name: str) -> Union[Channel, MpChannel]:
        channel = MpChannel(self, channel_name) if channel_name.startwith('#mp_') else Channel(self, channel_name)
        self.channels[channel_name] = channel
        self.log.debug(f'NEW_CHANNEL: {channel=}')
        return channel
    
    
    def command(self, name: str = None):
        def wapper(func):
            cmd_name = name or func.__name__
            self.commands[cmd_name] = Command(func)
        return wapper
    

    def message(self, regex: str, users: Optional[List[str]] = None):
        def wapper(func: Coroutine):
            pattern = re.compile(regex)
            self.messages[pattern] = MsgCommand(func, users)
        return wapper


    async def call_command(self, ctx: Message):
        if ctx.content.startswith('!'):
            ctx_split = ctx.content.removeprefix(self.prefix).split()
            cmd = ctx_split[0]
            args = ctx_split[1:]
            
            if command := self.commands.get(cmd):
                return asyncio.create_task(command(ctx, *args))
        else:
            for m in self.messages:
                if match := re.match(ctx.content):
                    command = self.messages[m]
                    if ctx.author.lower() in command.allow_users or command.allow_users is None:
                        return asyncio.create_task(command(ctx, **match.groupdict()))
                
                
    # Events
    async def on_ready(self):
        pass
    
    async def on_ping(self, message: str):
        pass
    
    async def on_message(self, ctx: Message):
        await self.call_command(ctx)
    
    async def on_join(self, user: str, channel: Channel):
        pass
    
    async def on_part(self, user: str, channel: Channel):
        pass
    
    async def on_quit(self, user: str, reason: str):
        pass