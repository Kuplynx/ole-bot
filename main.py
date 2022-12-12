import aiohttp
import discord
import asyncio
import datetime

from discord.ext import commands

bot = discord.Bot()

with open("ethkey.txt") as f:
    ethkey = f.read().strip()

UP_ARROW   = "\u2191"
DOWN_ARROW = "\u2193"

async def get_stats():
    async with aiohttp.ClientSession() as client:
        data = await(await client.get("https://api.coingecko.com/api/v3/coins/openleverage")).json()
        volume = 0
        csupply = 1000000000
        price = data["market_data"]["current_price"]["usd"]
        daily_high = float(data["market_data"]["high_24h"]["usd"])
        daily_low  = float(data["market_data"]["low_24h"]["usd"])
        daily_change = float(data["market_data"]["price_change_percentage_24h"])
        daily_change_dollars = float(data["market_data"]["price_change_24h"])
        for market in data["tickers"]:
            if market["market"]["name"] != "LBank": # Reports $900,000 trading volume despite not having OLE listed
                volume += market["converted_volume"]["usd"]
        addr1 = await (await client.get(f"https://api.etherscan.io/api?module=account&action=tokenbalance&contractaddress=0x92CfbEC26C206C90aeE3b7C66A9AE673754FaB7e&address=0xE9547CF7E592F83C5141bB50648317e35D27D29B&tag=latest&apikey={ethkey}")).json()
        addr2 = await (await client.get(f"https://api.etherscan.io/api?module=account&action=tokenbalance&contractaddress=0x92CfbEC26C206C90aeE3b7C66A9AE673754FaB7e&address=0xa000e438f66fd1c4baa8a9c807c697b0765ef52e&tag=latest&apikey={ethkey}")).json()
        csupply -= (int(addr1["result"]) + int(addr2["result"])) * 1e-18
        return float(volume), float(price), int(csupply), daily_low, daily_high, daily_change, daily_change_dollars


async def repeat(interval, func, *args, **kwargs): # Easy way of having stuff run at an interval
    while True:
        await asyncio.gather(
            func(*args, **kwargs),
            asyncio.sleep(interval)
        )

async def reminder():
    for channel in bot.get_all_channels():
        cname = channel.name.strip().lower()
        if "general" in cname or "trading" in cname or "price" in cname: # May be changed if needed
            await channel.send(f"Hello my fellow OLErs!\nIf you'd like to see the price & statistics of $OLE, try running /ole!", delete_after=6*3600) # 6 hours

async def presence():
    _, price, _, _, _, change, _ = await get_stats()
    if change > 0:
        arrow = UP_ARROW
    else:
        arrow = DOWN_ARROW
    change = abs(change)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"OLE: ${price:.4f} {arrow}{change:.2f}%"), status=discord.Status.online)

@bot.event
async def on_ready():
    print(f"Successfully logged in as {bot.user}")
    reminder_ = asyncio.ensure_future(repeat(3600*6, reminder))
    presence_ = asyncio.ensure_future(repeat(600, presence))
    await presence_, reminder_



@bot.slash_command(description="Retrieve the current price statistics of OpenLeverage's $OLE token.", cooldown=commands.CooldownMapping(commands.Cooldown(per=30, rate=1), commands.BucketType.user))
async def ole(ctx: commands.Context):
    await ctx.interaction.response.defer() # Tell Discord we are still working on the response
    volume, price, csupply, low, high, change, changed = await get_stats()
    if change > 0:
        arrow = UP_ARROW
    else:
        arrow = DOWN_ARROW
    change = abs(change)
    changed = abs(changed)
    timestamp = datetime.datetime.now()
    embed = discord.Embed(
        description="Current price and statistics of $OLE.", 
        type="rich", 
        title="$OLE Price Statistics", 
        color=0xad1457,
        fields=[
            discord.EmbedField("Price", f"${price:.4f}", inline=True), 
            discord.EmbedField("24-Hour Volume", f"${volume:,.2f}", inline=True),
            discord.EmbedField("Circulating Supply", f"{csupply:,.0f} OLE", inline=True),
            discord.EmbedField("Market Cap", f"${price*csupply:,.2f}", inline=True),
            discord.EmbedField("24-Hour High", f"${high:.4f}", inline=True),
            discord.EmbedField("24-Hour Low", f"${low:.4f}", inline=True),
            discord.EmbedField("24-Hour Change ($)", f"{arrow}${changed:.8f}", inline=True),
            discord.EmbedField("24-Hour Change (%)", f"{arrow}{change:.2f}%", inline=True)
            ],
        timestamp=timestamp,
    )
    embed.set_footer(text="Made with \u2665 by isaaac", icon_url="https://raw.githubusercontent.com/Kuplynx/ole-bot/main/author.jpg")
    embed.set_thumbnail(url="https://openleverage.finance/token-icons/OLE_Token_Logo.png")
    await ctx.respond(embed=embed, delete_after=60*10) # 10 minutes

@ole.error
async def on_command_error(ctx: commands.Context, error: Exception):
    if isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
        await ctx.respond(f"{ctx.author.mention} You are running /OLE too quickly. \nPlease wait 30s before trying again.", delete_after=10, ephemeral=True)
    else:
        await ctx.respond("An unknown error occured. Please contact isaaac#1933.", ephemeral=True)



with open("token.txt") as t:
    token = t.read().strip()
bot.run(token)
