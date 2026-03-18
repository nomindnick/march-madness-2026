"""Expected value scoring engine for the Points x Seed bracket system.

In our pool's scoring system, a correct pick in round R for a team with
seed S earns: base_points[R] x S points. This means higher-seeded (worse)
teams are worth more points when picked correctly.

The key insight: a 12-seed with 35% win probability often has HIGHER
expected value than the 5-seed favorite with 65% probability, because
0.35 x 12 = 4.20 > 0.65 x 5 = 3.25. This engine quantifies that.

This module provides the math layer. It does NOT traverse the bracket tree —
that's bracket_builder's job. It scores individual matchups and multi-round
advancement paths.
"""

from src.win_probability import win_probability_teams


# Points awarded for a correct pick in each round.
# Round 1 (R64) = 1 base point, scaling up to 32 for the championship.
BASE_POINTS = {
    1: 1,    # Round of 64
    2: 2,    # Round of 32
    3: 4,    # Sweet 16
    4: 8,    # Elite 8
    5: 16,   # Final Four
    6: 32,   # Championship
}

# Human-readable round names for display
ROUND_NAMES = {
    1: "R64",
    2: "R32",
    3: "S16",
    4: "E8",
    5: "FF",
    6: "Champ",
}


def score_correct_pick(round_number, seed):
    """Calculate points earned for a correct pick.

    Args:
        round_number: Tournament round (1=R64, 2=R32, 3=S16, 4=E8, 5=FF, 6=Championship).
        seed: The team's seed (1-16).

    Returns:
        int: Points earned = base_points[round] x seed.

    Examples:
        score_correct_pick(1, 12) = 1 x 12 = 12  (R64, 12-seed)
        score_correct_pick(6, 3) = 32 x 3 = 96   (Championship, 3-seed)
        Full champion path for a 3-seed: 3 x (1+2+4+8+16+32) = 3 x 63 = 189
    """
    return BASE_POINTS[round_number] * seed


def ev_of_pick(round_number, team, opponent, round_number_for_prob=None):
    """Calculate the expected value of picking a team to win a single game.

    EV = P(team wins) x base_points[round] x team.seed

    Args:
        round_number: Tournament round (1-6), determines base points.
        team: Team object for the team being picked.
        opponent: Team object for the opposing team.
        round_number_for_prob: Round number passed to win probability model.
            Defaults to round_number. Override this if you need to use a
            different round for Gonzaga's conditional rating.

    Returns:
        float: Expected points from this pick.
    """
    if round_number_for_prob is None:
        round_number_for_prob = round_number

    prob = win_probability_teams(team, opponent, round_number_for_prob)
    points = score_correct_pick(round_number, team.seed)
    return prob * points


def compare_ev(round_number, team_a, team_b):
    """Compare expected value for both sides of a matchup.

    This is the workhorse function — the bracket builder calls this at
    every game node to decide which team to pick.

    Args:
        round_number: Tournament round (1-6).
        team_a: Team object (typically the higher-seeded / favored team).
        team_b: Team object (typically the lower-seeded / underdog).

    Returns:
        tuple: (higher_ev_team, ev_a, ev_b)
            - higher_ev_team: The Team object with higher EV.
            - ev_a: EV of picking team_a.
            - ev_b: EV of picking team_b.
    """
    ev_a = ev_of_pick(round_number, team_a, team_b)
    ev_b = ev_of_pick(round_number, team_b, team_a)

    if ev_a >= ev_b:
        return (team_a, ev_a, ev_b)
    else:
        return (team_b, ev_a, ev_b)


def cumulative_ev(team, opponents_by_round):
    """Calculate total expected points for picking a team through multiple rounds.

    When you pick a team to win in Round 3, they must also win Rounds 1 and 2.
    The probability compounds: P(reach R3) = P(win R1) x P(win R2).

    The cumulative EV sums up each round's contribution:
        EV = sum over each round R:
            P(team wins all rounds up to R) x base_points[R] x seed

    Args:
        team: Team object being picked to advance.
        opponents_by_round: Dict mapping round_number -> opponent Team object.
            Example: {1: first_round_opponent, 2: second_round_opponent}
            Only include rounds where the opponent is known.

    Returns:
        float: Total expected points across all rounds in the path.

    Example:
        A 12-seed with opponents in rounds 1-2:
        R1: P(win) = 0.35, EV_R1 = 0.35 x 1 x 12 = 4.20
        R2: P(reach R2 and win) = 0.35 x 0.15 = 0.0525, EV_R2 = 0.0525 x 2 x 12 = 1.26
        Cumulative EV = 4.20 + 1.26 = 5.46
    """
    total_ev = 0.0
    cumulative_prob = 1.0  # P(team has survived all rounds so far)

    # Process rounds in order
    for round_num in sorted(opponents_by_round.keys()):
        opponent = opponents_by_round[round_num]

        # P(team wins this specific game)
        win_prob = win_probability_teams(team, opponent, round_num)

        # P(team reaches this round AND wins) = cumulative_prob x win_prob
        cumulative_prob *= win_prob

        # EV contribution from this round
        points = score_correct_pick(round_num, team.seed)
        total_ev += cumulative_prob * points

    return total_ev


