"""Bracket formatting, display, and file output for CBS entry.

Provides:
- Detailed bracket display with upset and consensus flags
- Portfolio summary with correlation matrix and simulation results
- CBS-entry-optimized text files for manual bracket submission
"""

import os

from src.data_loader import Team
from src.bracket_builder import Bracket, get_region_matchups
from src.win_probability import win_probability_teams


# ---------------------------------------------------------------------------
# Upset detection
# ---------------------------------------------------------------------------

def count_upsets(bracket, bracket_structure, teams):
    """Find all upset picks in a bracket.

    An upset is when the picked winner has a strictly higher seed number
    (worse seed) than their opponent. For R1, opponents come from the
    bracket structure. For R2+, opponents are reconstructed from the
    bracket's own prior-round picks.

    Args:
        bracket: Bracket object.
        bracket_structure: Bracket JSON (First Four resolved).
        teams: dict[str, Team].

    Returns:
        list of dicts: {region, round, winner, loser, winner_seed, loser_seed}.
    """
    upsets = []

    for region_name, region_picks in bracket.picks.items():
        # --- R1 upsets: compare against bracket structure ---
        matchups = get_region_matchups(region_name, bracket_structure, teams)
        for slot_idx, (top, bot) in enumerate(matchups):
            winner = region_picks[1][slot_idx]
            loser = bot if winner.name == top.name else top
            if winner.seed > loser.seed:
                upsets.append({
                    "region": region_name,
                    "round": 1,
                    "winner": winner,
                    "loser": loser,
                    "winner_seed": winner.seed,
                    "loser_seed": loser.seed,
                })

        # --- R2+ upsets: reconstruct from bracket's own picks ---
        for round_num in [2, 3, 4]:
            prev_winners = region_picks[round_num - 1]
            curr_winners = region_picks[round_num]

            for game_idx, winner in enumerate(curr_winners):
                # The two teams that played this game
                team_a = prev_winners[game_idx * 2]
                team_b = prev_winners[game_idx * 2 + 1]
                loser = team_b if winner.name == team_a.name else team_a

                if winner.seed > loser.seed:
                    upsets.append({
                        "region": region_name,
                        "round": round_num,
                        "winner": winner,
                        "loser": loser,
                        "winner_seed": winner.seed,
                        "loser_seed": loser.seed,
                    })

    # --- Final Four upsets ---
    ff = bracket.final_four

    # SF1
    sf1_loser = ff["sf1_team2"] if ff["sf1_winner"].name == ff["sf1_team1"].name else ff["sf1_team1"]
    if ff["sf1_winner"].seed > sf1_loser.seed:
        upsets.append({
            "region": "Final Four",
            "round": 5,
            "winner": ff["sf1_winner"],
            "loser": sf1_loser,
            "winner_seed": ff["sf1_winner"].seed,
            "loser_seed": sf1_loser.seed,
        })

    # SF2
    sf2_loser = ff["sf2_team2"] if ff["sf2_winner"].name == ff["sf2_team1"].name else ff["sf2_team1"]
    if ff["sf2_winner"].seed > sf2_loser.seed:
        upsets.append({
            "region": "Final Four",
            "round": 5,
            "winner": ff["sf2_winner"],
            "loser": sf2_loser,
            "winner_seed": ff["sf2_winner"].seed,
            "loser_seed": sf2_loser.seed,
        })

    # Championship
    champ = bracket.champion
    champ_opponent = ff["sf2_winner"] if ff["sf1_winner"].name == champ.name else ff["sf1_winner"]
    if champ.seed > champ_opponent.seed:
        upsets.append({
            "region": "Championship",
            "round": 6,
            "winner": champ,
            "loser": champ_opponent,
            "winner_seed": champ.seed,
            "loser_seed": champ_opponent.seed,
        })

    return upsets


# ---------------------------------------------------------------------------
# Bracket display
# ---------------------------------------------------------------------------

ROUND_LABELS = {1: "R64", 2: "R32", 3: "S16", 4: "E8"}


