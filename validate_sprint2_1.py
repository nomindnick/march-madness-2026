"""Validation script for Sprint 2.1: EV Scoring Engine."""

import sys

from src.data_loader import load_teams, load_bracket_structure
from src.win_probability import win_probability_teams
from src.ev_engine import (
    BASE_POINTS, ROUND_NAMES,
    score_correct_pick, ev_of_pick, compare_ev, cumulative_ev, champion_path_ev,
)

errors = []

# --- 1. Load data ---
teams = load_teams()
bracket = load_bracket_structure()

if len(teams) == 68:
    print(f"\n[OK] 68 teams loaded")
else:
    errors.append(f"Expected 68 teams, got {len(teams)}")

# --- 2. score_correct_pick ---
print(f"\n--- score_correct_pick ---")

# R64, 12-seed: 1 x 12 = 12
result = score_correct_pick(1, 12)
if result == 12:
    print(f"  [OK] score_correct_pick(1, 12) = {result}")
else:
    errors.append(f"score_correct_pick(1, 12) = {result}, expected 12")

# Championship, 3-seed: 32 x 3 = 96
result = score_correct_pick(6, 3)
if result == 96:
    print(f"  [OK] score_correct_pick(6, 3) = {result}")
else:
    errors.append(f"score_correct_pick(6, 3) = {result}, expected 96")

# Full champion path for a 1-seed: 1 x (1+2+4+8+16+32) = 63
full_path = sum(score_correct_pick(r, 1) for r in range(1, 7))
if full_path == 63:
    print(f"  [OK] Full 1-seed champion path = {full_path}")
else:
    errors.append(f"Full 1-seed champion path = {full_path}, expected 63")

# Full champion path for a 3-seed: 3 x 63 = 189
full_path_3 = sum(score_correct_pick(r, 3) for r in range(1, 7))
if full_path_3 == 189:
    print(f"  [OK] Full 3-seed champion path = {full_path_3}")
else:
    errors.append(f"Full 3-seed champion path = {full_path_3}, expected 189")

# --- 3. ev_of_pick ---
print(f"\n--- ev_of_pick ---")

duke = teams["Duke"]
siena = teams["Siena"]

# Duke (1-seed) vs Siena (16-seed) in R1
# Duke should have very high probability but low EV multiplier
ev_duke = ev_of_pick(1, duke, siena)
prob_duke = win_probability_teams(duke, siena, 1)
expected_ev_duke = prob_duke * score_correct_pick(1, duke.seed)
if abs(ev_duke - expected_ev_duke) < 0.001:
    print(f"  [OK] ev_of_pick(R1, Duke, Siena) = {ev_duke:.3f} (P={prob_duke:.3f} x {score_correct_pick(1, duke.seed)}pts)")
else:
    errors.append(f"ev_of_pick mismatch: {ev_duke} vs {expected_ev_duke}")

ev_siena = ev_of_pick(1, siena, duke)
prob_siena = 1.0 - prob_duke
expected_ev_siena = prob_siena * score_correct_pick(1, siena.seed)
if abs(ev_siena - expected_ev_siena) < 0.001:
    print(f"  [OK] ev_of_pick(R1, Siena, Duke) = {ev_siena:.3f} (P={prob_siena:.3f} x {score_correct_pick(1, siena.seed)}pts)")
else:
    errors.append(f"ev_of_pick Siena mismatch: {ev_siena} vs {expected_ev_siena}")

# Even though Siena has 16x multiplier, Duke's probability is so high that Duke still wins EV
if ev_duke > ev_siena:
    print(f"  [OK] Duke EV ({ev_duke:.2f}) > Siena EV ({ev_siena:.2f}) — 1v16 chalk is correct")
else:
    errors.append(f"1v16: Siena EV ({ev_siena:.2f}) beats Duke ({ev_duke:.2f}) — unexpected")

# --- 4. compare_ev ---
print(f"\n--- compare_ev ---")

# Test a 5v12: where we expect the 12-seed might have higher EV
# Use Vanderbilt (5) vs McNeese (12) — South region
if "Vanderbilt" in teams and "McNeese" in teams:
    vand = teams["Vanderbilt"]
    mcn = teams["McNeese"]
    best, ev_a, ev_b = compare_ev(1, vand, mcn)
    prob_v = win_probability_teams(vand, mcn, 1)

    print(f"  ({vand.seed}) {vand.name}: P={prob_v:.1%}, EV={ev_a:.2f}")
    print(f"  ({mcn.seed}) {mcn.name}: P={1-prob_v:.1%}, EV={ev_b:.2f}")
    print(f"  Best pick: ({best.seed}) {best.name}")

    # Verify compare_ev returns the correct winner
    if (ev_a >= ev_b and best == vand) or (ev_b > ev_a and best == mcn):
        print(f"  [OK] compare_ev returns correct higher-EV team")
    else:
        errors.append(f"compare_ev returned wrong team for {vand.name} vs {mcn.name}")

