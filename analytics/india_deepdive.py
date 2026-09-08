# analytics/india_deepdive.py
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data.processors.venue_normalizer import add_venue_fields
from analytics.batting_conditions import load, australian_batting, batting_summary

df = add_venue_fields(australian_batting(load()))
tests = df[df["match_type"] == "Test"]

# Innings phase: how deep into the innings the over falls
tests = tests.copy()
tests["phase"] = pd.cut(
    tests["over"],
    bins=[-1, 15, 40, 80, 200],
    labels=["1-15 (new ball)", "16-40", "41-80", "80+ (worn)"],
)

print("\n=== Australia Test batting by innings phase: India vs England ===")
subset = tests[tests["host_country"].isin(["India", "England", "Australia"])]
out = batting_summary(subset, ["host_country", "phase"], min_balls=600, min_innings=5)
print(
    out.set_index(["host_country", "phase"])[["runs", "balls", "average", "strike_rate"]]
    .sort_index()
)

print("\n=== Dismissal types: India vs elsewhere ===")
tests_out = tests[tests["is_wicket"] & (tests["player_out"] == tests["batter"])].copy()
tests_out["where"] = tests_out["host_country"].apply(
    lambda c: "India" if c == "India" else ("Australia" if c == "Australia" else "Other away")
)
pivot = (
    pd.crosstab(tests_out["wicket_kind"], tests_out["where"], normalize="columns") * 100
).round(1)
print(pivot)