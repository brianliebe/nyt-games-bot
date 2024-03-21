from enum import Enum, auto
from typing import Protocol

class PuzzleQueryType(Enum):
    SINGLE_PUZZLE = auto()
    MULTI_PUZZLE = auto()
    ALL_TIME = auto()

class BasePlayerStats(Protocol):
    user_id: str
    missed_games: int
    rank: int
    raw_mean: float
    adj_mean: float

class BasePuzzleEntry(Protocol):
    puzzle_id: int
    user_id: str
