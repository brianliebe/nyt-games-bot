import re, json, os
from datetime import date, datetime, timezone, timedelta
from utils.puzzle import Puzzle, PuzzlePlayer, PuzzleEntry
from utils.puzzle_handler import PuzzleHandler
from utils.player_handler import PlayerHandler
from utils.bot_utilities import BotUtilities

class DatabaseHandler():
    def __init__(self, puzzles: PuzzleHandler, players: PlayerHandler, utils: BotUtilities, filename: str = "database.json") -> None:
        self.puzzles = puzzles
        self.players = players
        self.utils = utils
        self.filename = filename

    def add_entry(self, user_id: int, title: str, puzzle: str) -> bool:
        if 'X/6' in title:
            puzzle_id, _ = re.findall(r'\d+', title)
            score = 7
        else:
            puzzle_id, score, _ = re.findall(r'\d+', title)
            score = int(score)

        week_start = self.utils.convert_date_to_str(self.puzzles.get_date_by_puzzle(puzzle_id))

        entry = PuzzleEntry(puzzle_id, user_id, week_start,
                score, 
                puzzle.count('🟩'),
                puzzle.count('🟨'),
                puzzle.count('⬜') + puzzle.count('⬛'))

        self.puzzles.add(entry)
        self.players.add(entry)
        self.save()

    def save(self) -> None:
        f = open(self.filename, 'w', encoding='utf-8')
        db = {}
        for user_id in self.players.get_ids():
            player = self.players.get(user_id)
            entries = {}
            for puzzle_id in player.get_ids():
                entry: PuzzleEntry = player.get_entry(puzzle_id)
                entries[puzzle_id] = { "week" : entry.week, "score" : entry.score, "green" : entry.green, \
                        "yellow" : entry.yellow, "other" : entry.other }
            db[player.user_id] = { "display_name" : self.utils.get_nickname(player.user_id), "entries" : entries }
        f.write(json.dumps(db, indent=4, sort_keys=True, ensure_ascii=False))
        f.close()
    
    def load(self) -> None:
        db = {}
        if os.path.exists(self.filename):
            db = json.loads(open(self.filename).read())

        for user_id_str in db.keys():
            user_id = int(user_id_str)
            for puzzle_id in db[user_id_str]['entries'].keys():
                db_entry = db[user_id_str]['entries'][puzzle_id]
                entry = PuzzleEntry(int(puzzle_id), \
                                    user_id, \
                                    db_entry['week'], \
                                    db_entry['score'], \
                                    db_entry['green'], \
                                    db_entry['yellow'], \
                                    db_entry['other'])
                self.players.add(entry)
                self.puzzles.add(entry)