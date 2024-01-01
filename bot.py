import os, discord, asyncio
from discord.ext import commands
from utils.database_handler import DatabaseHandler
from utils.bot_utilities import BotUtilities
from utils.help_handler import HelpMenuHandler

# turn off logging for webdriver manager
os.environ['WDM_LOG_LEVEL'] = '0'

# parse environment variables
token = os.getenv('DISCORD_TOKEN')
discord_env = os.getenv('DISCORD_ENV')
guild_id = os.getenv('GUILD_ID')

# build Discord client
intents = discord.Intents.all()
intents.members = True
client = discord.Client(intents=intents)
activity = discord.Game(name="BOT IS DOWN!") if discord_env == 'DEV' else discord.Game(name="?help")

# set up the bot
bot = commands.Bot(command_prefix='?', intents=intents, activity=activity, help_command=None)
bot.guild_id = int(guild_id) if guild_id.isnumeric() else -1
bot.utils = BotUtilities(client, bot)
bot.db = DatabaseHandler(bot.utils)
bot.help_menu = HelpMenuHandler()

# load the cogs
#if __name__ == '__main__':
async def main():
    async with bot:
        for extension in ['cogs.members', 'cogs.owner']:
            try:
                await bot.load_extension(extension)
            except Exception as e:
                print(f"Failed to load extension '{extension}'.\n{e}")
        await bot.start(token, reconnect=True)

# load the database when ready
@bot.event
async def on_ready():
    try:
        bot.db.connect()
        print("Database loaded & successfully logged in.")
    except Exception as e:
        print(f"Failed to load database: {e}")

# run the bot
asyncio.run(main())
