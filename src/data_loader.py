"""Load and merge bracket structure, team ratings, and injury overrides.

This module is the main data pipeline for the bracket generator. It loads
three config files, merges them into Team objects, and applies injury
adjustments. All downstream modules (win_probability, ev_engine, etc.)
consume Team objects produced here.
"""

import json
import os
import sys
from dataclasses import dataclass


@dataclass
class Team:
    """A tournament team with efficiency ratings and bracket position."""
    name: str
    seed: int
    region: str
    adj_o: float            # Adjusted Offensive Efficiency (points per 100 possessions)
    adj_d: float            # Adjusted Defensive Efficiency (points allowed per 100 possessions)
    adj_em: float           # Adjusted Efficiency Margin, after injury overrides (rounds 1-2)
    adj_em_base: float      # AdjEM before injury overrides (raw KenPom value)
    sweet_16_adj_em: float = None  # Rounds 3+ AdjEM (only set for Gonzaga)


def get_adj_em(team, round_number=1):
    """Get the effective AdjEM for a team in a given round.

    Most teams have a single AdjEM. Gonzaga has a different value for rounds
    3+ because Braden Huff may return from injury for the Sweet 16.

    Args:
        team: A Team object.
        round_number: Tournament round (1=R64, 2=R32, 3=S16, 4=E8, 5=FF, 6=Championship).

    Returns:
        The team's effective AdjEM for that round.
    """
    if team.sweet_16_adj_em is not None and round_number >= 3:
        return team.sweet_16_adj_em
    return team.adj_em


def load_teams(config_dir="config"):
    """Load all config files and return a dict mapping team name -> Team.

    This is the main entry point for data loading. It:
    1. Loads bracket_2026.json (teams, seeds, regions)
    2. Loads team_ratings.json (KenPom efficiency ratings)
    3. Loads injury_overrides.json (AdjEM adjustments for injured teams)
    4. Merges everything into Team objects with adjusted ratings

    Args:
        config_dir: Path to the config directory (default "config").

    Returns:
        dict[str, Team]: Team name -> Team object for all 68 tournament teams.
    """
    # --- Step 1: Load bracket structure ---
    bracket_path = os.path.join(config_dir, "bracket_2026.json")
    with open(bracket_path) as f:
        bracket = json.load(f)

    # Extract all team names with their seed and region
    team_info = {}  # name -> {"seed": int, "region": str}

    # Teams from regional matchups
    for region_name, region_data in bracket["regions"].items():
        for matchup in region_data["matchups"]:
            for side in ["top", "bottom"]:
                team_name = matchup[side]["team"]
                seed = matchup[side]["seed"]
                if team_name is not None:
                    team_info[team_name] = {"seed": seed, "region": region_name}

    # Teams from First Four (both candidates get entries)
    for ff in bracket["first_four"]:
        for team_name in ff["teams"]:
            team_info[team_name] = {"seed": ff["seed"], "region": ff["region"]}

    print(f"[OK] Loaded bracket: {len(team_info)} teams from {len(bracket['regions'])} regions")

    # --- Step 2: Load team ratings ---
    ratings_path = os.path.join(config_dir, "team_ratings.json")
    with open(ratings_path) as f:
        ratings = json.load(f)
    ratings_teams = ratings["teams"]

    # Validate: every bracket team must have a rating
    bracket_names = set(team_info.keys())
    ratings_names = set(ratings_teams.keys())
    missing_ratings = bracket_names - ratings_names
    if missing_ratings:
        print(f"\n[ERROR] These {len(missing_ratings)} teams are in the bracket but missing from team_ratings.json:")
        for name in sorted(missing_ratings):
            print(f"  - {name}")
        print(f"\nPlease add them to {ratings_path}")
        sys.exit(1)

    extra_ratings = ratings_names - bracket_names
    if extra_ratings:
        print(f"[WARN] {len(extra_ratings)} teams in team_ratings.json are not in the bracket (ignored)")

    print(f"[OK] Loaded ratings: {len(ratings_teams)} teams from {ratings['source']}")

    # --- Step 3: Load injury overrides ---
    overrides_path = os.path.join(config_dir, "injury_overrides.json")
    with open(overrides_path) as f:
        overrides = json.load(f)["overrides"]

    # Validate: every override team must exist in the bracket
    for name in overrides:
        if name not in bracket_names:
            print(f"[ERROR] Injury override team '{name}' not found in bracket")
            sys.exit(1)

    print(f"[OK] Loaded {len(overrides)} injury overrides")

    # --- Step 4: Build Team objects ---
    teams = {}
    for name, info in team_info.items():
        rating = ratings_teams[name]
        base_em = rating["adj_em"]

        # Apply injury override if present
        override = overrides.get(name)
        if override:
            adjusted_em = base_em + override["adj_em_delta"]

            # Handle Gonzaga's conditional Sweet 16 rating
            sweet_16_em = None
            if "sweet_16_override" in override:
                sweet_16_em = base_em + override["sweet_16_override"]
        else:
            adjusted_em = base_em
            sweet_16_em = None

        teams[name] = Team(
            name=name,
            seed=info["seed"],
            region=info["region"],
            adj_o=rating["adj_o"],
            adj_d=rating["adj_d"],
            adj_em=adjusted_em,
            adj_em_base=base_em,
            sweet_16_adj_em=sweet_16_em,
        )

    print(f"[OK] Built {len(teams)} Team objects")
    return teams


