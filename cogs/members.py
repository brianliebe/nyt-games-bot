import discord, re, io, traceback
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from enum import Enum, auto
from datetime import timedelta
from discord.ext import commands
from models.connections_entry import ConnectionsPuzzleEntry
from models.connections_player_stats import ConnectionsPlayerStats
from models.wordle_entry import WordlePuzzleEntry
from models.wordle_player_stats import WordlePlayerStats
from utils.bot_utilities import BotUtilities, NYTGame
from utils.connections_db import ConnectionsDatabaseHandler
from utils.help_handler import HelpMenuHandler
from utils.wordle_db import WordleDatabaseHandler

class PuzzleQueryType(Enum):
    SINGLE_PUZZLE = auto()
    MULTI_PUZZLE = auto()
    ALL_TIME = auto()

class MembersCog(commands.Cog, name="Normal Members Commands"):

    MAX_DATAFRAME_ROWS = 10

    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.utils: BotUtilities = self.bot.utils
        self.wordle_db: WordleDatabaseHandler = self.bot.wordle_db
        self.conns_db: ConnectionsDatabaseHandler = self.bot.conns_db
        self.help_menu: HelpMenuHandler = self.bot.help_menu
        self.build_help_menu()

    #####################
    #   COMMAND SETUP   #
    #####################

    @commands.guild_only()
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        try:
            if message.author.id != self.bot.user.id and message.content.count("\n") >= 2:
                # parse non-puzzle lines from message
                user_id = str(message.author.id)
                first_line = message.content.splitlines()[0].strip()
                first_two_lines = '\n'.join(message.content.splitlines()[:2])
                # add entry to either Wordle or Connections
                if 'Wordle' in first_line and self.utils.is_wordle_submission(first_line):
                    content = '\n'.join(message.content.splitlines()[1:])
                    self.wordle_db.add_entry(user_id, first_line, content)
                    await message.add_reaction('✅')
                elif 'Connections' in first_line and self.utils.is_connections_submission(first_two_lines):
                    content = '\n'.join(message.content.splitlines()[2:])
                    self.conns_db.add_entry(user_id, first_two_lines, content)
                    await message.add_reaction('✅')
        except Exception as e:
            print(f"Caught exception: {e}")
            traceback.print_exception(e)

    @commands.guild_only()
    @commands.command(name="help")
    async def help(self, ctx: commands.Context, *args: str) -> None:
        if len(args) == 0:
            await ctx.reply(self.help_menu.get_all())
        elif len(args) == 1:
            await ctx.reply(self.help_menu.get_message(args[0]))
        else:
            await ctx.reply("Couldn't understand command. Try `?help <command>`.")

    @commands.guild_only()
    @commands.command(name='ranks', help='Show ranks of players in the server')
    async def get_ranks(self, ctx: commands.Context, *args: str) -> None:
        try:
            match self.utils.get_game_from_channel(ctx.message):
                case NYTGame.WORDLE:
                    await self.get_ranks_wordle(ctx, *args)
                case NYTGame.CONNECTIONS:
                    await self.get_ranks_connections(ctx, *args)
                case NYTGame.UNKNOWN:
                    print(f"[RANKS] Unsure of game mode, skipping response to: '{args}'")
        except Exception as e:
            print(f"Caught exception: {e}")
            traceback.print_exception(e)

    @commands.guild_only()
    @commands.command(name='missing', help='Show all players missing an entry for a puzzle')
    async def get_missing(self, ctx: commands.Context, *args: str) -> None:
        try:
            match self.utils.get_game_from_channel(ctx.message):
                case NYTGame.WORDLE:
                    await self.get_missing_wordle(ctx, *args)
                case NYTGame.CONNECTIONS:
                    await self.get_missing_connections(ctx, *args)
                case NYTGame.UNKNOWN:
                    print(f"[MISSING] Unsure of game mode, skipping response to: '{args}'")
        except Exception as e:
            print(f"Caught exception: {e}")
            traceback.print_exception(e)

    @commands.guild_only()
    @commands.command(name='entries', help='Show all recorded entries for a player')
    async def get_entries(self, ctx: commands.Context, *args: str) -> None:
        try:
            match self.utils.get_game_from_channel(ctx.message):
                case NYTGame.WORDLE:
                    await self.get_entries_wordle(ctx, *args)
                case NYTGame.CONNECTIONS:
                    await self.get_entries_connections(ctx, *args)
                case NYTGame.UNKNOWN:
                    print(f"[ENTRIES] Unsure of game mode, skipping response to: '{args}'")
        except Exception as e:
            print(f"Caught exception: {e}")
            traceback.print_exception(e)

    @commands.guild_only()
    @commands.command(name="view", help="Show player's entry for a given puzzle number")
    async def get_entry(self, ctx: commands.Context, *args: str) -> None:
        try:
            match self.utils.get_game_from_channel(ctx.message):
                case NYTGame.WORDLE:
                    await self.get_entry_wordle(ctx, *args)
                case NYTGame.CONNECTIONS:
                    await self.get_entry_connections(ctx, *args)
                case NYTGame.UNKNOWN:
                    print(f"[ENTRY] Unsure of game mode, skipping response to: '{args}'")
        except Exception as e:
            print(f"Caught exception: {e}")
            traceback.print_exception(e)

    @commands.guild_only()
    @commands.command(name="stats", help="Show basic stats for a player")
    async def get_stats(self, ctx: commands.Context, *args: str) -> None:
        try:
            match self.utils.get_game_from_channel(ctx.message):
                case NYTGame.WORDLE:
                    await self.get_stats_wordle(ctx, *args)
                case NYTGame.CONNECTIONS:
                    await self.get_stats_connections(ctx, *args)
                case NYTGame.UNKNOWN:
                    print(f"[STATS] Unsure of game mode, skipping response to: '{args}'")
        except Exception as e:
            print(f"Caught exception: {e}")
            traceback.print_exception(e)

    ######################
    #   WORDLE METHODS   #
    ######################

    async def get_ranks_wordle(self, ctx: commands.Context, *args: str) -> None:
        if len(args) == 0 or (len(args) == 1 and args[0] in ['week', 'weekly']):
            # WEEKLY
            start_of_week = self.utils.get_week_start(self.utils.get_todays_date())
            todays_puzzle_id = self.wordle_db.get_puzzle_by_date(self.utils.get_todays_date())
            valid_puzzles = [p_id for p_id in self.wordle_db.get_puzzles_by_week(start_of_week) if p_id <= todays_puzzle_id]
            explanation_str = "This Week (so far)"
            query_type = PuzzleQueryType.MULTI_PUZZLE
        elif len(args) == 1 and args[0] in ['10day', '10-day']:
            # 10-DAY AVERAGE
            seven_days_ago_puzzle = self.wordle_db.get_puzzle_by_date(self.utils.get_todays_date() - timedelta(days=10))
            valid_puzzles = list(range(seven_days_ago_puzzle, seven_days_ago_puzzle + 10))
            explanation_str = "Last 10 Days"
            query_type = PuzzleQueryType.MULTI_PUZZLE
        elif len(args) == 1 and args[0] in ['alltime', 'all-time']:
            # ALL TIME
            valid_puzzles = self.wordle_db.get_all_puzzles()
            explanation_str = "All-time"
            query_type = PuzzleQueryType.ALL_TIME
        elif len(args) == 1 and args[0] == 'today':
            # TODAY ONLY
            valid_puzzles = [self.wordle_db.get_puzzle_by_date(self.utils.get_todays_date())]
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
            todays_puzzle_id = self.wordle_db.get_puzzle_by_date(self.utils.get_todays_date())
            if self.utils.is_sunday(query_date):
                valid_puzzles = [p_id for p_id in self.wordle_db.get_puzzles_by_week(query_date) if p_id <= todays_puzzle_id]
                explanation_str = f"Week of {self.utils.convert_date_to_str(query_date)}"
                query_type = PuzzleQueryType.MULTI_PUZZLE
            else:
                await ctx.reply("Query date is not a Sunday. Try `?help ranks`.")
                return
        else:
            await ctx.reply("Couldn't understand your command. Try `?help ranks`.")
            return

        stats: list[WordlePlayerStats] = []
        for user_id in self.wordle_db.get_all_players():
            player_puzzles = self.wordle_db.get_puzzles_by_player(user_id)
            intersection = list(set(player_puzzles).intersection(valid_puzzles))
            if len(intersection) > 0:
                stats.append(WordlePlayerStats(user_id, valid_puzzles, self.wordle_db))

        if len(stats) == 0:
            await ctx.reply(f"Sorry, no users could be found for this query.")
            return

        if query_type != PuzzleQueryType.ALL_TIME:
            # for all queries except 'All-time', we rank based on the adjusted mean
            stats.sort(key = lambda p: (p.adj_mean, p.avg_other, p.avg_yellow, p.avg_green))
        else:
            # for all-time queries, we must rank on the raw score (since adj. will be skewed)
            stats.sort(key = lambda p: (p.raw_mean, p.avg_other, p.avg_yellow, p.avg_green))

        if query_type == PuzzleQueryType.SINGLE_PUZZLE:
            # stats for just 1 puzzle
            df = pd.DataFrame(columns=['Rank', 'User', 'Score', '🟩', '🟨', '⬜'])
            for i, player_stats in enumerate(stats):
                if i > 0 and player_stats.get_stat_list() == stats[i - 1].get_stat_list():
                    player_stats.rank = stats[i - 1].rank
                else:
                    player_stats.rank = i + 1

                if i <= self.MAX_DATAFRAME_ROWS:
                    df.loc[i] = [
                        player_stats.rank,
                        self.utils.get_nickname(player_stats.user_id),
                        f"{player_stats.raw_mean:d}/6",
                        f"{player_stats.avg_green:d}",
                        f"{player_stats.avg_yellow:d}",
                        f"{player_stats.avg_other:d}"
                    ]
        elif query_type == PuzzleQueryType.MULTI_PUZZLE:
            # stats for 2+ puzzles, but not all-time
            df = pd.DataFrame(columns=['Rank', 'User', 'Average', '🟩', '🟨', '⬜', '🧩', '🚫'])
            for i, player_stats in enumerate(stats):
                if i > 0 and player_stats.get_stat_list() == stats[i - 1].get_stat_list():
                    player_stats.rank = stats[i - 1].rank
                else:
                    player_stats.rank = i + 1
                if i <= self.MAX_DATAFRAME_ROWS:
                    df.loc[i] = [
                        player_stats.rank,
                        self.utils.get_nickname(player_stats.user_id),
                        f"{player_stats.adj_mean:.2f}/6 ({player_stats.raw_mean:.2f}/6)",
                        f"{player_stats.avg_green:.2f}",
                        f"{player_stats.avg_yellow:.2f}",
                        f"{player_stats.avg_other:.2f}",
                        len(valid_puzzles) - player_stats.missed_games,
                        player_stats.missed_games
                    ]
        elif query_type == PuzzleQueryType.ALL_TIME:
            # stats for 2+ puzzles, for all-time
            df = pd.DataFrame(columns=['Rank', 'User', 'Average', '🟩', '🟨', '⬜', '🧩'])
            for i, player_stats in enumerate(stats):
                if i > 0 and player_stats.get_stat_list() == stats[i - 1].get_stat_list():
                    player_stats.rank = stats[i - 1].rank
                else:
                    player_stats.rank = i + 1
                if i <= self.MAX_DATAFRAME_ROWS:
                    df.loc[i] = [
                        player_stats.rank,
                        self.utils.get_nickname(player_stats.user_id),
                        f"{player_stats.raw_mean:.2f}/6",
                        f"{player_stats.avg_green:.2f}",
                        f"{player_stats.avg_yellow:.2f}",
                        f"{player_stats.avg_other:.2f}",
                        len(valid_puzzles) - player_stats.missed_games
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

    async def get_missing_wordle(self, ctx: commands.Context, *args: str) -> None:
        if len(args) == 0:
            puzzle_id = self.wordle_db.get_puzzle_by_date(self.utils.get_todays_date())
        elif len(args) == 1 and re.match(r"^[#]?\d+$", args[0]):
            puzzle_id = int(args[0].strip("# "))
        else:
            await ctx.reply("Couldn't understand command. Try `?help missing`")
            return

        missing_ids = [user_id for user_id in self.wordle_db.get_all_players() if user_id not in self.wordle_db.get_players_by_puzzle_id(puzzle_id)]
        if len(missing_ids) == 0:
            await ctx.reply(f"All known players have submitted Puzzle #{puzzle_id}!")
        else:
            await ctx.reply("The following players are missing Puzzle #{}: <@{}>".format(puzzle_id, '>, <@'.join(missing_ids)))

    async def get_entries_wordle(self, ctx: commands.Context, *args: str) -> None:
        if len(args) == 0:
            user_id = str(ctx.author.id)
        elif len(args) == 1 and self.utils.is_user(args[0]):
            user_id = args[0].strip("<@!> ")
        else:
            await ctx.reply("Couldn't understand command. Try `?help entries`.")
            return

        if user_id in self.wordle_db.get_all_players():
            found_puzzles = [str(p_id) for p_id in self.wordle_db.get_puzzles_by_player(user_id)]
            if len(found_puzzles) < 50:
                await ctx.reply(f"{len(found_puzzles)} entries found:\n#{', #'.join(found_puzzles)}\nUse `?view <puzzle #>` to see details of a submission.")
            else:
                await ctx.reply(f"{len(found_puzzles)} entries found, too many to display. First 10 and last 10:\n#{', #'.join(found_puzzles[:10])} ... #{', #'.join(found_puzzles[-10:])}\nUse `?view <puzzle #>` to see details of a submission.")
        else:
            await ctx.reply(f"Couldn't find any recorded entries for <@{user_id}>.")

    async def get_entry_wordle(self, ctx: commands.Context, *args: str) -> None:
        if len(args) >= 1:
            if self.utils.is_user(args[0]):
                user_id = args[0].strip("<@!> ")
                query_args = args[1:]
            else:
                user_id = str(ctx.author.id)
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

        if user_id in self.wordle_db.get_all_players():
            user_puzzles: list[WordlePuzzleEntry] = self.wordle_db.get_entries_by_player(user_id)
            df = pd.DataFrame(columns=['User', 'Puzzle', 'Score', '🟩', '🟨', '⬜'])
            for i, puzzle_id in enumerate(puzzle_ids):
                found_match = False
                for entry in user_puzzles:
                    if entry.puzzle_id == puzzle_id:
                        df.loc[i] = [
                            self.utils.get_nickname(user_id),
                            f"#{puzzle_id}",
                            f"{entry.score}/6",
                            entry.green,
                            entry.yellow,
                            entry.other
                        ]
                        found_match = True
                        break
                if not found_match:
                    df.loc[i] = [
                        self.utils.get_nickname(user_id),
                        f"#{puzzle_id}",
                        "?/6",
                        "?",
                        "?",
                        "?"
                    ]
            entries_img = self.utils.get_image_from_df(df)
            if entries_img is not None:
                with io.BytesIO() as image_binary:
                    entries_img.save(image_binary, 'PNG')
                    image_binary.seek(0)
                    await ctx.reply(file=discord.File(fp=image_binary, filename='image.png'))
            else:
                await ctx.reply("Sorry, failed to fetch stats.")
        else:
            await ctx.reply(f"No records found for user <@{user_id}>.")

    async def get_stats_wordle(self, ctx: commands.Context, *args: str) -> None:
        missing_users_str = None
        if len(args) == 0:
            user_ids = [str(ctx.author.id)]
        else:
            user_ids = []
            unknown_ids = []
            for arg in args:
                if self.utils.is_user(arg):
                    user_id = arg.strip("<@!> ")
                    if user_id in self.wordle_db.get_all_players():
                        user_ids.append(user_id)
                    else:
                        unknown_ids.append(str(user_id))
                else:
                    await ctx.reply("Couldn't understand command. Try `?help <stats>`.")
                    return
            if len(unknown_ids) > 0:
                if len(user_ids) > 0:
                    missing_users_str = f"Couldn't find user(s): <@{'>, <@'.join(unknown_ids)}>"
                else:
                    await ctx.reply(f"Couldn't find user(s): <@{'>, <@'.join(unknown_ids)}>")
                    return

        df = pd.DataFrame(columns=['User', 'Avg Score', 'Avg 🟩', 'Avg 🟨', 'Avg ⬜', '🧩', '🚫'])
        for i, user_id in enumerate(user_ids):
            puzzle_list = self.wordle_db.get_puzzles_by_player(user_id)
            player_stats = WordlePlayerStats(user_id, puzzle_list, self.wordle_db)
            df.loc[i] = [
                self.utils.get_nickname(user_id),
                f"{player_stats.raw_mean:.4f}",
                f"{player_stats.avg_green:.4f}",
                f"{player_stats.avg_yellow:.4f}",
                f"{player_stats.avg_other:.4f}",
                len(puzzle_list),
                len(self.wordle_db.get_all_puzzles()) - len(puzzle_list),
            ]

        stats_img = self.utils.get_image_from_df(df)

        hist_img = None
        if len(user_ids) < 5:
            valid_scores = ['1/6', '2/6', '3/6', '4/6', '5/6', '6/6', '7/6']
            plt.rcParams.update({'font.size': 20})

            df = pd.DataFrame(columns=['Player', 'Score', 'Count'])
            for i, user_id in enumerate(user_ids):
                score_counts = [0] * len(valid_scores)
                entries: list[WordlePuzzleEntry] = self.wordle_db.get_entries_by_player(user_id)
                for score in [entry.score for entry in entries]:
                    score_counts[score - 1] += 1
                for j in range(0, len(valid_scores)):
                    df.loc[i*len(valid_scores) + j] = [
                        self.utils.remove_emojis(self.utils.get_nickname(user_id)),
                        valid_scores[j],
                        score_counts[j]
                    ]
            sns.catplot(x='Score', y='Count', hue='Player', data=df, kind='bar')
            fig: plt.Figure = plt.gcf()
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

    #######################
    # CONNECTIONS METHODS #
    #######################

    async def get_ranks_connections(self, ctx: commands.Context, *args: str) -> None:
        if len(args) == 0 or (len(args) == 1 and args[0] in ['week', 'weekly']):
            # WEEKLY
            start_of_week = self.utils.get_week_start(self.utils.get_todays_date())
            todays_puzzle_id = self.conns_db.get_puzzle_by_date(self.utils.get_todays_date())
            valid_puzzles = [p_id for p_id in self.conns_db.get_puzzles_by_week(start_of_week) if p_id <= todays_puzzle_id]
            explanation_str = "This Week (so far)"
            query_type = PuzzleQueryType.MULTI_PUZZLE
        elif len(args) == 1 and args[0] in ['10day', '10-day']:
            # 10-DAY AVERAGE
            seven_days_ago_puzzle = self.conns_db.get_puzzle_by_date(self.utils.get_todays_date() - timedelta(days=10))
            valid_puzzles = list(range(seven_days_ago_puzzle, seven_days_ago_puzzle + 10))
            explanation_str = "Last 10 Days"
            query_type = PuzzleQueryType.MULTI_PUZZLE
        elif len(args) == 1 and args[0] in ['alltime', 'all-time']:
            # ALL TIME
            valid_puzzles = self.conns_db.get_all_puzzles()
            explanation_str = "All-time"
            query_type = PuzzleQueryType.ALL_TIME
        elif len(args) == 1 and args[0] == 'today':
            # TODAY ONLY
            valid_puzzles = [self.conns_db.get_puzzle_by_date(self.utils.get_todays_date())]
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
            todays_puzzle_id = self.conns_db.get_puzzle_by_date(self.utils.get_todays_date())
            if self.utils.is_sunday(query_date):
                valid_puzzles = [p_id for p_id in self.conns_db.get_puzzles_by_week(query_date) if p_id <= todays_puzzle_id]
                explanation_str = f"Week of {self.utils.convert_date_to_str(query_date)}"
                query_type = PuzzleQueryType.MULTI_PUZZLE
            else:
                await ctx.reply("Query date is not a Sunday. Try `?help ranks`.")
                return
        else:
            await ctx.reply("Couldn't understand your command. Try `?help ranks`.")
            return

        stats: list[ConnectionsPlayerStats] = []
        for user_id in self.conns_db.get_all_players():
            player_puzzles = self.conns_db.get_puzzles_by_player(user_id)
            intersection = list(set(player_puzzles).intersection(valid_puzzles))
            if len(intersection) > 0:
                stats.append(ConnectionsPlayerStats(user_id, valid_puzzles, self.conns_db))

        if len(stats) == 0:
            await ctx.reply(f"Sorry, no users could be found for this query.")
            return

        if query_type != PuzzleQueryType.ALL_TIME:
            # for all queries except 'All-time', we rank based on the adjusted mean
            stats.sort(key = lambda p: (p.adj_mean))
        else:
            # for all-time queries, we must rank on the raw score (since adj. will be skewed)
            stats.sort(key = lambda p: (p.raw_mean))

        if query_type == PuzzleQueryType.SINGLE_PUZZLE:
            # stats for just 1 puzzle
            df = pd.DataFrame(columns=['Rank', 'User', 'Score'])
            for i, player_stats in enumerate(stats):
                if i > 0 and player_stats.get_stat_list() == stats[i - 1].get_stat_list():
                    player_stats.rank = stats[i - 1].rank
                else:
                    player_stats.rank = i + 1

                if i <= self.MAX_DATAFRAME_ROWS:
                    df.loc[i] = [
                        player_stats.rank,
                        self.utils.get_nickname(player_stats.user_id),
                        f"{player_stats.raw_mean:d}/7"
                    ]
        elif query_type == PuzzleQueryType.MULTI_PUZZLE:
            # stats for 2+ puzzles, but not all-time
            df = pd.DataFrame(columns=['Rank', 'User', 'Average', '🧩', '🚫'])
            for i, player_stats in enumerate(stats):
                if i > 0 and player_stats.get_stat_list() == stats[i - 1].get_stat_list():
                    player_stats.rank = stats[i - 1].rank
                else:
                    player_stats.rank = i + 1
                if i <= self.MAX_DATAFRAME_ROWS:
                    df.loc[i] = [
                        player_stats.rank,
                        self.utils.get_nickname(player_stats.user_id),
                        f"{player_stats.adj_mean:.2f}/7 ({player_stats.raw_mean:.2f}/7)",
                        len(valid_puzzles) - player_stats.missed_games,
                        player_stats.missed_games
                    ]
        elif query_type == PuzzleQueryType.ALL_TIME:
            # stats for 2+ puzzles, for all-time
            df = pd.DataFrame(columns=['Rank', 'User', 'Average', '🧩'])
            for i, player_stats in enumerate(stats):
                if i > 0 and player_stats.get_stat_list() == stats[i - 1].get_stat_list():
                    player_stats.rank = stats[i - 1].rank
                else:
                    player_stats.rank = i + 1
                if i <= self.MAX_DATAFRAME_ROWS:
                    df.loc[i] = [
                        player_stats.rank,
                        self.utils.get_nickname(player_stats.user_id),
                        f"{player_stats.raw_mean:.2f}/7",
                        len(valid_puzzles) - player_stats.missed_games
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

    async def get_missing_connections(self, ctx: commands.Context, *args: str) -> None:
        if len(args) == 0:
            puzzle_id = self.conns_db.get_puzzle_by_date(self.utils.get_todays_date())
        elif len(args) == 1 and re.match(r"^[#]?\d+$", args[0]):
            puzzle_id = int(args[0].strip("# "))
        else:
            await ctx.reply("Couldn't understand command. Try `?help missing`")
            return

        missing_ids = [user_id for user_id in self.conns_db.get_all_players() if user_id not in self.conns_db.get_players_by_puzzle_id(puzzle_id)]
        if len(missing_ids) == 0:
            await ctx.reply(f"All known players have submitted Puzzle #{puzzle_id}!")
        else:
            await ctx.reply("The following players are missing Puzzle #{}: <@{}>".format(puzzle_id, '>, <@'.join(missing_ids)))

    async def get_entries_connections(self, ctx: commands.Context, *args: str) -> None:
        if len(args) == 0:
            user_id = str(ctx.author.id)
        elif len(args) == 1 and self.utils.is_user(args[0]):
            user_id = args[0].strip("<@!> ")
        else:
            await ctx.reply("Couldn't understand command. Try `?help entries`.")
            return

        if user_id in self.conns_db.get_all_players():
            found_puzzles = [str(p_id) for p_id in self.conns_db.get_puzzles_by_player(user_id)]
            if len(found_puzzles) < 50:
                await ctx.reply(f"{len(found_puzzles)} entries found:\n#{', #'.join(found_puzzles)}\nUse `?view <puzzle #>` to see details of a submission.")
            else:
                await ctx.reply(f"{len(found_puzzles)} entries found, too many to display. First 10 and last 10:\n#{', #'.join(found_puzzles[:10])} ... #{', #'.join(found_puzzles[-10:])}\nUse `?view <puzzle #>` to see details of a submission.")
        else:
            await ctx.reply(f"Couldn't find any recorded entries for <@{user_id}>.")

    async def get_entry_connections(self, ctx: commands.Context, *args: str) -> None:
        if len(args) >= 1:
            if self.utils.is_user(args[0]):
                user_id = args[0].strip("<@!> ")
                query_args = args[1:]
            else:
                user_id = str(ctx.author.id)
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

        if user_id in self.conns_db.get_all_players():
            user_puzzles: list[ConnectionsPuzzleEntry] = self.conns_db.get_entries_by_player(user_id)
            df = pd.DataFrame(columns=['User', 'Puzzle', 'Score'])
            for i, puzzle_id in enumerate(puzzle_ids):
                found_match = False
                for entry in user_puzzles:
                    if entry.puzzle_id == puzzle_id:
                        df.loc[i] = [
                            self.utils.get_nickname(user_id),
                            f"#{puzzle_id}",
                            f"{entry.score}/8",
                        ]
                        found_match = True
                        break
                if not found_match:
                    df.loc[i] = [
                        self.utils.get_nickname(user_id),
                        f"#{puzzle_id}",
                        "?/8",
                    ]
            entries_img = self.utils.get_image_from_df(df)
            if entries_img is not None:
                with io.BytesIO() as image_binary:
                    entries_img.save(image_binary, 'PNG')
                    image_binary.seek(0)
                    await ctx.reply(file=discord.File(fp=image_binary, filename='image.png'))
            else:
                await ctx.reply("Sorry, failed to fetch stats.")
        else:
            await ctx.reply(f"No records found for user <@{user_id}>.")

    async def get_stats_connections(self, ctx: commands.Context, *args: str) -> None:
        missing_users_str = None
        if len(args) == 0:
            user_ids = [str(ctx.author.id)]
        else:
            user_ids = []
            unknown_ids = []
            for arg in args:
                if self.utils.is_user(arg):
                    user_id = arg.strip("<@!> ")
                    if user_id in self.conns_db.get_all_players():
                        user_ids.append(user_id)
                    else:
                        unknown_ids.append(str(user_id))
                else:
                    await ctx.reply("Couldn't understand command. Try `?help <stats>`.")
                    return
            if len(unknown_ids) > 0:
                if len(user_ids) > 0:
                    missing_users_str = f"Couldn't find user(s): <@{'>, <@'.join(unknown_ids)}>"
                else:
                    await ctx.reply(f"Couldn't find user(s): <@{'>, <@'.join(unknown_ids)}>")
                    return

        df = pd.DataFrame(columns=['User', 'Avg Score', '🧩', '🚫'])
        for i, user_id in enumerate(user_ids):
            puzzle_list = self.conns_db.get_puzzles_by_player(user_id)
            player_stats = ConnectionsPlayerStats(user_id, puzzle_list, self.conns_db)
            df.loc[i] = [
                self.utils.get_nickname(user_id),
                f"{player_stats.raw_mean:.4f}",
                len(puzzle_list),
                len(self.conns_db.get_all_puzzles()) - len(puzzle_list),
            ]

        stats_img = self.utils.get_image_from_df(df)

        hist_img = None
        if len(user_ids) < 5:
            valid_scores = ['1/7', '2/7', '3/7', '4/7', '5/7', '6/7', '7/7', '8/7']
            plt.rcParams.update({'font.size': 20})

            df = pd.DataFrame(columns=['Player', 'Score', 'Count'])
            for i, user_id in enumerate(user_ids):
                score_counts = [0] * len(valid_scores)
                entries: list[ConnectionsPuzzleEntry] = self.conns_db.get_entries_by_player(user_id)
                for score in [entry.score for entry in entries]:
                    score_counts[score - 1] += 1
                for j in range(0, len(valid_scores)):
                    df.loc[i*len(valid_scores) + j] = [
                        self.utils.remove_emojis(self.utils.get_nickname(user_id)),
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

    ######################
    #   HELPER METHODS   #
    ######################

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
        self.help_menu.add('add', \
                explanation = "Manually add an entry to the database.", \
                usage = "`?add [<player>] <entry>`", \
                owner_only=True)
        self.help_menu.add('remove', \
                explanation = "Remove an entry from the database.", \
                usage = "`?remove [<player>] <puzzle #>`", \
                owner_only=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(MembersCog(bot))
