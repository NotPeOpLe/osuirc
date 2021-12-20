import re

QUIT = re.compile(r'^:(\S+)!cho@ppy\.sh QUIT :(.*)')
PING = re.compile(r'^PING (.*)')
ERRPASS = re.compile(r'^:cho\.ppy\.sh 464 .* :(.*)')
WELCOME = re.compile(r'^:cho\.ppy\.sh 001.*')
MOTD = re.compile(r'^:cho\.ppy\.sh (375|372|376) .+ :(.*)')
JOIN = re.compile(r'^:(.+)!cho@ppy.sh JOIN :(.+)')
PART = re.compile(r'^:(.+)!cho@ppy.sh PART :(.+)')
MODE = re.compile(r'^:(.+)!cho@cho.ppy.sh MODE (.+) ([+-][ov]) (.+)')
PRIVMSG = re.compile(r'^:(.+)!cho@ppy\.sh PRIVMSG (.+) :(.*)')
CHTOPIC = re.compile(r'^:cho\.ppy\.sh 332 .+ (.+) :(.*)')
CHCTIME = re.compile(r'^:cho\.ppy\.sh 333 .+ (.+) .+!.+@cho\.ppy\.sh (\d+)')
CHUSERS = re.compile(r'^:cho\.ppy\.sh 353 .+ = (.+) :(.*)')
CHENDNA = re.compile(r'^:cho\.ppy\.sh 366 .+ (.+) :End of /NAMES list')


MP_GAMEID = re.compile(r'multiplayer game #(\d+)')