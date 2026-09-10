"""
Charts for the Australian Test batting analysis.

Regenerates all figures from the delivery data; nothing is hardcoded, so the
charts stay correct if the underlying data is refreshed. Outputs PNGs to
reports/figures/ for embedding in the README.
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data.processors.venue_normalizer import add_venue_fields
from analytics.batting_conditions import load, australian_batting, batting_summary

FIG_DIR = Path(__file__).resolve().parents[1] / "reports" / "figures"

# Restrained palette: one accent for the subject, grey for context.
ACCENT = "#C1272D"     # India / the anomaly
NEUTRAL = "#9AA0A6"    # other away countries
HOME = "#1B5E9E"       # Australia at home
GRID = "#E0E0E0"


def style_axes(ax, title, subtitle=None, xlabel=None, ylabel=None):
    """Apply a consistent, uncluttered style."""
    ax.set_title(title, fontsize=13, fontweight="bold", loc="left", pad=18 if subtitle else 10)
    if subtitle:
        ax.text(
            0, 1.02, subtitle, transform=ax.transAxes,
            fontsize=9.5, color="#5F6368", va="bottom",
        )
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=10, color="#3C4043")
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10, color="#3C4043")

    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#BDC1C6")

    ax.tick_params(colors="#3C4043", labelsize=9.5)
    ax.set_axisbelow(True)


def save(fig, name):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / f"{name}.png"
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  saved {path.relative_to(Path.cwd())}")


# ---------------------------------------------------------------- chart 1

def plot_away_by_country(tests: pd.DataFrame):
    """Away Test batting average by host country, with home average as reference."""
    away = tests[~tests["is_home"]]
    data = (
        batting_summary(away, ["host_country"], min_balls=1000, min_innings=5)
        .sort_values("average")
    )

    home_avg = batting_summary(
        tests[tests["is_home"]], ["location"], min_balls=1000
    )["average"].iloc[0]

    colors = [ACCENT if c == "India" else NEUTRAL for c in data["host_country"]]

    fig, ax = plt.subplots(figsize=(8, 4.2))
    bars = ax.barh(data["host_country"], data["average"], color=colors, height=0.65)

    ax.axvline(home_avg, color=HOME, linestyle="--", linewidth=1.4, zorder=0)
    ax.text(
        home_avg + 0.4, -0.55, f"Home: {home_avg:.1f}",
        color=HOME, fontsize=9, fontweight="bold", va="center",
    )

    for bar, row in zip(bars, data.itertuples()):
        ax.text(
            bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
            f"{row.average:.1f}  ({row.innings} inns)",
            va="center", fontsize=9, color="#3C4043",
        )

    ax.set_xlim(0, max(data["average"].max(), home_avg) * 1.28)
    style_axes(
        ax,
        "Australia bat worst in India — and it isn't a subcontinent problem",
        "Test batting average by host country, men's internationals 2002–2026",
        xlabel="Batting average",
    )
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.yaxis.grid(False)

    save(fig, "01_away_by_country")


# ---------------------------------------------------------------- chart 2

def plot_phase_decay(tests: pd.DataFrame):
    """Batting average and strike rate across innings phases, three countries."""
    df = tests.copy()
    df["phase"] = pd.cut(
        df["over"],
        bins=[-1, 15, 40, 80, 200],
        labels=["Overs 1–15", "16–40", "41–80", "80+"],
    )

    subset = df[df["host_country"].isin(["India", "England", "Australia"])]
    data = batting_summary(subset, ["host_country", "phase"], min_balls=600, min_innings=5)

    series = {
        "India": (ACCENT, 2.6),
        "England": (NEUTRAL, 1.9),
        "Australia": (HOME, 1.9),
    }

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))

    for ax, metric, label in zip(
        axes, ["average", "strike_rate"], ["Batting average", "Runs per 100 balls"]
    ):
        for country, (color, lw) in series.items():
            sub = data[data["host_country"] == country].sort_values("phase")
            ax.plot(
                sub["phase"].astype(str), sub[metric],
                marker="o", markersize=6, color=color, linewidth=lw,
                label=country if metric == "average" else None,
            )
        style_axes(ax, label, ylabel=label)
        ax.yaxis.grid(True, color=GRID, linewidth=0.8)

    axes[0].legend(frameon=False, fontsize=9.5, loc="lower left")
    fig.suptitle(
        "In India the collapse starts when the seamers come off",
        fontsize=13, fontweight="bold", x=0.09, ha="left", y=1.04,
    )
    fig.text(
        0.09, 0.985,
        "Australian Test batting by innings phase — flat in England, falling away in India",
        fontsize=9.5, color="#5F6368", ha="left",
    )

    save(fig, "02_phase_decay")


# ---------------------------------------------------------------- chart 3

def plot_dismissal_mix(tests: pd.DataFrame):
    """Share of dismissal types: India vs home vs other away."""
    out = tests[tests["is_wicket"] & (tests["player_out"] == tests["batter"])].copy()
    out["where"] = out.apply(
        lambda r: "India" if r["host_country"] == "India"
        else ("Australia (home)" if r["is_home"] else "Other away"),
        axis=1,
    )

    share = pd.crosstab(out["where"], out["wicket_kind"], normalize="index") * 100

    # Spin-indicative modes first, then caught, then the rest.
    spin_modes = ["lbw", "bowled", "stumped"]
    other = [c for c in share.columns if c not in spin_modes + ["caught"]]
    order = spin_modes + ["caught"] + other
    share = share[[c for c in order if c in share.columns]]

    palette = {
        "lbw": ACCENT, "bowled": "#E07A5F", "stumped": "#F2CC8F",
        "caught": "#4A6FA5",
    }
    colors = [palette.get(c, "#D3D3D3") for c in share.columns]

    rows = ["Australia (home)", "Other away", "India"]
    share = share.loc[[r for r in rows if r in share.index]]

    fig, ax = plt.subplots(figsize=(9, 3.4))
    left = pd.Series(0.0, index=share.index)

    for col, color in zip(share.columns, colors):
        ax.barh(share.index, share[col], left=left, color=color, height=0.6, label=col)
        for idx in share.index:
            v = share.loc[idx, col]
            if v >= 4:
                ax.text(
                    left[idx] + v / 2, idx, f"{v:.0f}%",
                    ha="center", va="center", fontsize=9,
                    color="white" if col in ("lbw", "caught", "bowled") else "#3C4043",
                    fontweight="bold",
                )
        left += share[col]

    spin_total = share[[c for c in spin_modes if c in share.columns]].sum(axis=1)
    style_axes(
        ax,
        "Dismissals in India shift from caught to lbw, bowled and stumped",
        f"Spin-indicative dismissals: {spin_total.get('India', 0):.0f}% in India "
        f"vs {spin_total.get('Australia (home)', 0):.0f}% at home",
        xlabel="Share of Australian dismissals (%)",
    )
    ax.set_xlim(0, 100)
    ax.legend(
        frameon=False, fontsize=9, ncol=4,
        loc="upper center", bbox_to_anchor=(0.5, -0.28),
    )
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)

    save(fig, "03_dismissal_mix")


if __name__ == "__main__":
    print("Building figures...")
    df = add_venue_fields(australian_batting(load()))
    tests = df[df["match_type"] == "Test"]

    plot_away_by_country(tests)
    plot_phase_decay(tests)
    plot_dismissal_mix(tests)

    print("Done.")