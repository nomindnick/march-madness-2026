"""Validation script for Sprint 1.1 config files."""
import json
import sys

BASE = "/home/nick/Projects/march-madness-2026/config"
errors = []

# Load all config files
try:
    with open(f"{BASE}/bracket_2026.json") as f:
        bracket = json.load(f)
    print("[OK] bracket_2026.json is valid JSON")
except Exception as e:
    errors.append(f"bracket_2026.json: {e}")

try:
    with open(f"{BASE}/injury_overrides.json") as f:
        injuries = json.load(f)
    print("[OK] injury_overrides.json is valid JSON")
except Exception as e:
    errors.append(f"injury_overrides.json: {e}")

try:
    with open(f"{BASE}/portfolio_plan.json") as f:
        portfolio = json.load(f)
    print("[OK] portfolio_plan.json is valid JSON")
except Exception as e:
    errors.append(f"portfolio_plan.json: {e}")

# Collect all team names from bracket
all_teams = set()
first_four_ids_defined = set()
first_four_ids_referenced = set()

# First Four teams
for ff in bracket["first_four"]:
    first_four_ids_defined.add(ff["id"])
    for t in ff["teams"]:
        all_teams.add(t)

# Region teams
for region_name, region in bracket["regions"].items():
    matchups = region["matchups"]

    # Check 8 matchups per region
    if len(matchups) != 8:
        errors.append(f"{region_name}: expected 8 matchups, got {len(matchups)}")

    seeds_found = set()
    for m in matchups:
        for side in ["top", "bottom"]:
            team = m[side]["team"]
            seed = m[side]["seed"]
            seeds_found.add(seed)
            if team is not None:
                all_teams.add(team)
            else:
                ff_id = m[side].get("first_four_id")
                if ff_id:
                    first_four_ids_referenced.add(ff_id)
                else:
                    errors.append(f"{region_name} slot {m['slot']}: null team without first_four_id")

    expected_seeds = set(range(1, 17))
    if seeds_found != expected_seeds:
        missing = expected_seeds - seeds_found
        extra = seeds_found - expected_seeds
        errors.append(f"{region_name}: seed issues - missing {missing}, extra {extra}")
    else:
        print(f"[OK] {region_name}: all seeds 1-16 present")

# First Four ID cross-reference
if first_four_ids_defined == first_four_ids_referenced:
    print(f"[OK] First Four IDs match: {sorted(first_four_ids_defined)}")
else:
    errors.append(f"First Four ID mismatch - defined: {first_four_ids_defined}, referenced: {first_four_ids_referenced}")

# Total team count
print(f"\n[INFO] Total unique team names: {len(all_teams)}")
if len(all_teams) == 68:
    print("[OK] 68 unique teams confirmed")
else:
    errors.append(f"Expected 68 unique teams, got {len(all_teams)}")

# Injury override team names exist in bracket
for team in injuries["overrides"]:
    if team in all_teams:
        print(f"[OK] Injury override '{team}' found in bracket")
    else:
        errors.append(f"Injury override team '{team}' not found in bracket")

# Portfolio champion names exist in bracket
for b in portfolio["portfolio"]:
    champ = b["champion"]
    if champ == "TBD":
        print(f"[OK] Bracket {b['bracket_number']}: champion TBD (skipped)")
    elif champ in all_teams:
        print(f"[OK] Bracket {b['bracket_number']}: champion '{champ}' found in bracket")
    else:
        errors.append(f"Bracket {b['bracket_number']}: champion '{champ}' not found in bracket")

# Final Four regions check
ff_regions = set(bracket["final_four"]["semifinal_1"] + bracket["final_four"]["semifinal_2"])
bracket_regions = set(bracket["regions"].keys())
if ff_regions == bracket_regions:
    print("[OK] Final Four covers all 4 regions")
else:
    errors.append(f"Final Four regions {ff_regions} != bracket regions {bracket_regions}")

# Sample output: East region
print("\n--- Sample: East Region ---")
for m in bracket["regions"]["East"]["matchups"]:
    top = m["top"]
    bot = m["bottom"]
    bot_name = bot["team"] if bot["team"] else f"[First Four {bot.get('first_four_id', '?')}]"
    print(f"  Slot {m['slot']}: ({top['seed']}) {top['team']}  vs  ({bot['seed']}) {bot_name}")

# Summary
print()
if errors:
    print(f"FAILED: {len(errors)} error(s):")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("ALL CHECKS PASSED")
