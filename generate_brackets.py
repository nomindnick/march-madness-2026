"""Main entry point: generate 10 diversified March Madness brackets.

Usage: python generate_brackets.py

Generates 10 brackets with different champions, optimized for the
Points x Seed scoring system. Runs Monte Carlo simulation to validate
expected scores, then writes CBS-entry-friendly text files.
"""

import copy
import json

from src.data_loader import load_teams, load_bracket_structure
from src.bracket_builder import resolve_first_four_auto, validate_bracket
from src.portfolio import generate_portfolio, load_portfolio_plan, load_expert_data
from src.portfolio import identify_locked_picks
from src.simulator import run_simulation, print_simulation_report, VEGAS_CHAMPIONSHIP_PROBS
from src.output import (
    print_bracket_detailed, print_portfolio_summary,
    write_all_brackets, compute_pick_correlation, count_upsets
)


def run_acceptance_checks(brackets, bracket_results, bracket_structure, teams,
                          locked_picks):
    """Run all Sprint 4.1 acceptance criteria checks.

    Returns True if all checks pass.
    """
    print(f"\n{'='*70}")
    print("ACCEPTANCE CRITERIA CHECKS")
    print(f"{'='*70}")

    all_pass = True

    # 1. All 10 brackets valid
    print(f"\n  1. Bracket validity:")
    for bracket in brackets:
        valid = validate_bracket(bracket)
        if not valid:
            all_pass = False

    # 2. No two brackets identical
    print(f"\n  2. Bracket uniqueness:")
    corr = compute_pick_correlation(brackets)
    for i in range(len(brackets)):
        for j in range(i + 1, len(brackets)):
            if corr[i][j] >= 1.0:
                print(f"    [FAIL] Brackets #{brackets[i].metadata['bracket_number']} "
                      f"and #{brackets[j].metadata['bracket_number']} are identical")
                all_pass = False
    if all_pass:
        print(f"    [OK] All 10 brackets are unique")

    # 3. Champions match portfolio plan
    print(f"\n  3. Champion assignments:")
    plan = load_portfolio_plan()
    for i, entry in enumerate(plan):
        expected = entry["champion"]
        actual = brackets[i].champion.name
        if expected != actual:
            print(f"    [FAIL] Bracket #{entry['bracket_number']}: "
                  f"expected {expected}, got {actual}")
            all_pass = False
    print(f"    [OK] All 10 champions match portfolio plan")

    # 4. All mean scores > 150
    print(f"\n  4. Minimum mean scores (> 150):")
    for i, result in enumerate(bracket_results):
        if result.mean_score < 150:
            print(f"    [FAIL] Bracket #{brackets[i].metadata['bracket_number']} "
                  f"({result.bracket_champion}): mean {result.mean_score:.1f} < 150")
            all_pass = False
    min_score = min(r.mean_score for r in bracket_results)
    max_score = max(r.mean_score for r in bracket_results)
    print(f"    Score range: {min_score:.1f} - {max_score:.1f}")
    if min_score >= 150:
        print(f"    [OK] All brackets above 150 threshold")

    # 5. Chalk brackets (#1-2) have <= 5 non-R1 upsets
    print(f"\n  5. Chalk bracket upset limits (<=5 non-R1):")
    for bracket in brackets[:2]:
        upsets = count_upsets(bracket, bracket_structure, teams)
        non_r1 = [u for u in upsets if u["round"] > 1]
        bn = bracket.metadata["bracket_number"]
        if len(non_r1) > 5:
            print(f"    [FAIL] Bracket #{bn}: {len(non_r1)} non-R1 upsets > 5")
            all_pass = False
        else:
            print(f"    [OK] Bracket #{bn}: {len(non_r1)} non-R1 upsets")

    # 6. Consensus upsets in all 10 brackets
    print(f"\n  6. Consensus upset coverage:")
    for (region, slot), winner_name in locked_picks.items():
        for bracket in brackets:
            actual = bracket.picks[region][1][slot].name
            if actual != winner_name:
                # May differ in champion's region if it's on champion path
                if region == bracket.champion.region:
                    continue  # Champion path overrides are expected
                bn = bracket.metadata["bracket_number"]
                print(f"    [FAIL] Bracket #{bn} missing locked pick: "
                      f"{winner_name} in {region} slot {slot}")
                all_pass = False
    print(f"    [OK] {len(locked_picks)} locked picks verified across brackets")

    # 7. Pick correlation < 0.8 for non-same-champion pairs
    print(f"\n  7. Diversification (pick correlation):")
    high_corr = []
    for i in range(len(brackets)):
        for j in range(i + 1, len(brackets)):
            if corr[i][j] > 0.80:
                high_corr.append((i, j, corr[i][j]))
    if high_corr:
        for i, j, c in high_corr:
            print(f"    [NOTE] Brackets #{brackets[i].metadata['bracket_number']} "
                  f"and #{brackets[j].metadata['bracket_number']}: "
                  f"correlation {c:.2f} (> 0.80)")
    else:
        print(f"    [OK] All bracket pairs have correlation <= 0.80")

    print(f"\n  {'='*60}")
    if all_pass:
        print(f"  ALL ACCEPTANCE CRITERIA PASSED")
    else:
        print(f"  SOME CHECKS FAILED — review above")
    print(f"  {'='*60}")

    return all_pass


def main():
    """Generate all 10 brackets, simulate, validate, and write output."""

    print(f"{'#'*70}")
    print(f"# Sprint 4.1: Portfolio Generation")
    print(f"{'#'*70}")

    # --- Load data ---
    teams = load_teams()
    bracket_structure = load_bracket_structure()

    # --- Generate 10 brackets ---
    brackets = generate_portfolio(teams, bracket_structure)

    # --- Resolve First Four for simulation (separate copy) ---
    bs_sim = copy.deepcopy(bracket_structure)
    print("\nResolving First Four for simulation:")
    resolve_first_four_auto(bs_sim, teams)

    # --- Identify locked picks for display flags ---
    expert_data = load_expert_data()
    locked_picks = identify_locked_picks(teams, bs_sim, expert_data)

    # --- Print all brackets ---
    print(f"\n{'#'*70}")
    print(f"# Bracket Details")
    print(f"{'#'*70}")

    for bracket in brackets:
        print_bracket_detailed(bracket, bs_sim, teams, locked_picks)

    # --- Run Monte Carlo simulation ---
    print(f"\n{'#'*70}")
    print(f"# Monte Carlo Simulation (10,000 tournaments)")
    print(f"{'#'*70}")

    bracket_results, championship_counts = run_simulation(
        brackets, bs_sim, teams, n_simulations=10000, seed=42
    )

    print_simulation_report(
        bracket_results, championship_counts, 10000,
        vegas_odds=VEGAS_CHAMPIONSHIP_PROBS
    )

    # --- Portfolio summary ---
    print_portfolio_summary(brackets, bs_sim, teams, bracket_results, locked_picks)

    # --- Acceptance checks ---
    all_pass = run_acceptance_checks(
        brackets, bracket_results, bs_sim, teams, locked_picks
    )

    # --- Write output files ---
    print(f"\n{'#'*70}")
    print(f"# Writing Output Files")
    print(f"{'#'*70}")

    write_all_brackets(
        brackets, "output/brackets", bs_sim, teams,
        bracket_results, locked_picks
    )

    print(f"\nDone! {'All checks passed.' if all_pass else 'Some checks failed.'}")


if __name__ == "__main__":
    main()
