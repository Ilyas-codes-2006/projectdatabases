def calculate_elo_simple(rating_winner: int, rating_loser: int) -> tuple[int, int]:
    """
    Calculate a simple Elo rating update using a fixed rating change.

    :param rating_winner: Current rating of the player who won the match.
    :param rating_loser: Current rating of the player who lost the match.
    :return: A tuple ``(new_winner_rating, new_loser_rating)`` with the updated
        ratings after applying a fixed +25/-25 point adjustment.
    """
    return rating_winner + 25, rating_loser - 25
