# osuirc

這是用 python 寫的 irc 客戶端專門給 osu 使用，我沒有完全的理解 async 到底是什麼，反正他能運行...

這還未完成，還有一些我不知道的訊息我不知道改如何處理，還有頻道的存在辨識等等...

## 安裝

```
pip install -U git+https://github.com/NotPeOpLe/osuirc.git
```

## 用法

用法非常簡單，就跟寫 Discord 機器人一樣:

```py
from osuirc import IrcClient
import random
import os

nickname = os.getenv('IRC_NICK')
password = os.getenv('IRC_PASS')

bot = IrcClient(nickname, password, prefix = '?')

# 指令觸發
@bot.command()
async def hello(ctx):
    await ctx.reply(f'Hello {ctx.author}')

# 帶參數的指令
@bot.command()
async def roll(ctx, num=100):
    point = random.randint(0, num)
    await ctx.reply(f'{ctx.author} roll {point} point(s).')

bot.run()
```

## 2022-09-25 更新

MultiplayerHandler 完全大改版，我給它搞得很簡化了，不過可能會需要文檔參考之類的(懶)

```py
import logging
import typing
from asyncio import Event
from rich.logging import RichHandler
from osuirc import IrcClient, Message
from osuirc.utils.events import *

if typing.TYPE_CHECKING:
    from osuirc import MpChannel


FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

NICK = "xxxx"
PASS = "xxxx"

bot = IrcClient(NICK, PASS)


@bot.command()
async def join_mp(ctx: Message, mpid: str):
    if not ctx.is_private:
        return

    if mpid.isdigit():
        await bot.join("#mp_" + mpid)
        await ctx.reply("我正在進入到 #mp_" + mpid)


@bot.command()
async def start(ctx: Message):
    if not ctx.channel.is_mutiplayer:
        return

    if ctx.channel.started:
        await ctx.reply("遊戲已經開始了!")
    else:
        await ctx.reply("!mp start 10")


@bot.mp_listen(AllPlayerReady)
async def auto_start(event: AllPlayerReady):
    """
    當觸發 AllPlayerReady 時檢查房間狀態確認所有玩家是否真的都準備及都有帶NoFail，否則不予開始遊戲
    auto_start -> 這裡會先發送 !mp settings ，暫時停止運行先放一邊
    on_player_count_changed -> 在 channel 初始化人數計數器 
    on_slot_updated -> 當計數器與channel.player_count相同，開始檢查所有玩家是否準備與帶NoFail，檢查完設置結果
    auto_start -> 判斷是否檢查成功，是則開始遊戲，否則不開始遊戲並提示。
    """
    event.channel.check_players = Event()  # Flag
    await event.channel.send("!mp settings")
    await event.channel.check_players.wait()  # 等待檢查完
    if event.channel.checked:
        await event.channel.send("!mp start 10")
    else:
        await event.channel.send("檢查失敗,請確認已準備及攜帶NoFail!")


@bot.mp_listen(MatchPlayerCountChanged)
async def on_player_count_changed(event: MatchPlayerCountChanged):
    event.channel.player_i = 0  # 設定起始


@bot.mp_listen(SlotUpdated)
async def on_slot_updated(event: SlotUpdated):
    event.channel.player_i += 1

    # 確認所有玩家資料都有更新
    if event.channel.player_i == event.channel.player_count:
        for player in event.channel.slots:
            if player.status != "Ready":
                event.channel.checked = False
                break
            if Mods.NoFail not in player.enabled_mods:
                event.channel.checked = False
                break
            event.channel.checked = True
        event.channel.check_players.set()


bot.run()
```
