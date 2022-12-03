import aiohttp
import discord
import asyncio
import datetime

from discord.ext import commands

bot = discord.Bot()

with open("bsckey.txt") as f:
    bsckey = f.read().strip()

async def get_stats():
    async with aiohttp.ClientSession() as client:
        data = await(await client.get("https://api.coingecko.com/api/v3/coins/openleverage")).json()
        volume = 0
        csupply = 0
        price = data["tickers"][0]["last"] # Use pancakeswap for must up to date price
        for market in data["tickers"]:
            if market["market"]["name"] != "LBank": # Reports $900,000 trading volume despite not having OLE listed
                volume += market["converted_volume"]["usd"]
        data = await (await client.get(f"https://api.bscscan.com/api?module=stats&action=tokenCsupply&contractaddress=0xa865197a84e780957422237b5d152772654341f3&apikey={bsckey}")).json()
        csupply += int(data["result"]) * 1e-18
        csupply += int(7427908.926180246) # Approximate supply on KCC, still working on finding it through their API, also working on it from etherscan
        return str("$" + format(int(volume), ',d')), round(price, 4), int(csupply)


async def repeat(interval, func,*args, **kwargs): # Easy way of having stuff run at an interval
    while True:
        await asyncio.gather(
            func(*args, **kwargs),
            asyncio.sleep(interval)
        )

async def reminder():
    for channel in bot.get_all_channels():
        cname = channel.name.strip().lower()
        if "general" in cname or "trading" in cname or "price" in cname: # May be changed if needed
            await channel.send(f"Hello my fellow olers!\n\nRun /ole if you'd like to see the price of $OLE!", delete_after=6*3600) # 6 hours

async def presence():
    volume, price, _ = await get_stats()
    await bot.change_presence(activity=discord.Game(f"OLE: ${price} 24-Hour Volume: {volume}"), status=discord.Status.online)

@bot.event
async def on_ready():
    print(f"Successfully logged in as {bot.user}\nPlease wait until the bot has a presence to run any commands.")
    reminder_ = asyncio.ensure_future(repeat(3600*6, reminder))
    presence_ = asyncio.ensure_future(repeat(15, presence))
    await reminder_
    await presence_



cooldown = commands.Cooldown(per=30, rate=1)

@bot.slash_command(description="Retrieve the current price statistics of OpenLeverage's $OLE token.", cooldown=commands.CooldownMapping(cooldown, commands.BucketType.user))
async def ole(ctx):
    volume, price, csupply = await get_stats()
    timestamp = datetime.datetime.now()
    embed = discord.Embed(
        description="Current price and statistics of $OLE.", 
        type="rich", 
        title="$OLE Price Statistics", 
        color=0xad1457,
        fields=[
            discord.EmbedField("Price", "$" + str(price)), 
            discord.EmbedField("24-Hour Volume", str(volume)),
            discord.EmbedField("Circulating Supply", f"{csupply:,.0f} OLE"),
            discord.EmbedField("Market Cap", f"${price*csupply:,.2f}")
            ],
        timestamp=timestamp,
    )
    embed.set_footer(text="Made with \u2665 by isaaac", icon_url="https://cdn.discordapp.com/avatars/526880733705404436/1aeccfd1aae2e9fdd83a04da1c9556c5.webp?size=80")
    embed.set_thumbnail(url="https://openleverage.finance/token-icons/OLE_Token_Logo.png")
    await ctx.respond(embed=embed, delete_after=3600) # 1 hour

@ole.error
async def on_command_error(ctx: commands.Context, error: Exception):
    print(error)
    await ctx.respond(f"{ctx.author.mention}\nYou are running /OLE too quickly. \nPlease wait 30s before running /OLE again.", delete_after=5, ephemeral=True)


with open("token.txt") as t:
    token = t.read().strip()
bot.run(token)
