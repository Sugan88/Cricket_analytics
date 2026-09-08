"""
Australian batting performance split by condition.
Computes averages and strike rates from Cricsheet ball-by-ball data.
Venue names and the home/away flag come from data.processors.venue_normalizer,
which collapses inconsistent Cricsheet venue strings to canonical grounds.
The earlier city-based home/away flag was unreliable: 158k deliveries have a
null city, which silently classified home Tests at the MCG, SCG and Adelaide
Oval as away.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data.processors.venue_normalizer import add_venue_fields

DATA = Path(__file__).resolve().parents[1] / "data" / "processed" / "aus_deliveries.parquet"

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)


def load() -> pd.DataFrame:
    df = pd.read_parquet(DATA)
    df["date"] = pd.to_datetime(df["date"])
    return df


def australian_batting(df: pd.DataFrame) -> pd.DataFrame:
    """Deliveries where Australia was batting."""
    return df[df["batting_team"] == "Australia"].copy()


def batting_summary(
    df: pd.DataFrame,
    group_cols: list[str],
    min_balls: int = 200,
    min_innings: int = 5,
) -> pd.DataFrame:
    """
    Aggregate batting performance.

    Average = runs / dismissals. A dismissal counts only when the batter facing
    the ball is the one dismissed, which excludes non-striker run-outs — those
    would otherwise inflate the dismissal count and depress the average.

    Both thresholds matter: min_balls alone lets a single large innings through,
    which is how a 3-innings ground topped an earlier venue ranking.
    """
    df = df.copy()
    df["batter_dismissed"] = df["is_wicket"] & (df["player_out"] == df["batter"])

    agg = (
        df.groupby(group_cols)
        .agg(
            runs=("runs_batter", "sum"),
            balls=("is_legal_ball", "sum"),
            dismissals=("batter_dismissed", "sum"),
            innings=("match_id", "nunique"),
        )
        .reset_index()
    )

    agg = agg[(agg["balls"] >= min_balls) & (agg["innings"] >= min_innings)]
    agg["average"] = (agg["runs"] / agg["dismissals"].replace(0, pd.NA)).round(2)
    agg["strike_rate"] = (agg["runs"] / agg["balls"] * 100).round(2)

    return agg.sort_values("runs", ascending=False)


if __name__ == "__main__":
    df = add_venue_fields(australian_batting(load()))

    print("\n=== 1. Australia batting: home vs away, by format ===")
    print(
        batting_summary(df, ["match_type", "location"], min_balls=500)
        .set_index(["match_type", "location"])[["innings", "runs", "average", "strike_rate"]]
        .sort_index()
    )

    print("\n=== 2. Top Australian Test run-scorers (2002 onwards) ===")
    tests = df[df["match_type"] == "Test"]
    print(
        batting_summary(tests, ["batter"], min_balls=1000, min_innings=10)
        .head(15)
        .set_index("batter")[["innings", "runs", "balls", "average", "strike_rate"]]
    )

    print("\n=== 3. Home vs away split, top Test batters ===")
    top = batting_summary(tests, ["batter"], min_balls=2000, min_innings=20)["batter"].head(10)
    split = batting_summary(
        tests[tests["batter"].isin(top)],
        ["batter", "location"],
        min_balls=400,
        min_innings=8,
    )
    pivot = split.pivot(index="batter", columns="location", values="average")
    pivot["gap"] = (pivot["Home"] - pivot["Away/Neutral"]).round(2)
    print(pivot.sort_values("gap", ascending=False))

    print("\n=== 4. Australia's Test venues by batting average (min 8 innings) ===")
    print(
        batting_summary(tests, ["venue_clean"], min_balls=1500, min_innings=8)
        .sort_values("average", ascending=False)
        .set_index("venue_clean")[["innings", "runs", "average", "strike_rate"]]
    )

        # add as section 5 in batting_conditions.py
    print("\n=== 5. Away Test batting by host venue (min 6 innings) ===")
    away_tests = tests[~tests["is_home"]]
    print(
    batting_summary(away_tests, ["venue_clean"], min_balls=800, min_innings=6)
    .sort_values("average")
    .set_index("venue_clean")[["innings", "runs", "average", "strike_rate"]]
)