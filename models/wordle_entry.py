class WordlePuzzleEntry():
    def __init__(self, puzzle_id: int, user_id: str, score: int, green: int, yellow: int, other: int) -> None:
        self.puzzle_id = puzzle_id
        self.user_id = user_id
        self.score = score
        self.green = green
        self.yellow = yellow
        self.other = other