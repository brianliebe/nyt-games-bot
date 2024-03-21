import statistics as stats
from data.base_data_handler import BaseDatabaseHandler
from models.base_game import BasePlayerStats, BasePuzzleEntry

class StrandsPlayerStats(BasePlayerStats):
    # strands-specific stats
    avg_spangram_index: float

    def __init__(self, user_id: str, puzzle_list: list[int], db: BaseDatabaseHandler) -> None:
        self.user_id = user_id

        player_puzzles = db.get_puzzles_by_player(self.user_id)
        player_entries: list[StrandsPuzzleEntry] = db.get_entries_by_player(self.user_id, puzzle_list)

        self.missed_games = len([p for p in puzzle_list if p not in player_puzzles])

        if len(player_entries) > 0:
            self.raw_mean = stats.mean([e.hints for e in player_entries])
            self.adj_mean = stats.mean([e.hints for e in player_entries] + ([6] * self.missed_games))
            self.avg_spangram_index = stats.mean([e.spangram_index for e in player_entries if e.spangram_index > 0])
        else:
            self.raw_mean = 0
            self.adj_mean = 0
            self.avg_spangram_index = 0
        self.rank = -1

    def get_stat_list(self) -> tuple[float, float, float]:
        return self.raw_mean, self.adj_mean, self.avg_spangram_index

class StrandsPuzzleEntry(BasePuzzleEntry):
    # strands-specific details
    hints: int
    spangram_index: int
    puzzle_str: str

    def __init__(self, puzzle_id: int, user_id: str, hints: int, puzzle_str: str) -> None:
        self.puzzle_id = puzzle_id
        self.user_id = user_id
        self.hints = hints
        self.puzzle_str = puzzle_str
        self.spangram_index = self.__get_spangram_index(puzzle_str)

    def __get_spangram_index(self, puzzle_str: str) -> int:
        for index, item in enumerate(puzzle_str.strip().replace('\n', '')):
            if item == '🟡':
                return index + 1
        return -1
