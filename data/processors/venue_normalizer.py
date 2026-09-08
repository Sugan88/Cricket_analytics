"""
Venue normalisation for Cricsheet data.

Cricsheet venue strings are inconsistent across files: the same ground appears
with and without a trailing city ("Basin Reserve" vs "Basin Reserve, Wellington"),
and some grounds were renamed or abbreviated. This module collapses those
variants to a canonical name and attaches a reliable country.
"""

import re
import pandas as pd

# Grounds whose variants differ by more than a trailing city qualifier.
# Left side is matched after cleaning; right side is the canonical name.
EXPLICIT_ALIASES = {
    "w a c a ground": "Western Australia Cricket Association Ground",
    "waca ground": "Western Australia Cricket Association Ground",
    "marrara stadium": "Marrara Cricket Ground",
    "optus stadium": "Perth Stadium",
    "feroz shah kotla": "Arun Jaitley Stadium",
    "ami stadium": "Hagley Oval",
    "punjab cricket association stadium": "Punjab Cricket Association IS Bindra Stadium",
    "new wanderers stadium": "The Wanderers Stadium",
}

# Canonical names of grounds located in Australia.
AUSTRALIAN_VENUES = {
    "Adelaide Oval",
    "Melbourne Cricket Ground",
    "Sydney Cricket Ground",
    "Brisbane Cricket Ground",
    "Western Australia Cricket Association Ground",
    "Perth Stadium",
    "Bellerive Oval",
    "Manuka Oval",
    "Marrara Cricket Ground",
    "Great Barrier Reef Arena",
    "Cazaly's Stadium",
    "Traeger Park",
    "Aurora Stadium",
    "Sydney Showground Stadium",
    "Carrara Oval",
    "Docklands Stadium",
    "Stadium Australia",
    "Junction Oval",
    "Simonds Stadium",
    "GMHBA Stadium",
    "Kardinia Park",
    "Riverway Stadium",
    "Ninja Stadium",
}


def _clean(name: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    s = name.lower()
    s = re.sub(r"[.\-']", " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def canonical_venue(name: str) -> str:
    """Collapse a raw Cricsheet venue string to a canonical ground name."""
    if pd.isna(name):
        return None

    # Take the portion before the first comma — this strips trailing
    # city/suburb qualifiers such as ", Wellington" or ", Woolloongabba".
    base = name.split(",")[0].strip()
    key = _clean(base)

    if key in EXPLICIT_ALIASES:
        return EXPLICIT_ALIASES[key]

    return base


def add_venue_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Add canonical venue and a venue-derived home/away flag."""
    df = df.copy()
    df["venue_clean"] = df["venue"].map(canonical_venue)
    df["is_home"] = df["venue_clean"].isin(AUSTRALIAN_VENUES)
    df["location"] = df["is_home"].map({True: "Home", False: "Away/Neutral"})
    return df


def audit(df: pd.DataFrame) -> None:
    """Print what the normalisation did, so it can be checked rather than trusted."""
    raw = df["venue"].nunique()
    clean = df["venue_clean"].nunique()
    print(f"Venues: {raw} raw -> {clean} canonical\n")

    print("=== Collapsed groups (raw variants -> canonical) ===")
    groups = (
        df.groupby("venue_clean")["venue"]
        .unique()
        .loc[lambda s: s.map(len) > 1]
    )
    for canon, variants in groups.items():
        print(f"  {canon}")
        for v in variants:
            print(f"      <- {v}")

    print("\n=== Australian Test venues found, by matches ===")
    tests = df[(df["match_type"] == "Test") & df["is_home"]]
    print(tests.groupby("venue_clean")["match_id"].nunique().sort_values(ascending=False))

    print("\n=== Home/away Test match counts ===")
    t = df[df["match_type"] == "Test"]
    print(t.groupby("location")["match_id"].nunique())

    print("\n=== Non-Australian venues with many Tests (check none should be home) ===")
    away = t[~t["is_home"]]
    print(away.groupby("venue_clean")["match_id"].nunique().sort_values(ascending=False).head(15))


if __name__ == "__main__":
    from pathlib import Path

    DATA = Path("data/processed/aus_deliveries.parquet")
    df = add_venue_fields(pd.read_parquet(DATA))
    audit(df)