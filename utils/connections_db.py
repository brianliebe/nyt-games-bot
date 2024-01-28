import re, os
from datetime import date
from collections import Counter
from models.connections_entry import ConnectionsPuzzleEntry
from utils.bot_utilities import BotUtilities
from utils.db_handler import DatabaseHandler

class ConnectionsDatabaseHandler(DatabaseHandler):
    def __init__(self, utils: BotUtilities) -> None:
        # init
        super().__init__(utils)

        # puzzles
        self._arbitrary_date = date(2024, 1, 7)
        self._arbitrary_date_puzzle = 210

        # mysql connection
        self._mysql_host = os.environ.get('CONNECTIONS_MYSQL_HOST', None)
        self._mysql_user = os.environ.get('CONNECTIONS_MYSQL_USER', "root")
        self._mysql_pass = os.environ.get('CONNECTIONS_MYSQL_PASS', "")
        self._mysql_db_name = os.environ.get('CONNECTIONS_MYSQL_DB_NAME', "connections")

    ####################
    #  PUZZLE METHODS  #
    ####################

    def add_entry(self, user_id: str, title: str, puzzle: str) -> bool:
        puzzle_id_title = re.findall(r'\d+', title)
        score = self.__get_score_from_puzzle(puzzle)

        if puzzle_id_title:
            puzzle_id = int(puzzle_id_title[0])
        else:
            return

        if not self._db.is_connected():
            self.connect()

        if not self.user_exists(user_id):
            user_name = self._utils.get_nickname(user_id)
            self._cur.execute("insert into users (user_id, name) values ('{}', '{}')".format(user_id, user_name))

        if self.entry_exists(user_id, puzzle_id):
            self._cur.execute(
                f"update entries set score = {score}, puzzle_str = '{puzzle}' "
                    + f"where user_id = '{user_id}' and puzzle_id = '{puzzle_id}'"
            )
        else:
            self._cur.execute(
                "insert into entries (puzzle_id, user_id, score, puzzle_str) "
                    + f"values ({puzzle_id}, {user_id}, {score}, '{puzzle}')"
            )
        self._db.commit()
        return self._cur.rowcount > 0

    ####################
    #  PLAYER METHODS  #
    ####################

    def get_entries_by_player(self, user_id: str, puzzle_list: list[int] = []) -> list[ConnectionsPuzzleEntry]:
        if not self._db.is_connected():
            self.connect()
        if not puzzle_list or len(puzzle_list) == 0:
            query = f"select puzzle_id, score, puzzle_str from entries where user_id = {user_id}"
        else:
            puzzle_list_str = ','.join([str(p_id) for p_id in puzzle_list])
            query = f"select puzzle_id, score, puzzle_str from entries where user_id = {user_id} and puzzle_id in ({puzzle_list_str})"
        self._cur.execute(query)
        entries: list[ConnectionsPuzzleEntry] = []
        for row in self._cur.fetchall():
            entries.append(ConnectionsPuzzleEntry(row[0], user_id, row[1], row[2]))
        return entries

    ####################
    #  HELPER METHODS  #
    ####################

    def __get_score_from_puzzle(self, puzzle: str) -> int:
        puzzle_lines = puzzle.split('\n')
        if len(Counter(puzzle_lines[-1]).keys()) == 1:
            return len(puzzle_lines)
        else:
            return 7
