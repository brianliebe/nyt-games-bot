import re
from discord.ext import commands

class OwnerCog(commands.Cog, name="Owner-Only Commands"):

    def __init__(self, bot):
        self.bot = bot
        
    @commands.is_owner()
    @commands.command(name='save', help='Saves all data to the database (done automatically)')
    async def manual_save(self, ctx, *args):
        self.bot.utils.save()
        await ctx.message.add_reaction('✅')

    @commands.is_owner()
    @commands.command(name="remove", help="Removes one puzzle entry for a player")
    async def remove_entry(self, ctx, *args):
        if len(args) == 1 and self.bot.utils.is_user(args[0]):
            query_id = int(args[0].strip("<@!> "))
            puzzle_num = self.bot.utils.get_todays_puzzle()
        elif len(args) == 1 and re.match(r"^\d+$", args[0]):
            query_id = ctx.author.id
            puzzle_num = args[0].strip()
        elif len(args) == 2 and self.bot.utils.is_user(args[0]) and re.match(r"^\d+$", args[1]):
            query_id = int(args[0].strip("<@!> "))
            puzzle_num = args[1].strip()
        else:
            await ctx.reply("Could not understand command. Try `?remove <user> <puzzle #>`.")
            return
        
        if query_id in self.bot.players.keys() and puzzle_num in self.bot.puzzles.keys():
            puzzle = self.bot.puzzles[puzzle_num]
            puzzle_player = self.bot.players[query_id]
            if puzzle.remove_entry(query_id):
                if puzzle_player.remove_entry(puzzle_num):
                    self.bot.utils.save()
                    await ctx.message.add_reaction('✅')
                    return
                else:
                    print("ERROR: Player entry removal failed!")
            else:
                print("ERROR: Puzzle entry removal failed!")
            await ctx.message.add_reaction('❌')
        else:
            await ctx.reply(f"Could not find entry for Puzzle #{puzzle_num} for user <@{query_id}>.")

    @commands.is_owner()
    @commands.command(name='add', help='Manually adds a puzzle entry for a player')
    async def add_score(self, ctx, *args):
        if args is not None and len(args) >= 4:
            if self.bot.utils.is_user(args[0]):
                user_id = int(args[0].strip("<>@! "))
                title = ' '.join(args[1:4])
                content = '\n'.join(args[4:])
            else:
                user_id = int(ctx.author.id)
                title = ' '.join(args[0:3])
                content = '\n'.join(args[3:])
            if self.bot.utils.is_wordle_submission(title):
                self.bot.utils.add_entry(user_id, title, content)
                await ctx.message.add_reaction('✅')
        else:
            await ctx.reply("To manually add a Wordle score, please use `?add <user> <Wordle output>` (specifying a user is optional).")


def setup(bot):
    bot.add_cog(OwnerCog(bot))