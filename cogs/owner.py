import re
from discord.ext import commands
from utils.bot_utilities import BotUtilities
from utils.database_handler import DatabaseHandler

class OwnerCog(commands.Cog, name="Owner-Only Commands"):

    def __init__(self, bot):
        self.bot = bot
        self.utils: BotUtilities = self.bot.utils
        self.db: DatabaseHandler = self.bot.db

    @commands.is_owner()
    @commands.command(name="remove", help="Removes one puzzle entry for a player")
    async def remove_entry(self, ctx, *args):
        if len(args) == 1 and self.utils.is_user(args[0]):
            user_id = args[0].strip("<@!> ")
            puzzle_id = self.puzzles.get_puzzle_by_date(self.utils.get_todays_date())
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
            # puzzle = self.puzzles.get(puzzle_id)
            # player = self.players.get(query_id)
            if self.db.remove_entry(user_id, puzzle_id):
                await ctx.message.add_reaction('✅')
            else:
                print("ERROR: Puzzle entry removal failed!")
                await ctx.message.add_reaction('❌')
        else:
            await ctx.reply(f"Could not find entry for Puzzle #{puzzle_id} for user <@{user_id}>.")

    @commands.is_owner()
    @commands.command(name='add', help='Manually adds a puzzle entry for a player')
    async def add_score(self, ctx, *args):
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
                self.db.add_entry(user_id, title, content)
                await ctx.message.add_reaction('✅')
        else:
            await ctx.reply("To manually add a Wordle score, please use `?add <user> <Wordle output>` (specifying a user is optional).")


def setup(bot):
    bot.add_cog(OwnerCog(bot))