def load_bracket_structure(config_dir="config"):
    """Load and return the raw bracket JSON structure.

    This is needed by downstream modules (bracket_builder, simulator) that
    need the matchup tree, not just team data.

    Returns:
        dict: The full bracket_2026.json contents.
    """
    bracket_path = os.path.join(config_dir, "bracket_2026.json")
    with open(bracket_path) as f:
        return json.load(f)


def resolve_first_four(bracket, winners):
    """Plug First Four winners into the main bracket.

    Args:
        bracket: The bracket structure dict (from load_bracket_structure).
        winners: Dict mapping first_four_id -> winning team name.
                 Example: {"FF1": "Howard", "FF2": "Texas", "FF3": "Lehigh", "FF4": "SMU"}

    Returns:
        The modified bracket dict with null team slots filled in.
    """
    for region_name, region_data in bracket["regions"].items():
        for matchup in region_data["matchups"]:
            for side in ["top", "bottom"]:
                slot = matchup[side]
                if slot["team"] is None and "first_four_id" in slot:
                    ff_id = slot["first_four_id"]
                    if ff_id in winners:
                        slot["team"] = winners[ff_id]
                    else:
                        print(f"[WARN] No winner specified for First Four game {ff_id}")
    return bracket


# --- Run standalone for quick verification ---
if __name__ == "__main__":
    teams = load_teams()

    print(f"\n{'='*70}")
    print(f"All {len(teams)} teams sorted by Adjusted Efficiency Margin:")
    print(f"{'='*70}")
    print(f"{'Rank':>4}  {'AdjEM':>7}  {'Seed':>4}  {'Region':>8}  {'Team':<25}  {'Note'}")
    print(f"{'-'*4}  {'-'*7}  {'-'*4}  {'-'*8}  {'-'*25}  {'-'*20}")

    sorted_teams = sorted(teams.values(), key=lambda t: t.adj_em, reverse=True)
    for i, team in enumerate(sorted_teams, 1):
        # Flag injured teams
        note = ""
        if team.adj_em != team.adj_em_base:
            delta = team.adj_em - team.adj_em_base
            note = f"(injury: {delta:+.1f})"
        if team.sweet_16_adj_em is not None:
            note += f" [S16+: {team.sweet_16_adj_em:+.1f}]"

        print(f"{i:>4}  {team.adj_em:>+7.2f}  {team.seed:>4}  {team.region:>8}  {team.name:<25}  {note}")
