import asyncio
import logging
import re
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Pattern,
    Set,
    TypeVar,
    Union,
)

from osuirc.objects.osu import Beatmap


from .objects.message import Message
from .objects.enums import GameMode, Mods, ScoreMode, TeamMode, TeamType
from .objects.user import User
from .utils.errors import LoginFailError
from .utils.events import *
from .utils.regex import *

if TYPE_CHECKING:
    from .client import IrcClient
    from .objects.channel import MpChannel

MatchEventT = TypeVar("MatchEventT", bound=BaseMatchEvent)
log = logging.getLogger("IrcClient")


class IrcHandler:
    def __init__(self, client: "IrcClient") -> None:
        self.client: "IrcClient" = client

        self.events: Dict[Pattern[str], Callable] = {
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
            WHOISUSER: self.on_whoisuser,
            WHOISSERVER: self.on_whoisserver,
            WHOISCHANNELS: self.on_whoischannels,
            ENDOFWHOIS: self.on_endofwhois,
        }

    async def __call__(self, payload: str) -> None:
        for pattern in self.events:
            if m := re.match(pattern, payload):
                return await self.events[pattern](*m.groups())

        log.debug(f"NOT PROCESSED: {payload=}")  # 無處理方式的訊息

    async def nothing(self, *_):
        return

    async def on_welcome(self):
        self.client.events.welcome.set()
        asyncio.create_task(self.on_ready())

    async def on_motd(self, code: str, message: str):
        log.debug(message)
        if code == "375":
            self.client.events.motd_start.set()
        elif code == "376":
            self.client.events.motd_end.set()
        else:
            pass

    async def on_ready(self):
        await self.client.events.welcome.wait()
        await self.client.events.motd_start.wait()
        await self.client.events.motd_end.wait()
        asyncio.create_task(self.client.on_ready())
        log.debug("ON_READY.")

    async def on_login_fail(self, message: str):
        log.debug(f"ON_LOGIN_FAIL: {message=}")
        raise LoginFailError()

    async def on_ping(self, content: str):
        await self.client.send_command(f"PONG {content}")
        asyncio.create_task(self.client.on_ping(content))
        log.debug(f"ON_PING: {content=}")

    async def on_quit(self, user: str, reason: str):
        asyncio.create_task(self.client.on_quit(user, reason))

    async def on_join(self, user: str, channel_name: str):
        channel = self.client.get_channel(channel_name)
        channel.users.add(user)
        asyncio.create_task(self.client.on_join(user, channel))
        log.debug(f"ON_JOIN: {user=} {channel_name=}")

    async def on_part(self, user: str, channel_name: str):
        channel = self.client.channels[channel_name]
        channel.users.discard(user)
        if user.lower() == self.client.nickname.lower():
            channel.joined = False
        asyncio.create_task(self.client.on_part(user, channel))
        log.debug(f"ON_PART: {user=} {channel_name=}")

    async def on_message(self, sender: str, target: str, content: str):
        if not (user := self.client.users_cache.get(sender)):
            user = User(self.client, sender)
            self.client.users_cache[sender] = user
        context = Message(self.client, user, target, content)
        if sender == self.client.nickname:
            if content[0] == ":":
                await self.client.send_command(content[1:])
        asyncio.create_task(self.client.on_message(context))
        log.debug(f"ON_MESSAGE: {user=} {target=} {content=}")

    async def on_mode(self, admin: str, channel_name: str, mode: str, user: str):
        log.debug(f"ON_MODE: {admin=} {channel_name=} {mode=} {user=}")

    async def on_chtopic(self, channel_name: str, topic: str):
        channel = self.client.channels[channel_name]
        if m := re.match(MP_GAMEID, topic):
            game_id = int(m.group(1))
            channel.game_id = game_id
        log.debug(f"ON_CHANNEL_TOPIC: {channel_name=} {topic=}")

    async def on_chtime(self, channel_name: str, time: int):
        channel = self.client.channels[channel_name]
        channel.created_time = float(time)
        log.debug(f"ON_CHANNEL_CREATED_TIME: {channel_name=} {time=}")

    async def on_chusers(self, channel_name: str, users: str):
        channel = self.client.channels[channel_name]
        channel.users = set(
            (u.removeprefix("@").removeprefix("+") for u in users.split())
        )
        log.debug(f"ON_CHANNEL_USERS: {channel_name=} {users=}")

    async def on_endofnames(self, channel_name: str):
        log.debug(f"ON_ENDOFNAMES: {channel_name=}")
        channel = self.client.channels[channel_name]
        log.debug(f"channel={channel.__dict__}")

    async def on_whoisuser(self, username: str, user_id: str):
        user = self.client.users_cache[username]
        user.user_id = int(user_id)
        log.debug(f"ON_WHOISUSER: {username=} {user_id=}")

    async def on_whoisserver(self, username: str, host: str, server_info: str):
        log.debug(f"ON_WHOISSERVER: {username=} {host=} {server_info=}")

    async def on_whoischannels(self, username: str, channels: str):
        log.debug(f"ON_WHOISCHANNELS: {username=} {channels=}")

    async def on_endofwhois(
        self,
        username: str,
    ):
        log.debug(f"ON_ENDOFWHOIS: {username=} End of /WHOIS list")


