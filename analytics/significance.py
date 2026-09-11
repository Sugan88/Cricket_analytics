"""
Bootstrap confidence intervals for batting averages by host country.

Point estimates alone can't tell us whether Australia's 26.5 average in India
is meaningfully worse than 30.2 in England, or whether that gap is noise across
20 Tests. This resamples innings with replacement to put an interval around
each estimate, and tests the India-England gap directly.

Innings, not deliveries, are the resampling unit: balls within an innings are
strongly dependent (a set batter faces many of them), so resampling deliveries
would badly understate variance.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data.processors.venue_normalizer import add_venue_fields
from analytics.batting_conditions import load, australian_batting

RNG = np.random.default_rng(seed=42)
N_BOOT = 10_000


def to_innings(df: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse deliveries to one row per batter-innings.

    Each row is a single stint: runs scored, balls faced, and whether it ended
    in dismissal. Not-outs contribute runs but no dismissal, which is what makes
    a batting average an average rather than a mean.
    """
    df = df.copy()
    df["batter_dismissed"] = df["is_wicket"] & (df["player_out"] == df["batter"])

    return (
        df.groupby(["match_id", "innings", "batter", "host_country"], observed=True)
        .agg(
            runs=("runs_batter", "sum"),
            balls=("is_legal_ball", "sum"),
            dismissed=("batter_dismissed", "any"),
        )
        .reset_index()
    )


def batting_average(runs: np.ndarray, dismissed: np.ndarray) -> float:
    """Runs per dismissal. Returns nan if a resample contains no dismissals."""
    n_out = dismissed.sum()
    return runs.sum() / n_out if n_out > 0 else np.nan


def bootstrap_average(
    innings: pd.DataFrame, n_boot: int = N_BOOT
) -> tuple[float, float, float]:
    """Return (point estimate, lower 95%, upper 95%) for a set of innings."""
    runs = innings["runs"].to_numpy()
    out = innings["dismissed"].to_numpy()
    n = len(runs)

    point = batting_average(runs, out)

    idx = RNG.integers(0, n, size=(n_boot, n))
    boots = np.array([batting_average(runs[i], out[i]) for i in idx])
    boots = boots[~np.isnan(boots)]

    lo, hi = np.percentile(boots, [2.5, 97.5])
    return point, lo, hi


def country_intervals(innings: pd.DataFrame, min_innings: int = 40) -> pd.DataFrame:
    """Bootstrap interval per host country."""
    rows = []
    for country, grp in innings.groupby("host_country"):
        if len(grp) < min_innings:
            continue
        point, lo, hi = bootstrap_average(grp)
        rows.append({
            "host_country": country,
            "batter_innings": len(grp),
            "average": round(point, 2),
            "ci_low": round(lo, 2),
            "ci_high": round(hi, 2),
            "ci_width": round(hi - lo, 2),
        })

    return pd.DataFrame(rows).sort_values("average")


def compare_two(
    innings: pd.DataFrame, a: str, b: str, n_boot: int = N_BOOT
) -> dict:
    """
    Bootstrap the difference between two countries' averages.

    Resamples each group independently and takes the difference each time.
    If the resulting interval excludes zero, the gap is unlikely to be noise.
    The p-value is the share of resamples where the sign flips, doubled for a
    two-sided test.
    """
    ga = innings[innings["host_country"] == a]
    gb = innings[innings["host_country"] == b]

    ra, oa = ga["runs"].to_numpy(), ga["dismissed"].to_numpy()
    rb, ob = gb["runs"].to_numpy(), gb["dismissed"].to_numpy()

    ia = RNG.integers(0, len(ra), size=(n_boot, len(ra)))
    ib = RNG.integers(0, len(rb), size=(n_boot, len(rb)))

    diffs = np.array([
        batting_average(ra[x], oa[x]) - batting_average(rb[y], ob[y])
        for x, y in zip(ia, ib)
    ])
    diffs = diffs[~np.isnan(diffs)]

    lo, hi = np.percentile(diffs, [2.5, 97.5])
    observed = batting_average(ra, oa) - batting_average(rb, ob)

    # Share of resamples on the opposite side of zero from the observed effect
    p = (diffs >= 0).mean() if observed < 0 else (diffs <= 0).mean()

    return {
        "comparison": f"{a} minus {b}",
        "observed_diff": round(observed, 2),
        "ci_low": round(lo, 2),
        "ci_high": round(hi, 2),
        "excludes_zero": bool(lo > 0 or hi < 0),
        "p_two_sided": round(min(p * 2, 1.0), 4),
    }

