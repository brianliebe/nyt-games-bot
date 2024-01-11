import statistics as stats
from models.wordle_entry import WordlePuzzleEntry
from utils.wordle_db import WordleDatabaseHandler

class WordlePlayerStats():
    def __init__(self, user_id: str, puzzle_list: list[int], db: WordleDatabaseHandler) -> None:
        self.user_id = user_id

        player_puzzles = db.get_puzzles_by_player(self.user_id)
        player_entries: list[WordlePuzzleEntry] = db.get_entries_by_player(self.user_id, puzzle_list)

        self.missed_games = len([p for p in puzzle_list if p not in player_puzzles])

        if len(player_entries) > 0:
            self.raw_mean = stats.mean([e.score for e in player_entries])
            self.adj_mean = stats.mean([e.score for e in player_entries] + ([7] * self.missed_games))
            self.avg_green = stats.mean([e.green for e in player_entries])
            self.avg_yellow = stats.mean([e.yellow for e in player_entries])
            self.avg_other = stats.mean([e.other for e in player_entries])
        else:
            self.raw_mean = 0
            self.adj_mean = 0
            self.avg_green = 0
            self.avg_yellow = 0
            self.avg_other = 0
        self.rank = -1

    def get_stat_list(self) -> list[float, float, float, float, float]:
        return [self.raw_mean, self.adj_mean, self.avg_green, self.avg_yellow, self.avg_other]