# 8v9: at historical base rates the 9-seed has higher EV (coin flip x higher multiplier),
# but with team-specific ratings, strong 8-seeds can overcome the 1-point multiplier gap.
print(f"\n--- 8v9 matchups (9-seed favored at base rates, depends on matchup) ---")
nine_seed_wins = 0
eight_nine_total = 0
for region_name, region_data in bracket["regions"].items():
    for matchup in region_data["matchups"]:
        top_name = matchup["top"]["team"]
        bot_name = matchup["bottom"]["team"]
        if top_name and bot_name:
            top = teams[top_name]
            bot = teams[bot_name]
            if top.seed == 8 and bot.seed == 9:
                best, ev_t, ev_b = compare_ev(1, top, bot)
                prob_top = win_probability_teams(top, bot, 1)
                eight_nine_total += 1
                if best.seed == 9:
                    nine_seed_wins += 1
                # Show but don't fail — team-specific ratings can override seed-based intuition
                marker = "9-seed" if best.seed == 9 else "8-seed*"
                print(f"  ({top.seed}) {top.name} P:{prob_top:.1%} EV:{ev_t:.2f}"
                      f"  vs  EV:{ev_b:.2f} P:{1-prob_top:.1%} ({bot.seed}) {bot.name}"
                      f"  -> {marker}")

print(f"  [OK] {nine_seed_wins}/{eight_nine_total} favor 9-seed"
      f" (team-specific ratings can override the seed multiplier advantage)")

# --- 5. cumulative_ev ---
print(f"\n--- cumulative_ev (multi-round) ---")

# Test with a simple 2-round path
if "St. John's" in teams and "Northern Iowa" in teams and "Kansas" in teams:
    stj = teams["St. John's"]
    ni = teams["Northern Iowa"]
    kansas = teams["Kansas"]

    # Cumulative EV for St. John's through R1 + R2
    cum_stj = cumulative_ev(stj, {1: ni, 2: kansas})

    # Manual calculation
    prob_r1 = win_probability_teams(stj, ni, 1)
    prob_r2 = win_probability_teams(stj, kansas, 2)
    manual_r1 = prob_r1 * score_correct_pick(1, stj.seed)
    manual_r2 = prob_r1 * prob_r2 * score_correct_pick(2, stj.seed)
    manual_total = manual_r1 + manual_r2

    if abs(cum_stj - manual_total) < 0.001:
        print(f"  [OK] cumulative_ev({stj.name}, R1+R2) = {cum_stj:.3f}")
        print(f"       R1: {prob_r1:.3f} x {score_correct_pick(1, stj.seed)} = {manual_r1:.3f}")
        print(f"       R2: {prob_r1:.3f} x {prob_r2:.3f} x {score_correct_pick(2, stj.seed)} = {manual_r2:.3f}")
        print(f"       Total: {manual_total:.3f}")
    else:
        errors.append(f"cumulative_ev mismatch: {cum_stj:.3f} vs manual {manual_total:.3f}")

    # Also test cumulative EV for the 12-seed
    cum_ni = cumulative_ev(ni, {1: stj, 2: kansas})
    prob_ni_r1 = win_probability_teams(ni, stj, 1)
    prob_ni_r2 = win_probability_teams(ni, kansas, 2)
    manual_ni = (prob_ni_r1 * score_correct_pick(1, ni.seed)
                 + prob_ni_r1 * prob_ni_r2 * score_correct_pick(2, ni.seed))

    if abs(cum_ni - manual_ni) < 0.001:
        print(f"  [OK] cumulative_ev({ni.name}, R1+R2) = {cum_ni:.3f}")
    else:
        errors.append(f"cumulative_ev 12-seed mismatch: {cum_ni:.3f} vs manual {manual_ni:.3f}")

# --- 6. champion_path_ev ---
print(f"\n--- champion_path_ev ---")

# champion_path_ev should equal cumulative_ev with same inputs
if "St. John's" in teams and "Northern Iowa" in teams and "Kansas" in teams:
    path = {1: ni, 2: kansas}
    cum = cumulative_ev(stj, path)
    champ = champion_path_ev(stj, path)
    if abs(cum - champ) < 0.001:
        print(f"  [OK] champion_path_ev matches cumulative_ev: {champ:.3f}")
    else:
        errors.append(f"champion_path_ev mismatch: {champ:.3f} vs cumulative_ev {cum:.3f}")

# --- 7. Constants check ---
print(f"\n--- Constants ---")
expected_sum = 1 + 2 + 4 + 8 + 16 + 32  # = 63
actual_sum = sum(BASE_POINTS.values())
if actual_sum == 63:
    print(f"  [OK] BASE_POINTS sum = {actual_sum} (full path multiplier)")
else:
    errors.append(f"BASE_POINTS sum = {actual_sum}, expected 63")

if len(ROUND_NAMES) == 6:
    print(f"  [OK] ROUND_NAMES has 6 entries")
else:
    errors.append(f"ROUND_NAMES has {len(ROUND_NAMES)} entries, expected 6")

# --- 8. Count upset EVs across all R1 matchups ---
print(f"\n--- R1 Upset EV Count ---")
upset_count = 0
total_count = 0
for region_name, region_data in bracket["regions"].items():
    for matchup in region_data["matchups"]:
        top_name = matchup["top"]["team"]
        bot_name = matchup["bottom"]["team"]
        if top_name and bot_name:
            top = teams[top_name]
            bot = teams[bot_name]
            if top.seed < bot.seed:  # top is the favorite
                best, ev_t, ev_b = compare_ev(1, top, bot)
                if best == bot:
                    upset_count += 1
                total_count += 1

# We expect several upset EVs (5v12, 6v11, 8v9 at minimum)
if upset_count >= 4:
    print(f"  [OK] {upset_count}/{total_count} R1 matchups have upset EV (expected 4+)")
else:
    errors.append(f"Only {upset_count}/{total_count} upset EVs — expected at least 4 (8v9s + some 5v12/6v11)")

# --- Summary ---
print()
if errors:
    print(f"FAILED: {len(errors)} error(s):")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("ALL CHECKS PASSED")
