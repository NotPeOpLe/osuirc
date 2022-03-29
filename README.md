# osuirc

這是用python寫的irc客戶端專門給osu使用，我沒有完全的理解async到底是什麼，反正他能運行...

這還未完成，還有一些我不知道的訊息我不知道改如何處理，還有頻道的存在辨識等等...

## 安裝

```
pip install -U git+https://github.com/NotPeOpLe/osuirc.git
```

## 用法

用法非常簡單，就跟寫Discord機器人一樣:

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

# 訊息觸發
@bot.message('727')
async def say_WYSI(ctx):
    await ctx.reply('WHEN YOU SEE IT')

# 也可以使用 regex
@bot.message(r'跟著我說(.*)')
async def say_what(ctx, msg):
    await ctx.reply(msg)

bot.run()
```

## 2022-03-30 更新

新增 MultiplayerHandler，此程式專門處理MP房的事件及管理房間的狀態

```py
import logging
from asyncio import Event
from typing import Union
from osuirc import IrcClient, Message, MpChannel, Channel, Mods
from osuirc.handler import MultiplayerHandler
from rich.logging import RichHandler


logging.basicConfig(
    level="NOTSET", format="%(message)s", datefmt="[%X]", handlers=[RichHandler(rich_tracebacks=True)]
)

class CutsomMultiplayerHandler(MultiplayerHandler):
    async def update_player_count(self, channel: "MpChannel", player_count: str):
        channel.player_i = 0 # 設定起始
        await super().update_player_count(channel, player_count)

    async def update_palyer(self, channel: "MpChannel", slot: str, status: str, user_id: str, user_name: str, flags: str):
        channel.player_i += 1
        await super().update_palyer(channel, slot, status, user_id, user_name, flags)
        if channel.player_i == channel.player_count:
            for p in channel.slots:
                if channel.slots[p].status != "Ready": # 檢查狀態是否為 Ready
                    channel.checked = False
                    break
                if Mods.NoFail not in channel.slots[p].enabled_mods: # 檢查玩家Mods是否有 NoFail
                    channel.checked = False
                    break
                channel.checked = True
            channel.check_players.set() # flag set

    async def on_ready(self, channel: "MpChannel"):
        # 所有人準備時進行檢查
        channel.check_players = Event() # flag
        await channel.send("!mp settings") 
        await channel.check_players.wait() # 等待檢查完
        if channel.checked:
            await channel.send("!mp start 10")
        else:
            await channel.send("檢查失敗,請確認已準備及攜帶NoFail!")

class Bot(IrcClient):
    joined = Event()
    joined_channel = None

    async def on_ready(self):
        await self.send("BanchoBot", "!mp make test")
        await self.joined.wait()
        await self.send(self.joined_channel, "!mp settings")

    async def on_join(self, user: str, channel: Union["Channel", "MpChannel"]):
        if user.lower() == self.nickname.lower():
            self.joined_channel = channel
            self.joined.set()

bot = Bot(nickname="xxxxxxxx", password="xxxxxx")
bot.mphandler = CutsomMultiplayerHandler(bot)


@bot.command()
async def ping(ctx: Message):
    await ctx.reply("pong")


if __name__ == "__main__":
    bot.run()
```