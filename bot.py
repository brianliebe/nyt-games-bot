import os, sys, re, json, io
import statistics as stats
import discord
import pandas as pd

from discord.ext import commands
from datetime import date
from bokeh.io.export import get_screenshot_as_png
from bokeh.models import ColumnDataSource, DataTable, TableColumn
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from puzzle import Puzzle, PuzzleEntry, PuzzlePlayer

# turn off logging for webdriver manager
os.environ['WDM_LOG_LEVEL'] = '0'

# parse environment variables
token = os.getenv('DISCORD_TOKEN')
guild_id = os.getenv('GUILD_ID')

# build Discord client
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
 
bot = commands.Bot(command_prefix='?', intents=intents)
bot.guild_id = int(guild_id)
bot.puzzles = {}
bot.players = {}

if __name__ == '__main__':
    for extension in ['cogs.members']:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(f"Failed to load extension '{extension}'.", file=sys.stderr)
            print(e)

@bot.event
async def on_ready():
    db = {}
    if os.path.exists("db.json"):
        db = json.loads(open("db.json").read())
    for puzzle_num in sorted(db.keys()):
        puzzle = Puzzle(puzzle_num)
        for puzzle_entry in db[puzzle_num]:
            user_id = puzzle_entry['user_id']
            if user_id not in bot.players.keys():
                bot.players[user_id] = PuzzlePlayer(user_id)
            entry = PuzzleEntry(puzzle_num, \
                                user_id, \
                                puzzle_entry['score'], \
                                puzzle_entry['green'], \
                                puzzle_entry['yellow'], \
                                puzzle_entry['other'])
            puzzle.add(entry)
            bot.players[user_id].add(entry)
        bot.puzzles[puzzle_num] = puzzle
    print(f"Database loaded & successfully logged in.")

bot.run(token, bot=True, reconnect=True)