import discord, io, re
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from datetime import timedelta
from discord.ext import commands
from data.strands import StrandsDatabaseHandler
from games.base_command_handler import BaseCommandHandler
from models.base_game import PuzzleQueryType
from models.strands import StrandsPlayerStats, StrandsPuzzleEntry
from utils.bot_utilities import BotUtilities

class StrandsCommandHandler(BaseCommandHandler):
    def __init__(self, utils: BotUtilities) -> None:
        super().__init__(utils, StrandsDatabaseHandler(utils))

    ######################
    #   MEMBER METHODS   #
    ######################

    async def get_ranks(self, ctx: commands.Context, *args: str) -> None:
        if len(args) == 0 or (len(args) == 1 and args[0] in ['week', 'weekly']):
            # WEEKLY
            start_of_week = self.utils.get_week_start(self.utils.get_todays_date())
            todays_puzzle_id = self.db.get_puzzle_by_date(self.utils.get_todays_date())
            valid_puzzles = [p_id for p_id in self.db.get_puzzles_by_week(start_of_week) if p_id <= todays_puzzle_id]
            explanation_str = "This Week (so far)"
            query_type = PuzzleQueryType.MULTI_PUZZLE
        elif len(args) == 1 and args[0] in ['10day', '10-day']:
            # 10-DAY AVERAGE
            seven_days_ago_puzzle = self.db.get_puzzle_by_date(self.utils.get_todays_date() - timedelta(days=10))
            valid_puzzles = list(range(seven_days_ago_puzzle, seven_days_ago_puzzle + 10))
            explanation_str = "Last 10 Days"
            query_type = PuzzleQueryType.MULTI_PUZZLE
        elif len(args) == 1 and args[0] in ['alltime', 'all-time']:
            # ALL TIME
            valid_puzzles = self.db.get_all_puzzles()
            explanation_str = "All-time"
            query_type = PuzzleQueryType.ALL_TIME
        elif len(args) == 1 and args[0] == 'today':
            # TODAY ONLY
            valid_puzzles = [self.db.get_puzzle_by_date(self.utils.get_todays_date())]
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
            todays_puzzle_id = self.db.get_puzzle_by_date(self.utils.get_todays_date())
            if self.utils.is_sunday(query_date):
                valid_puzzles = [p_id for p_id in self.db.get_puzzles_by_week(query_date) if p_id <= todays_puzzle_id]
                explanation_str = f"Week of {self.utils.convert_date_to_str(query_date)}"
                query_type = PuzzleQueryType.MULTI_PUZZLE
            else:
                await ctx.reply("Query date is not a Sunday. Try `?help ranks`.")
                return
        else:
            await ctx.reply("Couldn't understand your command. Try `?help ranks`.")
            return

        stats: list[StrandsPlayerStats] = []
        for user_id in self.db.get_all_players():
            player_puzzles = self.db.get_puzzles_by_player(user_id)
            intersection = list(set(player_puzzles).intersection(valid_puzzles))
            if len(intersection) > 0:
                stats.append(StrandsPlayerStats(user_id, valid_puzzles, self.db))

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
            df = pd.DataFrame(columns=['Rank', 'User', 'Hints'])
            for i, player_stats in enumerate(stats):
                if i > 0 and player_stats.get_stat_list() == stats[i - 1].get_stat_list():
                    player_stats.rank = stats[i - 1].rank
                else:
                    player_stats.rank = i + 1

                if i <= self.MAX_DATAFRAME_ROWS:
                    df.loc[i] = [
                        player_stats.rank,
                        self.utils.get_nickname(player_stats.user_id),
                        f"{player_stats.raw_mean:d}"
                    ]
        elif query_type == PuzzleQueryType.MULTI_PUZZLE:
            # stats for 2+ puzzles, but not all-time
            df = pd.DataFrame(columns=['Rank', 'User', 'Avg Hints', '🧩', '🚫'])
            for i, player_stats in enumerate(stats):
                if i > 0 and player_stats.get_stat_list() == stats[i - 1].get_stat_list():
                    player_stats.rank = stats[i - 1].rank
                else:
                    player_stats.rank = i + 1
                if i <= self.MAX_DATAFRAME_ROWS:
                    df.loc[i] = [
                        player_stats.rank,
                        self.utils.get_nickname(player_stats.user_id),
                        f"{player_stats.adj_mean:.2f} ({player_stats.raw_mean:.2f})",
                        len(valid_puzzles) - player_stats.missed_games,
                        player_stats.missed_games
                    ]
        elif query_type == PuzzleQueryType.ALL_TIME:
            # stats for 2+ puzzles, for all-time
            df = pd.DataFrame(columns=['Rank', 'User', 'Avg Hints', '🧩'])
            for i, player_stats in enumerate(stats):
                if i > 0 and player_stats.get_stat_list() == stats[i - 1].get_stat_list():
                    player_stats.rank = stats[i - 1].rank
                else:
                    player_stats.rank = i + 1
                if i <= self.MAX_DATAFRAME_ROWS:
                    df.loc[i] = [
                        player_stats.rank,
                        self.utils.get_nickname(player_stats.user_id),
                        f"{player_stats.raw_mean:.2f}",
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

    async def get_missing(self, ctx: commands.Context, *args: str) -> None:
        if len(args) == 0:
            puzzle_id = self.db.get_puzzle_by_date(self.utils.get_todays_date())
        elif len(args) == 1 and re.match(r"^[#]?\d+$", args[0]):
            puzzle_id = int(args[0].strip("# "))
        else:
            await ctx.reply("Couldn't understand command. Try `?help missing`")
            return

        missing_ids = [user_id for user_id in self.db.get_all_players() if user_id not in self.db.get_players_by_puzzle_id(puzzle_id)]
        if len(missing_ids) == 0:
            await ctx.reply(f"All tracked players have submitted Puzzle #{puzzle_id}!")
        else:
            await ctx.reply("The following players are missing Puzzle #{}: <@{}>".format(puzzle_id, '>, <@'.join(missing_ids)))

    async def get_entries(self, ctx: commands.Context, *args: str) -> None:
        if len(args) == 0:
            user_id = str(ctx.author.id)
        elif len(args) == 1 and self.utils.is_user(args[0]):
            user_id = args[0].strip("<@!> ")
        else:
            await ctx.reply("Couldn't understand command. Try `?help entries`.")
            return

        if user_id in self.db.get_all_players():
            found_puzzles = [str(p_id) for p_id in self.db.get_puzzles_by_player(user_id)]
            if len(found_puzzles) == 0:
                await ctx.reply(f"Couldn't find any recorded entries for <@{user_id}>.")
            elif len(found_puzzles) < 50:
                await ctx.reply(f"{len(found_puzzles)} entries found:\n#{', #'.join(found_puzzles)}\nUse `?view <puzzle #>` to see details of a submission.")
            else:
                await ctx.reply(f"{len(found_puzzles)} entries found, too many to display. First 10 and last 10:\n#{', #'.join(found_puzzles[:10])} ... #{', #'.join(found_puzzles[-10:])}\nUse `?view <puzzle #>` to see details of a submission.")
        else:
            await ctx.reply(f"Couldn't find any recorded entries for <@{user_id}>.")

    async def get_entry(self, ctx: commands.Context, *args: str) -> None:
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

        if user_id in self.db.get_all_players():
            user_puzzles: list[StrandsPuzzleEntry] = self.db.get_entries_by_player(user_id)
            df = pd.DataFrame(columns=['User', 'Puzzle', 'Hints'])
            for i, puzzle_id in enumerate(puzzle_ids):
                found_match = False
                for entry in user_puzzles:
                    if entry.puzzle_id == puzzle_id:
                        df.loc[i] = [
                            self.utils.get_nickname(user_id),
                            f"#{puzzle_id}",
                            f"{entry.hints}",
                        ]
                        found_match = True
                        break
                if not found_match:
                    df.loc[i] = [
                        self.utils.get_nickname(user_id),
                        f"#{puzzle_id}",
                        "?",
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

    async def get_stats(self, ctx: commands.Context, *args: str) -> None:
        missing_users_str = None
        if len(args) == 0:
            user_ids = [str(ctx.author.id)]
        else:
            user_ids = []
            unknown_ids = []
            for arg in args:
                if self.utils.is_user(arg):
                    user_id = arg.strip("<@!> ")
                    if user_id in self.db.get_all_players():
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

        df = pd.DataFrame(columns=['User', 'Avg Hints', '🧩', '🚫'])
        for i, user_id in enumerate(user_ids):
            puzzle_list = self.db.get_puzzles_by_player(user_id)
            player_stats = StrandsPlayerStats(user_id, puzzle_list, self.db)
            df.loc[i] = [
                self.utils.get_nickname(user_id),
                f"{player_stats.raw_mean:.4f}",
                len(puzzle_list),
                len(self.db.get_all_puzzles()) - len(puzzle_list),
            ]

        stats_img = self.utils.get_image_from_df(df)

        hist_img = None
        if len(user_ids) < 5:
            valid_hints = ['0', '1', '2', '3', '4', '5', '6', '7']
            plt.rcParams.update({'font.size': 20})

            df = pd.DataFrame(columns=['Player', 'Hints', 'Count'])
            for i, user_id in enumerate(user_ids):
                hint_counts = [0] * len(valid_hints)
                entries: list[StrandsPuzzleEntry] = self.db.get_entries_by_player(user_id)
                for hints in [entry.hints for entry in entries]:
                    hint_counts[hints] += 1
                for j in range(0, len(valid_hints)):
                    df.loc[i*len(valid_hints) + j] = [
                        self.utils.remove_emojis(self.utils.get_nickname(user_id)),
                        valid_hints[j],
                        hint_counts[j]
                    ]
            g = sns.catplot(x='Hints', y='Count', hue='Player', data=df, kind='bar')
            for ax in g.axes.ravel():
                for c in ax.containers:
                    labels = ['%d' % v.get_height() for v in c]
                    ax.bar_label(c, labels=labels, label_type='edge', fontsize=15)
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
    #   OWNER METHODS    #
    ######################

    async def remove_entry(self, ctx: commands.Context, *args: str) -> None:
        if len(args) == 1 and self.utils.is_user(args[0]):
            user_id = args[0].strip("<@!> ")
            puzzle_id = self.db.get_puzzle_by_date(self.utils.get_todays_date())
        elif len(args) == 1 and re.match(r"^[#]?\d+$", args[0]):
            user_id = str(ctx.author.id)
            puzzle_id = int(args[0].strip("# "))
        elif len(args) == 2 and self.utils.is_user(args[0]) and re.match(r"^[#]?\d+$", args[1]):
            user_id = args[0].strip("<@!> ")
            puzzle_id = int(args[1].strip("# "))
        else:
            await ctx.reply("Could not understand command. Try `?remove <user> <puzzle #>`.")
            return

        if user_id in self.db.get_all_players() and puzzle_id in self.db.get_all_puzzles():
            if self.db.remove_entry(user_id, puzzle_id):
                await ctx.message.add_reaction('✅')
            else:
                await ctx.message.add_reaction('❌')
        else:
            await ctx.reply(f"Could not find entry for Puzzle #{puzzle_id} for user <@{user_id}>.")

    async def add_score(self, ctx: commands.Context, *args: str) -> None:
        if args is not None and len(args) >= 3:
            if self.utils.is_user(args[0]):
                user_id = args[0].strip("<>@! ")
                title = f"{args[1]} {args[2]}"
                content = '\n'.join(args[3:])
            else:
                user_id = str(ctx.author.id)
                title = f"{args[0]} {args[1]}"
                content = '\n'.join(args[2:])
            if self.utils.is_strands_submission(title):
                self.db.add_entry(user_id, title, content)
                await ctx.message.add_reaction('✅')
        else:
            await ctx.reply("To manually add a Strands score, please use `?add <user> <Strands output>` (specifying a user is optional).")
