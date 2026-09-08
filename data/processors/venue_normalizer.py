"""
Venue normalisation for Cricsheet data.

Cricsheet venue strings are inconsistent across files: the same ground appears
with and without a trailing city ("Basin Reserve" vs "Basin Reserve, Wellington"),
and some grounds were renamed or abbreviated over the years. This module
collapses those variants to a canonical name, flags Australian grounds, and
attaches a host country.

The home/away flag is derived from venue rather than the `city` field, because
158k of 756k deliveries have a null city — which previously misclassified 41
home Tests at the MCG, SCG and Adelaide Oval as away.
"""

import re

import pandas as pd

# Grounds whose variants differ by more than a trailing city qualifier:
# renames, abbreviations, and alternate spellings. Keys are matched after
# _clean(); values are the canonical name.
EXPLICIT_ALIASES = {
    "w a c a ground": "Western Australia Cricket Association Ground",
    "waca ground": "Western Australia Cricket Association Ground",
    "marrara stadium": "Marrara Cricket Ground",
    "optus stadium": "Perth Stadium",
    "feroz shah kotla": "Arun Jaitley Stadium",
    "ami stadium": "Hagley Oval",
    "punjab cricket association stadium": "Punjab Cricket Association IS Bindra Stadium",
    "new wanderers stadium": "The Wanderers Stadium",
    "sardar patel stadium": "Narendra Modi Stadium",
    "sheikh zayed stadium": "Sheikh Zayed Stadium",
    "m chinnaswamy stadium": "M Chinnaswamy Stadium",
    "r premadasa stadium": "R Premadasa Stadium",
    "vidarbha cricket association ground": "Vidarbha Cricket Association Stadium",
    "zayed cricket stadium": "Sheikh Zayed Stadium",
    "dubai sports city cricket stadium": "Dubai International Cricket Stadium",
    "queen s park new": "Queen's Park Oval",
    "vra cricket ground": "VRA Ground",
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
    "Blundstone Arena",
    "Metricon Stadium",
    "Sydney Cricket Ground No 2",
    "Tony Ireland Stadium",
    "Bundaberg Rum Stadium",
}

# Canonical venue -> host country. Anything unmapped falls through to
# "Other/Neutral"; audit() reports those so the map can be extended.
VENUE_COUNTRY = {
    **{v: "Australia" for v in AUSTRALIAN_VENUES},

    # England
    "Lord's": "England",
    "Kennington Oval": "England",
    "Edgbaston": "England",
    "Headingley": "England",
    "Old Trafford": "England",
    "Trent Bridge": "England",
    "Sophia Gardens": "England",
    "Riverside Ground": "England",
    "The Rose Bowl": "England",
    "County Ground": "England",

    # India
    "Arun Jaitley Stadium": "India",
    "Eden Gardens": "India",
    "M Chinnaswamy Stadium": "India",
    "MA Chidambaram Stadium": "India",
    "Wankhede Stadium": "India",
    "Brabourne Stadium": "India",
    "Punjab Cricket Association IS Bindra Stadium": "India",
    "Rajiv Gandhi International Stadium": "India",
    "Vidarbha Cricket Association Stadium": "India",
    "Maharashtra Cricket Association Stadium": "India",
    "Himachal Pradesh Cricket Association Stadium": "India",
    "Holkar Cricket Stadium": "India",
    "Saurashtra Cricket Association Stadium": "India",
    "JSCA International Stadium Complex": "India",
    "Narendra Modi Stadium": "India",
    "Barsapara Cricket Stadium": "India",
    "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium": "India",
    "Nehru Stadium": "India",
    "Green Park": "India",
    "Barabati Stadium": "India",
    "Sawai Mansingh Stadium": "India",
    "Vidarbha C.A. Ground": "India",

    # Sri Lanka
    "Galle International Stadium": "Sri Lanka",
    "R Premadasa Stadium": "Sri Lanka",
    "Pallekele International Cricket Stadium": "Sri Lanka",
    "Sinhalese Sports Club Ground": "Sri Lanka",
    "P Sara Oval": "Sri Lanka",
    "Rangiri Dambulla International Stadium": "Sri Lanka",
    "Mahinda Rajapaksa International Cricket Stadium": "Sri Lanka",

    # South Africa
    "Newlands": "South Africa",
    "Kingsmead": "South Africa",
    "SuperSport Park": "South Africa",
    "The Wanderers Stadium": "South Africa",
    "St George's Park": "South Africa",
    "Mangaung Oval": "South Africa",
    "Senwes Park": "South Africa",
    "Boland Park": "South Africa",
    "De Beers Diamond Oval": "South Africa",
    "Buffalo Park": "South Africa",
    "Sahara Stadium Kingsmead": "South Africa",

    # New Zealand
    "Basin Reserve": "New Zealand",
    "Eden Park": "New Zealand",
    "Hagley Oval": "New Zealand",
    "Seddon Park": "New Zealand",
    "Bay Oval": "New Zealand",
    "McLean Park": "New Zealand",
    "University Oval": "New Zealand",
    "Sky Stadium": "New Zealand",
    "Westpac Stadium": "New Zealand",
    "Jade Stadium": "New Zealand",

    # West Indies
    "Kensington Oval": "West Indies",
    "Sabina Park": "West Indies",
    "Queen's Park Oval": "West Indies",
    "Sir Vivian Richards Stadium": "West Indies",
    "Antigua Recreation Ground": "West Indies",
    "National Cricket Stadium": "West Indies",
    "Warner Park": "West Indies",
    "Windsor Park": "West Indies",
    "Daren Sammy National Cricket Stadium": "West Indies",
    "Beausejour Stadium": "West Indies",
    "Providence Stadium": "West Indies",
    "Bourda": "West Indies",
    "Arnos Vale Ground": "West Indies",
    "Central Broward Regional Park Stadium Turf Ground": "West Indies",

    # Pakistan, and the UAE grounds used as Pakistan's neutral home 2009-2019
    "Gaddafi Stadium": "Pakistan",
    "National Stadium": "Pakistan",
    "Rawalpindi Cricket Stadium": "Pakistan",
    "Multan Cricket Stadium": "Pakistan",
    "Dubai International Cricket Stadium": "UAE (neutral)",
    "Sharjah Cricket Stadium": "UAE (neutral)",
    "Sheikh Zayed Stadium": "UAE (neutral)",
    "ICC Academy": "UAE (neutral)",

    # Bangladesh
    "Shere Bangla National Stadium": "Bangladesh",
    "Zahur Ahmed Chowdhury Stadium": "Bangladesh",
    "Khan Shaheb Osman Ali Stadium": "Bangladesh",
    "Bangabandhu National Stadium": "Bangladesh",
    "MA Aziz Stadium": "Bangladesh",

    # Zimbabwe
    "Harare Sports Club": "Zimbabwe",
    "Queens Sports Club": "Zimbabwe",
    "Bulawayo Athletic Club": "Zimbabwe",

    # Other
    "Sportpark Westvliet": "Netherlands",
    "VRA Ground": "Netherlands",
    "Civil Service Cricket Club": "Ireland",
    "The Village": "Ireland",
    "Grange Cricket Club Ground": "Scotland",
    "Kinrara Academy Oval": "Malaysia (neutral)",
    "Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium": "India",
    "Greenfield International Stadium": "India",
    "Captain Roop Singh Stadium": "India",
    "Shaheed Veer Narayan Singh International Stadium": "India",
    "Sector 16 Stadium": "India",
    "Reliance Stadium": "India",
    "Bir Sreshtho Flight Lieutenant Matiur Rahman Stadium": "Bangladesh",
    "Narayanganj Osmani Stadium": "Bangladesh",
    "Chittagong Divisional Stadium": "Bangladesh",
    "Willowmoore Park": "South Africa",
    "North West Cricket Stadium": "South Africa",
    "Tolerance Oval": "UAE (neutral)",
    "The Cooper Associates County Ground": "England",
    "St Lawrence Ground": "England",
    "Clontarf Cricket Club Ground": "Ireland",
}


