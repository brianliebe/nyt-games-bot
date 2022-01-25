import statistics as stats

class PuzzleEntry():
    def __init__(self, puzzle_num, user_id, week, score, green, yellow, other) -> None:
        self.puzzle_num = puzzle_num
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
    
    def add(self, puzzle_entry: PuzzleEntry) -> None:
        self.entries[puzzle_entry.puzzle_num] = puzzle_entry

    def get_entry(self, puzzle_num):
        return self.entries[puzzle_num] if puzzle_num in self.get_puzzles() else None

    def remove_entry(self, puzzle_num):
        if puzzle_num in self.entries.keys():
            del self.entries[puzzle_num]
            return True
        return False

    def generate_stats(self, puzzles):
        self.stats = {}
        self.stats['missed_games'] = len([p for p in puzzles if p not in self.get_puzzles()])
        self.stats['raw_mean'] = stats.mean([e.score for e in self.entries.values() if e.puzzle_num in puzzles])
        self.stats['adj_mean'] = stats.mean([e.score for e in self.entries.values() if e.puzzle_num in puzzles] + ([7] * self.stats['missed_games']))
        self.stats['avg_green'] = stats.mean([e.green for e in self.entries.values() if e.puzzle_num in puzzles])
        self.stats['avg_yellow'] = stats.mean([e.yellow for e in self.entries.values() if e.puzzle_num in puzzles])
        self.stats['avg_other'] = stats.mean([e.other for e in self.entries.values() if e.puzzle_num in puzzles])

    def get_avgs(self):
        return self.stats['raw_mean'], self.stats['adj_mean'], self.stats['avg_green'], self.stats['avg_yellow'], self.stats['avg_other']

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

    def remove_entry(self, user_id):
        if user_id in self.entries.keys():
            del self.entries[user_id]
            return True
        return False

    def get_users(self):
        return self.entries.keys()