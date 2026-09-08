"""
Cricsheet JSON loader.
Flattens ball-by-ball match JSON into a tidy DataFrame — one row per delivery.
"""

import json
import logging
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "australia_male"
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"


def parse_match(path: Path) -> list[dict]:
    """Parse one Cricsheet match file into a list of delivery dicts."""
    with open(path) as f:
        match = json.load(f)

    info = match.get("info", {})
    innings_list = match.get("innings", [])

    # Match-level context, repeated on every delivery row
    dates = info.get("dates", [])
    teams = info.get("teams", [])
    outcome = info.get("outcome", {})
    toss = info.get("toss", {})

    base = {
        "match_id": path.stem,
        "date": dates[0] if dates else None,
        "match_type": info.get("match_type"),
        "venue": info.get("venue"),
        "city": info.get("city"),
        "team_1": teams[0] if len(teams) > 0 else None,
        "team_2": teams[1] if len(teams) > 1 else None,
        "toss_winner": toss.get("winner"),
        "toss_decision": toss.get("decision"),
        "winner": outcome.get("winner"),
    }

    rows = []
    for innings_num, innings in enumerate(innings_list, start=1):
        batting_team = innings.get("team")
        bowling_team = next((t for t in teams if t != batting_team), None)

        for over in innings.get("overs", []):
            over_num = over.get("over")

            for ball_num, d in enumerate(over.get("deliveries", []), start=1):
                runs = d.get("runs", {})
                extras = d.get("extras", {})
                wickets = d.get("wickets", [])

                # A delivery is "legal" unless it's a wide or a no-ball
                is_legal = not ("wides" in extras or "noballs" in extras)

                rows.append({
                    **base,
                    "innings": innings_num,
                    "batting_team": batting_team,
                    "bowling_team": bowling_team,
                    "over": over_num,
                    "ball": ball_num,
                    "batter": d.get("batter"),
                    "bowler": d.get("bowler"),
                    "non_striker": d.get("non_striker"),
                    "runs_batter": runs.get("batter", 0),
                    "runs_extras": runs.get("extras", 0),
                    "runs_total": runs.get("total", 0),
                    "is_legal_ball": is_legal,
                    "is_wicket": len(wickets) > 0,
                    "wicket_kind": wickets[0].get("kind") if wickets else None,
                    "player_out": wickets[0].get("player_out") if wickets else None,
                })

    return rows


def load_all(raw_dir: Path = RAW_DIR, limit: int | None = None) -> pd.DataFrame:
    """Load every match JSON in raw_dir into one DataFrame."""
    files = sorted(raw_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No JSON files in {raw_dir} — did the unzip work?")

    if limit:
        files = files[:limit]

    all_rows = []
    failed = []

    for i, path in enumerate(files, start=1):
        try:
            all_rows.extend(parse_match(path))
        except Exception as e:
            failed.append((path.name, str(e)))

        if i % 100 == 0:
            print(f"  parsed {i}/{len(files)} matches...")

    df = pd.DataFrame(all_rows)

    print(f"\nParsed {len(files) - len(failed)}/{len(files)} matches")
    if failed:
        print(f"Failed: {len(failed)} — first few: {failed[:3]}")

    return df


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading Cricsheet data...")
    df = load_all()

    print(f"\nShape: {df.shape[0]:,} deliveries x {df.shape[1]} columns")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")

    print("\nMatches by format:")
    print(
        df.groupby("match_type")["match_id"]
        .nunique()
        .rename("matches")
        .to_frame()
    )

    out = OUT_DIR / "aus_deliveries.parquet"
    df.to_parquet(out, index=False)
    print(f"\nSaved to {out}")