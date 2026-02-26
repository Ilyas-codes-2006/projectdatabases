def calculate_elo_simple(rating_winner: int, rating_loser: int) -> tuple[int, int] :
    return rating_winner + 25, rating_loser - 25
