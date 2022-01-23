import re, json
from datetime import date, datetime, timezone, timedelta

def is_user(word) -> bool:
    return re.match(r'^<@[!]?\d+>', word)

def get_todays_puzzle() -> str:
    arbitrary_date = date(2022, 1, 10)
    arbitrary_date_puzzle = 205
    todays_date = datetime.now(timezone(timedelta(hours=-5), 'EST')).date()
    return str(arbitrary_date_puzzle + (todays_date - arbitrary_date).days)

def is_wordle_submission(title) -> str:
    return re.match(r'^Wordle \d{3} \d{1}/\d{1}$', title) or re.match(r'^Wordle \d{3} X/\d{1}$', title)

def save(bot) -> bool:
    db = open('db.json', 'w')
    full_dict = {}
    for puzzle_num in sorted(bot.puzzles.keys()):
        puzzle = bot.puzzles[puzzle_num]
        db_entries = []
        for user_id in puzzle.entries.keys():
            entry = puzzle.entries[user_id]
            db_entries.append({'user_id' : entry.user_id, 'score' : entry.score, 'green' : entry.green, \
                    'yellow' : entry.yellow, 'other' : entry.other})
        full_dict[puzzle_num] = db_entries
    db.write(json.dumps(full_dict, indent=4, sort_keys=True))
    db.close()
    return True