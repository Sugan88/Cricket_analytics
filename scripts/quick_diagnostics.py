# quick_diagnostics.py — put in project root
import pandas as pd
from pathlib import Path

DATA = Path("data/processed/aus_deliveries.parquet")
df = pd.read_parquet(DATA)

print("=== Null cities ===")
print(f"{df['city'].isna().sum():,} of {len(df):,} deliveries have no city")

print("\n=== Venues containing 'Brisbane' or 'WACA' or 'Perth' ===")
mask = df["venue"].str.contains("Brisbane|WACA|W.A.C.A|Perth|Western Australia", case=False, na=False)
print(df[mask].groupby("venue")["match_id"].nunique().sort_values(ascending=False))

print("\n=== Test matches with null city, by venue ===")
tests = df[df["match_type"] == "Test"]
null_city = tests[tests["city"].isna()]
print(null_city.groupby("venue")["match_id"].nunique().sort_values(ascending=False).head(15))

print("\n=== All distinct venue spellings (Tests) ===")
print(tests["venue"].nunique(), "distinct venues")
print(sorted(tests["venue"].dropna().unique())[:40])