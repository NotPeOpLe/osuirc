import re

QUIT = re.compile(r"^:(\S+)!cho@ppy\.sh QUIT :(.*)")
PING = re.compile(r"^PING (.*)")
ERRPASS = re.compile(r"^:cho\.ppy\.sh 464 .* :(.*)")
WELCOME = re.compile(r"^:cho\.ppy\.sh 001.*")
MOTD = re.compile(r"^:cho\.ppy\.sh (375|372|376) .+ :(.*)")
JOIN = re.compile(r"^:(.+)!cho@ppy.sh JOIN :(.+)")
PART = re.compile(r"^:(.+)!cho@ppy.sh PART :(.+)")
MODE = re.compile(r"^:(.+)!cho@cho.ppy.sh MODE (.+) ([+-][ov]) (.+)")
PRIVMSG = re.compile(r"^:(.+)!cho@ppy\.sh PRIVMSG (.+) :(.*)")
CHTOPIC = re.compile(r"^:cho\.ppy\.sh 332 .+ (.+) :(.*)")
CHCTIME = re.compile(r"^:cho\.ppy\.sh 333 .+ (.+) .+!.+@cho\.ppy\.sh (\d+)")
CHUSERS = re.compile(r"^:cho\.ppy\.sh 353 .+ = (.+) :(.*)")
CHENDNA = re.compile(r"^:cho\.ppy\.sh 366 .+ (.+) :End of /NAMES list")
WHOISUSER = re.compile(
    r"^:cho\.ppy\.sh 311 .+ (.+) https://osu\.ppy\.sh/u/(\d+) \* :.*"
)
WHOISSERVER = re.compile(r"^:cho\.ppy\.sh 312 .+ (.+) (.+) :(.+)")
ENDOFWHOIS = re.compile(r"^:cho\.ppy\.sh 318 .+ (.+) :End of /WHOIS list")
WHOISCHANNELS = re.compile(r"^:cho\.ppy\.sh 319 .+ (.+) :(.*)")


MP_GAMEID = re.compile(r"multiplayer game #(\d+)")
MP_LOCKED = re.compile(r"Locked the match")
MP_UNLOCK = re.compile(r"Unlocked the match")
MP_CHANGED_SIZE = re.compile(r"Changed match to size (?P<size>\d{1,2})")
MP_CHANGED_SET = re.compile(r"Changed match settings to (?P<settings>.*)")
MP_PLAYER_MOVED = re.compile(r"(?P<username>.*) moved to slot (?P<new_slot>\d{1,2})")
MP_CHANGED_HOST = re.compile(r"(?P<host>.*) became the host.")
MP_CLEARHOST = re.compile(r"Cleared match host")
MP_CHANGED_NAME = re.compile(r"Room name updated to \"(?P<room_name>.*)\"")
MP_UPDATE_NAME = re.compile(r"Room name: (?P<room_name>.*),.*")
MP_UPDATE_MAP = re.compile(
    r"Beatmap: https://osu.ppy.sh/b/(?P<map_id>\d+) (?P<map_repl>.*)"
)
MP_CHANGED_MAP = re.compile(
    r"Beatmap changed to: (?P<map_repl>.*) \(https://osu.ppy.sh/b/(?P<map_id>\d+)\)"
)
MP_CHANGED_MAP2 = re.compile(
    r"Changed beatmap to https://osu.ppy.sh/b/(?P<map_id>\d+) (?P<map_repl>.*)"
)
MP_UPDATE_SET = re.compile(
    r"Team mode: (?P<team_mode>\S+), Win condition: (?P<score_mode>\S+)"
)
MP_UPDATE_PC = re.compile(r"Players: (?P<player_count>\d+)")
MP_SLOT_INFO = re.compile(
    r"Slot (?P<slot>\d{1,2})  (?P<status>Ready|Not Ready|No Map)\s*https://osu\.ppy\.sh/u/(?P<user_id>\d+) (?P<user_name>\S*)(?P<flags>.*)"
)
MP_STARTED = re.compile(r"The match has started!")
MP_ABORTED = re.compile(r"Aborted the match")
MP_CHANGED_TEAM = re.compile(r"(?P<user>) changed to (?P<team>Red|Blue)")
MP_CHANGED_MODE = re.compile(
    r"Changed match mode to (?P<game_mode>OsuMania|Osu|Taiko|CatchTheBeat)"
)
MP_CHANGED_MODS = re.compile(
    r"(Disabled all mods|Enabled (?P<enabled_mods>.*)), (?P<freemod>dis|en)abled FreeMod"
)
MP_CHANGED_PASSWD = re.compile(r"(?P<password>Removed|Changed) the match password")
MP_ADDED_REF = re.compile(r"Added (?P<ref>.*) to the match referees")
MP_REMOVED_REF = re.compile(r"Removed (?P<ref>.*) from the match referees")
MP_KICKED = re.compile(r"Kicked (?P<user>.*) from the match")
MP_TIMER_START = re.compile(r"Countdown ends in (\d+) (minutes|seconds)")
MP_TIMER_ABORT = re.compile(r"Countdown aborted")
MP_BANNED = re.compile(r"Banned (?P<user>.*) from the match")
MP_CLOSE = re.compile(r"Closed the match")
MP_JOIN = re.compile(
    r"(?P<user>.*) joined in slot (?P<slot>\d+)( for team (?P<team>blue|red))\."
)
MP_LEFT = re.compile(r"(?P<user>.*) left the game.")
MP_ALL_READY = re.compile(r"All players are ready")
MP_FINISED_PLAYING = re.compile(
    r"(?P<user>.*) finished playing \(Score: (?P<score>\d+), (?P<status>FAILED|PASSED)\)\."
)
MP_FINISED = re.compile(r"The match has finished!")
