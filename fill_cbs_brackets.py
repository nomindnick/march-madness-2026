"""Generate CBS Sports button click sequences for all 10 brackets.

Reads our bracket data and produces the CBS button names (e.g. "1 Duke",
"11 South Florida") in the correct click order for manual bracket entry.

CBS click order: all R1 picks first, then R2, S16, E8, FF, Championship.
Within each round, regions go: East, West, South, Midwest.
Within each region, matchups are in slot order (0-7 for R1).

Usage: python fill_cbs_brackets.py
"""

import copy
from src.data_loader import load_teams, load_bracket_structure
from src.portfolio import generate_portfolio

# ---------------------------------------------------------------------------
# CBS region order (matches CBS bracket editor layout)
# ---------------------------------------------------------------------------
CBS_REGION_ORDER = ["East", "West", "South", "Midwest"]

# ---------------------------------------------------------------------------
# Canonical name -> CBS abbreviated name mapping
#
# CBS uses shortened names for some schools. Most teams keep their full name.
# This dict only contains teams that differ from our canonical names.
# ---------------------------------------------------------------------------
CBS_NAME_MAP = {
    "Ohio State": "Ohio St.",
    "Michigan State": "Michigan St.",
    "Northern Iowa": "N. Iowa",
    "California Baptist": "Cal Baptist",
    "North Dakota State": "N. Dakota St.",
    "Utah State": "Utah St.",
    "Kennesaw State": "Kennesaw St.",
    "North Carolina": "N. Carolina",
    "Iowa State": "Iowa St.",
    "Tennessee State": "Tenn. State",
    "Wright State": "Wright St.",
    "Queens (NC)": "Queens",
    "Miami (FL)": "Miami",
    "St. John's": "St. John's",       # same on CBS
    "Saint Mary's": "Saint Mary's",    # same on CBS
    "Saint Louis": "Saint Louis",      # same on CBS
    "Texas A&M": "Texas A&M",         # same on CBS
    "Prairie View A&M": "Prairie View A&M",  # same on CBS (if ever needed)
    "Miami (OH)": "Miami (OH)",        # only in First Four, not in main bracket
}


def to_cbs_name(canonical_name):
    """Convert a canonical team name to its CBS button label.

    Args:
        canonical_name: Team name from our bracket data (e.g. "Michigan State").

    Returns:
        CBS-style name (e.g. "Michigan St.").
    """
    return CBS_NAME_MAP.get(canonical_name, canonical_name)


def to_cbs_button(team):
    """Format a Team object as a CBS button string: "{seed} {cbs_name}".

    Args:
        team: A Team object with .seed and .name attributes.

    Returns:
        String like "1 Duke" or "11 South Florida".
    """
    return f"{team.seed} {to_cbs_name(team.name)}"


# ---------------------------------------------------------------------------
# Click sequence builder
# ---------------------------------------------------------------------------

def get_bracket_clicks(bracket):
    """Generate the 63 CBS button names in click order for a bracket.

    Click order:
        R1: 32 picks (8 per region, East/West/South/Midwest)
        R2: 16 picks (4 per region)
        S16: 8 picks (2 per region)
        E8: 4 picks (1 per region)
        FF: 2 picks (semifinal winners)
        Championship: 1 pick (champion)

    Args:
        bracket: A Bracket object from generate_portfolio().

    Returns:
        list[str]: 63 CBS button name strings in click order.
    """
    clicks = []

    # --- Rounds 1-4: region picks in CBS region order ---
    for round_num in [1, 2, 3, 4]:
        for region in CBS_REGION_ORDER:
            winners = bracket.picks[region][round_num]
            for team in winners:
                clicks.append(to_cbs_button(team))

    # --- Final Four: 2 semifinal winners ---
    ff = bracket.final_four
    clicks.append(to_cbs_button(ff["sf1_winner"]))
    clicks.append(to_cbs_button(ff["sf2_winner"]))

    # --- Championship: 1 champion ---
    clicks.append(to_cbs_button(bracket.champion))

    return clicks


