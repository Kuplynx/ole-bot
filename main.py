import aiohttp
import discord
import asyncio
import datetime

from discord.ext import commands

bot = discord.Bot()

with open("bsckey.txt") as f:
    bsckey = f.read().strip()

UP_ARROW   = "\u2191"
DOWN_ARROW = "\u2193"

async def get_stats():
    async with aiohttp.ClientSession() as client:
        data = await(await client.get("https://api.coingecko.com/api/v3/coins/openleverage")).json()
        volume = 0
        csupply = 0
        price = data["market_data"]["current_price"]["usd"]
        daily_high = data["market_data"]["high_24h"]["usd"]
        daily_low  = data["market_data"]["low_24h"]["usd"]
        daily_change = data["market_data"]["price_change_percentage_24h"]
        daily_change_dollars = data["market_data"]["price_change_24h"]
        for market in data["tickers"]:
            if market["market"]["name"] != "LBank": # Reports $900,000 trading volume despite not having OLE listed
                volume += market["converted_volume"]["usd"]
        data = await (await client.get(f"https://api.bscscan.com/api?module=stats&action=tokenCsupply&contractaddress=0xa865197a84e780957422237b5d152772654341f3&apikey={bsckey}")).json()
        csupply += int(data["result"]) * 1e-18
        csupply += int(7427908.926180246) # Approximate supply on KCC, still working on finding it through their API, etherscan has no data
        return float(volume), float(price), int(csupply), float(daily_low), float(daily_high), float(daily_change), float(daily_change_dollars)


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
            await channel.send(f"Hello my fellow olers!\n\nRun /ole if you'd like to see the price of $OLE!", delete_after=6*3600) # 6 hours

async def presence():
    volume, price, _, _, _, change, _ = await get_stats()
    if change > 0:
        arrow = UP_ARROW
    else:
        arrow = DOWN_ARROW
    await bot.change_presence(activity=discord.Game(f"OLE: ${price:.4f} {arrow}{change:.2f}%"), status=discord.Status.online)

@bot.event
async def on_ready():
    print(f"Successfully logged in as {bot.user}")
    reminder_ = asyncio.ensure_future(repeat(3600*6, reminder))
    presence_ = asyncio.ensure_future(repeat(15, presence))
    await reminder_
    await presence_



cooldown = commands.Cooldown(per=30, rate=1)

@bot.slash_command(description="Retrieve the current price statistics of OpenLeverage's $OLE token.", cooldown=commands.CooldownMapping(cooldown, commands.BucketType.user))
async def ole(ctx: commands.Context):
    await ctx.interaction.response.defer() # Tell Discord we are still working on the response
    volume, price, csupply, low, high, change, changed = await get_stats()
    if change > 0:
        arrow = UP_ARROW
    else:
        arrow = DOWN_ARROW
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
    embed.set_footer(text="Made with \u2665 by isaaac", icon_url="https://cdn.discordapp.com/avatars/526880733705404436/1aeccfd1aae2e9fdd83a04da1c9556c5.webp?size=80")
    embed.set_thumbnail(url="https://openleverage.finance/token-icons/OLE_Token_Logo.png")
    await ctx.respond(embed=embed, delete_after=60*10) # 10 minutes

@ole.error
async def on_command_error(ctx: commands.Context, error: Exception):
    print(error)
    if isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
        await ctx.respond(f"{ctx.author.mention}\nYou are running /OLE too quickly. \nPlease wait 30s before running /OLE again.", delete_after=10, ephemeral=True)
    else:
        await ctx.respond("An unknown error occured. Please contact isaaac#1933.", ephemeral=True)



with open("token.txt") as t:
    token = t.read().strip()
bot.run(token)
