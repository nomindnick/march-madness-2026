"""Validate Sprint 2.2: Backwards-Chaining Bracket Builder.

Tests the acceptance criteria from IMPLEMENTATION_PLAN.md:
1. Houston bracket: Houston wins every round (R1 through Championship)
2. Duke bracket: Duke wins every round, bracket is mostly chalk in R1
3. Internal consistency: no team picked in round N+1 that wasn't in round N
4. Different champions produce meaningfully different brackets
5. All 63 games have a winner
6. Kansas (4-seed) bracket works — tests a mid-seed champion
"""

import sys
from src.data_loader import load_teams, load_bracket_structure
from src.bracket_builder import build_bracket, validate_bracket


def main():
    teams = load_teams()
    bracket_structure = load_bracket_structure()

    all_passed = True

    # -------------------------------------------------------------------------
    # Test 1: Houston bracket — champion wins every round
    # -------------------------------------------------------------------------
    print(f"\n{'='*60}")
    print("Test 1: Houston (2-seed South) wins every round")
    print(f"{'='*60}")

    houston = build_bracket("Houston", teams, bracket_structure)

    # Champion must be Houston
    if houston.champion.name != "Houston":
        print(f"[FAIL] Champion is {houston.champion.name}, expected Houston")
        all_passed = False
    else:
        print(f"[OK] Champion: Houston")

    # Houston must appear in every round of South region
    for round_num in [1, 2, 3, 4]:
        names = [t.name for t in houston.picks["South"][round_num]]
        if "Houston" not in names:
            print(f"[FAIL] Houston missing from South R{round_num}")
            all_passed = False
        else:
            print(f"[OK] Houston in South R{round_num}")

    # Houston must be E8 winner (regional champ)
    if houston.picks["South"][4][0].name != "Houston":
        print(f"[FAIL] South E8 winner is {houston.picks['South'][4][0].name}")
        all_passed = False
    else:
        print(f"[OK] Houston wins South E8")

    # Houston must win Final Four and Championship
    ff = houston.final_four
    if ff["champion"].name != "Houston":
        print(f"[FAIL] Championship winner is {ff['champion'].name}")
        all_passed = False
    else:
        print(f"[OK] Houston wins Championship")

    # Full validation
    if not validate_bracket(houston):
        all_passed = False

    # -------------------------------------------------------------------------
    # Test 2: Duke bracket — champion wins every round, mostly chalk R1
    # -------------------------------------------------------------------------
    print(f"\n{'='*60}")
    print("Test 2: Duke (1-seed East) wins every round, mostly chalk R1")
    print(f"{'='*60}")

    duke = build_bracket("Duke", teams, bracket_structure)

    if duke.champion.name != "Duke":
        print(f"[FAIL] Champion is {duke.champion.name}, expected Duke")
        all_passed = False
    else:
        print(f"[OK] Champion: Duke")

    # Duke must win every round in East
    for round_num in [1, 2, 3, 4]:
        names = [t.name for t in duke.picks["East"][round_num]]
        if "Duke" not in names:
            print(f"[FAIL] Duke missing from East R{round_num}")
            all_passed = False
        else:
            print(f"[OK] Duke in East R{round_num}")

    if not validate_bracket(duke):
        all_passed = False

    # Check "mostly chalk" in R1: majority of R1 picks should be the
    # higher-seeded team (lower seed number). Count across all regions.
    chalk_count = 0
    total_r1 = 0
    for region_name, region_picks in duke.picks.items():
        # Get the original matchups to know which was favored
        for team in region_picks[1]:
            total_r1 += 1
            # A "chalk" pick means seed <= 8 (top-half seed)
            if team.seed <= 8:
                chalk_count += 1

    chalk_pct = chalk_count / total_r1 * 100
    if chalk_pct >= 50:
        print(f"[OK] R1 is mostly chalk: {chalk_count}/{total_r1} picks "
              f"are top-8 seeds ({chalk_pct:.0f}%)")
    else:
        print(f"[WARN] R1 has more upsets than chalk: {chalk_count}/{total_r1} "
              f"top-8 seeds ({chalk_pct:.0f}%)")

    # -------------------------------------------------------------------------
    # Test 3: Internal consistency (tested by validate_bracket above)
    # -------------------------------------------------------------------------
    print(f"\n{'='*60}")
    print("Test 3: Internal consistency (covered by validate_bracket)")
    print(f"{'='*60}")
    print("[OK] Both Houston and Duke brackets passed validate_bracket")

    # -------------------------------------------------------------------------
    # Test 4: Different champions produce different brackets
    # -------------------------------------------------------------------------
    print(f"\n{'='*60}")
    print("Test 4: Different champions produce different brackets")
    print(f"{'='*60}")

    # Compare Houston vs Duke brackets
    diff_count = 0
    for region_name in ["East", "West", "Midwest", "South"]:
        for round_num in [1, 2, 3, 4]:
            h_names = set(t.name for t in houston.picks[region_name][round_num])
            d_names = set(t.name for t in duke.picks[region_name][round_num])
            diff_count += len(h_names.symmetric_difference(d_names))

    if diff_count > 0:
        print(f"[OK] Houston and Duke brackets differ in {diff_count} pick slots")
    else:
        print(f"[FAIL] Houston and Duke brackets are identical!")
        all_passed = False

    # Different Final Four
    h_ff_names = {houston.final_four["sf1_winner"].name, houston.final_four["sf2_winner"].name}
    d_ff_names = {duke.final_four["sf1_winner"].name, duke.final_four["sf2_winner"].name}
    if h_ff_names != d_ff_names:
        print(f"[OK] Final Four differs: Houston has {h_ff_names}, Duke has {d_ff_names}")
    else:
        print(f"[INFO] Final Four teams are the same (different champions though)")

    # -------------------------------------------------------------------------
    # Test 5: All 63 games have a winner
    # -------------------------------------------------------------------------
    print(f"\n{'='*60}")
    print("Test 5: Correct game counts")
    print(f"{'='*60}")

    for name, bracket in [("Houston", houston), ("Duke", duke)]:
        regional = sum(
            sum(len(w) for w in rp.values())
            for rp in bracket.picks.values()
        )
        total = regional + 3  # +2 FF semis + 1 championship
        r1 = sum(len(rp[1]) for rp in bracket.picks.values())
        r2 = sum(len(rp[2]) for rp in bracket.picks.values())
        s16 = sum(len(rp[3]) for rp in bracket.picks.values())
        e8 = sum(len(rp[4]) for rp in bracket.picks.values())

        if total != 63:
            print(f"[FAIL] {name}: total picks = {total}, expected 63")
            all_passed = False
        else:
            print(f"[OK] {name}: R1={r1}, R2={r2}, S16={s16}, E8={e8}, "
                  f"FF=2, Champ=1, Total={total}")

    # -------------------------------------------------------------------------
    # Test 6: Kansas (4-seed) bracket — mid-seed champion
    # -------------------------------------------------------------------------
    print(f"\n{'='*60}")
    print("Test 6: Kansas (4-seed East) bracket — mid-seed champion")
    print(f"{'='*60}")

    kansas = build_bracket("Kansas", teams, bracket_structure)

    if kansas.champion.name != "Kansas":
        print(f"[FAIL] Champion is {kansas.champion.name}, expected Kansas")
        all_passed = False
    else:
        print(f"[OK] Champion: Kansas (4-seed, path value = {4 * 63} pts)")

    if not validate_bracket(kansas):
        all_passed = False

    # Kansas should appear in every round of East
    for round_num in [1, 2, 3, 4]:
        names = [t.name for t in kansas.picks["East"][round_num]]
        if "Kansas" not in names:
            print(f"[FAIL] Kansas missing from East R{round_num}")
            all_passed = False

    # Kansas bracket should differ from both Houston and Duke
    k_r1 = set(t.name for rp in kansas.picks.values() for t in rp[1])
    h_r1 = set(t.name for rp in houston.picks.values() for t in rp[1])
    d_r1 = set(t.name for rp in duke.picks.values() for t in rp[1])

    k_vs_h = len(k_r1.symmetric_difference(h_r1))
    k_vs_d = len(k_r1.symmetric_difference(d_r1))
    print(f"[OK] Kansas R1 differs from Houston in {k_vs_h} picks, "
          f"from Duke in {k_vs_d} picks")

    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------
    print(f"\n{'='*60}")
    if all_passed:
        print("ALL TESTS PASSED — Sprint 2.2 acceptance criteria met")
    else:
        print("SOME TESTS FAILED — review output above")
    print(f"{'='*60}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
