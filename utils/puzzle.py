import statistics as stats

class PuzzleEntry():
    def __init__(self, puzzle_id, user_id, week, score, green, yellow, other) -> None:
        self.puzzle_id = puzzle_id
        self.user_id = user_id
        self.week = week
        self.score = score
        self.green = green
        self.yellow = yellow
        self.other = other

class PuzzlePlayer():
    def __init__(self, user_id) -> None:
        self.user_id = user_id
        self.entries = {}
        self.stats = {}
        self.rank = 0
    
    def add(self, puzzle_entry: PuzzleEntry) -> None:
        self.entries[puzzle_entry.puzzle_id] = puzzle_entry

    def get_entry(self, puzzle_id):
        return self.entries[puzzle_id] if puzzle_id in self.get_ids() else None

    def remove_entry(self, puzzle_id):
        if puzzle_id in self.get_ids():
            del self.entries[puzzle_id]
            return True
        return False

    def generate_stats(self, puzzles):
        self.rank = 0
        self.stats = {}
        self.stats['missed_games'] = len([p for p in puzzles if p not in self.get_ids()])
        self.stats['raw_mean'] = stats.mean([e.score for e in self.entries.values() if e.puzzle_id in puzzles])
        self.stats['adj_mean'] = stats.mean([e.score for e in self.entries.values() if e.puzzle_id in puzzles] + ([7] * self.stats['missed_games']))
        self.stats['avg_green'] = stats.mean([e.green for e in self.entries.values() if e.puzzle_id in puzzles])
        self.stats['avg_yellow'] = stats.mean([e.yellow for e in self.entries.values() if e.puzzle_id in puzzles])
        self.stats['avg_other'] = stats.mean([e.other for e in self.entries.values() if e.puzzle_id in puzzles])

    def get_avgs(self):
        return self.stats['raw_mean'], self.stats['adj_mean'], self.stats['avg_green'], self.stats['avg_yellow'], self.stats['avg_other']

    def get_ids(self):
        return [*self.entries.keys()]

    def get_entries(self) -> list[PuzzleEntry]:
        return [*self.entries.values()]

class Puzzle():
    def __init__(self, puzzle_id) -> None:
        self.puzzle_id = puzzle_id
        self.entries = {}

    def add(self, puzzle_entry):
        self.entries[puzzle_entry.user_id] = puzzle_entry

    def remove_entry(self, user_id):
        if user_id in self.get_users():
            del self.entries[user_id]
            return True
        return False

    def get_users(self):
        return [*self.entries.keys()]