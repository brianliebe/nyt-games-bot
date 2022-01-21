import discord, re, io, json
import pandas as pd
import statistics as stats
from discord.ext import commands
from datetime import date, datetime, timezone, timedelta
from bokeh.io.export import get_screenshot_as_png
from bokeh.models import ColumnDataSource, DataTable, TableColumn
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from puzzle import Puzzle, PuzzleEntry, PuzzlePlayer

class MembersCog(commands.Cog, name="Normal Members Commands"):

    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.command(name='ranks', help='Shows guild-wide ranks based on past scores')
    async def get_ranks(self, ctx, *args):
        if len(args) == 0:
            valid_puzzles = self.get_puzzles(limit=7)
            explanation_str = "Last 7 Days"
        elif len(args) == 1 and args[0] in ['alltime', 'all-time']:
            valid_puzzles = self.get_puzzles(limit=None)
            explanation_str = "All-time"
        elif len(args) == 1 and args[0] == 'today':
            valid_puzzles = self.get_puzzles(limit=1)
            explanation_str = f"Puzzle #{valid_puzzles[0]}"
        elif len(args) == 1 and re.match(r'^\d+$', args[0]):
            valid_puzzles = [args[0].strip("# ")]
            explanation_str = f"Puzzle #{valid_puzzles[0]}"
        else:
            await ctx.reply("Couldn't understand your command. Try `?ranks`, `?ranks today`, `?ranks all-time`, or `?ranks <puzzle #>`.")
            return

        players = []
        for user_id in self.bot.players.keys():
            player = self.bot.players[user_id]
            intersection = list(set(player.get_puzzles()).intersection(valid_puzzles))
            if len(intersection) > 0:
                player.refresh_stats(puzzles=valid_puzzles)
                players.append(player)

        if len(players) == 0:
            await ctx.reply(f"Sorry, no users could be found for this query.")
            return

        players.sort(key = lambda p: (p.adj_mean, p.avg_other, p.avg_yellow, p.avg_green))

        if len(valid_puzzles) == 1:
            # stats for just 1 puzzle
            df = pd.DataFrame(columns=['Rank', 'User', 'Score', '🟩', '🟨', '⬜'])
            for i, player in enumerate(players):
                if i > 0 and player.get_avgs() == players[i - 1].get_avgs():
                    player.rank = players[i - 1].rank
                else:
                    player.rank = i + 1
                if i <= 10:
                    df.loc[i] = [   player.rank, 
                                    self.get_nickname(player.user_id),
                                    f"{player.raw_mean}/6",
                                    f"{player.avg_green}",
                                    f"{player.avg_yellow}",
                                    f"{player.avg_other}" ]
        else:
            # stats for 2+ puzzles
            df = pd.DataFrame(columns=['Rank', 'User', 'Average', '🟩', '🟨', '⬜', '🧩'])
            for i, player in enumerate(players):
                if i > 0 and player.get_avgs() == players[i - 1].get_avgs():
                    player.rank = players[i - 1].rank
                else:
                    player.rank = i + 1
                if i <= 10:
                    df.loc[i] = [   player.rank, 
                                    self.get_nickname(player.user_id),
                                    "{:.2f}/6 ({:.2f}/6)".format(player.adj_mean, player.raw_mean),
                                    "{:.2f}".format(player.avg_green),
                                    "{:.2f}".format(player.avg_yellow),
                                    "{:.2f}".format(player.avg_other),
                                    player.matching_puzzles_count ]

        ranks_img = self.get_table_image(df)

        if ranks_img is not None:
            with io.BytesIO() as image_binary:
                ranks_img.save(image_binary, 'PNG')
                image_binary.seek(0)
                await ctx.send(f"Leaderboard (🧩: {explanation_str})", \
                        file=discord.File(fp=image_binary, filename='image.png'))
        else:
            await ctx.reply("Sorry, there was an issue fetching ranks. Please try again later.")

    def trim_image(self, image):
        if image is None: return None
        rgb_image = image.convert('RGB')
        width, height = image.size
        for y in reversed(range(height)):
            for x in range(width):
                rgb = rgb_image.getpixel((x,y))
                if rgb != (255, 255, 255):
                    return rgb_image.crop([5, 5, width, y + 5])
        return None

    def get_table_image(self, df):
        source = ColumnDataSource(df)

        df_columns = df.columns.values
        columns_for_table=[]
        for column in df_columns:
            columns_for_table.append(TableColumn(field=column, title=column))

        data_table = DataTable(source=source, columns=columns_for_table, index_position=None, autosize_mode='fit_viewport')

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--window-size=1024,768")
        chrome_options.add_argument('--no-proxy-server')
        chrome_options.add_argument("--proxy-server='direct://'")
        chrome_options.add_argument("--proxy-bypass-list=*")

        service = webdriver.chrome.service.Service(ChromeDriverManager().install())
        generated = get_screenshot_as_png(data_table, driver=webdriver.Chrome(service=service, options=chrome_options))

        generated = self.trim_image(generated)
        return generated

    def get_puzzles(self, limit: int = None) -> str:
        if limit is None:
            return sorted(self.bot.puzzles.keys())
        else:
            todays_puzzle = int(self.get_todays_puzzle())
            puzzles = [str(p) for p in range(todays_puzzle - limit + 1, todays_puzzle + 1)]
            return puzzles

    def get_todays_puzzle(self) -> str:
        arbitrary_date = date(2022, 1, 10)
        arbitrary_date_puzzle = 205
        todays_date = datetime.now(timezone(timedelta(hours=-5), 'EST')).date()
        return str(arbitrary_date_puzzle + (todays_date - arbitrary_date).days)

    def get_nickname(self, user_id) -> str:
        guild = self.bot.get_guild(self.bot.guild_id)
        for member in guild.members:
            if member.id == user_id:
                return member.display_name
        return "?"

    @commands.guild_only()
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == self.bot.user.id: return
        
        if '\n' in message.content:
            title = message.content[0:message.content.index('\n')].strip()
            content = message.content[message.content.index('\n') + 1:].strip()
            if self.is_wordle_submission(title):
                success = await self.__add_score(int(message.author.id), title, content, message.channel)
                if success:
                    await message.add_reaction('✅')
                else:
                    await message.add_reaction('❌')

    @commands.guild_only()
    @commands.command(name='missing', help='Shows all players missing an entry for a puzzle')
    async def get_missing(self, ctx, *args):
        if len(args) == 0:
            puzzle_num = self.get_todays_puzzle()
        elif len(args) == 1 and re.match(r"^\d+$", args[0]):
            puzzle_num = args[0].strip("# ")
        else:
            await ctx.reply("Couldn't understand command. Try `?missing` or `?missing <puzzle #>`")
            return
        missing_ids = [str(player.user_id) for player in self.bot.players.values() if puzzle_num not in player.get_puzzles()]
        if len(missing_ids) == 0:
            await ctx.reply(f"All known players have submitted Puzzle #{puzzle_num}!")
        else:
            await ctx.reply("The following players are missing Puzzle #{}: <@{}>".format(puzzle_num, '>, <@'.join(missing_ids)))

    @commands.guild_only()
    @commands.command(name='entries', help='Shows all recorded entries for a player')
    async def get_entries(self, ctx, *args):
        if len(args) == 0:
            query_id = ctx.author.id
        elif len(args) == 1 and self.is_user(args[0]):
            query_id = int(args[0].strip("<@!> "))
        else:
            await ctx.reply("Couldn't understand command. Try `?entries` or `?entries <user>`.")
            return

        if query_id in self.bot.players.keys():
            player = self.bot.players[query_id]
            df = pd.DataFrame(columns=['Puzzle', 'Score', '🟩', '🟨', '⬜'])
            for i, puzzle_num in enumerate(sorted(player.get_puzzles())):
                entry = player.get_entry(puzzle_num)
                df.loc[i] = [f"#{puzzle_num}", f"{entry.score}/6", entry.green, entry.yellow, entry.other]
            entries_img = self.get_table_image(df)
            if entries_img is not None:
                with io.BytesIO() as image_binary:
                    entries_img.save(image_binary, 'PNG')
                    image_binary.seek(0)
                    player.refresh_stats(self.get_puzzles(limit=None))
                    await ctx.reply("{} games found:", \
                        file=discord.File(fp=image_binary, filename='image.png'))
            else:
                await ctx.reply("Sorry, there was an issue fetching entries. Please try again later.")
        else:
            await ctx.reply(f"Couldn't find any recorded entries for <@{query_id}>.")

    @commands.guild_only()
    @commands.command(name="stats", help="Shows basic stats for a player")
    async def get_stats(self, ctx, *args):
        if len(args) == 0:
            query_id = ctx.author.id
        elif len(args) == 1 and self.is_user(args[0]):
            query_id = int(args[0].strip("<@!> "))
        else:
            await ctx.reply("Couldn't understand command. Try `?stats` or `?stats <user>`.")

        if query_id in self.bot.players.keys():
            player = self.bot.players[query_id]
            df = pd.DataFrame(columns=['User', 'Puzzles', 'Missed', 'Avg Score', 'Avg 🟩', 'Avg 🟨', 'Avg ⬜'])
            df.loc[0] = [
                self.get_nickname(query_id),
                len(player.get_puzzles()),
                len(self.bot.puzzles.keys()) - len(player.get_puzzles()),
                "{:.4f}".format(stats.mean([e.score for e in player.entries.values()])),
                "{:.4f}".format(stats.mean([e.green for e in player.entries.values()])),
                "{:.4f}".format(stats.mean([e.yellow for e in player.entries.values()])),
                "{:.4f}".format(stats.mean([e.other for e in player.entries.values()])),
            ]
            stats_img = self.get_table_image(df)
            if stats_img is not None:
                with io.BytesIO() as image_binary:
                    stats_img.save(image_binary, 'PNG')
                    image_binary.seek(0)
                    player.refresh_stats(self.get_puzzles(limit=None))
                    await ctx.reply(file=discord.File(fp=image_binary, filename='image.png'))
        else:
            await ctx.reply(f"Couldn't find any recorded entries for <@{query_id}>.")

    @commands.guild_only()
    @commands.command(name='add', help='Manually adds a puzzle entry for a player')
    async def add_score(self, ctx, *args):
        if args is not None and len(args) >= 4:
            if self.is_user(args[0]):
                user_id = int(args[0].strip("<>@! "))
                title = ' '.join(args[1:4])
                content = '\n'.join(args[4:])
            else:
                user_id = int(ctx.author.id)
                title = ' '.join(args[0:3])
                content = '\n'.join(args[3:])
            if self.is_wordle_submission(title):
                success = await self.__add_score(user_id, title, content, ctx)
                if success:
                    await ctx.message.add_reaction('✅')
        else:
            await ctx.reply("To manually add a Wordle score, please use `?add <user> <Wordle output>` (specifying a user is optional).")


    @commands.guild_only()
    async def __add_score(self, user_id, title, puzzle, channel) -> bool:
        if 'X/6' in title:
            puzzle_num, _ = re.findall(r'\d+', title)
            score = 7
        else:
            puzzle_num, score, _ = re.findall(r'\d+', title)
            score = int(score)

        entry = PuzzleEntry(puzzle_num, user_id, score, 
                puzzle.count('🟩'),
                puzzle.count('🟨'),
                puzzle.count('⬜') + puzzle.count('⬛'))

        if puzzle_num not in self.bot.puzzles.keys():
            self.bot.puzzles[puzzle_num] = Puzzle(puzzle_num)
        self.bot.puzzles[puzzle_num].add(entry)

        if user_id not in self.bot.players.keys():
            self.bot.players[user_id] = PuzzlePlayer(user_id)
        self.bot.players[user_id].add(entry)

        return self.save()

    def is_user(self, word) -> bool:
        return re.match(r'^<@[!]?\d+>', word)

    def is_wordle_submission(self, title) -> str:
        return re.match(r'^Wordle \d{3} \d{1}/\d{1}$', title) or re.match(r'^Wordle \d{3} X/\d{1}$', title)

    @commands.guild_only()
    @commands.command(name='save', help='Saves all data to the database (done automatically)')
    async def manual_save(self, ctx, *args):
        if self.save():
            await ctx.message.add_reaction('✅')
        else:
            await ctx.reply("Failed to save the database!")

    def save(self) -> bool:
        db = open('db.json', 'w')
        full_dict = {}
        for puzzle_num in sorted(self.bot.puzzles.keys()):
            puzzle = self.bot.puzzles[puzzle_num]
            db_entries = []
            for user_id in puzzle.entries.keys():
                entry = puzzle.entries[user_id]
                db_entries.append({'user_id' : entry.user_id, 'score' : entry.score, 'green' : entry.green, \
                        'yellow' : entry.yellow, 'other' : entry.other})
            full_dict[puzzle_num] = db_entries
        db.write(json.dumps(full_dict, indent=4, sort_keys=True))
        db.close()
        return True

def setup(bot):
    bot.add_cog(MembersCog(bot))