def bootstrap_strike_rate(innings: pd.DataFrame, n_boot: int = N_BOOT) -> tuple:
    """CI for runs per 100 balls."""
    runs = innings["runs"].to_numpy()
    balls = innings["balls"].to_numpy()
    n = len(runs)

    point = runs.sum() / balls.sum() * 100
    idx = RNG.integers(0, n, size=(n_boot, n))
    boots = np.array([runs[i].sum() / balls[i].sum() * 100 for i in idx])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return point, lo, hi


def spin_dismissal_share(tests: pd.DataFrame, n_boot: int = N_BOOT) -> pd.DataFrame:
    """
    CI for the share of dismissals that are lbw, bowled or stumped.

    Resamples dismissals directly — each dismissal is one observation here,
    unlike runs where innings is the right unit.
    """
    out = tests[tests["is_wicket"] & (tests["player_out"] == tests["batter"])].copy()
    out["context"] = out.apply(
        lambda r: "India" if r["host_country"] == "India"
        else ("Australia (home)" if r["is_home"] else "Other away"),
        axis=1,
    )
    out["is_spin_mode"] = out["wicket_kind"].isin(["lbw", "bowled", "stumped"])

    rows = []
    for ctx, grp in out.groupby("context"):
        v = grp["is_spin_mode"].to_numpy()
        idx = RNG.integers(0, len(v), size=(n_boot, len(v)))
        boots = v[idx].mean(axis=1) * 100
        lo, hi = np.percentile(boots, [2.5, 97.5])
        rows.append({
            "context": ctx,
            "dismissals": len(v),
            "spin_mode_pct": round(v.mean() * 100, 1),
            "ci_low": round(lo, 1),
            "ci_high": round(hi, 1),
        })
    return pd.DataFrame(rows)

if __name__ == "__main__":
    df = add_venue_fields(australian_batting(load()))
    tests = df[df["match_type"] == "Test"]
    innings = to_innings(tests)

    print(f"\n{len(innings):,} batter-innings across {tests['match_id'].nunique()} Tests")
    print(f"Bootstrap: {N_BOOT:,} resamples, seed 42\n")

    print("=== Batting average by host country, 95% CI ===")
    ci = country_intervals(innings)
    print(ci.to_string(index=False))

    print("\n=== Is India worse than the other away countries? ===")
    comparisons = [
        ("India", "England"),
        ("India", "South Africa"),
        ("India", "Sri Lanka"),
        ("India", "Australia"),
    ]
    results = pd.DataFrame([compare_two(innings, a, b) for a, b in comparisons])
    print(results.to_string(index=False))

    print("\n=== Strike rate by host country, 95% CI ===")
    sr_rows = []
    for c in ["India", "England", "Australia", "South Africa"]:
        grp = innings[innings["host_country"] == c]
        p, lo, hi = bootstrap_strike_rate(grp)
        sr_rows.append({"host_country": c, "strike_rate": round(p, 2),
                        "ci_low": round(lo, 2), "ci_high": round(hi, 2)})
    print(pd.DataFrame(sr_rows).to_string(index=False))

    print("\n=== Spin-mode dismissal share, 95% CI ===")
    print(spin_dismissal_share(tests).to_string(index=False))