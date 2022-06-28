"""
A bunch of helper functions for the bot.
"""


def has_user_asked(questions, author):
    """
    Determine if the user has already asked a question.
    """

    for question in questions:
        if author == question[1]:
            return True, question

    return False, None


def display_points(old, new):
    """
    Display the points of the user.
    """
    if old > new:
        return f"You lost {round(old - new, 1)} points"

    return f"You gained {round(new - old, 1)} points"