def format_bracket_lines(bracket, bracket_structure, teams, locked_picks=None):
    """Generate text lines for a bracket display.

    Args:
        bracket: Bracket object.
        bracket_structure: Bracket JSON (First Four resolved).
        teams: dict[str, Team].
        locked_picks: Optional dict {(region, slot): winner_name} for [C] flags.

    Returns:
        list of strings (one per line).
    """
    if locked_picks is None:
        locked_picks = {}

    champion = bracket.champion
    meta = bracket.metadata
    bn = meta.get("bracket_number", "?")
    tier = meta.get("tier", "?")
    path_value = meta.get("path_value", champion.seed * 63)

    lines = []
    lines.append(f"BRACKET #{bn}: {champion.name} ({champion.seed}-seed, "
                 f"{champion.region}) — {tier.replace('_', ' ').title()} — "
                 f"Path: {path_value} pts")
    lines.append("=" * 70)

    upsets = count_upsets(bracket, bracket_structure, teams)
    upset_set = {(u["region"], u["round"], u["winner"].name) for u in upsets}

    for region_name in ["East", "West", "Midwest", "South"]:
        region_picks = bracket.picks[region_name]
        tag = " [CHAMPION]" if region_name == champion.region else ""
        lines.append(f"\n{region_name}{tag}")

        matchups = get_region_matchups(region_name, bracket_structure, teams)

        # --- Round 1 ---
        lines.append(f"  {ROUND_LABELS[1]}:")
        for slot_idx, (top, bot) in enumerate(matchups):
            winner = region_picks[1][slot_idx]
            loser = bot if winner.name == top.name else top

            # Flags
            flags = []
            is_champ_path = (winner.name == champion.name)
            if is_champ_path:
                prefix = "*"
            else:
                prefix = " "

            if (region_name, 1, winner.name) in upset_set:
                flags.append("U")
            if (region_name, slot_idx) in locked_picks:
                flags.append("C")

            flag_str = " [" + ",".join(flags) + "]" if flags else ""
            lines.append(f"  {prefix} ({winner.seed:>2}) {winner.name:<24s} "
                         f"over ({loser.seed:>2}) {loser.name}{flag_str}")

        # --- Rounds 2-4 ---
        for round_num in [2, 3, 4]:
            lines.append(f"  {ROUND_LABELS[round_num]}:")
            prev_winners = region_picks[round_num - 1]
            curr_winners = region_picks[round_num]

            for game_idx, winner in enumerate(curr_winners):
                team_a = prev_winners[game_idx * 2]
                team_b = prev_winners[game_idx * 2 + 1]
                loser = team_b if winner.name == team_a.name else team_a

                is_champ_path = (winner.name == champion.name)
                prefix = "*" if is_champ_path else " "

                flags = []
                if (region_name, round_num, winner.name) in upset_set:
                    flags.append("U")
                flag_str = " [" + ",".join(flags) + "]" if flags else ""

                lines.append(f"  {prefix} ({winner.seed:>2}) {winner.name:<24s} "
                             f"over ({loser.seed:>2}) {loser.name}{flag_str}")

    # --- Final Four ---
    ff = bracket.final_four
    lines.append(f"\nFinal Four")

    sf1_loser = ff["sf1_team2"] if ff["sf1_winner"].name == ff["sf1_team1"].name else ff["sf1_team1"]
    sf2_loser = ff["sf2_team2"] if ff["sf2_winner"].name == ff["sf2_team1"].name else ff["sf2_team1"]

    def fmt_ff(team):
        marker = "*" if team.name == champion.name else " "
        return f"{marker}({team.seed}) {team.name}"

    lines.append(f"  SF1 (East vs South):   {fmt_ff(ff['sf1_team1'])} vs {fmt_ff(ff['sf1_team2'])}")
    lines.append(f"    Winner: {fmt_ff(ff['sf1_winner'])}")
    lines.append(f"  SF2 (West vs Midwest): {fmt_ff(ff['sf2_team1'])} vs {fmt_ff(ff['sf2_team2'])}")
    lines.append(f"    Winner: {fmt_ff(ff['sf2_winner'])}")

    champ_opponent = ff["sf2_winner"] if ff["sf1_winner"].name == champion.name else ff["sf1_winner"]
    lines.append(f"\n  Championship: {fmt_ff(champion)} over {fmt_ff(champ_opponent)}")

    # --- Summary ---
    r1_upsets = [u for u in upsets if u["round"] == 1]
    later_upsets = [u for u in upsets if u["round"] > 1]
    lines.append(f"\n  Upsets: {len(r1_upsets)} in R1, {len(later_upsets)} in R2+ "
                 f"({len(upsets)} total)")
    lines.append(f"  Total picks: 63")

    return lines


