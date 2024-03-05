import discord, traceback
from discord.ext import commands
from games.base_command_handler import BaseCommandHandler
from utils.bot_utilities import BotUtilities, NYTGame
from utils.help_handler import HelpMenuHandler

class MembersCog(commands.Cog, name="Normal Members Commands"):
    # class variables
    bot: commands.Bot
    utils: BotUtilities
    help_menu: HelpMenuHandler

    # games
    connections: BaseCommandHandler
    strands: BaseCommandHandler
    wordle: BaseCommandHandler

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.utils = self.bot.utils
        self.help_menu = self.bot.help_menu
        self.build_help_menu()

        self.connections = self.bot.connections
        self.strands = self.bot.strands
        self.wordle = self.bot.wordle

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
                    self.wordle.add_entry(user_id, first_line, content)
                    await message.add_reaction('✅')
                elif 'Connections' in first_line and self.utils.is_connections_submission(first_two_lines):
                    content = '\n'.join(message.content.splitlines()[2:])
                    self.connections.add_entry(user_id, first_two_lines, content)
                    await message.add_reaction('✅')
                elif 'Strands' in first_line and self.utils.is_strands_submission(first_two_lines):
                    content = '\n'.join(message.content.splitlines()[2:])
                    self.strands.add_entry(user_id, first_two_lines, content)
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
                case NYTGame.CONNECTIONS:
                    await self.connections.get_ranks(ctx, *args)
                case NYTGame.STRANDS:
                    await self.strands.get_ranks(ctx, *args)
                case NYTGame.WORDLE:
                    await self.wordle.get_ranks(ctx, *args)
        except Exception as e:
            print(f"Caught exception: {e}")
            traceback.print_exception(e)

    @commands.guild_only()
    @commands.command(name='missing', help='Show all players missing an entry for a puzzle')
    async def get_missing(self, ctx: commands.Context, *args: str) -> None:
        try:
            match self.utils.get_game_from_channel(ctx.message):
                case NYTGame.CONNECTIONS:
                    await self.connections.get_missing(ctx, *args)
                case NYTGame.STRANDS:
                    await self.strands.get_missing(ctx, *args)
                case NYTGame.WORDLE:
                    await self.wordle.get_missing(ctx, *args)
        except Exception as e:
            print(f"Caught exception: {e}")
            traceback.print_exception(e)

    @commands.guild_only()
    @commands.command(name='entries', help='Show all recorded entries for a player')
    async def get_entries(self, ctx: commands.Context, *args: str) -> None:
        try:
            match self.utils.get_game_from_channel(ctx.message):
                case NYTGame.CONNECTIONS:
                    await self.connections.get_entries(ctx, *args)
                case NYTGame.STRANDS:
                    await self.strands.get_entries(ctx, *args)
                case NYTGame.WORDLE:
                    await self.wordle.get_entries(ctx, *args)
        except Exception as e:
            print(f"Caught exception: {e}")
            traceback.print_exception(e)

    @commands.guild_only()
    @commands.command(name="view", help="Show player's entry for a given puzzle number")
    async def get_entry(self, ctx: commands.Context, *args: str) -> None:
        try:
            match self.utils.get_game_from_channel(ctx.message):
                case NYTGame.CONNECTIONS:
                    await self.connections.get_entry(ctx, *args)
                case NYTGame.STRANDS:
                    await self.strands.get_entry(ctx, *args)
                case NYTGame.WORDLE:
                    await self.wordle.get_entry(ctx, *args)
        except Exception as e:
            print(f"Caught exception: {e}")
            traceback.print_exception(e)

    @commands.guild_only()
    @commands.command(name="stats", help="Show basic stats for a player")
    async def get_stats(self, ctx: commands.Context, *args: str) -> None:
        try:
            match self.utils.get_game_from_channel(ctx.message):
                case NYTGame.CONNECTIONS:
                    await self.connections.get_stats(ctx, *args)
                case NYTGame.STRANDS:
                    await self.strands.get_stats(ctx, *args)
                case NYTGame.WORDLE:
                    await self.wordle.get_stats(ctx, *args)
        except Exception as e:
            print(f"Caught exception: {e}")
            traceback.print_exception(e)

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
