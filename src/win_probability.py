"""Win probability calculator using a logistic model on efficiency margins.

Given two teams' adjusted efficiency margins, estimates P(Team A wins) on
a neutral court. The logistic function is calibrated so that 1 point of
AdjEM difference shifts win probability ~3% from 50%.

This model is standard in college basketball analytics (used by KenPom,
BartTorvik, etc.) and works well for tournament prediction.
"""

import math


# Calibration constant for the logistic model.
# K = 0.1198 means: logistic(0.1198 * 1) ≈ 0.53, so 1 point of AdjEM
# margin ≈ 3% win probability shift from 50%.
#
# Validation targets with typical AdjEM gaps:
#   1-seed vs 16-seed (~38 pt gap): P ≈ 99%
#   5-seed vs 12-seed (~5 pt gap):  P ≈ 65%
#   8-seed vs 9-seed  (~0 pt gap):  P ≈ 50%
K = 0.1198


def win_probability(adj_em_a, adj_em_b):
    """Calculate P(Team A beats Team B) on a neutral court.

    Uses a logistic model: P = 1 / (1 + exp(-K * (AdjEM_A - AdjEM_B)))

    Args:
        adj_em_a: Adjusted efficiency margin for Team A.
        adj_em_b: Adjusted efficiency margin for Team B.

    Returns:
        Float between 0 and 1 — Team A's win probability.
    """
    margin = adj_em_a - adj_em_b
    return 1.0 / (1.0 + math.exp(-K * margin))


def win_probability_teams(team_a, team_b, round_number=1):
    """Calculate P(Team A beats Team B) using Team objects.

    Handles round-dependent AdjEM (e.g., Gonzaga's conditional rating
    changes from Sweet 16 onward).

    Args:
        team_a: Team object for Team A.
        team_b: Team object for Team B.
        round_number: Tournament round (1-6). Affects teams with
                      conditional ratings (Gonzaga).

    Returns:
        Float between 0 and 1 — Team A's win probability.
    """
    # Import here to avoid circular imports
    from src.data_loader import get_adj_em

    em_a = get_adj_em(team_a, round_number)
    em_b = get_adj_em(team_b, round_number)
    return win_probability(em_a, em_b)


def print_matchup(team_a, team_b, round_number=1):
    """Print a formatted matchup line showing win probabilities.

    Example output:
      ( 1) Duke                  99.4%  vs   0.6% (16) Siena

    Args:
        team_a: Team object (typically the higher seed / "top" team).
        team_b: Team object (typically the lower seed / "bottom" team).
        round_number: Tournament round (1-6).
    """
    prob_a = win_probability_teams(team_a, team_b, round_number)
    prob_b = 1.0 - prob_a
    print(f"  ({team_a.seed:>2}) {team_a.name:<22s} {prob_a:5.1%}  vs  {prob_b:5.1%} ({team_b.seed:>2}) {team_b.name}")


# --- Run standalone for quick verification ---
if __name__ == "__main__":
    from src.data_loader import load_teams, load_bracket_structure

    teams = load_teams()
    bracket = load_bracket_structure()

    # Print all first-round matchups for the East region
    print(f"\n{'='*70}")
    print("East Region — Round of 64 Matchups")
    print(f"{'='*70}")

    for matchup in bracket["regions"]["East"]["matchups"]:
        top_name = matchup["top"]["team"]
        bot_name = matchup["bottom"]["team"]

        if top_name and bot_name:
            print_matchup(teams[top_name], teams[bot_name])
        elif bot_name is None:
            ff_id = matchup["bottom"].get("first_four_id", "?")
            print(f"  ({matchup['top']['seed']:>2}) {top_name:<22s}   vs   [First Four {ff_id}]")

    # Calibration check
    print(f"\n{'='*70}")
    print("Calibration Check")
    print(f"{'='*70}")

    # 1v16: Duke vs Siena
    duke = teams["Duke"]
    siena = teams["Siena"]
    p = win_probability_teams(duke, siena)
    status = "OK" if p > 0.95 else "WARN"
    print(f"  [{status}] Duke (1) vs Siena (16): {p:.1%}  (expected ~99%)")

    # 5v12: St. John's vs Northern Iowa
    stj = teams["St. John's"]
    ni = teams["Northern Iowa"]
    p = win_probability_teams(stj, ni)
    status = "OK" if 0.55 < p < 0.80 else "WARN"
    print(f"  [{status}] St. John's (5) vs Northern Iowa (12): {p:.1%}  (expected ~60-70%)")

    # 8v9: Ohio State vs TCU
    osu = teams["Ohio State"]
    tcu = teams["TCU"]
    p = win_probability_teams(osu, tcu)
    status = "OK" if 0.40 < p < 0.60 else "WARN"
    print(f"  [{status}] Ohio State (8) vs TCU (9): {p:.1%}  (expected ~50%)")

    # Gonzaga conditional: show rounds 1-2 vs rounds 3+
    print(f"\n{'='*70}")
    print("Gonzaga Conditional Rating Check")
    print(f"{'='*70}")
    gonz = teams["Gonzaga"]
    ks = teams["Kennesaw State"]
    p_r1 = win_probability_teams(gonz, ks, round_number=1)
    p_r3 = win_probability_teams(gonz, ks, round_number=3)
    print(f"  Gonzaga AdjEM (R1-R2): {gonz.adj_em:+.2f}  (base {gonz.adj_em_base:+.2f}, injury {gonz.adj_em - gonz.adj_em_base:+.1f})")
    print(f"  Gonzaga AdjEM (S16+):  {gonz.sweet_16_adj_em:+.2f}  (base {gonz.adj_em_base:+.2f}, injury {gonz.sweet_16_adj_em - gonz.adj_em_base:+.1f})")
    print(f"  vs Kennesaw State: R1 = {p_r1:.1%}, S16 = {p_r3:.1%}")
