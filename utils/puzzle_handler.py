from datetime import date, timedelta
from utils.puzzle import Puzzle, PuzzleEntry
from utils.bot_utilities import BotUtilities

class PuzzleHandler():
    def __init__(self, utils: BotUtilities) -> None:
        self.utils = utils
        self._puzzles = {}
        self._arbitrary_date = date(2022, 1, 10)
        self._arbitrary_date_puzzle = 205

    def add(self, entry: PuzzleEntry) -> None:
        if entry.puzzle_id not in self._puzzles.keys():
            self._puzzles[entry.puzzle_id] = Puzzle(entry.puzzle_id)
        self._puzzles[entry.puzzle_id].add(entry)

    def get(self, puzzle_id: int) -> Puzzle:
        return self._puzzles[puzzle_id] if puzzle_id in self.get_ids() else None

    def get_ids(self) -> list[int]:
        return sorted(self._puzzles.keys())

    def get_puzzles_by_week(self, query_date: date) -> list[int]:
        if self.utils.is_sunday(query_date):
            sunday_puzzle_id = self.get_puzzle_by_date(query_date)
            return list(range(sunday_puzzle_id, sunday_puzzle_id + 7))
        else:
            return []

    def get_puzzle_by_date(self, query_date: date) -> int:
        return self._arbitrary_date_puzzle + (query_date - self._arbitrary_date).days

    def get_date_by_puzzle(self, puzzle_id) -> date:
        return self._arbitrary_date + timedelta(days=(puzzle_id - self._arbitrary_date_puzzle))

    def get_all_puzzles(self) -> list[int]:
        return sorted(self._puzzles.keys())