# ---------------------------------------------------------------------------
# Round labels for display
# ---------------------------------------------------------------------------

ROUND_LABELS = {
    1: "ROUND OF 64",
    2: "ROUND OF 32",
    3: "SWEET 16",
    4: "ELITE 8",
    5: "FINAL FOUR",
    6: "CHAMPIONSHIP",
}


def print_bracket_clicks(bracket, clicks=None):
    """Print a bracket's click sequence with round headers.

    Args:
        bracket: A Bracket object (for metadata).
        clicks: Optional pre-computed click list. If None, computes it.
    """
    if clicks is None:
        clicks = get_bracket_clicks(bracket)

    meta = bracket.metadata
    bn = meta.get("bracket_number", "?")
    champ = bracket.champion
    tier = meta.get("tier", "?")

    print(f"\n{'='*60}")
    print(f"BRACKET #{bn}: {champ.name} ({champ.seed}-seed, {champ.region}) — {tier}")
    print(f"{'='*60}")

    idx = 0

    # R1: 32 picks (8 per region)
    print(f"\n  {ROUND_LABELS[1]} (32 picks):")
    for region in CBS_REGION_ORDER:
        region_clicks = clicks[idx:idx + 8]
        print(f"    {region}: {', '.join(region_clicks)}")
        idx += 8

    # R2: 16 picks (4 per region)
    print(f"\n  {ROUND_LABELS[2]} (16 picks):")
    for region in CBS_REGION_ORDER:
        region_clicks = clicks[idx:idx + 4]
        print(f"    {region}: {', '.join(region_clicks)}")
        idx += 4

    # S16: 8 picks (2 per region)
    print(f"\n  {ROUND_LABELS[3]} (8 picks):")
    for region in CBS_REGION_ORDER:
        region_clicks = clicks[idx:idx + 2]
        print(f"    {region}: {', '.join(region_clicks)}")
        idx += 2

    # E8: 4 picks (1 per region)
    print(f"\n  {ROUND_LABELS[4]} (4 picks):")
    for region in CBS_REGION_ORDER:
        region_clicks = clicks[idx:idx + 1]
        print(f"    {region}: {region_clicks[0]}")
        idx += 1

    # FF: 2 picks
    print(f"\n  {ROUND_LABELS[5]} (2 picks):")
    print(f"    SF1 (East vs South): {clicks[idx]}")
    print(f"    SF2 (West vs Midwest): {clicks[idx + 1]}")
    idx += 2

    # Championship: 1 pick
    print(f"\n  {ROUND_LABELS[6]} (1 pick):")
    print(f"    Champion: {clicks[idx]}")
    idx += 1

    assert idx == 63, f"Expected 63 clicks, got {idx}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Generate and print CBS click sequences for all 10 brackets."""

    print("Loading teams and bracket structure...")
    teams = load_teams()
    bracket_structure = load_bracket_structure()

    print("\nGenerating 10 brackets...")
    brackets = generate_portfolio(teams, bracket_structure)

    print(f"\n{'#'*60}")
    print(f"# CBS BRACKET ENTRY — CLICK SEQUENCES")
    print(f"{'#'*60}")

    for bracket in brackets:
        clicks = get_bracket_clicks(bracket)
        print_bracket_clicks(bracket, clicks)

    # Print a compact summary for quick reference
    print(f"\n{'#'*60}")
    print(f"# COMPACT CLICK LIST (copy-paste friendly)")
    print(f"{'#'*60}")

    for bracket in brackets:
        clicks = get_bracket_clicks(bracket)
        bn = bracket.metadata["bracket_number"]
        champ = bracket.champion
        print(f"\n--- Bracket #{bn}: {champ.name} ---")
        for i, click in enumerate(clicks, 1):
            print(f"  {i:>2}. {click}")


if __name__ == "__main__":
    main()
