from datetime import date
from utils.bot_utilities import BotUtilities
from typing import Protocol
from mysql.connector import MySQLConnection, connect
from mysql.connector.cursor import MySQLCursor

class DatabaseHandler(Protocol):
    _utils: BotUtilities
    _db: MySQLConnection
    _cur: MySQLCursor
    _arbitrary_date: date
    _arbitrary_date_puzzle: int
    _mysql_host: str
    _mysql_user: str
    _mysql_pass: str
    _mysql_db_name: str

    def __init__(self, utils: BotUtilities) -> None:
        self._utils = utils
        self._db = None
        self._cur = None

    def remove_entry(self, user_id: str, puzzle_id: int) -> bool:
        if not self._db.is_connected():
            self.connect()
        self._cur.execute(f"delete from entries where user_id = {user_id} and puzzle_id = {puzzle_id}")
        self._db.commit()
        return self._cur.rowcount > 0

    def user_exists(self, user_id: str) -> bool:
        if not self._db.is_connected():
            self.connect()
        self._cur.execute(f"select * from users where user_id = {user_id}")
        return self._cur.rowcount > 0

    def entry_exists(self, user_id: str, puzzle_id: int) -> bool:
        if not self._db.is_connected():
            self.connect()
        self._cur.execute(f"select * from entries where user_id = {user_id} and puzzle_id = {puzzle_id}")
        return self._cur.rowcount > 0

    def connect(self) -> None:
        if not self._mysql_host:
            raise Exception("Environment variable for MySQL HOST cannot be empty/null")

        self._db = connect(
            host=self._mysql_host,
            user=self._mysql_user,
            password=self._mysql_pass,
            database=self._mysql_db_name
        )
        self._cur = self._db.cursor(buffered=True)

    ####################
    #  PUZZLE METHODS  #
    ####################

    def get_puzzle_by_date(self, query_date: date) -> int:
        return self._arbitrary_date_puzzle + (query_date - self._arbitrary_date).days

    def get_puzzles_by_week(self, query_date: date) -> list[int]:
        if self._utils.is_sunday(query_date):
            sunday_puzzle_id = self.get_puzzle_by_date(query_date)
            return list(range(sunday_puzzle_id, sunday_puzzle_id + 7))
        return []

    def get_all_puzzles(self) -> list[int]:
        if not self._db.is_connected():
            self.connect()
        self._cur.execute("select distinct puzzle_id from entries")
        return [row[0] for row in self._cur.fetchall()]

    ####################
    #  PLAYER METHODS  #
    ####################

    def get_all_players(self) -> list[str]:
        if not self._db.is_connected():
            self.connect()
        self._cur.execute("select distinct user_id from users")
        return [row[0] for row in self._cur.fetchall()]

    def get_puzzles_by_player(self, user_id) -> list[int]:
        if not self._db.is_connected():
            self.connect()
        self._cur.execute(f"select distinct puzzle_id from entries where user_id = {user_id}")
        return [row[0] for row in self._cur.fetchall()]

    def get_players_by_puzzle_id(self, puzzle_id: int) -> list[str]:
        if not self._db.is_connected():
            self.connect()
        self._cur.execute(f"select distinct user_id from entries where puzzle_id = {puzzle_id}")
        return [row[0] for row in self._cur.fetchall()]