def champion_path_ev(team, opponents_by_round):
    """Calculate EV for a full champion path (all 6 rounds).

    Convenience wrapper around cumulative_ev. The maximum possible value
    is seed x 63 (if the team were certain to win every game).

    Args:
        team: Team object being picked as champion.
        opponents_by_round: Dict mapping round_number (1-6) -> opponent Team.

    Returns:
        float: Total expected points for the full champion path.
    """
    return cumulative_ev(team, opponents_by_round)


def print_ev_comparison(team_a, team_b, round_number):
    """Print a formatted EV comparison for a single matchup.

    Shows win probability and EV for both teams, with an arrow indicating
    the higher-EV pick. Flags upset-EV situations where the lower seed
    (higher seed number) has better EV.

    Args:
        team_a: Team object (typically top/higher-seeded team in bracket).
        team_b: Team object (typically bottom/lower-seeded team in bracket).
        round_number: Tournament round (1-6).
    """
    prob_a = win_probability_teams(team_a, team_b, round_number)
    prob_b = 1.0 - prob_a
    ev_a = prob_a * score_correct_pick(round_number, team_a.seed)
    ev_b = prob_b * score_correct_pick(round_number, team_b.seed)

    # Determine which pick has higher EV
    if ev_a >= ev_b:
        marker = " >>>"
    else:
        marker = "    "

    # Flag if the lower-seeded team (higher seed number = worse seed) has better EV
    upset_flag = ""
    if team_b.seed > team_a.seed and ev_b > ev_a:
        upset_flag = "  [UPSET EV]"
    elif team_a.seed > team_b.seed and ev_a > ev_b:
        upset_flag = "  [UPSET EV]"

    print(f"  ({team_a.seed:>2}) {team_a.name:<20s} {prob_a:5.1%} EV:{ev_a:5.2f}"
          f"  vs  "
          f"{prob_b:5.1%} EV:{ev_b:5.2f} ({team_b.seed:>2}) {team_b.name:<20s}{upset_flag}")