def _clean(name: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace — for alias matching."""
    s = name.lower()
    s = re.sub(r"[.\-']", " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def canonical_venue(name: str) -> str | None:
    """Collapse a raw Cricsheet venue string to a canonical ground name."""
    if pd.isna(name):
        return None

    # Everything before the first comma — strips trailing city and suburb
    # qualifiers such as ", Wellington" or ", Woolloongabba, Brisbane".
    base = name.split(",")[0].strip()
    key = _clean(base)

    return EXPLICIT_ALIASES.get(key, base)


def add_venue_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Add canonical venue, home/away flag, and host country."""
    df = df.copy()
    df["venue_clean"] = df["venue"].map(canonical_venue)
    df["is_home"] = df["venue_clean"].isin(AUSTRALIAN_VENUES)
    df["location"] = df["is_home"].map({True: "Home", False: "Away/Neutral"})
    df["host_country"] = df["venue_clean"].map(VENUE_COUNTRY).fillna("Other/Neutral")
    return df


def audit(df: pd.DataFrame) -> None:
    """Print what normalisation did, so it can be checked rather than trusted."""
    print(f"Venues: {df['venue'].nunique()} raw -> {df['venue_clean'].nunique()} canonical\n")

    print("=== Collapsed groups (canonical <- raw variants) ===")
    groups = (
        df.groupby("venue_clean")["venue"]
        .unique()
        .loc[lambda s: s.map(len) > 1]
    )
    for canon, variants in groups.items():
        print(f"  {canon}")
        for v in variants:
            print(f"      <- {v}")

    tests = df[df["match_type"] == "Test"]

    print("\n=== Australian Test venues, by matches ===")
    print(
        tests[tests["is_home"]]
        .groupby("venue_clean")["match_id"]
        .nunique()
        .sort_values(ascending=False)
    )

    print("\n=== Home/away Test match counts ===")
    print(tests.groupby("location")["match_id"].nunique())

    print("\n=== Test matches by host country ===")
    print(
        tests.groupby("host_country")["match_id"]
        .nunique()
        .sort_values(ascending=False)
    )

    print("\n=== Unmapped venues (all formats, by matches) ===")
    unmapped = df[df["host_country"] == "Other/Neutral"]
    if unmapped.empty:
        print("  none")
    else:
        print(
            unmapped.groupby("venue_clean")["match_id"]
            .nunique()
            .sort_values(ascending=False)
            .head(25)
        )


if __name__ == "__main__":
    from pathlib import Path

    DATA = Path("data/processed/aus_deliveries.parquet")
    audit(add_venue_fields(pd.read_parquet(DATA)))