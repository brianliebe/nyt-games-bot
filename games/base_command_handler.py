from discord.ext import commands
from typing import Protocol
from data.base_data_handler import BaseDatabaseHandler
from utils.bot_utilities import BotUtilities

class BaseCommandHandler(Protocol):
    MAX_DATAFRAME_ROWS: int = 10

    db: BaseDatabaseHandler
    utils: BotUtilities

    def __init__(self, utils: BotUtilities, db: BaseDatabaseHandler) -> None:
        self.utils = utils
        self.db = db

    def connect(self) -> None:
        self.db.connect()

    ######################
    #   MEMBER METHODS   #
    ######################

    def add_entry(self, user_id: str, title: str, puzzle: str) -> bool:
        return self.db.add_entry(user_id, title, puzzle)

    async def get_ranks(self, ctx: commands.Context, *args: str) -> None:
        pass

    async def get_missing(self, ctx: commands.Context, *args: str) -> None:
        pass

    async def get_entries(self, ctx: commands.Context, *args: str) -> None:
        pass

    async def get_entry(self, ctx: commands.Context, *args: str) -> None:
        pass

    async def get_stats(self, ctx: commands.Context, *args: str) -> None:
        pass

    ######################
    #   OWNER METHODS    #
    ######################

    async def remove_entry(self, ctx: commands.Context, *args: str) -> None:
        pass

    async def add_score(self, ctx: commands.Context, *args: str) -> None:
        pass
