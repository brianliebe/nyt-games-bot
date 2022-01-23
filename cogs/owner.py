import discord, re, io, json
import utilities
from discord.ext import commands

class OwnerCog(commands.Cog, name="Owner-Only Commands"):

    def __init__(self, bot):
        self.bot = bot
        
    @commands.is_owner()
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

    @commands.is_owner()
    @commands.command(name="remove", help="Removes one puzzle entry for a player")
    async def remove_entry(self, ctx, *args):
        if len(args) == 1 and utilities.is_user(args[0]):
            query_id = int(args[0].strip("<@!> "))
            puzzle_num = utilities.get_todays_puzzle()
        elif len(args) == 1 and re.match(r"^\d+$", args[0]):
            query_id = ctx.author.id
            puzzle_num = args[0].strip()
        elif len(args) == 2 and utilities.is_user(args[0]) and re.match(r"^\d+$", args[1]):
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
                    if self.save():
                        await ctx.message.add_reaction('✅')
                        return
                    else:
                        print("ERROR: Saving failed!")
                else:
                    print("ERROR: Player entry removal failed!")
            else:
                print("ERROR: Puzzle entry removal failed!")
            await ctx.message.add_reaction('❌')
        else:
            await ctx.reply(f"Could not find entry for Puzzle #{puzzle_num} for user <@{query_id}>.")


def setup(bot):
    bot.add_cog(OwnerCog(bot))