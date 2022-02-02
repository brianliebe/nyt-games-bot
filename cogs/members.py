import discord, re, io, os
import pandas as pd
import statistics as stats
import matplotlib.pyplot as plt
import seaborn as sns
from enum import Enum, auto
from discord.ext import commands
from datetime import timedelta
from utils.bot_utilities import BotUtilities
from utils.database_handler import DatabaseHandler
from utils.help_handler import HelpMenuHandler
from utils.puzzle import PuzzleEntry, PuzzlePlayer
from utils.puzzle_handler import PuzzleHandler
from utils.player_handler import PlayerHandler
from matplotlib.font_manager import FontProperties

class PuzzleQueryType(Enum):
    SINGLE_PUZZLE = auto()
    MULTI_PUZZLE = auto()
    ALL_TIME = auto()

class MembersCog(commands.Cog, name="Normal Members Commands"):

    MAX_DATAFRAME_ROWS = 10

    def __init__(self, bot):
        self.bot = bot
        self.puzzles: PuzzleHandler = self.bot.puzzles
        self.players: PlayerHandler = self.bot.players
        self.utils: BotUtilities = self.bot.utils
        self.db: DatabaseHandler = self.bot.db
        self.help_menu: HelpMenuHandler = self.bot.help_menu
        self.build_help_menu()

    @commands.guild_only()
    @commands.command(name='ranks')
    async def get_ranks(self, ctx, *args):
        if len(args) == 0 or (len(args) == 1 and args[0] in ['week', 'weekly']):
            # WEEKLY
            start_of_week = self.utils.get_week_start(self.utils.get_todays_date())
            todays_puzzle_id = self.puzzles.get_puzzle_by_date(self.utils.get_todays_date())
            valid_puzzles = [p_id for p_id in self.puzzles.get_puzzles_by_week(start_of_week) if p_id <= todays_puzzle_id]
            explanation_str = "This Week (so far)"
            query_type = PuzzleQueryType.MULTI_PUZZLE
        elif len(args) == 1 and args[0] in ['10day', '10-day']:
            # 10-DAY AVERAGE
            seven_days_ago_puzzle = self.puzzles.get_puzzle_by_date(self.utils.get_todays_date() - timedelta(days=10))
            valid_puzzles = list(range(seven_days_ago_puzzle, seven_days_ago_puzzle + 10))
            explanation_str = "Last 10 Days"
            query_type = PuzzleQueryType.MULTI_PUZZLE
        elif len(args) == 1 and args[0] in ['alltime', 'all-time']:
            # ALL TIME
            valid_puzzles = self.puzzles.get_all_puzzles()
            explanation_str = "All-time"
            query_type = PuzzleQueryType.ALL_TIME
        elif len(args) == 1 and args[0] == 'today':
            # TODAY ONLY
            valid_puzzles = [self.puzzles.get_puzzle_by_date(self.utils.get_todays_date())]
            explanation_str = f"Puzzle #{valid_puzzles[0]}"
            query_type = PuzzleQueryType.SINGLE_PUZZLE
        elif len(args) == 1 and re.match(r'^[#]?\d+$', args[0]):
            # SPECIFIC PUZZLE ONLY
            valid_puzzles = [int(args[0].strip("# "))]
            explanation_str = f"Puzzle #{valid_puzzles[0]}"
            query_type = PuzzleQueryType.SINGLE_PUZZLE
        elif len(args) == 1 and self.utils.is_date(args[0]):
            # WEEKLY (BY SPECIFIC DATE)
            query_date = self.utils.get_date_from_str(args[0])
            todays_puzzle_id = self.puzzles.get_puzzle_by_date(self.utils.get_todays_date())
            if self.utils.is_sunday(query_date):
                valid_puzzles = [p_id for p_id in self.puzzles.get_puzzles_by_week(query_date) if p_id <= todays_puzzle_id]
                explanation_str = f"Week of {self.utils.convert_date_to_str(query_date)}"
                query_type = PuzzleQueryType.MULTI_PUZZLE
            else:
                await ctx.reply("Query date is not a Sunday. Try `?help ranks`.")
                return
        else:
            await ctx.reply("Couldn't understand your command. Try `?help ranks`.")
            return

        players: list[PuzzlePlayer] = []
        for user_id in self.players.get_ids():
            player = self.players.get(user_id)
            intersection = list(set(player.get_ids()).intersection(valid_puzzles))
            if len(intersection) > 0:
                player.generate_stats(puzzles=valid_puzzles)
                players.append(player)

        if len(players) == 0:
            await ctx.reply(f"Sorry, no users could be found for this query.")
            return

        if query_type != PuzzleQueryType.ALL_TIME:
            # for all queries except 'All-time', we rank based on the adjusted mean
            players.sort(key = lambda p: (p.stats['adj_mean'], p.stats['avg_other'], p.stats['avg_yellow'], p.stats['avg_green']))
        else:
            # for all-time queries, we must rank on the raw score (since adj. will be skewed)
            players.sort(key = lambda p: (p.stats['raw_mean'], p.stats['avg_other'], p.stats['avg_yellow'], p.stats['avg_green']))

        if query_type == PuzzleQueryType.SINGLE_PUZZLE:
            # stats for just 1 puzzle
            df = pd.DataFrame(columns=['Rank', 'User', 'Score', '🟩', '🟨', '⬜'])
            for i, player in enumerate(players):
                if i > 0 and player.get_avgs() == players[i - 1].get_avgs():
                    player.rank = players[i - 1].rank
                else:
                    player.rank = i + 1
                if i <= self.MAX_DATAFRAME_ROWS:
                    df.loc[i] = [   
                                    player.rank, 
                                    self.utils.get_nickname(player.user_id),
                                    f"{player.stats['raw_mean']}/6",
                                    f"{player.stats['avg_green']}",
                                    f"{player.stats['avg_yellow']}",
                                    f"{player.stats['avg_other']}"
                                ]
        elif query_type == PuzzleQueryType.MULTI_PUZZLE:
            # stats for 2+ puzzles, but not all-time
            df = pd.DataFrame(columns=['Rank', 'User', 'Average', '🟩', '🟨', '⬜', '🧩', '🚫'])
            for i, player in enumerate(players):
                if i > 0 and player.get_avgs() == players[i - 1].get_avgs():
                    player.rank = players[i - 1].rank
                else:
                    player.rank = i + 1
                if i <= self.MAX_DATAFRAME_ROWS:
                    df.loc[i] = [   
                                player.rank, 
                                self.bot.utils.get_nickname(player.user_id),
                                "{:.2f}/6 ({:.2f}/6)".format(player.stats['adj_mean'], player.stats['raw_mean']),
                                "{:.2f}".format(player.stats['avg_green']),
                                "{:.2f}".format(player.stats['avg_yellow']),
                                "{:.2f}".format(player.stats['avg_other']),
                                len(valid_puzzles) - player.stats['missed_games'],
                                player.stats['missed_games']
                            ]
        elif query_type == PuzzleQueryType.ALL_TIME:
            # stats for 2+ puzzles, for all-time
            df = pd.DataFrame(columns=['Rank', 'User', 'Average', '🟩', '🟨', '⬜', '🧩'])
            for i, player in enumerate(players):
                if i > 0 and player.get_avgs() == players[i - 1].get_avgs():
                    player.rank = players[i - 1].rank
                else:
                    player.rank = i + 1
                if i <= self.MAX_DATAFRAME_ROWS:
                    df.loc[i] = [   
                                player.rank, 
                                self.bot.utils.get_nickname(player.user_id),
                                "{:.2f}/6".format(player.stats['raw_mean']),
                                "{:.2f}".format(player.stats['avg_green']),
                                "{:.2f}".format(player.stats['avg_yellow']),
                                "{:.2f}".format(player.stats['avg_other']),
                                len(valid_puzzles) - player.stats['missed_games']
                            ]

        ranks_img = self.utils.get_image_from_df(df)

        if ranks_img is not None:
            with io.BytesIO() as image_binary:
                ranks_img.save(image_binary, 'PNG')
                image_binary.seek(0)
                await ctx.send(f"Leaderboard 🧩: {explanation_str}", \
                        file=discord.File(fp=image_binary, filename='image.png'))
        else:
            await ctx.reply("Sorry, there was an issue fetching ranks. Please try again later.")

    @commands.guild_only()
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == self.bot.user.id: return
        
        if '\n' in message.content:
            title = message.content[0:message.content.index('\n')].strip()
            content = message.content[message.content.index('\n') + 1:].strip()
            if self.utils.is_wordle_submission(title):
                self.db.add_entry(int(message.author.id), title, content)
                await message.add_reaction('✅')

    @commands.guild_only()
    @commands.command(name='missing', help='Shows all players missing an entry for a puzzle')
    async def get_missing(self, ctx, *args):
        if len(args) == 0:
            puzzle_id = self.puzzles.get_puzzle_by_date(self.utils.get_todays_date())
        elif len(args) == 1 and re.match(r"^[#]?\d+$", args[0]):
            puzzle_id = int(args[0].strip("# "))
        else:
            await ctx.reply("Couldn't understand command. Try `?help missing`")
            return
        missing_ids = [str(user_id) for user_id in self.players.get_ids() if puzzle_id not in self.players.get(user_id).get_ids()]
        if len(missing_ids) == 0:
            await ctx.reply(f"All known players have submitted Puzzle #{puzzle_id}!")
        else:
            await ctx.reply("The following players are missing Puzzle #{}: <@{}>".format(puzzle_id, '>, <@'.join(missing_ids)))

    @commands.guild_only()
    @commands.command(name='entries', help='Shows all recorded entries for a player')
    async def get_entries(self, ctx, *args):
        if len(args) == 0:
            query_id = int(ctx.author.id)
        elif len(args) == 1 and self.utils.is_user(args[0]):
            query_id = int(args[0].strip("<@!> "))
        else:
            await ctx.reply("Couldn't understand command. Try `?help entries`.")
            return

        if query_id in self.players.get_ids():
            player = self.players.get(query_id)
            found_puzzles = [str(puzzle_id) for puzzle_id in player.get_ids()]
            await ctx.reply(f"{len(found_puzzles)} entries found:\n#{', #'.join(found_puzzles)}\nUse `?view <puzzle #>` to see details of a submission.")
        else:
            await ctx.reply(f"Couldn't find any recorded entries for <@{query_id}>.")

    @commands.guild_only()
    @commands.command(name="view", help="Show player's entry for a given puzzle number")
    async def view_entry(self, ctx, *args):
        if len(args) >= 1:
            if self.utils.is_user(args[0]):
                query_id = int(args[0].strip("<@!> "))
                query_args = args[1:]
            else:
                query_id = int(ctx.author.id)
                query_args = args
            puzzle_ids = []
            for arg in query_args:
                if re.match(r'^[#]?\d+$', arg):
                    puzzle_ids.append(int(arg.strip("# ")))
                else:
                    await ctx.reply(f"Couldn't understand command. Try `?help view`.")
                    return
        else:
            await ctx.reply(f"Couldn't understand command. Try `?help view`.")
            return

        puzzle_ids.sort()

        if query_id in self.players.get_ids():
            player = self.players.get(query_id)
            df = pd.DataFrame(columns=['User', 'Puzzle', 'Week', 'Score', '🟩', '🟨', '⬜'])
            for i, puzzle_id in enumerate(puzzle_ids):
                if puzzle_id in player.get_ids():
                    entry: PuzzleEntry = player.get_entry(puzzle_id)
                    df.loc[i] = [self.utils.get_nickname(query_id), f"#{puzzle_id}", entry.week, f"{entry.score}/6", entry.green, entry.yellow, entry.other]
                else:
                    df.loc[i] = [self.utils.get_nickname(query_id), f"#{puzzle_id}", "?", "?/6", "?", "?", "?"]
            entries_img = self.utils.get_image_from_df(df)
            if entries_img is not None:
                with io.BytesIO() as image_binary:
                    entries_img.save(image_binary, 'PNG')
                    image_binary.seek(0)
                    await ctx.reply(file=discord.File(fp=image_binary, filename='image.png'))
            else:
                await ctx.reply("Sorry, failed to fetch stats.")
        else:
            await ctx.reply(f"No records found for user <@{query_id}>.")
        

    @commands.guild_only()
    @commands.command(name="stats", help="Shows basic stats for a player\nUsage: ?stats <user>\n       ?stats <user1> <user2> <...>")
    async def get_stats(self, ctx, *args):
        missing_users_str = None
        if len(args) == 0:
            query_ids = [int(ctx.author.id)]
        else:
            query_ids = []
            unknown_ids = []
            for arg in args:
                if self.utils.is_user(arg):
                    user_id = int(arg.strip("<@!> "))
                    if user_id in self.players.get_ids():
                        query_ids.append(user_id)
                    else:
                        unknown_ids.append(str(user_id))
                else:
                    await ctx.reply("Couldn't understand command. Try `?help <stats>`.")
                    return
            if len(unknown_ids) > 0:
                if len(query_ids) > 0:
                    missing_users_str = f"Couldn't find user(s): <@{'>, <@'.join(unknown_ids)}>"
                else:
                    await ctx.reply(f"Couldn't find user(s): <@{'>, <@'.join(unknown_ids)}>")
                    return

        df = pd.DataFrame(columns=['User', 'Avg Score', 'Avg 🟩', 'Avg 🟨', 'Avg ⬜', '🧩', '🚫'])
        for i, query_id in enumerate(query_ids):
            player = self.players.get(query_id)
            df.loc[i] = [
                self.utils.get_nickname(query_id),
                "{:.4f}".format(stats.mean([e.score for e in player.get_entries()])),
                "{:.4f}".format(stats.mean([e.green for e in player.get_entries()])),
                "{:.4f}".format(stats.mean([e.yellow for e in player.get_entries()])),
                "{:.4f}".format(stats.mean([e.other for e in player.get_entries()])),
                len(player.get_ids()),
                len(self.puzzles.get_ids()) - len(player.get_ids()),
            ]
        stats_img = self.utils.get_image_from_df(df)

        hist_img = None
        if len(query_ids) < 5:
            valid_scores = ['1/6', '2/6', '3/6', '4/6', '5/6', '6/6', '7/6']
            plt.rcParams.update({'font.size': 20})
            
            df = pd.DataFrame(columns=['Player', 'Score', 'Count'])
            for i, query_id in enumerate(query_ids):
                score_counts = [0, 0, 0, 0, 0, 0, 0]
                player = self.players.get(query_id)
                for score in [entry.score for entry in player.get_entries()]:
                    score_counts[score - 1] += 1
                for j in range(0, len(valid_scores)):
                    df.loc[i*7 + j] = [
                        self.utils.remove_emojis(self.utils.get_nickname(query_id)),
                        valid_scores[j],
                        score_counts[j]
                    ]
            sns.catplot(x='Score', y='Count', hue='Player', data=df, kind='bar')
            fig = plt.gcf()
            fig.subplots_adjust(bottom=0.2)
            fig.set_size_inches(10, 5)
            hist_img = self.utils.fig_to_image(fig)
            hist_img = self.utils.resize_image(hist_img, width = stats_img.size[0])
            plt.close()

        if hist_img is not None:
            stats_img = self.utils.combine_images(stats_img, hist_img)

        if stats_img is not None:
            stats_binary = self.utils.image_to_binary(stats_img)
            if missing_users_str is None:
                await ctx.reply(file=discord.File(fp=stats_binary, filename='image.png'))
            else:
                await ctx.reply(missing_users_str, file=discord.File(fp=stats_binary, filename='image.png'))
        else:
            await ctx.reply("Sorry, an error occurred while trying to fetch stats.")

    @commands.guild_only()
    @commands.command(name="help")
    async def help(self, ctx, *args):
        if len(args) == 0:
            await ctx.reply(self.help_menu.get_all())
        elif len(args) == 1:
            await ctx.reply(self.help_menu.get_message(args[0]))
        else:
            await ctx.reply("Couldn't understand command. Try `?help <command>`.")

    def build_help_menu(self) -> None:
        self.help_menu.add('ranks', \
                explanation = "View the leaderboard over time or for a specific puzzle.", \
                usage = "`?ranks (today|weekly|10-day|all-time)`\n`?ranks <MM/DD/YYYY>`\n`?ranks <puzzle #>`", \
                notes = "- `?ranks` will default to `?ranks weekly`.\n- When using MM/DD/YYYY format, the date must be a Sunday.")
        self.help_menu.add('missing', \
                explanation = "View and mention all players who have not yet submitted a puzzle.", \
                usage = "`?missing [<puzzle #>]`", \
                notes = "`?missing` will default to today's puzzle.")
        self.help_menu.add('entries', \
                explanation = "View a list of all submitted entries for a player.", \
                usage = "`?entries [<player>]`")
        self.help_menu.add('stats', \
                explanation = "View more details stats on one or players.", \
                usage = "`?stats <player1> [<player2> ...]`", \
                notes = "`?stats` will default to just query for the calling user.")
        self.help_menu.add('view', \
                explanation = "View specific details of one or more entries.", \
                usage = "`?view [<player>] <puzzle #1> [<puzzle #2> ...]`")
        self.help_menu.add('save', \
                explanation = "Manually save to the database (debug usage only).", \
                usage = "`?save`", \
                owner_only=True)
        self.help_menu.add('add', \
                explanation = "Manually add an entry to the database.", \
                usage = "`?add [<player>] <entry>`", \
                owner_only=True)
        self.help_menu.add('remove', \
                explanation = "Remove an entry from the database.", \
                usage = "`?remove [<player>] <puzzle #>`", \
                owner_only=True)


def setup(bot: commands.Bot):
    bot.add_cog(MembersCog(bot))