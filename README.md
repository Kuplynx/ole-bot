# OpenLeverage $OLE Bot

### Getting Started
1. Get a BSCScan API key under Account -> API Keys
2. Save it in a file called bsckey.txt (Please note this may be changed to etherscan in the future)
3. Get your discord bot token and save it in a file called token.txt
4. Add the bot to your server using the oauth url generator with the permission of slash commands
5. Make you sure have python and poetry installed, then run `poetry install`
5. Run the bot to queue the slash command registration (It takes a while) with `poetry run python main.py`
6. Test it out with /ole once it has registered

### Missing Features
 - I am still working on determining the total supply on ethereum, but it makes it hard since all OLE is technically in circulation there. If I could get the addresses for OPL that hold a lot of the token that isn't in circulation, that would be amazing

TODO
 - Get Approximate Circulating Supply on ETH (Will be done soon)