class MultiplayerHandler:
    def __init__(self, client: "IrcClient") -> None:
        self.client = client
        self.ext_events: Dict[MatchEventT, Set[Callable[[MatchEventT], Any]]] = {}
        self.events: Dict[Pattern[str], Callable] = {
            MP_LOCKED: self.on_lock,
            MP_UNLOCK: self.on_unlock,
            MP_CHANGED_SIZE: self.on_change_size,
            MP_CHANGED_SET: self.on_set,
            MP_PLAYER_MOVED: self.on_move,
            MP_CHANGED_HOST: self.on_change_host,
            MP_CLEARHOST: self.on_change_host,
            MP_CHANGED_NAME: self.update_room_name,
            MP_UPDATE_NAME: self.update_room_name,
            MP_UPDATE_MAP: self.update_current_map,
            MP_CHANGED_MAP: self.update_current_map,
            MP_CHANGED_MAP2: self.update_current_map,
            MP_UPDATE_SET: self.update_settings,
            MP_UPDATE_PC: self.update_player_count,
            MP_SLOT_INFO: self.update_palyer,
            MP_STARTED: self.on_start,
            MP_ABORTED: self.on_abort,
            MP_CHANGED_TEAM: self.on_change_team,
            MP_CHANGED_MODE: self.on_change_mode,
            MP_CHANGED_MODS: self.on_change_mods,
            MP_CHANGED_PASSWD: self.on_change_password,
            MP_ADDED_REF: self.on_addref,
            MP_REMOVED_REF: self.on_removeref,
            MP_KICKED: self.on_kick,
            MP_TIMER_START: self.on_timer,
            MP_TIMER_ABORT: self.on_aborttimer,
            MP_BANNED: self.on_ban,
            MP_CLOSE: self.on_close,
            MP_JOIN: self.on_join,
            MP_LEFT: self.on_left,
            MP_ALL_READY: self.on_ready,
            MP_FINISED_PLAYING: self.on_result,
            MP_FINISED: self.on_finished,
        }

    async def __call__(self, ctx: Message) -> None:
        for pattern in self.events:
            if m := re.match(pattern, ctx.content):
                asyncio.create_task(self.events[pattern](ctx.channel, **m.groupdict()))

    async def call_ext(self, event: MatchEventT, channel: "MpChannel", **kwargs):
        # 擴充mp處理程序呼叫器
        if handlers := self.ext_events.get(event):
            Event = event(channel, **kwargs)
            for handler in handlers:
                asyncio.create_task(handler(Event))

    # MP_LOCKED
    async def on_lock(self, channel: "MpChannel"):
        # !mp lock
        # Locked the match
        old = channel.locked
        channel.locked = True
        await self.call_ext(
            MatchLockChanged,
            channel,
            old=old,
            new=channel.locked,
        )

    # MP_UNLOCK
    async def on_unlock(self, channel: "MpChannel"):
        # !mp unlock
        # Unlocked the match
        old = channel.locked
        channel.locked = False
        await self.call_ext(
            MatchLockChanged,
            channel,
            old=old,
            new=channel.locked,
        )

    # async def on_make(self):
    #     # !mp make 840
    #     # !mp makeprivate 840
    #     # success: Created the tournament match https://osu.ppy.sh/mp/98932732 840
    #     # fail: You cannot create any more tournament matches. Please close any previous tournament matches you have open.
    #     pass

    # MP_CHANGED_SIZE
    async def on_change_size(self, channel: "MpChannel", size: int):
        # !mp size 12
        # Changed match to size 12
        old = channel.size
        channel.size = size
        await self.call_ext(
            MatchSizeChanged,
            channel,
            old=old,
            new=channel.size,
        )

    # MP_CHANGED_SET
    async def on_set(self, channel: "MpChannel", settings: str):
        # !mp set 0 0 2
        # Changed match settings to 2 slots, HeadToHead, Score
        # Teammode 0: HeadToHead, 1: TagCoop, 2: TeamVs, 3: TagTeamVs
        # Scoremode 0: Score, 1: Accuracy, 2: Combo
        settings = settings.split(", ")
        for s in settings:
            if s.endswith(" slots"):
                old_size = channel.size
                channel.size = int(s.removesuffix(" slots"))
                await self.call_ext(
                    MatchSizeChanged,
                    channel,
                    old=old_size,
                    new=channel.size,
                )
            # 這個轉移給 !mp settings處理
            # if team_mode := TeamMode._member_map_.get(s):
            #     old_team_mode = channel.team_mode
            #     channel.team_mode = team_mode
            #     await self.call_ext(
            #         MatchTeamModeChanged,
            #         channel,
            #         old=old_team_mode,
            #         new=channel.team_mode,
            #     )
            # if score_mode := ScoreMode._member_map_.get(s):
            #     old_score_mode = channel.score_mode
            #     channel.score_mode = score_mode
            #     await self.call_ext(
            #         MatchScoreModeChanged,
            #         channel,
            #         old=old_score_mode,
            #         new=channel.score_mode,
            #     )
        await channel.send("!mp settings")

    # MP_PLAYER_MOVED
    async def on_move(self, channel: "MpChannel", username: str, new_slot: str):
        # _CHIMERA moved to slot 5
        old_slot = channel.slots._username_slot[username]
        new_slot = int(new_slot)
        channel.slots.move(username, new_slot)
        await self.call_ext(
            PlayerSlotChanged,
            channel,
            username=username,
            old=old_slot,
            new=new_slot,
        )

    # async def on_invite(self, channel: "MpChannel", user):
    #     # !mp invite _CHIMERA
    #     # Invited _CHIMERA to the room
    #     ...

    # MP_CHANGED_HOST
    # MP_CLEARHOST
    async def on_change_host(self, channel: "MpChannel", host=None):
        old_host = channel.host
        channel.host = host
        await self.call_ext(
            MatchHostChanged,
            channel,
            old=old_host,
            new=channel.host,
        )

    # MP_CHANGED_NAME
    # MP_UPDATE_NAME
    async def update_room_name(self, channel: "MpChannel", room_name: str):
        # !mp name 484
        # Room name updated to "484"
        # !mp settings
        # Room name: 840, History: https://osu.ppy.sh/mp/98933063
        old_room_name = channel.room_name
        channel.room_name = room_name
        await self.call_ext(
            MatchRoomNameChanged,
            channel,
            old=old_room_name,
            new=channel.room_name,
        )

    # MP_UPDATE_MAP
    # MP_CHANGED_MAP
    # MP_CHANGED_MAP2
    async def update_current_map(
        self, channel: "MpChannel", map_id: str, map_repl: str
    ):
        # !mp settings
        # Beatmap: https://osu.ppy.sh/b/3360065 Raimukun - Firmament star [Cup]
        # host change map
        # Beatmap changed to: Aitsuki Nakuru - phony [x] (https://osu.ppy.sh/b/3461204)
        # !mp map 3461204
        # Changed beatmap to https://osu.ppy.sh/b/96 Hinoi Team - Emoticons
        old_map = channel.current_map
        channel.current_map = Beatmap(
            id=int(map_id),
            artist=map_repl.split(" - ")[0],
            title=map_repl.split(" - ")[1].split(" [")[0],  # 有些地圖名稱會有 [xxx] 這種東西
            version=map_repl.split(" [")[1].removesuffix("]"),
        )
        await self.call_ext(
            MatchMapChanged,
            channel,
            old=old_map,
            new=channel.current_map,
        )

    # MP_UPDATE_SET
    async def update_settings(
        self, channel: "MpChannel", team_mode: str, score_mode: str
    ):
        # !mp settings
        # Team mode: HeadToHead, Win condition: Score
        old_team_mode = channel.team_mode
        channel.team_mode = TeamMode[team_mode]
        await self.call_ext(
            MatchTeamModeChanged,
            channel,
            old=old_team_mode,
            new=channel.team_mode,
        )

        old_score_mode = channel.score_mode
        channel.score_mode = ScoreMode[score_mode]
        await self.call_ext(
            MatchScoreModeChanged,
            channel,
            old=old_score_mode,
            new=channel.score_mode,
        )

    # MP_UPDATE_PC
    async def update_player_count(self, channel: "MpChannel", player_count: str):
        # !mp settings
        # Players: 1
        old_player_count = channel.player_count
        channel.player_count = int(player_count)
        channel.slots.clear()
        await self.call_ext(
            MatchPlayerCountChanged,
            channel,
            old=old_player_count,
            new=channel.player_count,
        )

    # MP_SLOT_INFO
    async def update_palyer(
        self,
        channel: "MpChannel",
        slot: str,
        status: str,
        user_id: str,
        user_name: str,
        flags: str,
    ):
        # !mp settings
        # Slot 1  Not Ready https://osu.ppy.sh/u/6008293 _CHIMERA        [Host / Team Blue / Hidden]
        #         No Map
        #         Ready

        # 初始化
        channel.host = None
        is_host = False
        team = TeamType.Neutral
        enabled_mods = Mods.NoMod

        for flag in flags.strip()[1:-1].split(" / "):
            if flag == "Host":
                channel.host = user_name
                is_host = True
            elif flag == "Team Blue":
                team = TeamType.Blue
            elif flag == "Team Red":
                team = TeamType.Red
            else:
                enabled_mods = Mods.from_str(*flag.split(", "))

        channel.slots.set(
            slot_number=int(slot),
            username=user_name,
            user_id=user_id,
            status=status,
            is_host=is_host,
            team=team,
            enabled_mods=enabled_mods,
        )
        await self.call_ext(
            SlotUpdated,
            channel,
            slot_number=int(slot),
            username=user_name,
            user_id=user_id,
            status=status,
            is_host=is_host,
            team=team,
            enabled_mods=enabled_mods,
        )

    # MP_STARTED
    async def on_start(self, channel: "MpChannel"):
        # !mp start
        # success: The match has started!
        # fail: The match has already been started
        channel.started = True
        await self.call_ext(
            MatchStarted,
            channel,
        )

    # MP_ABORTED
    async def on_abort(
        self,
        channel: "MpChannel",
    ):
        # !mp abort
        # success: Aborted the match
        # fail: The match is not in progress
        channel.started = False
        await self.call_ext(
            MatchAborted,
            channel,
        )

    # MP_CHANGED_TEAM
    async def on_change_team(self, channel: "MpChannel", user: str, team: str):
        # _CHIMERA changed to Red
        user = channel.slots.get(user)
        old_team = user.team
        user.team = TeamType[team]
        await self.call_ext(
            PlayerTeamChanged,
            channel,
            user=user,
            old=old_team,
            new=user.team,
        )

    # MP_CHANGED_MODE
    async def on_change_mode(self, channel: "MpChannel", game_mode: str):
        # Changed match mode to OsuMania
        old_game_mode = channel.game_mode
        channel.game_mode = GameMode[game_mode]
        await self.call_ext(
            MatchGameModeChanged,
            channel,
            old=old_game_mode,
            new=channel.game_mode,
        )

    # MP_CHANGED_MODS
    async def on_change_mods(
        self, channel: "MpChannel", enabled_mods: str, freemod: str
    ):
        # no params: Disabled all mods, disabled FreeMod
        # has params: Enabled NoFail, disabled FreeMod
        # freemod: Disabled all mods, enabled FreeMod
        old_enabled_mods = channel.enabled_mods
        old_freemod = channel.freemod
        channel.active_mods = Mods.from_str(*enabled_mods.split(", "))
        channel.freemod = freemod == "en"
        await self.call_ext(
            MatchModsChanged,
            channel,
            old_enabled_mods=old_enabled_mods,
            new_enabled_mods=channel.active_mods,
            old_freemod=old_freemod,
            new_freemod=channel.freemod,
        )

    # MP_CHANGED_PASSWD
    async def on_change_password(self, channel: "MpChannel", password: str):
        # no params: Removed the match password
        # has params: Changed the match password
        channel.has_password = password == "Changed"
        await self.call_ext(
            MatchPasswordChanged,
            channel,
            has_password=channel.has_password,
        )

    # MP_ADDED_REF
    async def on_addref(self, channel: "MpChannel", ref: str):
        # Added _CHIMERA to the match referees
        channel.refs.add(ref)
        await self.call_ext(
            MatchRefereeAdded,
            channel,
            ref=ref,
        )

    # MP_REMOVED_REF
    async def on_removeref(self, channel: "MpChannel", ref: str):
        # Removed _CHIMERA from the match referees
        channel.refs.remove(ref)
        await self.call_ext(
            MatchRefereeRemoved,
            channel,
            ref=ref,
        )

    # async def update_refs(self, channel: "MpChannel", ):
    # Match referees:
    # xxxx
    # _CHIMERA
    # 這玩意有點麻煩 可能要用 event 暫時不使用

    # MP_KICKED
    async def on_kick(self, channel: "MpChannel", user: str):
        # Kicked _CHIMERA from the match
        await self.call_ext(
            PlayerKicked,
            channel,
            user=user,
        )

    # MP_TIMER_START
    async def on_timer(self, channel: "MpChannel", time: str):
        # Countdown ends in ?? minutes/seconds
        await self.call_ext(
            MatchTimerStarted,
            channel,
            time=int(time),
        )

    # MP_TIMER_ABORT
    async def on_aborttimer(self, channel: "MpChannel"):
        # Countdown aborted
        await self.call_ext(
            MatchTimerAborted,
            channel,
        )

    # MP_BANNED
    async def on_ban(self, channel: "MpChannel", user: str):
        # Banned _CHIMERA from the match
        await self.call_ext(
            PlayerBanned,
            channel,
            user=user,
        )

    # MP_CLOSE
    async def on_close(self, channel: "MpChannel"):
        # Closed the match
        await self.call_ext(
            MatchClosed,
            channel,
        )

    # MP_JOIN
    async def on_join(
        self, channel: "MpChannel", user: str, slot: str, team: Union[str, None]
    ):
        # _CHIMERA joined in slot 1.
        # _CHIMERA joined in slot 1 for team blue/red.
        channel.slots.set(int(slot), user, TeamType(team))
        await self.call_ext(
            PlayerJoined,
            channel,
            user=user,
            slot=int(slot),
            team=TeamType(team),
        )

    # MP_LEFT
    async def on_left(self, channel: "MpChannel", user: str):
        # _CHIMERA left the game.
        channel.slots.remove_from_username(user)
        await self.call_ext(
            PlayerLeft,
            channel,
            user=user,
        )

    # async def on_changing_map(self, channel: "MpChannel", ):
    # Host is changing map...

    # MP_ALL_READY
    async def on_ready(self, channel: "MpChannel"):
        # All players are ready
        await self.call_ext(
            AllPlayerReady,
            channel,
        )

    # MP_FINISED_PLAYING
    async def on_result(self, channel: "MpChannel", user: str, score: str, status: str):
        # _CHIMERA finished playing (Score: 86698, FAILED).
        passed = status == "PASSED"
        await self.call_ext(
            PlayerFinished,
            channel,
            user=user,
            score=int(score),
            passed=passed,
        )

    # MP_FINISED
    async def on_finished(self, channel: "MpChannel"):
        # The match has finished!
        channel.started = False
        await self.call_ext(
            MatchFinished,
            channel,
        )
