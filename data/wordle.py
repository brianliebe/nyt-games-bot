import os, re
from datetime import date
from data.base_data_handler import BaseDatabaseHandler
from models.wordle import WordlePuzzleEntry
from utils.bot_utilities import BotUtilities

class WordleDatabaseHandler(BaseDatabaseHandler):
    def __init__(self, utils: BotUtilities) -> None:
        # init
        super().__init__(utils)

        # puzzles
        self._arbitrary_date = date(2022, 1, 10)
        self._arbitrary_date_puzzle = 205

        # mysql connection
        self._mysql_host = os.environ.get('WORDLE_MYSQL_HOST', None)
        self._mysql_user = os.environ.get('WORDLE_MYSQL_USER', "root")
        self._mysql_pass = os.environ.get('WORDLE_MYSQL_PASS', "")
        self._mysql_db_name = os.environ.get('WORDLE_MYSQL_DB_NAME', "wordle")

    ####################
    #  PUZZLE METHODS  #
    ####################

    def add_entry(self, user_id: str, title: str, puzzle: str) -> bool:
        if 'X/6' in title:
            reg_match = re.search(r'\d{1,3}(,\d{3})*', title)
            if reg_match:
                puzzle_id = reg_match.group(0).replace(',', '')
                score = 7
            else:
                return False
        else:
            reg_match = re.search(r'\d{1,3}(,\d{3})*', title)
            if reg_match:
                puzzle_id = reg_match.group(0).replace(',', '')
                reg_match = re.search(r'(\d)\/(\d)', title)
                if reg_match:
                    score = reg_match.group(1)
                else:
                    return False
            else:
                return False

        puzzle_id = int(puzzle_id)
        score = int(score)

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
                f"update entries set score = {score}, green = {total_green}, yellow = {total_yellow}, other = {total_other} "
                    + f"where user_id = '{user_id}' and puzzle_id = '{puzzle_id}'"
            )
            self._db.commit()
            return True
        else:
            self._cur.execute(
                "insert into entries (puzzle_id, user_id, score, green, yellow, other) "
                    + f"values ({puzzle_id}, {user_id}, {score}, {total_green}, {total_yellow}, {total_other})"
            )
            self._db.commit()
            return self._cur.rowcount > 0

    ####################
    #  PLAYER METHODS  #
    ####################

    def get_entries_by_player(self, user_id: str, puzzle_list: list[int] = []) -> list[WordlePuzzleEntry]:
        if not self._db.is_connected():
            self.connect()
        if not puzzle_list or len(puzzle_list) == 0:
            query = f"select puzzle_id, score, green, yellow, other from entries where user_id = {user_id}"
        else:
            puzzle_list_str = ','.join([str(p_id) for p_id in puzzle_list])
            query = f"select puzzle_id, score, green, yellow, other from entries where user_id = {user_id} and puzzle_id in ({puzzle_list_str})"
        self._cur.execute(query)
        entries: list[WordlePuzzleEntry] = []
        for row in self._cur.fetchall():
            entries.append(WordlePuzzleEntry(row[0], user_id, row[1], row[2], row[3], row[4]))
        return entries