def print_bracket_detailed(bracket, bracket_structure, teams, locked_picks=None):
    """Print a detailed bracket to the console.

    Shows all picks with upset [U] and consensus [C] flags,
    champion path marked with *, and summary stats.
    """
    lines = format_bracket_lines(bracket, bracket_structure, teams, locked_picks)
    print("\n" + "\n".join(lines))


# ---------------------------------------------------------------------------
# Pick correlation
# ---------------------------------------------------------------------------

def compute_pick_correlation(brackets):
    """Compute pairwise pick agreement between brackets.

    For each pair, counts how many of the 63 games have the same pick.
    Returns a 2D list (n x n) of agreement fractions (0.0 to 1.0).

    Args:
        brackets: list of Bracket objects.

    Returns:
        list[list[float]]: n x n matrix where [i][j] = fraction of
        63 games where brackets i and j agree.
    """
    n = len(brackets)
    matrix = [[0.0] * n for _ in range(n)]

    for i in range(n):
        matrix[i][i] = 1.0
        for j in range(i + 1, n):
            agree = 0
            total = 0

            # Regional picks (rounds 1-4)
            for region_name in brackets[i].picks:
                for round_num in [1, 2, 3, 4]:
                    winners_i = brackets[i].picks[region_name][round_num]
                    winners_j = brackets[j].picks[region_name][round_num]
                    for k in range(len(winners_i)):
                        total += 1
                        if winners_i[k].name == winners_j[k].name:
                            agree += 1

            # Final Four (3 games: SF1, SF2, Championship)
            ff_i = brackets[i].final_four
            ff_j = brackets[j].final_four

            total += 3
            if ff_i["sf1_winner"].name == ff_j["sf1_winner"].name:
                agree += 1
            if ff_i["sf2_winner"].name == ff_j["sf2_winner"].name:
                agree += 1
            if ff_i["champion"].name == ff_j["champion"].name:
                agree += 1

            frac = agree / total if total > 0 else 0.0
            matrix[i][j] = frac
            matrix[j][i] = frac

    return matrix


# ---------------------------------------------------------------------------
# Portfolio summary
# ---------------------------------------------------------------------------

def print_portfolio_summary(brackets, bracket_structure, teams,
                            bracket_results=None, locked_picks=None):
    """Print portfolio-level analysis across all 10 brackets.

    Shows champion table, upset counts, simulation scores (if available),
    and pick correlation matrix.

    Args:
        brackets: list of Bracket objects.
        bracket_structure: Bracket JSON.
        teams: dict[str, Team].
        bracket_results: Optional list of SimulationResults.
        locked_picks: Optional dict for identifying consensus picks.
    """
    print(f"\n{'='*70}")
    print("PORTFOLIO SUMMARY")
    print(f"{'='*70}")

    # --- Champion table ---
    print(f"\n  {'#':<3} {'Champion':<20} {'Seed':<5} {'Region':<10} "
          f"{'Tier':<15} {'Path':<6}", end="")
    if bracket_results:
        print(f" {'Mean':>6} {'Champ%':>7}", end="")
    print()

    print(f"  {'-'*3} {'-'*20} {'-'*5} {'-'*10} {'-'*15} {'-'*6}", end="")
    if bracket_results:
        print(f" {'-'*6} {'-'*7}", end="")
    print()

    for i, bracket in enumerate(brackets):
        meta = bracket.metadata
        c = bracket.champion
        line = (f"  {meta['bracket_number']:<3} {c.name:<20} "
                f"{c.seed:<5} {c.region:<10} "
                f"{meta['tier']:<15} {meta['path_value']:<6}")
        if bracket_results and i < len(bracket_results):
            r = bracket_results[i]
            line += f" {r.mean_score:6.1f} {r.champion_hit_rate:6.1%}"
        print(line)

    # --- Upset counts ---
    print(f"\n  Upset Counts:")
    print(f"  {'#':<3} {'Champion':<20} {'R1':>4} {'R2+':>4} {'Total':>6}")
    print(f"  {'-'*3} {'-'*20} {'-'*4} {'-'*4} {'-'*6}")

    for bracket in brackets:
        upsets = count_upsets(bracket, bracket_structure, teams)
        r1 = sum(1 for u in upsets if u["round"] == 1)
        later = sum(1 for u in upsets if u["round"] > 1)
        meta = bracket.metadata
        print(f"  {meta['bracket_number']:<3} {bracket.champion.name:<20} "
              f"{r1:>4} {later:>4} {len(upsets):>6}")

    # --- Regional champion distribution ---
    print(f"\n  Regional Champions (E8 Winners):")
    for region_name in ["East", "West", "Midwest", "South"]:
        winners = [b.picks[region_name][4][0].name for b in brackets]
        # Count occurrences
        counts = {}
        for w in winners:
            counts[w] = counts.get(w, 0) + 1
        summary = ", ".join(f"{name} x{c}" for name, c in
                           sorted(counts.items(), key=lambda x: -x[1]))
        print(f"    {region_name:<10}: {summary}")

    # --- Pick correlation matrix ---
    print(f"\n  Pick Correlation Matrix (fraction of 63 games that agree):")
    corr = compute_pick_correlation(brackets)
    n = len(brackets)

    # Header
    header = "       " + "  ".join(f"#{brackets[j].metadata['bracket_number']:>2}" for j in range(n))
    print(f"  {header}")

    for i in range(n):
        bn = brackets[i].metadata['bracket_number']
        row = f"  #{bn:>2}  "
        for j in range(n):
            if i == j:
                row += "  -- "
            else:
                row += f" {corr[i][j]:.2f}"
        print(row)

    # --- Unique bracket check ---
    all_unique = True
    for i in range(n):
        for j in range(i + 1, n):
            if corr[i][j] >= 1.0:
                print(f"\n  [WARN] Brackets #{brackets[i].metadata['bracket_number']} "
                      f"and #{brackets[j].metadata['bracket_number']} are identical!")
                all_unique = False
    if all_unique:
        print(f"\n  [OK] All {n} brackets are unique.")


