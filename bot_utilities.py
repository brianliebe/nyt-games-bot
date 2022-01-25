import re, json, os
from datetime import date, datetime, timezone, timedelta
from puzzle import Puzzle, PuzzlePlayer, PuzzleEntry

class BotUtilities():
    def __init__(self, bot) -> None:
        self.bot = bot
        self.arbitrary_date = date(2022, 1, 10)
        self.arbitrary_date_puzzle = 205

    # VALIDATION

    def is_user(self, word) -> bool:
        return re.match(r'^<@[!]?\d+>', word)

    def is_date(self, date_str: str) -> bool:
        return re.match(r'^\d{1,2}/\d{1,2}(/\d{2}(?:\d{2})?)?$', date_str)
        
    def is_valid_week(self, query_date) -> bool:
        if query_date is not None:
            return query_date.strftime('%A') == 'Sunday'
        else:
            return False

    def is_wordle_submission(self, title) -> str:
        return re.match(r'^Wordle \d{3} \d{1}/\d{1}$', title) or re.match(r'^Wordle \d{3} X/\d{1}$', title)

    # GETS (dates)

    def get_sunday(self, puzzle_num) -> str:
        puzzle_date = self.get_date_by_puzzle(puzzle_num)
        return puzzle_date - timedelta(days = (puzzle_date.weekday() + 1) % 7)

    def get_date_from_str(self, date_str: str) -> date:
        if not self.is_date(date_str): return None

        if re.match(r'^\d{1,2}/\d{1,2}$', date_str):
            return datetime.strptime(date_str, f'%m/%d').replace(year=datetime.today().year).date()
        elif re.match(r'^\d{1,2}/\d{1,2}/\d{2}$', date_str):
            return datetime.strptime(date_str, f'%m/%d/%y').date()
        elif re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
            return datetime.strptime(date_str, f'%m/%d/%Y').date()
        else:
            return None

    def get_date_by_puzzle(self, puzzle_num) -> date:
        return self.arbitrary_date + timedelta(days=(int(puzzle_num) - self.arbitrary_date_puzzle))

    def get_todays_date(self) -> date:
        return datetime.now(timezone(timedelta(hours=-5), 'EST')).date()

    # GET (puzzles)

    def get_puzzle_by_date(self, query_date: date) -> str:
        return str(self.arbitrary_date_puzzle + (query_date - self.arbitrary_date).days)

    def get_todays_puzzle(self) -> str:
        return self.get_puzzle_by_date(self.get_todays_date())

    def get_puzzles_by_week(self, query_date: date) -> str:
        if not self.is_valid_week(query_date): return None
        return [str(int(self.get_puzzle_by_date(query_date)) + i) for i in range(7)]

    # GET (misc)

    def get_nickname(self, user_id) -> str:
        guild = self.bot.get_guild(self.bot.guild_id)
        for member in guild.members:
            if member.id == user_id:
                return member.display_name
        return "?"

    def get_str_from_date(self, query_date) -> str:
        return query_date.strftime(f'%m/%d/%Y')

    # ADD

    def add_entry(self, user_id, title, puzzle) -> bool:
        if 'X/6' in title:
            puzzle_num, _ = re.findall(r'\d+', title)
            score = 7
        else:
            puzzle_num, score, _ = re.findall(r'\d+', title)
            score = int(score)

        week_start = self.get_str_from_date(self.get_sunday(puzzle_num))

        entry = PuzzleEntry(puzzle_num, user_id, week_start,
                score, 
                puzzle.count('🟩'),
                puzzle.count('🟨'),
                puzzle.count('⬜') + puzzle.count('⬛'))

        if puzzle_num not in self.bot.puzzles.keys():
            self.bot.puzzles[puzzle_num] = Puzzle(puzzle_num)
        self.bot.puzzles[puzzle_num].add(entry)

        if user_id not in self.bot.players.keys():
            self.bot.players[user_id] = PuzzlePlayer(user_id)
        self.bot.players[user_id].add(entry)
        self.save()

    # SAVE/LOAD

    def save(self, filename: str = 'database.json'):
        f = open(filename, 'w', encoding='utf-8')
        db = {}
        for user_id in self.bot.players.keys():
            player = self.bot.players[user_id]
            entries = {}
            for puzzle_num in player.get_puzzles():
                pe = player.get_entry(puzzle_num)
                entries[puzzle_num] = { "week" : pe.week, "score" : pe.score, "green" : pe.green, "yellow" : pe.yellow, "other" : pe.other }
            db[player.user_id] = { "display_name" : self.get_nickname(player.user_id), "entries" : entries }
        f.write(json.dumps(db, indent=4, sort_keys=True, ensure_ascii=False))
        f.close()

    def load(self, filename: str = 'database.json') -> bool:
        db = {}
        if os.path.exists(filename):
            db = json.loads(open(filename).read())
        for user_id_str in db.keys():
            user_id = int(user_id_str)
            for puzzle_num in db[user_id_str]['entries'].keys():
                db_entry = db[user_id_str]['entries'][puzzle_num]
                if user_id not in self.bot.players.keys():
                    self.bot.players[user_id] = PuzzlePlayer(user_id)
                if puzzle_num not in self.bot.puzzles.keys():
                    self.bot.puzzles[puzzle_num] = Puzzle(puzzle_num)
                entry = PuzzleEntry(puzzle_num, \
                                    user_id, \
                                    db_entry['week'], \
                                    db_entry['score'], \
                                    db_entry['green'], \
                                    db_entry['yellow'], \
                                    db_entry['other'])
                self.bot.players[user_id].add(entry)
                self.bot.puzzles[puzzle_num].add(entry)
        return True
