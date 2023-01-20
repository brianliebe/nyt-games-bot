import re, os
import mysql.connector
from datetime import date
from utils.puzzle_entry import PuzzleEntry
from utils.bot_utilities import BotUtilities

class DatabaseHandler():
    def __init__(self, utils: BotUtilities) -> None:
        # init
        self._utils = utils
        self._db = None
        self._cur = None

        # puzzles
        self._arbitrary_date = date(2022, 1, 10)
        self._arbitrary_date_puzzle = 205

        # mysql connection
        self._mysql_host = os.environ.get('WORDLE_MYSQL_HOST', None)
        self._mysql_user = os.environ.get('WORDLE_MYSQL_USER', "root")
        self._mysql_pass = os.environ.get('WORDLE_MYSQL_PASS', "")
        self._mysql_db_name = os.environ.get('WORDLE_MYSQL_USER', "wordle")

    def add_entry(self, user_id: str, title: str, puzzle: str) -> bool:
        if 'X/6' in title:
            puzzle_id, _ = re.findall(r'\d+', title)
            score = 7
        else:
            puzzle_id, score, _ = re.findall(r'\d+', title)
            score = int(score)

        puzzle_id = int(puzzle_id)

        total_green = puzzle.count('🟩')
        total_yellow = puzzle.count('🟨')
        total_other = puzzle.count('⬜') + puzzle.count('⬛')

        if not self._db.is_connected():
            self.connect()

        if not self.user_exists(user_id):
            user_name = self._utils.get_nickname(user_id)
            self._cur.execute("insert into users (user_id, name) values ('{}', '{}')".format(user_id, user_name))

        if self.entry_exists(user_id, puzzle_id):
            self._cur.execute(
                f"update entries set score = {score}, green = {green}, yellow = {yellow}, other = {other} "
                    + f"where user_id = '{user_id}' and puzzle_id = '{puzzle_id}'"
            )
        else:
            self._cur.execute(
                "insert into entries (puzzle_id, user_id, score, green, yellow, other) "
                    + f"values ({puzzle_id}, {user_id}, {score}, {total_green}, {total_yellow}, {total_other})"
            )
        self._db.commit()
        return self._cur.rowcount > 0

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
            raise Exception("Environment variable WORDLE_MYSQL_HOST cannot be empty/null")

        self._db = mysql.connector.connect(
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

    def get_entries_by_player(self, user_id: str, puzzle_list: list[int]) -> list[PuzzleEntry]:
        if not self._db.is_connected():
            self.connect()
        if not puzzle_list or len(puzzle_list) == 0:
            query = f"select puzzle_id, score, green, yellow, other from entries where user_id = {user_id}"
        else:
            puzzle_list_str = ','.join([str(p_id) for p_id in puzzle_list])
            query = f"select puzzle_id, score, green, yellow, other from entries where user_id = {user_id} and puzzle_id in ({puzzle_list_str})"
        self._cur.execute(query)
        entries: list[PuzzleEntry] = []
        for row in self._cur.fetchall():
            entries.append(PuzzleEntry(row[0], user_id, row[1], row[2], row[3], row[4]))
        return entries

    def get_players_by_puzzle_id(self, puzzle_id: int) -> list[str]:
        if not self._db.is_connected():
            self.connect()
        self._cur.execute(f"select distinct user_id from entries where puzzle_id = {puzzle_id}")
        return [row[0] for row in self._cur.fetchall()]
