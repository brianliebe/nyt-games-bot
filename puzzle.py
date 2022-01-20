import statistics as stats

class PuzzleEntry():
    def __init__(self, puzzle_num, user_id, score, green, yellow, other) -> None:
        self.puzzle_num = puzzle_num
        self.user_id = user_id
        self.score = score
        self.green = green
        self.yellow = yellow
        self.other = other

class PuzzlePlayer():
    def __init__(self, user_id) -> None:
        self.user_id = user_id
        self.entries = {}
        # stats
        self.rank = None
        self.raw_mean = None
        self.adj_mean = None
        self.avg_green = None
        self.avg_yellow = None
        self.avg_other = None
        self.matching_puzzles_count = None
    
    def add(self, puzzle_entry: PuzzleEntry) -> None:
        self.entries[puzzle_entry.puzzle_num] = puzzle_entry

    def get_entry(self, puzzle_num):
        return self.entries[puzzle_num] if puzzle_num in self.get_puzzles() else None
    
    def refresh_stats(self, puzzles):
        missed_games = len([p for p in puzzles if p not in self.get_puzzles()])
        self.raw_mean = stats.mean([e.score for e in self.entries.values() if e.puzzle_num in puzzles])
        self.adj_mean = stats.mean([e.score for e in self.entries.values() if e.puzzle_num in puzzles] + ([7] * missed_games))
        self.avg_green = stats.mean([e.green for e in self.entries.values() if e.puzzle_num in puzzles])
        self.avg_yellow = stats.mean([e.yellow for e in self.entries.values() if e.puzzle_num in puzzles])
        self.avg_other = stats.mean([e.other for e in self.entries.values() if e.puzzle_num in puzzles])
        self.matching_puzzles_count = len(puzzles) - missed_games

    def get_avgs(self):
        return self.raw_mean, self.adj_mean, self.avg_green, self.avg_yellow, self.avg_other

    def get_puzzles(self):
        return self.entries.keys()

class Puzzle():
    def __init__(self, puzzle_num, entry: PuzzleEntry = None) -> None:
        self.number = puzzle_num
        self.entries = {}
        if entry is not None:
            self.add(entry)

    def add(self, puzzle_entry):
        self.entries[puzzle_entry.user_id] = puzzle_entry 

    def get_users(self):
        return self.entries.keys()