# --- Run standalone for demo & validation ---
if __name__ == "__main__":
    from src.data_loader import load_teams, load_bracket_structure

    teams = load_teams()
    bracket = load_bracket_structure()

    # === Demo: All R1 matchups with EV analysis ===
    upset_ev_count = 0
    total_matchups = 0

    for region_name in ["East", "West", "Midwest", "South"]:
        region = bracket["regions"][region_name]
        print(f"\n{'='*80}")
        print(f"{region_name} Region — Round of 64: Expected Value Analysis")
        print(f"{'='*80}")
        print(f"  {'Team A':<26s} {'P(A)':>5} {'EV(A)':>6}  {'':4}  {'P(B)':>5} {'EV(B)':>6} {'Team B':<26s}")
        print(f"  {'-'*78}")

        for matchup in region["matchups"]:
            top_name = matchup["top"]["team"]
            bot_name = matchup["bottom"]["team"]

            if top_name and bot_name:
                top = teams[top_name]
                bot = teams[bot_name]

                prob_top = win_probability_teams(top, bot, 1)
                prob_bot = 1.0 - prob_top
                ev_top = prob_top * score_correct_pick(1, top.seed)
                ev_bot = prob_bot * score_correct_pick(1, bot.seed)

                # Flag upset EV (lower seed = higher seed number has better EV)
                upset_flag = ""
                if bot.seed > top.seed and ev_bot > ev_top:
                    upset_flag = "  [UPSET EV]"
                    upset_ev_count += 1

                print(f"  ({top.seed:>2}) {top.name:<22s} {prob_top:5.1%} {ev_top:5.2f}"
                      f"  vs  "
                      f"{prob_bot:5.1%} {ev_bot:5.2f} ({bot.seed:>2}) {bot.name:<22s}{upset_flag}")
                total_matchups += 1
            else:
                ff_id = matchup["bottom"].get("first_four_id") or matchup["top"].get("first_four_id") or "?"
                known = top_name or bot_name or "TBD"
                seed = matchup["top"]["seed"]
                print(f"  ({seed:>2}) {known:<22s}   vs   [First Four {ff_id}]")

    # === Summary ===
    print(f"\n{'='*80}")
    print(f"Summary: {upset_ev_count} of {total_matchups} matchups have UPSET EV")
    print(f"{'='*80}")
    print(f"  In these games, the underdog has higher expected value than the favorite")
    print(f"  because the x Seed multiplier outweighs the lower win probability.")

    # === Seed matchup EV patterns ===
    print(f"\n{'='*80}")
    print(f"EV by Seed Matchup Type (Round 1)")
    print(f"{'='*80}")

    # Group matchups by seed pairing
    from collections import defaultdict
    seed_groups = defaultdict(list)

    for region_name, region_data in bracket["regions"].items():
        for matchup in region_data["matchups"]:
            top_name = matchup["top"]["team"]
            bot_name = matchup["bottom"]["team"]
            if top_name and bot_name:
                top = teams[top_name]
                bot = teams[bot_name]
                key = f"{top.seed}v{bot.seed}"
                prob_top = win_probability_teams(top, bot, 1)
                ev_top = prob_top * score_correct_pick(1, top.seed)
                ev_bot = (1 - prob_top) * score_correct_pick(1, bot.seed)
                seed_groups[key].append({
                    "top": top, "bot": bot,
                    "prob_top": prob_top, "ev_top": ev_top, "ev_bot": ev_bot
                })

    for key in ["1v16", "2v15", "3v14", "4v13", "5v12", "6v11", "7v10", "8v9"]:
        games = seed_groups.get(key, [])
        if not games:
            continue
        upset_count = sum(1 for g in games if g["ev_bot"] > g["ev_top"])
        avg_ev_top = sum(g["ev_top"] for g in games) / len(games)
        avg_ev_bot = sum(g["ev_bot"] for g in games) / len(games)
        winner = "higher seed" if avg_ev_top >= avg_ev_bot else "LOWER SEED"
        print(f"  {key:>4}: Avg EV(top)={avg_ev_top:.2f}  Avg EV(bot)={avg_ev_bot:.2f}"
              f"  -> {winner}  ({upset_count}/{len(games)} upset EV)")

    # === Multi-round cumulative EV example ===
    print(f"\n{'='*80}")
    print(f"Multi-Round Cumulative EV Example")
    print(f"{'='*80}")

    # Pick a 5v12 matchup to demonstrate multi-round EV
    # Use East: St. John's (5) vs Northern Iowa (12)
    if "St. John's" in teams and "Northern Iowa" in teams:
        stj = teams["St. John's"]
        ni = teams["Northern Iowa"]

        # R1 probability
        prob_stj_r1 = win_probability_teams(stj, ni, 1)
        prob_ni_r1 = 1.0 - prob_stj_r1

        print(f"\n  Example: ({stj.seed}) {stj.name} vs ({ni.seed}) {ni.name}")
        print(f"  R1 win probability: {stj.name} {prob_stj_r1:.1%} vs {ni.name} {prob_ni_r1:.1%}")
        print()

        # Single-round EV
        ev_stj_r1 = prob_stj_r1 * score_correct_pick(1, stj.seed)
        ev_ni_r1 = prob_ni_r1 * score_correct_pick(1, ni.seed)
        print(f"  R1 EV: {stj.name} = {prob_stj_r1:.3f} x {score_correct_pick(1, stj.seed)} = {ev_stj_r1:.2f}")
        print(f"  R1 EV: {ni.name} = {prob_ni_r1:.3f} x {score_correct_pick(1, ni.seed)} = {ev_ni_r1:.2f}")
        r1_better = stj.name if ev_stj_r1 >= ev_ni_r1 else ni.name
        print(f"  -> R1 pick: {r1_better}")

        # Find the probable R2 opponent (4v13 winner from same region quadrant)
        # St. John's is slot 2 (5v12), R2 partner is slot 3 (4v13)
        # East slot 3: Kansas (4) vs Norfolk State (13)
        if "Kansas" in teams:
            kansas = teams["Kansas"]
            print(f"\n  Likely R2 opponent: ({kansas.seed}) {kansas.name}")

            # Cumulative EV through R2 for the 5-seed
            cum_stj = cumulative_ev(stj, {1: ni, 2: kansas})
            print(f"  Cumulative EV (R1+R2) for {stj.name}: {cum_stj:.2f}")
            print(f"    R1: {prob_stj_r1:.3f} x {score_correct_pick(1, stj.seed)} = {ev_stj_r1:.2f}")
            prob_stj_r2 = win_probability_teams(stj, kansas, 2)
            r2_contrib = prob_stj_r1 * prob_stj_r2 * score_correct_pick(2, stj.seed)
            print(f"    R2: {prob_stj_r1:.3f} x {prob_stj_r2:.3f} x {score_correct_pick(2, stj.seed)} = {r2_contrib:.2f}")

            # Cumulative EV through R2 for the 12-seed
            cum_ni = cumulative_ev(ni, {1: stj, 2: kansas})
            print(f"  Cumulative EV (R1+R2) for {ni.name}: {cum_ni:.2f}")
            prob_ni_r2 = win_probability_teams(ni, kansas, 2)
            r2_contrib_ni = prob_ni_r1 * prob_ni_r2 * score_correct_pick(2, ni.seed)
            print(f"    R1: {prob_ni_r1:.3f} x {score_correct_pick(1, ni.seed)} = {ev_ni_r1:.2f}")
            print(f"    R2: {prob_ni_r1:.3f} x {prob_ni_r2:.3f} x {score_correct_pick(2, ni.seed)} = {r2_contrib_ni:.2f}")

    # === Champion path value reference ===
    print(f"\n{'='*80}")
    print(f"Champion Path Maximum Values (seed x 63)")
    print(f"{'='*80}")
    for seed in range(1, 17):
        total = seed * 63
        print(f"  {seed:>2}-seed champion path: {total:>4} pts")
