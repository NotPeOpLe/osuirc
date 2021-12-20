# osuirc

這是用python寫的irc客戶端專門給osu使用，我沒有完全的理解async到底是什麼，反正他能運行...

這還未完成，還有一些我不知道的訊息我不知道改如何處理，還有頻道的存在辨識等等...

## 安裝

```
pip install git+https://github.com/NotPeOpLe/osuirc.git
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