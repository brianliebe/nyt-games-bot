import statistics as stats
from models.connections_entry import ConnectionsPuzzleEntry
from utils.connections_db import ConnectionsDatabaseHandler

class ConnectionsPlayerStats():
    def __init__(self, user_id: str, puzzle_list: list[int], db: ConnectionsDatabaseHandler) -> None:
        self.user_id = user_id

        player_puzzles = db.get_puzzles_by_player(self.user_id)
        player_entries: list[ConnectionsPuzzleEntry] = db.get_entries_by_player(self.user_id, puzzle_list)

        self.missed_games = len([p for p in puzzle_list if p not in player_puzzles])

        if len(player_entries) > 0:
            self.raw_mean = stats.mean([e.score for e in player_entries])
            self.adj_mean = stats.mean([e.score for e in player_entries] + ([8] * self.missed_games))
        else:
            self.raw_mean = 0
            self.adj_mean = 0
        self.rank = -1

    def get_stat_list(self) -> tuple[float, float]:
        return self.raw_mean, self.adj_mean
