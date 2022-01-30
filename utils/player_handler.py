from utils.puzzle import PuzzlePlayer, PuzzleEntry
from utils.bot_utilities import BotUtilities

class PlayerHandler():
    def __init__(self, utils: BotUtilities) -> None:
        self.utils = utils
        self._players = {}

    def add(self, entry: PuzzleEntry) -> None:
        if entry.user_id not in self._players.keys():
            self._players[entry.user_id] = PuzzlePlayer(entry.user_id)
        self._players[entry.user_id].add(entry)

    def get(self, user_id: int) -> PuzzlePlayer:
        return self._players[user_id] if user_id in self.get_ids() else None

    def get_ids(self) -> list[int]:
        return self._players.keys()