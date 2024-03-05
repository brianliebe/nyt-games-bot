from discord.ext import commands
from games.base_command_handler import BaseCommandHandler
from utils.bot_utilities import BotUtilities, NYTGame

class OwnerCog(commands.Cog, name="Owner-Only Commands"):
    bot: commands.Bot
    utils: BotUtilities
    connections: BaseCommandHandler
    wordle: BaseCommandHandler

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.utils = self.bot.utils
        self.wordle = self.bot.wordle
        self.connections = self.bot.connections

    #####################
    #   COMMAND SETUP   #
    #####################

    @commands.is_owner()
    @commands.command(name="remove", help="Removes one puzzle entry for a player")
    async def remove_entry(self, ctx: commands.Context, *args: str) -> None:
        match self.utils.get_game_from_channel(ctx.message):
            case NYTGame.WORDLE:
                await self.wordle.remove_entry(ctx, *args)
            case NYTGame.CONNECTIONS:
                await self.connections.remove_entry(ctx, *args)


    @commands.is_owner()
    @commands.command(name='add', help='Manually adds a puzzle entry for a player')
    async def add_score(self, ctx: commands.Context, *args: str) -> None:
        match self.utils.get_game_from_channel(ctx.message):
            case NYTGame.WORDLE:
                await self.wordle.add_score(ctx, *args)
            case NYTGame.CONNECTIONS:
                await self.connections.add_score(ctx, *args)

async def setup(bot: commands.Bot):
    await bot.add_cog(OwnerCog(bot))
