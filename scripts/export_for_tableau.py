"""
Export analysis-ready CSVs for Tableau.

Tableau connects to flat files, not to your Python objects, so each view gets
its own pre-aggregated extract. Aggregating here rather than in Tableau keeps
the dismissal logic (batter-facing only, no non-striker run-outs) and the
min-innings thresholds in one place — Tableau just draws what it's given.

One wide delivery-level extract is also written for anyone who wants to slice
it freely, but the three aggregates are what the dashboard is built on.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data.processors.venue_normalizer import add_venue_fields
from analytics.batting_conditions import load, australian_batting, batting_summary

OUT_DIR = Path(__file__).resolve().parents[1] / "exports" / "tableau"


def write(df: pd.DataFrame, name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{name}.csv"
    df.to_csv(path, index=False)
    print(f"  {name}.csv  ({len(df):,} rows, {df.shape[1]} cols)")


def export_country_summary(tests: pd.DataFrame) -> None:
    """Sheet 1: batting average by host country, home row included."""
    away = batting_summary(
        tests[~tests["is_home"]], ["host_country"], min_balls=1000, min_innings=5
    )
    away["context"] = "Away"

    home = batting_summary(tests[tests["is_home"]], ["host_country"], min_balls=1000)
    home["context"] = "Home"

    out = pd.concat([home, away], ignore_index=True)
    out = out[["host_country", "context", "innings", "runs", "balls",
               "dismissals", "average", "strike_rate"]]
    out = out.rename(columns={"host_country": "Host Country"})

    write(out.sort_values("average", ascending=False), "01_country_summary")


def export_phase_decay(tests: pd.DataFrame) -> None:
    """Sheet 2: average and strike rate by innings phase and host country."""
    df = tests.copy()
    df["phase"] = pd.cut(
        df["over"],
        bins=[-1, 15, 40, 80, 200],
        labels=["Overs 1-15", "Overs 16-40", "Overs 41-80", "Overs 80+"],
    )
    # Tableau sorts strings alphabetically; give it an explicit order column.
    phase_order = {
        "Overs 1-15": 1, "Overs 16-40": 2, "Overs 41-80": 3, "Overs 80+": 4,
    }

    out = batting_summary(df, ["host_country", "phase"], min_balls=600, min_innings=5)
    out["phase"] = out["phase"].astype(str)
    out["phase_order"] = out["phase"].map(phase_order)
    out = out.rename(columns={"host_country": "Host Country", "phase": "Innings Phase"})

    write(out.sort_values(["Host Country", "phase_order"]), "02_phase_decay")


def export_dismissal_mix(tests: pd.DataFrame) -> None:
    """Sheet 3: dismissal-type shares by context, long format for Tableau."""
    out = tests[tests["is_wicket"] & (tests["player_out"] == tests["batter"])].copy()
    out["context"] = out.apply(
        lambda r: "India" if r["host_country"] == "India"
        else ("Australia (home)" if r["is_home"] else "Other away"),
        axis=1,
    )

    counts = (
        out.groupby(["context", "wicket_kind"])
        .size()
        .reset_index(name="dismissals")
    )
    totals = counts.groupby("context")["dismissals"].transform("sum")
    counts["share_pct"] = (counts["dismissals"] / totals * 100).round(2)

    # Flag for a simple two-colour split in Tableau.
    counts["spin_indicative"] = counts["wicket_kind"].isin(["lbw", "bowled", "stumped"])

    counts = counts.rename(columns={"wicket_kind": "Dismissal Type", "context": "Context"})
    write(counts.sort_values(["Context", "share_pct"], ascending=[True, False]),
          "03_dismissal_mix")


def export_player_splits(tests: pd.DataFrame) -> None:
    """Sheet 4: per-player home/away splits, for a filterable player view."""
    top = batting_summary(tests, ["batter"], min_balls=2000, min_innings=20)["batter"]

    split = batting_summary(
        tests[tests["batter"].isin(top)],
        ["batter", "location"],
        min_balls=400,
        min_innings=8,
    )
    split = split.rename(columns={"batter": "Player", "location": "Location"})
    write(split.sort_values(["Player", "Location"]), "04_player_home_away")


def export_deliveries(df: pd.DataFrame) -> None:
    """Wide delivery-level extract for ad-hoc exploration in Tableau."""
    cols = [
        "match_id", "date", "match_type", "venue_clean", "host_country",
        "location", "innings", "over", "batter", "bowler",
        "runs_batter", "runs_total", "is_legal_ball", "is_wicket",
        "wicket_kind", "player_out",
    ]
    out = df[cols].rename(columns={"venue_clean": "venue"})
    write(out, "00_deliveries_australia_batting")


if __name__ == "__main__":
    print("Exporting Tableau extracts...")

    df = add_venue_fields(australian_batting(load()))
    tests = df[df["match_type"] == "Test"]

    export_country_summary(tests)
    export_phase_decay(tests)
    export_dismissal_mix(tests)
    export_player_splits(tests)
    export_deliveries(df)

    print(f"\nWritten to {OUT_DIR}")