# ---------------------------------------------------------------------------
# File output for CBS entry
# ---------------------------------------------------------------------------

def write_bracket_file(bracket, filepath, bracket_structure, teams,
                       locked_picks=None):
    """Write a bracket to a text file optimized for CBS manual entry.

    Format: region by region, each game shows seed + team name,
    with flags for upsets [U], consensus picks [C], and champion path (*).

    Args:
        bracket: Bracket object.
        filepath: Output file path.
        bracket_structure: Bracket JSON.
        teams: dict[str, Team].
        locked_picks: Optional dict for [C] flags.
    """
    lines = format_bracket_lines(bracket, bracket_structure, teams, locked_picks)
    with open(filepath, "w") as f:
        f.write("\n".join(lines) + "\n")


def write_portfolio_summary(brackets, filepath, bracket_structure, teams,
                            bracket_results=None, locked_picks=None):
    """Write portfolio summary to a text file."""
    import io
    import sys

    # Capture print_portfolio_summary output
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    print_portfolio_summary(brackets, bracket_structure, teams,
                            bracket_results, locked_picks)
    sys.stdout = old_stdout

    with open(filepath, "w") as f:
        f.write(buffer.getvalue())


def write_all_brackets(brackets, output_dir, bracket_structure, teams,
                       bracket_results=None, locked_picks=None):
    """Write all bracket files and portfolio summary.

    Creates files:
        output_dir/bracket_01_duke.txt
        output_dir/bracket_02_arizona.txt
        ...
        output_dir/portfolio_summary.txt

    Args:
        brackets: list of Bracket objects.
        output_dir: Directory to write files to (e.g., "output/brackets").
        bracket_structure: Bracket JSON.
        teams: dict[str, Team].
        bracket_results: Optional simulation results.
        locked_picks: Optional dict for [C] flags.
    """
    os.makedirs(output_dir, exist_ok=True)

    for bracket in brackets:
        bn = bracket.metadata["bracket_number"]
        champ_slug = bracket.champion.name.lower().replace(" ", "_").replace("'", "")
        filename = f"bracket_{bn:02d}_{champ_slug}.txt"
        filepath = os.path.join(output_dir, filename)
        write_bracket_file(bracket, filepath, bracket_structure, teams, locked_picks)
        print(f"  Written: {filepath}")

    # Portfolio summary
    summary_path = os.path.join(output_dir, "portfolio_summary.txt")
    write_portfolio_summary(brackets, summary_path, bracket_structure, teams,
                            bracket_results, locked_picks)
    print(f"  Written: {summary_path}")
