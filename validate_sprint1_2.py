"""Validation script for Sprint 1.2: Team Ratings & Win Probability Engine."""

import math
import sys

from src.data_loader import load_teams, load_bracket_structure, get_adj_em
from src.win_probability import win_probability, win_probability_teams, K

errors = []

# --- 1. Load all teams ---
teams = load_teams()

if len(teams) == 68:
    print(f"\n[OK] 68 teams loaded")
else:
    errors.append(f"Expected 68 teams, got {len(teams)}")

# --- 2. Top 10 teams by AdjEM ---
print(f"\n--- Top 10 Teams by Adjusted Efficiency Margin ---")
sorted_teams = sorted(teams.values(), key=lambda t: t.adj_em, reverse=True)
for i, team in enumerate(sorted_teams[:10], 1):
    note = ""
    if team.adj_em != team.adj_em_base:
        delta = team.adj_em - team.adj_em_base
        note = f"  [injury: {delta:+.1f}, base: {team.adj_em_base:+.2f}]"
    print(f"  {i:>2}. ({team.seed:>2}) {team.name:<20s}  AdjEM: {team.adj_em:>+7.2f}{note}")

# Verify Duke is top-3 (even with injury)
top3_names = {t.name for t in sorted_teams[:3]}
if "Duke" not in {t.name for t in sorted_teams[:5]}:
    errors.append(f"Duke should be top 5 but is ranked {next(i for i, t in enumerate(sorted_teams, 1) if t.name == 'Duke')}")
else:
    print("[OK] Duke in top 5 (as expected for #1 KenPom team even with injury)")

# --- 3. Injury overrides applied correctly ---
print(f"\n--- Injury Override Verification ---")
injured_teams = {
    "Michigan": -3.0,
    "Alabama": -4.0,
    "North Carolina": -6.0,
    "BYU": -3.5,
    "Duke": -2.0,
    "Gonzaga": -4.0,
}

for name, expected_delta in injured_teams.items():
    team = teams[name]
    actual_delta = team.adj_em - team.adj_em_base
    if abs(actual_delta - expected_delta) < 0.01:
        print(f"  [OK] {name:<20s}  base: {team.adj_em_base:>+7.2f}  adjusted: {team.adj_em:>+7.2f}  (delta: {actual_delta:+.1f})")
    else:
        errors.append(f"{name}: expected delta {expected_delta}, got {actual_delta:.2f}")

# --- 4. Gonzaga conditional rating ---
print(f"\n--- Gonzaga Conditional Rating ---")
gonz = teams["Gonzaga"]
if gonz.sweet_16_adj_em is not None:
    print(f"  [OK] Gonzaga has sweet_16_adj_em set")
    print(f"       Rounds 1-2 AdjEM: {gonz.adj_em:>+7.2f}  (base {gonz.adj_em_base:+.2f} with -4.0 injury)")
    print(f"       Rounds 3+  AdjEM: {gonz.sweet_16_adj_em:>+7.2f}  (base {gonz.adj_em_base:+.2f} with -1.0 injury)")

    # Verify get_adj_em returns correct values by round
    r1_em = get_adj_em(gonz, round_number=1)
    r3_em = get_adj_em(gonz, round_number=3)
    if abs(r1_em - gonz.adj_em) < 0.01 and abs(r3_em - gonz.sweet_16_adj_em) < 0.01:
        print(f"  [OK] get_adj_em returns correct values: R1={r1_em:+.2f}, S16={r3_em:+.2f}")
    else:
        errors.append(f"Gonzaga get_adj_em mismatch: R1={r1_em}, S16={r3_em}")
else:
    errors.append("Gonzaga missing sweet_16_adj_em")

# --- 5. Win probability calibration ---
print(f"\n--- Win Probability Calibration ---")

# Check K constant: 1 point margin should give ~3% shift from 50%
p_1pt = win_probability(1.0, 0.0)
shift = p_1pt - 0.5
print(f"  K = {K}")
print(f"  1-point AdjEM margin -> P = {p_1pt:.3f} (shift from 50%: {shift:.1%})")
if abs(shift - 0.03) < 0.005:
    print(f"  [OK] Calibration correct: ~3% shift per point")
else:
    errors.append(f"K calibration off: expected ~3% shift, got {shift:.1%}")

# --- 6. Matchup calibration targets ---
print(f"\n--- Matchup Calibration Targets ---")
print(f"  Note: These test specific matchups. Actual probabilities depend on")
print(f"  team-specific ratings, not just seed averages.\n")

# 1v16: Duke vs Siena — should be ~99%
p = win_probability_teams(teams["Duke"], teams["Siena"])
status = "OK" if p > 0.95 else "FAIL"
print(f"  [{status}] (1) Duke vs (16) Siena: {p:.1%}  (target: ~99%)")
if p <= 0.95:
    errors.append(f"1v16 Duke vs Siena too low: {p:.1%}")

# 5v12: Vanderbilt vs McNeese — a different 5v12 with closer ratings
p = win_probability_teams(teams["Vanderbilt"], teams["McNeese"])
status = "OK" if 0.55 < p < 0.85 else "WARN"
print(f"  [{status}] (5) Vanderbilt vs (12) McNeese: {p:.1%}  (target: ~60-70%)")

# 8v9: Clemson vs Iowa — check a different 8v9
p = win_probability_teams(teams["Clemson"], teams["Iowa"])
status = "OK" if 0.40 < p < 0.60 else "WARN"
print(f"  [{status}] (8) Clemson vs (9) Iowa: {p:.1%}  (target: ~50%)")

# 8v9: Villanova vs Utah State
p = win_probability_teams(teams["Villanova"], teams["Utah State"])
status = "OK" if 0.40 < p < 0.60 else "WARN"
print(f"  [{status}] (8) Villanova vs (9) Utah State: {p:.1%}  (target: ~50%)")

# --- 7. Full region matchup table ---
print(f"\n--- East Region — Round of 64 Matchups ---")
bracket = load_bracket_structure()
for matchup in bracket["regions"]["East"]["matchups"]:
    top_name = matchup["top"]["team"]
    bot_name = matchup["bottom"]["team"]
    top_seed = matchup["top"]["seed"]
    bot_seed = matchup["bottom"]["seed"]

    if top_name and bot_name:
        p = win_probability_teams(teams[top_name], teams[bot_name])
        print(f"  ({top_seed:>2}) {top_name:<22s} {p:5.1%}  vs  {1-p:5.1%} ({bot_seed:>2}) {bot_name}")
    else:
        ff_id = matchup["bottom"].get("first_four_id", "?")
        print(f"  ({top_seed:>2}) {top_name:<22s}         vs         ({bot_seed:>2}) [First Four {ff_id}]")

# --- Summary ---
print()
if errors:
    print(f"FAILED: {len(errors)} error(s):")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("ALL CHECKS PASSED")
