from discord.ext import commands
from games.base_command_handler import BaseCommandHandler
from utils.bot_utilities import BotUtilities, NYTGame

class OwnerCog(commands.Cog, name="Owner-Only Commands"):
    # class variables
    bot: commands.Bot
    utils: BotUtilities

    # games
    connections: BaseCommandHandler
    strands: BaseCommandHandler
    wordle: BaseCommandHandler

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.utils = self.bot.utils
        self.connections = self.bot.connections
        self.strands = self.bot.strands
        self.wordle = self.bot.wordle

    #####################
    #   COMMAND SETUP   #
    #####################

    @commands.is_owner()
    @commands.command(name="remove", help="Removes one puzzle entry for a player")
    async def remove_entry(self, ctx: commands.Context, *args: str) -> None:
        match self.utils.get_game_from_channel(ctx.message):
            case NYTGame.CONNECTIONS:
                await self.connections.remove_entry(ctx, *args)
            case NYTGame.STRANDS:
                await self.strands.remove_entry(ctx, *args)
            case NYTGame.WORDLE:
                await self.wordle.remove_entry(ctx, *args)

    @commands.is_owner()
    @commands.command(name='add', help='Manually adds a puzzle entry for a player')
    async def add_score(self, ctx: commands.Context, *args: str) -> None:
        match self.utils.get_game_from_channel(ctx.message):
            case NYTGame.CONNECTIONS:
                await self.connections.add_score(ctx, *args)
            case NYTGame.STRANDS:
                await self.strands.add_score(ctx, *args)
            case NYTGame.WORDLE:
                await self.wordle.add_score(ctx, *args)

async def setup(bot: commands.Bot):
    await bot.add_cog(OwnerCog(bot))
