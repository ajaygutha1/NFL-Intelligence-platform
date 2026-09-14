# SHARAT — TASK 1/2: Explore One NFL Game (beginner, standalone)
#
# This does not depend on anything else in the pipeline and doesn't block Ajay.
# See GitHub issue #6 for the full task description.
#
# GOAL: pick one real NFL game from the play-by-play data, find one play with a
# high positive EPA and one play with a high negative EPA, and explain in plain
# English why each one probably had that value.
#
# You have everything you need in notebooks/01_team-gameexploration.py to see
# how to load the data and filter to one game — use it as a reference, don't
# just copy it. Write your own version here.

import nflreadpy as nfl

# TASK: load one season of play-by-play data.
# INPUT: a season year, e.g. 2025
# OUTPUT: a pandas DataFrame of play-by-play rows
# HINT: nfl.load_pbp(<season>) returns a Polars DataFrame — you'll need
#       .to_pandas() to work with it like Ajay did in notebooks/01_...py
pbp = None  # TODO: replace with your own load


# TASK: pick exactly one game and filter the data down to just its rows.
# INPUT: the play-by-play DataFrame
# OUTPUT: a DataFrame containing only the plays from one game_id
# HINT: look at the "game_id" column — pick any one value from it.
one_game = None  # TODO


# TASK: find one play with a high POSITIVE epa value and one with a high
# NEGATIVE epa value within that game.
# HINT: look at the "epa" column — sort or filter on it.
# Print out the play_type, down, distance, yards_gained, and epa for each one
# so you can actually see what happened on the play.
high_positive_play = None  # TODO
high_negative_play = None  # TODO


# TASK: write 2-3 sentences EACH explaining why you think each play had that
# EPA value. Put your explanation here as a comment or print statement —
# whichever you prefer, just make sure it ends up somewhere readable (this
# file, or copied into docs/learning-notes.md).
#
# Example of the kind of reasoning (don't just copy this, use your own game):
# "This was a 3rd-and-8 pass completed for a 45-yard touchdown — the offense
#  went from a low expected-points situation to 7 guaranteed points in one
#  play, hence the large positive EPA."

# YOUR EXPLANATION HERE:
