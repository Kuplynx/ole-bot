import aiohttp
import discord
import asyncio
import datetime

from discord.ext import commands

bot = discord.Bot()


async def get_stats():
    async with aiohttp.ClientSession() as client:
        data = await(await client.get("https://api.coingecko.com/api/v3/coins/openleverage")).json()
        volume = 0
        price = data["tickers"][0]["last"] # Use pancakeswap for must up to date price
        for market in data["tickers"]:
            if market["market"]["name"] != "LBank": # Reports $900,000 trading volume despite not having OLE listed
                volume += market["converted_volume"]["usd"]
        return str("$" + format(int(volume), ',d')), "$" + str(round(price, 4))

@bot.event
async def on_ready():
    print(f"Successfully logged in as {bot.user}")
    for channel in bot.get_all_channels():
        cname = channel.name.strip().lower()
        if "general" in cname or "trading" in cname or "price" in cname: # May be changed if needed
            await channel.send(f"Hello my fellow olers!\n\nRun /ole if you'd like to see the current price of it!", delete_after=6*3600) # 6 hours
    while True:
        await asyncio.sleep(15)
        volume, price = await get_stats()
        await bot.change_presence(activity=discord.CustomActivity(f"OLE: ${price} 24-Hour Volume: {volume}"))

cooldown = commands.Cooldown(per=30, rate=1)

@bot.slash_command(description="Retrieve the current price statistics of OpenLeverage's $OLE token.", cooldown=commands.CooldownMapping(cooldown, commands.BucketType.user))
async def ole(ctx):
    volume, price = await get_stats()
    timestamp = datetime.datetime.now()
    embed = discord.Embed(
        description="Current price and statistics of $OLE.", 
        type="rich", 
        title="$OLE Price Statistics", 
        color=0xad1457,
        fields=[discord.EmbedField("Price", str(price)), 
        discord.EmbedField("24-Hour Volume", str(volume))],
        timestamp=timestamp,
    )
    embed.set_footer(text="Made with \u2665 by isaaac", icon_url="https://cdn.discordapp.com/avatars/526880733705404436/1aeccfd1aae2e9fdd83a04da1c9556c5.webp?size=80")
    embed.set_thumbnail(url="https://openleverage.finance/token-icons/OLE_Token_Logo.png")
    await ctx.respond(embed=embed, delete_after=3600) # 1 hour

@ole.error
async def on_command_error(ctx: commands.Context, error: Exception):
    await ctx.send(f"{ctx.author.mention}\nYou are running /OLE too quickly. \nPlease wait 30s before running /OLE again.", delete_after=5)


with open("token.txt") as t:
    token = t.read().strip()
bot.run(token)
