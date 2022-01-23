import re
from datetime import date, datetime, timezone, timedelta

def is_user(word) -> bool:
    return re.match(r'^<@[!]?\d+>', word)

def get_todays_puzzle() -> str:
    arbitrary_date = date(2022, 1, 10)
    arbitrary_date_puzzle = 205
    todays_date = datetime.now(timezone(timedelta(hours=-5), 'EST')).date()
    return str(arbitrary_date_puzzle + (todays_date - arbitrary_date).days)