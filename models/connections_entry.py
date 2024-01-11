class ConnectionsPuzzleEntry():
    def __init__(self, puzzle_id: int, user_id: str, score: int, puzzle_str: str) -> None:
        self.puzzle_id = puzzle_id
        self.user_id = user_id
        self.score = score
        self.puzzle_str = puzzle_str