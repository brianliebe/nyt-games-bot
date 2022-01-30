import os, discord
from discord.ext import commands
from utils.database_handler import DatabaseHandler
from utils.player_handler import PlayerHandler
from utils.puzzle_handler import PuzzleHandler
from utils.bot_utilities import BotUtilities

# turn off logging for webdriver manager
os.environ['WDM_LOG_LEVEL'] = '0'

# parse environment variables
token = os.getenv('DISCORD_TOKEN')
discord_env = os.getenv('DISCORD_ENV')
guild_id = os.getenv('GUILD_ID')

# build Discord client
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
activity = discord.Game(name="BOT IS DOWN!") if discord_env == 'DEV' else discord.Game(name="?help")

# set up the bot
bot = commands.Bot(command_prefix='?', intents=intents, activity=activity, help_command=None)
bot.guild_id = int(guild_id)
bot.utils = BotUtilities(client, bot)
bot.puzzles = PuzzleHandler(bot.utils)
bot.players = PlayerHandler(bot.utils)
bot.db = DatabaseHandler(bot.puzzles, bot.players, bot.utils)

# load the cogs
if __name__ == '__main__':
    for extension in ['cogs.members', 'cogs.owner']:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(f"Failed to load extension '{extension}'.\n{e}")

# load the database when ready
@bot.event
async def on_ready():
    try:
        bot.db.load()
        print("Database loaded & successfully logged in.")
    except Exception as e:
        print(f"Failed to load database: {e}")

# run the bot
bot.run(token, bot=True, reconnect=True)