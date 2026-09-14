import nflreadpy as nfl
import pandas as pd

# Load one completed NFL season
pbp = nfl.load_pbp(2025)

#nflreadypy gives us Polars, convert it to pandas
pbp = pbp.to_pandas()

print(pbp.shape)
print(pbp.head())

columns = [
    "game_id",
    "game_date",
    "week",
    "home_team",
    "away_team",
     "posteam",
    "defteam",
    "play_type",
    "epa",
    "success",
    "qb_dropback",
    "rush_attempt",
    "qb_scramble",
    "qb_kneel"

]

print(pbp[columns].head(20).to_string())

regular_pbp = pbp[pbp["season_type"] == "REG"].copy()

game_id = regular_pbp["game_id"].dropna().iloc[0]

game = regular_pbp[
    regular_pbp["game_id"] == game_id
].copy()

print("Game:", game_id)
print("Home:", game["home_team"].iloc[0])
print("Away:", game["away_team"].iloc[0])

print(
    game[
        ["posteam", "defteam", "play_type", "epa", "success"]
    ].head(30).to_string()
)

plays = regular_pbp[
    regular_pbp["epa"].notna()
    & regular_pbp["posteam"].notna()
    & regular_pbp["defteam"].notna()
].copy()

plays = plays[
    (plays["qb_dropback"] == 1)
    | (plays["rush_attempt"] == 1)
].copy()

plays["is_pass"] = plays["qb_dropback"] == 1

plays["is_rush"]= (
    (plays["rush_attempt"] == 1)
    & (plays["qb_scramble"] != 1)
    & (plays["qb_kneel"] != 1)
)



home_team = game["home_team"].iloc[0]

home_offense = plays[
    (plays["game_id"] == game_id)
    & (plays["posteam"] == home_team)
]

print(
    home_offense[
        ["posteam","defteam","play_type","epa"]
    ].head(20).to_string()
)

off_epa = home_offense["epa"].mean()

print("Offensive EPA/play:", off_epa)

# for defensive EPA

home_team = game["home_team"].iloc[0]

home_defense = plays[
    (plays["game_id"] == game_id)
    & (plays["defteam"] == home_team)
]

def_epa = home_defense["epa"].mean()

print("Defensive EPA allowed/play:", def_epa)



pass_plays = home_offense[
    home_offense["is_pass"]
]

rush_plays = home_offense[
    home_offense["is_rush"]
]

pass_epa = pass_plays["epa"].mean()
rush_epa = rush_plays["epa"].mean()

success_rate = home_offense["success"].mean()

print("Pass EPA/play:", pass_epa)
print("Rush EPA/play:", rush_epa)
print("Success rate:", success_rate)

# step 9, creating dataset stuff from manual testing
plays["pass_epa_value"] = plays["epa"].where (
    plays["is_pass"]
)
plays["rush_epa_value"] = plays["epa"].where (
    plays["is_rush"]
)

print(
    plays[
        [
            "play_type",
            "epa",
            "is_pass",
            "is_rush",
            "pass_epa_value",
            "rush_epa_value"
        ]
    ].head(20).to_string()
)

offense = (
    plays
    .groupby(["game_id", "posteam"])
    .agg(
        off_epa=("epa", "mean"),
        pass_epa=("pass_epa_value", "mean"),
        rush_epa=("rush_epa_value", "mean"),
        success_rate=("success", "mean")
    )
    .reset_index()
)

print(offense.head(10).to_string())

defense = (
    plays
    .groupby(["game_id", "defteam"])
    .agg(
        def_epa=("epa", "mean")
    )
    .reset_index()
)
print(defense.head(10).to_string())


offense = offense.rename(
    columns={"posteam": "team"}
)

defense = defense.rename(
    columns={"defteam": "team"}
)

team_game = offense.merge(
    defense,
    on=["game_id","team"],
    how= "inner"
)
print(team_game.head(10).to_string())

rows_per_game = team_game.groupby("game_id").size()

print(rows_per_game.value_counts())

example_game_id = team_game["game_id"].iloc[0]

print(
    team_game[
        team_game["game_id"] == example_game_id
    ].to_string(index=False)
)

games = (
    regular_pbp[
        [
            "game_id",
            "season",
            "week",
            "game_date",
            "home_team",
            "away_team"
        ]
    ]
    .drop_duplicates("game_id")
)

team_game = team_game.merge(
    games,
    on="game_id",
    how="left"
)

print(team_game.head().to_string())

team_game["game_date"] = pd.to_datetime(
    team_game["game_date"]
)

# Step 16
team_game = team_game.sort_values(
    ["season", "team", "game_date"]
).reset_index(drop=True)



team_game["rest_days"] = (
    team_game
    .groupby(["season", "team"])["game_date"]
    .diff()
    .dt.days
)

print(
    team_game[
        [
            "team",
            "week",
            "game_date",
            "rest_days"
        ]
    ].head(20).to_string(index=False)
)

# First rolling feature
team_game["roll5_off_epa"] = (
    team_game
    .groupby(["season", "team"])["off_epa"]
    .transform(
        lambda x: x.shift(1)
                   .rolling(5, min_periods=5)
                   .mean()
    )
)

buf = (
    team_game[
        team_game["team"] == "BUF"
    ]
    .sort_values("game_date")
)

print(
    buf[
        [
            "week",
            "off_epa",
            "roll5_off_epa"
        ]
    ].head(10).to_string(index=False)
)



rolling_stats = [
    "off_epa",
    "def_epa",
    "pass_epa",
    "rush_epa",
    "success_rate"
]

for stat in rolling_stats:
    team_game[f"roll5_{stat}"] = (
        team_game
        .groupby(["season", "team"])[stat]
        .transform(
            lambda x: x.shift(1)
                       .rolling(5, min_periods=5)
                       .mean()
        )
    )

print(
    team_game[
        [
            "team",
            "week",
            "off_epa",
            "roll5_off_epa",
            "def_epa",
            "roll5_def_epa",
            "roll5_pass_epa",
            "roll5_rush_epa",
            "roll5_success_rate",
            "rest_days"
        ]
    ].head(25).to_string(index=False)
)


team_check = (
    team_game[
        team_game["team"] == "BUF"
    ]
    .sort_values("game_date")
    .reset_index(drop=True)
)

print(
    team_check[
        [
            "game_id",
            "week",
            "off_epa",
            "roll5_off_epa"
        ]
    ].head(7).to_string(index=False)
)
target_game = team_check.iloc[5]
print("\nGame being checked:")
print(target_game[[
    "game_id",
    "week",
    "off_epa",
    "roll5_off_epa"
]])

previous_five = team_check.iloc[0:5]
print("\nPrevious five games:")

print(
    previous_five[
        [
            "week",
            "off_epa"
        ]
    ].to_string(index=False)
)
manual_average = previous_five["off_epa"].mean()

print("\nManual previous-five average:")
print(manual_average)

rolling_average = target_game["roll5_off_epa"]

print("\nRolling feature:")
print(rolling_average)

print("\nDo they match?")
print(manual_average == rolling_average)

print("\nGame 6 actual EPA:")
print(target_game["off_epa"])
previous_five["off_epa"].mean()

import numpy as np

print(
    np.isclose(
        manual_average,
        rolling_average
    )
)

assert np.isclose(
    manual_average,
    rolling_average
)

