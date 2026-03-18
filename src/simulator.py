"""Monte Carlo tournament simulator for bracket validation.

Simulates the NCAA tournament thousands of times using win probabilities
from the logistic model. Scores brackets against simulated outcomes using
the Points x Seed scoring system. This validates that EV-optimized brackets
actually outscore chalk brackets in expectation.

Key outputs:
- Championship probability per team (calibrated against Vegas odds)
- Expected score distribution for each bracket
- Confirmation that EV optimization works under x Seed scoring
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np

from src.data_loader import Team, load_teams, load_bracket_structure, get_adj_em
from src.win_probability import win_probability_teams
from src.ev_engine import score_correct_pick, BASE_POINTS, ROUND_NAMES
from src.bracket_builder import (
    Bracket, build_bracket, get_region_matchups, resolve_first_four_auto
)


# ---------------------------------------------------------------------------
# Vegas championship probabilities for calibration (from Sprint 3.1)
# ---------------------------------------------------------------------------

VEGAS_CHAMPIONSHIP_PROBS = {
    "Duke": 0.22,
    "Michigan": 0.20,
    "Arizona": 0.19,
    "Florida": 0.12,
    "Houston": 0.09,
    "UConn": 0.056,
    "Illinois": 0.05,
    "Iowa State": 0.045,
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SimulatedTournament:
    """A single simulated tournament outcome.

    The picks dict has the same structure as Bracket.picks:
        {region_name: {round_number: [Team winners]}}
    This makes scoring a bracket against the simulation straightforward —
    just compare team names at the same position.
    """
    picks: dict         # {region_name: {round_number: [Team winners]}}
    final_four: dict    # Same keys as Bracket.final_four
    champion: Team


@dataclass
class BracketScore:
    """Score results for one bracket against one simulated tournament."""
    total_score: int
    round_scores: dict        # {round_number: int} — score contribution per round
    champion_correct: bool


@dataclass
class SimulationResults:
    """Aggregate results from N simulations for a single bracket."""
    bracket_champion: str
    n_simulations: int
    mean_score: float
    median_score: float
    percentile_10: float
    percentile_90: float
    std_score: float
    champion_hit_rate: float
    scores: list              # Raw score list for distribution analysis


# ---------------------------------------------------------------------------
# Core simulation functions
# ---------------------------------------------------------------------------

def simulate_game(team_a, team_b, round_number, rng):
    """Simulate a single game between two teams.

    Uses win_probability_teams() to get P(A wins), then draws a random
    number to determine the winner. The round_number matters because
    Gonzaga has different AdjEM for rounds 1-2 vs 3+.

    Args:
        team_a: Team object.
        team_b: Team object.
        round_number: Tournament round (1-6).
        rng: numpy random generator (from numpy.random.default_rng).

    Returns:
        Team: The winning team.
    """
    prob_a = win_probability_teams(team_a, team_b, round_number)
    return team_a if rng.random() < prob_a else team_b


def simulate_region(matchups, rng):
    """Simulate all 4 rounds within one region.

    Follows the same bracket tree structure as fill_region_ev() in
    bracket_builder.py, but uses random outcomes instead of EV optimization.

    Args:
        matchups: List of 8 (top_team, bottom_team) tuples, slot-ordered.
            Same format returned by get_region_matchups().
        rng: numpy random generator.

    Returns:
        dict: {round_number: [Team winners]} for rounds 1-4.
            R1: 8 winners, R2: 4, S16: 2, E8: 1.
    """
    picks = {}

    # Round 1: 8 games
    r1 = []
    for top, bot in matchups:
        winner = simulate_game(top, bot, 1, rng)
        r1.append(winner)
    picks[1] = r1

    # Round 2: 4 games (pair consecutive R1 winners)
    r2 = []
    for i in range(0, 8, 2):
        winner = simulate_game(r1[i], r1[i + 1], 2, rng)
        r2.append(winner)
    picks[2] = r2

    # Sweet 16: 2 games
    s16 = []
    for i in range(0, 4, 2):
        winner = simulate_game(r2[i], r2[i + 1], 3, rng)
        s16.append(winner)
    picks[3] = s16

    # Elite 8: 1 game (regional final)
    winner = simulate_game(s16[0], s16[1], 4, rng)
    picks[4] = [winner]

    return picks


def simulate_tournament(bracket_structure, teams, rng):
    """Simulate a complete 63-game tournament.

    First Four games must already be resolved in bracket_structure before
    calling this function (consistent with build_bracket's approach).

    Args:
        bracket_structure: dict from load_bracket_structure(), First Four resolved.
        teams: dict[str, Team] from load_teams().
        rng: numpy random generator.

    Returns:
        SimulatedTournament with all 63 game results.
    """
    # Simulate each region
    picks = {}
    for region_name in bracket_structure["regions"]:
        matchups = get_region_matchups(region_name, bracket_structure, teams)
        picks[region_name] = simulate_region(matchups, rng)

    # Final Four setup
    sf1_regions = bracket_structure["final_four"]["semifinal_1"]  # ["East", "South"]
    sf2_regions = bracket_structure["final_four"]["semifinal_2"]  # ["West", "Midwest"]

    sf1_team1 = picks[sf1_regions[0]][4][0]  # East E8 winner
    sf1_team2 = picks[sf1_regions[1]][4][0]  # South E8 winner
    sf2_team1 = picks[sf2_regions[0]][4][0]  # West E8 winner
    sf2_team2 = picks[sf2_regions[1]][4][0]  # Midwest E8 winner

    # Semifinal 1 (round 5)
    sf1_winner = simulate_game(sf1_team1, sf1_team2, 5, rng)
    # Semifinal 2 (round 5)
    sf2_winner = simulate_game(sf2_team1, sf2_team2, 5, rng)
    # Championship (round 6)
    champion = simulate_game(sf1_winner, sf2_winner, 6, rng)

    final_four = {
        "sf1_team1": sf1_team1,
        "sf1_team2": sf1_team2,
        "sf2_team1": sf2_team1,
        "sf2_team2": sf2_team2,
        "sf1_winner": sf1_winner,
        "sf2_winner": sf2_winner,
        "champion": champion,
    }

    return SimulatedTournament(
        picks=picks,
        final_four=final_four,
        champion=champion,
    )


# ---------------------------------------------------------------------------
# Bracket scoring
# ---------------------------------------------------------------------------

def score_bracket(bracket, simulated):
    """Score a bracket against a simulated tournament outcome.

    Compares each pick in the bracket to the corresponding winner in the
    simulation. Awards base_points[round] x seed for each correct pick.
    Uses positional comparison — same region, round, and index.

    Args:
        bracket: Bracket object (from build_bracket).
        simulated: SimulatedTournament object.

    Returns:
        BracketScore with total score and per-round breakdown.
    """
    total = 0
    round_scores = defaultdict(int)

    # Score regional picks (rounds 1-4)
    for region_name in bracket.picks:
        bracket_region = bracket.picks[region_name]
        sim_region = simulated.picks[region_name]

        for round_num in [1, 2, 3, 4]:
            bracket_winners = bracket_region[round_num]
            sim_winners = sim_region[round_num]

            for idx, bracket_team in enumerate(bracket_winners):
                if bracket_team.name == sim_winners[idx].name:
                    pts = score_correct_pick(round_num, bracket_team.seed)
                    total += pts
                    round_scores[round_num] += pts

    # Score Final Four semifinals (round 5)
    # SF1 winner
    if bracket.final_four["sf1_winner"].name == simulated.final_four["sf1_winner"].name:
        pts = score_correct_pick(5, bracket.final_four["sf1_winner"].seed)
        total += pts
        round_scores[5] += pts

    # SF2 winner
    if bracket.final_four["sf2_winner"].name == simulated.final_four["sf2_winner"].name:
        pts = score_correct_pick(5, bracket.final_four["sf2_winner"].seed)
        total += pts
        round_scores[5] += pts

    # Score Championship (round 6)
    champion_correct = (bracket.champion.name == simulated.champion.name)
    if champion_correct:
        pts = score_correct_pick(6, bracket.champion.seed)
        total += pts
        round_scores[6] += pts

    return BracketScore(
        total_score=total,
        round_scores=dict(round_scores),
        champion_correct=champion_correct,
    )


# ---------------------------------------------------------------------------
# Main simulation loop
# ---------------------------------------------------------------------------

def run_simulation(brackets, bracket_structure, teams, n_simulations=10000, seed=42):
    """Run Monte Carlo simulation and score brackets.

    Simulates the tournament n_simulations times. For each simulation,
    scores every bracket against the same simulated outcome (this captures
    correlation between brackets for portfolio analysis).

    Also tracks how often each team wins the championship.

    Args:
        brackets: List of Bracket objects to score.
        bracket_structure: dict from load_bracket_structure() (First Four resolved).
        teams: dict[str, Team].
        n_simulations: Number of tournament simulations (default 10,000).
        seed: Random seed for reproducibility (default 42).

    Returns:
        tuple: (bracket_results, championship_counts)
            - bracket_results: list of SimulationResults, one per bracket.
            - championship_counts: dict[str, int] mapping team name to
              number of championship wins.
    """
    rng = np.random.default_rng(seed)

    # Initialize score tracking: one list per bracket
    all_scores = [[] for _ in brackets]
    champion_correct_counts = [0 for _ in brackets]
    championship_counts = defaultdict(int)

    start_time = time.time()

    for sim_num in range(1, n_simulations + 1):
        # Simulate one tournament
        simulated = simulate_tournament(bracket_structure, teams, rng)
        championship_counts[simulated.champion.name] += 1

        # Score every bracket against this simulation
        for b_idx, bracket in enumerate(brackets):
            result = score_bracket(bracket, simulated)
            all_scores[b_idx].append(result.total_score)
            if result.champion_correct:
                champion_correct_counts[b_idx] += 1

        # Progress update every 1000 simulations
        if sim_num % 1000 == 0:
            elapsed = time.time() - start_time
            print(f"  Simulated {sim_num:,} / {n_simulations:,} tournaments... ({elapsed:.1f}s)")

    elapsed = time.time() - start_time
    print(f"  Done: {n_simulations:,} simulations in {elapsed:.1f}s")

    # Build results for each bracket
    bracket_results = []
    for b_idx, bracket in enumerate(brackets):
        scores = np.array(all_scores[b_idx])
        bracket_results.append(SimulationResults(
            bracket_champion=bracket.champion.name,
            n_simulations=n_simulations,
            mean_score=float(np.mean(scores)),
            median_score=float(np.median(scores)),
            percentile_10=float(np.percentile(scores, 10)),
            percentile_90=float(np.percentile(scores, 90)),
            std_score=float(np.std(scores)),
            champion_hit_rate=champion_correct_counts[b_idx] / n_simulations,
            scores=all_scores[b_idx],
        ))

    return bracket_results, dict(championship_counts)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def championship_probabilities(championship_counts, n_simulations):
    """Convert championship counts to sorted probability list.

    Args:
        championship_counts: dict[str, int] from run_simulation.
        n_simulations: Total simulations run.

    Returns:
        list of (team_name, probability, count) tuples, sorted by probability desc.
    """
    probs = []
    for name, count in championship_counts.items():
        probs.append((name, count / n_simulations, count))
    return sorted(probs, key=lambda x: x[1], reverse=True)


def print_simulation_report(bracket_results, championship_counts, n_simulations,
                            vegas_odds=None):
    """Print a comprehensive simulation report.

    Shows:
    1. Championship probability table (with Vegas comparison if provided)
    2. Each bracket's expected score distribution
    3. Key validation findings

    Args:
        bracket_results: List of SimulationResults.
        championship_counts: dict from run_simulation.
        n_simulations: Total simulations.
        vegas_odds: Optional dict {team_name: probability} for calibration.
    """
    # === Championship Probabilities ===
    probs = championship_probabilities(championship_counts, n_simulations)

    print(f"\n{'='*80}")
    if vegas_odds:
        print(f"Championship Probabilities: Model vs Vegas ({n_simulations:,} simulations)")
        print(f"{'='*80}")
        print(f"  {'Team':<22s} {'Model':>7} {'Vegas':>7} {'Delta':>7}  {'Flag'}")
        print(f"  {'-'*22} {'-'*7} {'-'*7} {'-'*7}  {'-'*10}")

        for name, prob, count in probs[:20]:  # Top 20
            vegas = vegas_odds.get(name)
            if vegas:
                delta = prob - vegas
                # Flag if our model differs from Vegas by more than 2x
                flag = ""
                if vegas > 0.01:  # Only flag meaningful probabilities
                    ratio = prob / vegas if vegas > 0 else float('inf')
                    if ratio > 2.0 or ratio < 0.5:
                        flag = "[CHECK]"
                print(f"  {name:<22s} {prob:6.1%} {vegas:6.1%} {delta:+6.1%}  {flag}")
            else:
                print(f"  {name:<22s} {prob:6.1%}      -       -")
    else:
        print(f"Championship Probabilities ({n_simulations:,} simulations)")
        print(f"{'='*80}")
        print(f"  {'Team':<22s} {'Prob':>7} {'Count':>7}")
        print(f"  {'-'*22} {'-'*7} {'-'*7}")

        for name, prob, count in probs[:20]:
            print(f"  {name:<22s} {prob:6.1%} {count:>7,}")

    # === Bracket Score Distributions ===
    print(f"\n{'='*80}")
    print(f"Bracket Score Distributions")
    print(f"{'='*80}")
    print(f"  {'Bracket':<28s} {'Mean':>6} {'Median':>7} {'10th':>6} {'90th':>6} {'StdDev':>7} {'Champ%':>7}")
    print(f"  {'-'*28} {'-'*6} {'-'*7} {'-'*6} {'-'*6} {'-'*7} {'-'*7}")

    for result in bracket_results:
        label = result.bracket_champion
        print(f"  {label:<28s} {result.mean_score:6.1f} {result.median_score:7.1f}"
              f" {result.percentile_10:6.1f} {result.percentile_90:6.1f}"
              f" {result.std_score:7.1f} {result.champion_hit_rate:6.1%}")

    # === Key Validation ===
    if len(bracket_results) >= 2:
        print(f"\n{'='*80}")
        print(f"Key Validation")
        print(f"{'='*80}")

        # Find best and worst brackets by mean score
        sorted_results = sorted(bracket_results, key=lambda r: r.mean_score, reverse=True)
        best = sorted_results[0]
        worst = sorted_results[-1]

        print(f"  Best bracket:  {best.bracket_champion} (mean {best.mean_score:.1f})")
        print(f"  Worst bracket: {worst.bracket_champion} (mean {worst.mean_score:.1f})")
        diff = best.mean_score - worst.mean_score
        pct = diff / worst.mean_score * 100 if worst.mean_score > 0 else 0
        print(f"  Advantage: +{diff:.1f} points ({pct:+.1f}%)")


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import copy

    teams = load_teams()
    bracket_structure = load_bracket_structure()

    print(f"\n{'#'*80}")
    print(f"# Sprint 2.3: Monte Carlo Simulator Demo")
    print(f"{'#'*80}")

    # Resolve First Four once (shared across bracket builds and simulation)
    bs = copy.deepcopy(bracket_structure)
    resolve_first_four_auto(bs, teams)

    # Build two brackets for comparison
    # Houston (2-seed South) — EV-optimized with higher-seed champion
    houston_bracket = build_bracket("Houston", teams, bracket_structure)
    # Duke (1-seed East) — chalk-style bracket
    duke_bracket = build_bracket("Duke", teams, bracket_structure)

    brackets = [houston_bracket, duke_bracket]

    # Run simulation
    print(f"\n{'='*80}")
    print(f"Running Monte Carlo Simulation: 10,000 tournaments")
    print(f"{'='*80}")

    bracket_results, championship_counts = run_simulation(
        brackets, bs, teams, n_simulations=10000, seed=42
    )

    # Print full report with Vegas comparison
    print_simulation_report(
        bracket_results, championship_counts, 10000,
        vegas_odds=VEGAS_CHAMPIONSHIP_PROBS
    )

    # Final validation message
    houston_result = bracket_results[0]
    duke_result = bracket_results[1]
    if houston_result.mean_score > duke_result.mean_score:
        diff = houston_result.mean_score - duke_result.mean_score
        print(f"\n  [OK] EV-optimized Houston bracket ({houston_result.mean_score:.1f}) "
              f"outscores chalk Duke ({duke_result.mean_score:.1f}) by {diff:.1f} pts")
    else:
        diff = duke_result.mean_score - houston_result.mean_score
        print(f"\n  [WARN] Chalk Duke ({duke_result.mean_score:.1f}) outscores "
              f"Houston ({houston_result.mean_score:.1f}) by {diff:.1f} pts")
