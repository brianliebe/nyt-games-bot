import re
from discord.ext import commands
from utils.bot_utilities import BotUtilities, NYTGame
from utils.connections_db import ConnectionsDatabaseHandler
from utils.wordle_db import WordleDatabaseHandler

class OwnerCog(commands.Cog, name="Owner-Only Commands"):

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.utils: BotUtilities = self.bot.utils
        self.wordle_db: WordleDatabaseHandler = self.bot.wordle_db
        self.conns_db: ConnectionsDatabaseHandler = self.bot.conns_db

    #####################
    #   COMMAND SETUP   #
    #####################

    @commands.is_owner()
    @commands.command(name="remove", help="Removes one puzzle entry for a player")
    async def remove_entry(self, ctx: commands.Context, *args: str) -> None:
        match self.utils.get_game_from_channel(ctx.message):
            case NYTGame.WORDLE:
                await self.remove_entry_wordle(ctx, args)
            case NYTGame.CONNECTIONS:
                await self.remove_entry_connections(ctx, args)
            case NYTGame.UNKNOWN:
                print(f"[REMOVE] Unsure of game mode, skipping response to: '{args}'")


    @commands.is_owner()
    @commands.command(name='add', help='Manually adds a puzzle entry for a player')
    async def add_score(self, ctx: commands.Context, *args: str) -> None:
        match self.utils.get_game_from_channel(ctx.message):
            case NYTGame.WORDLE:
                await self.add_score_wordle(ctx, args)
            case NYTGame.CONNECTIONS:
                await self.add_score_connections(ctx, args)
            case NYTGame.UNKNOWN:
                print(f"[ADD] Unsure of game mode, skipping response to: '{args}'")

    ######################
    #   WORDLE METHODS   #
    ######################

    async def remove_entry_wordle(self, ctx: commands.Context, *args: str) -> None:
        if len(args) == 1 and self.utils.is_user(args[0]):
            user_id = args[0].strip("<@!> ")
            puzzle_id = self.wordle_db.get_puzzle_by_date(self.utils.get_todays_date())
        elif len(args) == 1 and re.match(r"^[#]?\d+$", args[0]):
            user_id = str(ctx.author.id)
            puzzle_id = int(args[0].strip("# "))
        elif len(args) == 2 and self.utils.is_user(args[0]) and re.match(r"^[#]?\d+$", args[1]):
            user_id = args[0].strip("<@!> ")
            puzzle_id = int(args[1].strip("# "))
        else:
            await ctx.reply("Could not understand command. Try `?remove <user> <puzzle #>`.")
            return

        if user_id in self.wordle_db.get_all_players() and puzzle_id in self.wordle_db.get_all_puzzles():
            if self.wordle_db.remove_entry(user_id, puzzle_id):
                await ctx.message.add_reaction('✅')
            else:
                print("ERROR: Puzzle entry removal failed!")
                await ctx.message.add_reaction('❌')
        else:
            await ctx.reply(f"Could not find entry for Puzzle #{puzzle_id} for user <@{user_id}>.")

    async def add_score_wordle(self, ctx: commands.Context, *args: str) -> None:
        if args is not None and len(args) >= 4:
            if self.utils.is_user(args[0]):
                user_id = args[0].strip("<>@! ")
                title = ' '.join(args[1:4])
                content = '\n'.join(args[4:])
            else:
                user_id = str(ctx.author.id)
                title = ' '.join(args[0:3])
                content = '\n'.join(args[3:])
            if self.utils.is_wordle_submission(title):
                self.wordle_db.add_entry(user_id, title, content)
                await ctx.message.add_reaction('✅')
        else:
            await ctx.reply("To manually add a Wordle score, please use `?add <user> <Wordle output>` (specifying a user is optional).")

    #######################
    # CONNECTIONS METHODS #
    #######################

    async def remove_entry_connections(self, ctx: commands.Context, *args: str) -> None:
        if len(args) == 1 and self.utils.is_user(args[0]):
            user_id = args[0].strip("<@!> ")
            puzzle_id = self.conns_db.get_puzzle_by_date(self.utils.get_todays_date())
        elif len(args) == 1 and re.match(r"^[#]?\d+$", args[0]):
            user_id = str(ctx.author.id)
            puzzle_id = int(args[0].strip("# "))
        elif len(args) == 2 and self.utils.is_user(args[0]) and re.match(r"^[#]?\d+$", args[1]):
            user_id = args[0].strip("<@!> ")
            puzzle_id = int(args[1].strip("# "))
        else:
            await ctx.reply("Could not understand command. Try `?remove <user> <puzzle #>`.")
            return

        if user_id in self.conns_db.get_all_players() and puzzle_id in self.conns_db.get_all_puzzles():
            if self.conns_db.remove_entry(user_id, puzzle_id):
                await ctx.message.add_reaction('✅')
            else:
                print("ERROR: Puzzle entry removal failed!")
                await ctx.message.add_reaction('❌')
        else:
            await ctx.reply(f"Could not find entry for Puzzle #{puzzle_id} for user <@{user_id}>.")

    async def add_score_connections(self, ctx: commands.Context, *args: str) -> None:
        if args is not None and len(args) >= 4:
            if self.utils.is_user(args[0]):
                user_id = args[0].strip("<>@! ")
                title = f"{args[1]}\n{args[2]} {args[3]}"
                content = '\n'.join(args[4:])
            else:
                user_id = str(ctx.author.id)
                title = f"{args[0]}\n{args[1]} {args[2]}"
                content = '\n'.join(args[3:])
            if self.utils.is_connections_submission(title):
                self.conns_db.add_entry(user_id, title, content)
                await ctx.message.add_reaction('✅')
        else:
            await ctx.reply("To manually add a Connections score, please use `?add <user> <Connections output>` (specifying a user is optional).")

async def setup(bot: commands.Bot):
    await bot.add_cog(OwnerCog(bot))
