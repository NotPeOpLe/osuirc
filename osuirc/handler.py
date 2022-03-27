import asyncio
import re
from logging import Logger
from typing import TYPE_CHECKING, Coroutine, Dict, Pattern, Union

from osuirc.objects.slot import Slots

from .objects.osuenums import GameMode, Mods, ScoreMode, TeamMode, TeamType
from .objects.message import Message
from .utils.errors import LoginFailError
from .utils.regex import *

if TYPE_CHECKING:
    from .client import IrcClient
    from .objects.channel import MpChannel


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
        for pattern in self.events:
            if m := re.match(pattern, payload):
                return await self.events[pattern](*m.groups())

        self.log.debug(f'NOT PROCESSED: {payload=}')  # 無處理方式的訊息

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


class MultiplayerHandler:
    events: Dict[Pattern[str], Coroutine] = {}

    async def __call__(self, ctx: Message) -> None:
        for pattern in self.events:
            if m := re.match(pattern, ctx):
                return await self.events[pattern](ctx.channel, **m.groupdict())

    def match(self, regex):
        def wapper(func: Coroutine):
            pattern = re.compile(regex)
            self.events[pattern] = func
        return wapper

    @match(r"Locked the match")
    async def on_lock(self, channel: "MpChannel"):
        # !mp lock
        # Locked the match
        channel.locked = True

    @match(r"Unlocked the match")
    async def on_unlock(self, channel: "MpChannel"):
        # !mp unlock
        # Unlocked the match
        channel.locked = False

    # async def on_make(self):
    #     # !mp make 840
    #     # !mp makeprivate 840
    #     # success: Created the tournament match https://osu.ppy.sh/mp/98932732 840
    #     # fail: You cannot create any more tournament matches. Please close any previous tournament matches you have open.
    #     pass

    @match(r"Changed match to size (?P<size>\d{1,2})")
    async def on_change_size(self, channel: "MpChannel", size: int):
        # !mp size 12
        # Changed match to size 12
        channel.size = size

    @match(r"Changed match settings to (?P<settings>.*)")
    async def on_set(self, channel: "MpChannel", settings: str):
        # !mp set 0 0 2
        # Changed match settings to 2 slots, HeadToHead, Score
        # Teammode 0: HeadToHead, 1: TagCoop, 2: TeamVs, 3: TagTeamVs
        # Scoremode 0: Score, 1: Accuracy, 2: Combo
        settings = settings.split(", ")
        for s in settings:
            if s.endswith(" slots"):
                channel.size = int(s.removesuffix(" slots"))
            if team_mode := TeamMode._member_map_.get(s):
                channel.team_mode = team_mode
            if score_mode := ScoreMode._member_map_.get(s):
                channel.score_mode = score_mode

    @match(r"(?P<username>.*) moved to slot (?P<new_slot>\d{1,2})")
    async def on_move(self, channel: "MpChannel", username: str, new_slot: str):
        # _CHIMERA moved to slot 5
        channel.slots.move(username, int(new_slot))

    # async def on_invite(self, channel: "MpChannel", user):
    #     # !mp invite _CHIMERA
    #     # Invited _CHIMERA to the room
    #     ...

    @match(r"(?P<host>.*) became the host.")
    @match(r"Cleared match host")
    async def on_change_host(self, channel: "MpChannel", host=None):
        channel.host = host

    @match(r"Room name updated to \"(?P<room_name>.*)\"")
    @match(r"Room name: (?P<room_name>.*),.*")
    async def update_room_name(self, channel: "MpChannel", room_name: str):
        # !mp name 484
        # Room name updated to "484"
        # !mp settings
        # Room name: 840, History: https://osu.ppy.sh/mp/98933063
        channel.name = room_name

    @match(r"Beatmap: https://osu.ppy.sh/b/(?P<map_id>\d+) (?P<map_repl>.*)")
    @match(r"Beatmap changed to: (?P<map_repl>.*) \(https://osu.ppy.sh/b/(?P<map_id>\d+)\)")
    @match(r"Changed beatmap to https://osu.ppy.sh/b/(?P<map_id>\d+) (?P<map_repl>.*)")
    async def update_current_map(self, channel: "MpChannel", map_id: str, map_repl: str):
        # !mp settings
        # Beatmap: https://osu.ppy.sh/b/3360065 Raimukun - Firmament star [Cup]
        # host change map
        # Beatmap changed to: Aitsuki Nakuru - phony [x] (https://osu.ppy.sh/b/3461204)
        # !mp map 3461204
        # Changed beatmap to https://osu.ppy.sh/b/96 Hinoi Team - Emoticons
        channel.current_map_id = int(map_id)
        channel.current_map_repr = map_repl

    @match(r"Team mode: (?P<team_mode>\S+), Win condition: (?P<score_mode>\S+)")
    async def update_settings(self, channel: "MpChannel", team_mode: str, score_mode: str):
        # !mp settings
        # Team mode: HeadToHead, Win condition: Score
        channel.team_mode = TeamMode[team_mode]
        channel.score_mode = ScoreMode[score_mode]

    @match(r"Players: (?P<player_count>\d+)")
    async def update_player_count(self, channel: "MpChannel", player_count: str):
        # !mp settings
        # Players: 1
        channel.player_count = player_count
        channel.slots.clear()

    @match(r"Slot (?P<slot>\d{1,2})  (?P<status>Ready|Not Ready|No Map)\s*https://osu\.ppy\.sh/u/(?P<user_id>\d+) (?P<user_name>\S*)(?P<flags>.*)")
    async def update_palyer(
        self,
        channel: "MpChannel",
        slot: str,
        status: str,
        user_id: str,
        user_name: str,
        flags: str
    ):
        # !mp settings
        # Slot 1  Not Ready https://osu.ppy.sh/u/6008293 _CHIMERA        [Host / Team Blue / Hidden]
        #         No Map
        #         Ready
        # TODO: this
        is_host = False
        team = TeamType.Neutral
        enabled_mods = Mods.NoMod
        for flag in flags.strip()[1:-1].split(" / "):
            if flag == "Host":
                is_host = True
            elif flag == "Team Blue":
                team = TeamType.Blue
            elif flag == "Team Red":
                team == TeamType.Red
            else:
                enabled_mods = Mods.from_str(*flag.split(", "))

        channel.slots.set(
            slot_number=int(slot),
            username=user_name,
            user_id=user_id,
            status=status,
            is_host=is_host,
            team=team,
            enabled_mods=enabled_mods
        )

    @match(r"The match has started!")
    async def on_start(self, channel: "MpChannel"):
        # !mp start
        # success: The match has started!
        # fail: The match has already been started
        channel.started = True

    @match(r"The match has started!")
    async def on_abort(self, channel: "MpChannel", ):
        # !mp abort
        # success: Aborted the match
        # fail: The match is not in progress
        channel.started = False

    @match(r"(?P<user>) changed to (?P<team>Red|Blue)")
    async def on_change_team(self, channel: "MpChannel", user: str, team: str):
        # _CHIMERA changed to Red
        channel.slots.get(user).team = TeamType[team]

    @match(r"Changed match mode to (?P<game_mode>OsuMania|Osu|Taiko|CatchTheBeat)")
    async def on_change_mode(self, channel: "MpChannel", game_mode: str):
        # Changed match mode to OsuMania
        channel.game_mode = GameMode[game_mode]

    @match(r"(Disabled all mods|Enabled (?P<enabled_mods>.*)), (?P<freemod>dis|en)abled FreeMod")
    async def on_change_mods(self, channel: "MpChannel", enabled_mods: str, freemod: str):
        # no params: Disabled all mods, disabled FreeMod
        # has params: Enabled NoFail, disabled FreeMod
        # freemod: Disabled all mods, enabled FreeMod
        channel.active_mods = Mods.from_str(*enabled_mods.split(", "))
        channel.freemod = True if freemod == "en" else False

    @match(r"(?P<password>Removed|Changed) the match password")
    async def on_change_password(self, channel: "MpChannel", password: str):
        # no params: Removed the match password
        # has params: Changed the match password
        channel.has_password = True if password == "Changed" else False

    @match(r"Added (?P<ref>.*) to the match referees")
    async def on_addref(self, channel: "MpChannel", ref: str):
        # Added _CHIMERA to the match referees
        channel.refs.add(ref)

    @match(r"Removed (?P<ref>.*) from the match referees")
    async def on_removeref(self, channel: "MpChannel", ref: str):
        # Removed _CHIMERA from the match referees
        channel.refs.remove(ref)

    # async def update_refs(self, channel: "MpChannel", ):
        # Match referees:
        # xxxx
        # _CHIMERA
        # 這玩意有點麻煩 可能要用 event 暫時不使用

    @match(r"Kicked (?P<user>.*) from the match")
    async def on_kick(self, channel: "MpChannel", user: str):
        # Kicked _CHIMERA from the match
        pass

    @match(r"Countdown ends in (\d+) (minutes|seconds)")
    async def on_timer(self, channel: "MpChannel", time: str):
        # Countdown ends in ?? minutes/seconds
        pass

    @match(r"Countdown aborted")
    async def on_aborttimer(self, channel: "MpChannel"):
        # Countdown aborted
        pass

    @match(r"Banned (?P<user>.*) from the match")
    async def on_ban(self, channel: "MpChannel", user: str):
        # Banned _CHIMERA from the match
        pass

    @match(r"Closed the match")
    async def on_close(self, channel: "MpChannel"):
        # Closed the match
        pass

    @match(r"(?P<user>.*) joined in slot (?P<slot>\d+)( for team (?P<team>blue|red))\.")
    async def on_join(self, channel: "MpChannel", user: str, slot: str, team: Union[str, None]):
        # _CHIMERA joined in slot 1.
        # _CHIMERA joined in slot 1 for team blue/red.
        channel.slots.set(int(slot), user, TeamType(team))

    @match(r"(?P<user>.*) left the game.")
    async def on_left(self, channel: "MpChannel", user: str):
        # _CHIMERA left the game.
        channel.slots.remove_from_username(user)
        pass

    # async def on_changing_map(self, channel: "MpChannel", ):
        # Host is changing map...

    @match(r"All players are ready")
    async def on_ready(self, channel: "MpChannel"):
        # All players are ready
        pass

    @match(r"(?P<user>.*) finished playing \(Score: (?P<score>\d+), (?P<status>FAILED|PASSED)\)\.")
    async def on_result(self, channel: "MpChannel", user: str, score: str, status: str):
        # _CHIMERA finished playing (Score: 86698, FAILED).
        passed = True if status == "PASSED" else False

    @match(r"The match has finished!")
    async def on_finished(self, channel: "MpChannel"):
        # The match has finished!
        pass
