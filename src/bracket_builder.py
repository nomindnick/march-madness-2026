"""Backwards-chaining bracket builder for March Madness.

Given a pre-assigned champion, builds a complete 63-game bracket by:
1. Forcing the champion to win every round on their path
2. Using EV optimization (Points x Seed scoring) for all other games
3. Ensuring internal consistency (no team advances after losing)

The "backwards chaining" means we start from the champion assignment and
work backward to ensure the bracket is consistent. In practice, we build
forward (R1 -> Championship) but the champion constraint drives the design.
"""

import copy
from dataclasses import dataclass, field

from src.data_loader import (
    Team, load_teams, load_bracket_structure,
    resolve_first_four, get_adj_em
)
from src.win_probability import win_probability_teams
from src.ev_engine import (
    compare_ev, ROUND_NAMES, BASE_POINTS,
    score_correct_pick, champion_path_ev
)


# ---------------------------------------------------------------------------
# Data structure
# ---------------------------------------------------------------------------

@dataclass
class Bracket:
    """A complete 63-game tournament bracket.

    Attributes:
        champion: The assigned champion Team.
        picks: Regional picks: {region_name: {round_number: [Team winners]}}.
            Round 1 has 8 winners (slots 0-7), Round 2 has 4, S16 has 2, E8 has 1.
        final_four: Dict with semifinal matchups, winners, and championship result.
        metadata: Optional info (tier, bracket_number, notes).
    """
    champion: Team
    picks: dict
    final_four: dict
    metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def find_champion_slot(champion, bracket_structure):
    """Find the champion's R1 slot index (0-7) in their region.

    Args:
        champion: Team object for the assigned champion.
        bracket_structure: The bracket JSON structure.

    Returns:
        int: Slot index 0-7.
    """
    region_data = bracket_structure["regions"][champion.region]
    for matchup in region_data["matchups"]:
        if matchup["top"]["team"] == champion.name:
            return matchup["slot"]
        if matchup["bottom"]["team"] == champion.name:
            return matchup["slot"]

    raise ValueError(
        f"Champion '{champion.name}' not found in {champion.region} region matchups. "
        f"Check that the team name exactly matches bracket_2026.json."
    )


def get_region_matchups(region_name, bracket_structure, teams):
    """Get the 8 first-round matchups for a region as (Team, Team) tuples.

    Matchups are returned sorted by slot index (0-7), matching the bracket
    tree: slot 0 = 1v16, slot 1 = 8v9, ..., slot 7 = 2v15.

    Args:
        region_name: "East", "West", "Midwest", or "South".
        bracket_structure: Bracket JSON (First Four must already be resolved).
        teams: dict[str, Team] mapping team names to Team objects.

    Returns:
        list: 8 (top_team, bottom_team) tuples indexed by slot.
    """
    matchups = []
    region_data = bracket_structure["regions"][region_name]

    for matchup in sorted(region_data["matchups"], key=lambda m: m["slot"]):
        top_name = matchup["top"]["team"]
        bot_name = matchup["bottom"]["team"]

        # Check for unresolved First Four slots
        if top_name is None:
            ff_id = matchup["top"].get("first_four_id", "unknown")
            raise ValueError(
                f"Unresolved First Four ({ff_id}) in {region_name} slot {matchup['slot']}. "
                f"Resolve First Four games before building the bracket."
            )
        if bot_name is None:
            ff_id = matchup["bottom"].get("first_four_id", "unknown")
            raise ValueError(
                f"Unresolved First Four ({ff_id}) in {region_name} slot {matchup['slot']}. "
                f"Resolve First Four games before building the bracket."
            )

        # Look up Team objects
        if top_name not in teams:
            raise ValueError(f"Team '{top_name}' ({region_name} slot {matchup['slot']}) not in teams dict.")
        if bot_name not in teams:
            raise ValueError(f"Team '{bot_name}' ({region_name} slot {matchup['slot']}) not in teams dict.")

        matchups.append((teams[top_name], teams[bot_name]))

    return matchups


def resolve_first_four_auto(bracket_structure, teams):
    """Resolve First Four games using known results or AdjEM comparison.

    Games with a "winner" field in the bracket JSON use that result.
    Unresolved games pick the team with higher AdjEM.

    Args:
        bracket_structure: Bracket JSON (modified in place).
        teams: dict[str, Team] for AdjEM lookups.

    Returns:
        dict: {ff_id: winner_name} for all First Four games.
    """
    winners = {}

    for ff in bracket_structure["first_four"]:
        ff_id = ff["id"]

        if "winner" in ff and ff["winner"]:
            winners[ff_id] = ff["winner"]
            print(f"  {ff_id}: {ff['winner']} (known result)")
        else:
            name_a, name_b = ff["teams"]
            if name_a not in teams:
                raise ValueError(f"First Four team '{name_a}' not in teams dict.")
            if name_b not in teams:
                raise ValueError(f"First Four team '{name_b}' not in teams dict.")

            team_a, team_b = teams[name_a], teams[name_b]
            if team_a.adj_em >= team_b.adj_em:
                winners[ff_id] = name_a
            else:
                winners[ff_id] = name_b
            print(f"  {ff_id}: {winners[ff_id]} (auto-picked by AdjEM)")

    resolve_first_four(bracket_structure, winners)
    return winners


# ---------------------------------------------------------------------------
# Region-fill algorithms
# ---------------------------------------------------------------------------

def fill_region_ev(matchups):
    """Fill an entire region using pure EV optimization.

    At each game node, picks the team with higher expected value under the
    Points x Seed scoring system. Builds bottom-up: R1 -> R2 -> S16 -> E8.

    Args:
        matchups: List of 8 (top_team, bottom_team) tuples, slot-ordered.

    Returns:
        dict: {round_number: [Team winners]}.
            R1: 8 winners, R2: 4, S16: 2, E8: 1.
    """
    picks = {}

    # Round 1: 8 games
    r1 = []
    for top, bot in matchups:
        winner, _, _ = compare_ev(1, top, bot)
        r1.append(winner)
    picks[1] = r1

    # Round 2: 4 games (pair consecutive R1 winners)
    r2 = []
    for i in range(0, 8, 2):
        winner, _, _ = compare_ev(2, r1[i], r1[i + 1])
        r2.append(winner)
    picks[2] = r2

    # Sweet 16: 2 games
    s16 = []
    for i in range(0, 4, 2):
        winner, _, _ = compare_ev(3, r2[i], r2[i + 1])
        s16.append(winner)
    picks[3] = s16

    # Elite 8: 1 game
    winner, _, _ = compare_ev(4, s16[0], s16[1])
    picks[4] = [winner]

    return picks


def fill_region_champion(matchups, champion, champion_slot):
    """Fill a region where the assigned champion must win every round.

    The champion wins at every level (R1, R2, S16, E8). All other games
    in the region use EV optimization via compare_ev().

    The tree structure determines which game the champion plays each round:
      - R2 game = champion_slot // 2
      - S16 game = champion_slot // 4
      - E8 is always game 0 (regional final)

    Args:
        matchups: List of 8 (top_team, bottom_team) tuples, slot-ordered.
        champion: Team object for the assigned champion.
        champion_slot: The champion's R1 slot index (0-7).

    Returns:
        dict: {round_number: [Team winners]} for rounds 1-4.
    """
    picks = {}

    # === Round 1: 8 games ===
    r1 = []
    for slot_idx, (top, bot) in enumerate(matchups):
        if slot_idx == champion_slot:
            r1.append(champion)
        else:
            winner, _, _ = compare_ev(1, top, bot)
            r1.append(winner)
    picks[1] = r1

    # === Round 2: 4 games ===
    champ_r2 = champion_slot // 2  # Which R2 game the champion is in (0-3)

    r2 = []
    for game_idx in range(4):
        team_a = r1[game_idx * 2]
        team_b = r1[game_idx * 2 + 1]
        if game_idx == champ_r2:
            r2.append(champion)
        else:
            winner, _, _ = compare_ev(2, team_a, team_b)
            r2.append(winner)
    picks[2] = r2

    # === Sweet 16: 2 games ===
    champ_s16 = champion_slot // 4  # Which S16 game (0 or 1)

    s16 = []
    for game_idx in range(2):
        team_a = r2[game_idx * 2]
        team_b = r2[game_idx * 2 + 1]
        if game_idx == champ_s16:
            s16.append(champion)
        else:
            winner, _, _ = compare_ev(3, team_a, team_b)
            s16.append(winner)
    picks[3] = s16

    # === Elite 8: champion wins the regional final ===
    picks[4] = [champion]

    return picks


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def build_bracket(champion_name, teams, bracket_structure, first_four_winners=None):
    """Build a complete 63-game bracket with the given champion.

    Orchestrates:
    1. First Four resolution
    2. Champion's region (champion wins every round, EV for the rest)
    3. Remaining 3 regions (pure EV optimization)
    4. Final Four and Championship

    Args:
        champion_name: Name of the assigned champion (must match teams dict).
        teams: dict[str, Team] from load_teams().
        bracket_structure: dict from load_bracket_structure().
            A deep copy is made internally — the original is not modified.
        first_four_winners: Optional dict {ff_id: winner_name} to override
            auto-resolution. Example: {"FF3": "Lehigh", "FF4": "SMU"}.

    Returns:
        Bracket: Complete bracket with all 63 game picks.
    """
    if champion_name not in teams:
        raise ValueError(
            f"Champion '{champion_name}' not found in teams dict. "
            f"Check spelling against bracket_2026.json."
        )

    champion = teams[champion_name]

    # Deep copy so we don't modify the caller's bracket structure
    bs = copy.deepcopy(bracket_structure)

    # --- Phase 0: Resolve First Four ---
    print(f"\nBuilding bracket: {champion.name} ({champion.seed}-seed, {champion.region})")

    if first_four_winners:
        # Merge caller-provided winners with known results from bracket JSON
        all_winners = {}
        for ff in bs["first_four"]:
            ff_id = ff["id"]
            if ff_id in first_four_winners:
                all_winners[ff_id] = first_four_winners[ff_id]
            elif "winner" in ff and ff["winner"]:
                all_winners[ff_id] = ff["winner"]
            else:
                # Auto-resolve by AdjEM
                a, b = ff["teams"]
                all_winners[ff_id] = a if teams[a].adj_em >= teams[b].adj_em else b
        resolve_first_four(bs, all_winners)
    else:
        resolve_first_four_auto(bs, teams)

    # --- Build region matchups ---
    region_matchups = {}
    for region_name in bs["regions"]:
        region_matchups[region_name] = get_region_matchups(region_name, bs, teams)

    # --- Phase 1: Fill champion's region ---
    champion_slot = find_champion_slot(champion, bs)
    print(f"  Champion slot: {champion.region} slot {champion_slot}")

    picks = {}
    picks[champion.region] = fill_region_champion(
        region_matchups[champion.region], champion, champion_slot
    )

    # --- Phase 2: Fill remaining 3 regions with pure EV ---
    for region_name in bs["regions"]:
        if region_name != champion.region:
            picks[region_name] = fill_region_ev(region_matchups[region_name])

    # --- Phase 3: Final Four + Championship ---
    sf1_regions = bs["final_four"]["semifinal_1"]   # ["East", "South"]
    sf2_regions = bs["final_four"]["semifinal_2"]   # ["West", "Midwest"]

    # Which semifinal is the champion in?
    if champion.region in sf1_regions:
        champ_sf_regions = sf1_regions
        other_sf_regions = sf2_regions
    else:
        champ_sf_regions = sf2_regions
        other_sf_regions = sf1_regions

    # Champion's semifinal: champion beats the paired region's E8 winner
    paired_region = [r for r in champ_sf_regions if r != champion.region][0]
    champ_ff_opponent = picks[paired_region][4][0]

    # Other semifinal: EV-optimize between the two regional champions
    other_team_1 = picks[other_sf_regions[0]][4][0]
    other_team_2 = picks[other_sf_regions[1]][4][0]
    other_sf_winner, _, _ = compare_ev(5, other_team_1, other_team_2)

    # Assemble Final Four dict
    sf1_team1 = picks[sf1_regions[0]][4][0]
    sf1_team2 = picks[sf1_regions[1]][4][0]
    sf2_team1 = picks[sf2_regions[0]][4][0]
    sf2_team2 = picks[sf2_regions[1]][4][0]

    if champion.region in sf1_regions:
        sf1_winner = champion
        sf2_winner = other_sf_winner
    else:
        sf1_winner = other_sf_winner
        sf2_winner = champion

    final_four = {
        "sf1_team1": sf1_team1,
        "sf1_team2": sf1_team2,
        "sf2_team1": sf2_team1,
        "sf2_team2": sf2_team2,
        "sf1_winner": sf1_winner,
        "sf2_winner": sf2_winner,
        "champion_ff_opponent": champ_ff_opponent,
        "other_sf_winner": other_sf_winner,
        "champion": champion,
    }

    print(f"  Final Four: {champion.name} vs {champ_ff_opponent.name} | "
          f"{other_team_1.name} vs {other_team_2.name} -> {other_sf_winner.name}")
    print(f"  Championship: {champion.name} vs {other_sf_winner.name}")

    return Bracket(
        champion=champion,
        picks=picks,
        final_four=final_four,
        metadata={},
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_bracket(bracket):
    """Check bracket for internal consistency.

    Validates:
    1. Correct number of picks per round per region
    2. Every advancing team won their prior-round game
    3. Champion wins every round on their path
    4. No duplicate teams in the same round
    5. Total of 63 game picks

    Returns:
        bool: True if all checks pass. Prints details on failure.
    """
    valid = True
    champion = bracket.champion
    picks = bracket.picks

    for region_name, region_picks in picks.items():
        # --- Check pick counts ---
        expected = {1: 8, 2: 4, 3: 2, 4: 1}
        for round_num, count in expected.items():
            actual = len(region_picks.get(round_num, []))
            if actual != count:
                print(f"[FAIL] {region_name} R{round_num}: expected {count} picks, got {actual}")
                valid = False

        # --- Check advancing-team consistency ---
        for round_num in [2, 3, 4]:
            prev = region_picks.get(round_num - 1, [])
            curr = region_picks.get(round_num, [])

            for game_idx, winner in enumerate(curr):
                idx_a = game_idx * 2
                idx_b = game_idx * 2 + 1
                if idx_b >= len(prev):
                    print(f"[FAIL] {region_name} R{round_num} game {game_idx}: "
                          f"missing feeders in R{round_num - 1}")
                    valid = False
                    continue
                feeder_names = {prev[idx_a].name, prev[idx_b].name}
                if winner.name not in feeder_names:
                    print(f"[FAIL] {region_name} R{round_num} game {game_idx}: "
                          f"'{winner.name}' not in feeders {feeder_names}")
                    valid = False

        # --- No duplicates in same round ---
        for round_num, winners in region_picks.items():
            names = [t.name for t in winners]
            if len(names) != len(set(names)):
                dupes = {n for n in names if names.count(n) > 1}
                print(f"[FAIL] {region_name} R{round_num}: duplicate teams: {dupes}")
                valid = False

    # --- Champion appears in every round of their region ---
    champ_picks = picks[champion.region]
    for round_num in [1, 2, 3, 4]:
        names = [t.name for t in champ_picks[round_num]]
        if champion.name not in names:
            print(f"[FAIL] Champion '{champion.name}' missing from "
                  f"{champion.region} R{round_num}")
            valid = False

    # --- Champion is the championship winner ---
    if bracket.final_four["champion"].name != champion.name:
        print(f"[FAIL] Championship winner is '{bracket.final_four['champion'].name}', "
              f"expected '{champion.name}'")
        valid = False

    # --- Regional champion matches E8 winner ---
    if champ_picks[4][0].name != champion.name:
        print(f"[FAIL] {champion.region} E8 winner is '{champ_picks[4][0].name}', "
              f"expected '{champion.name}'")
        valid = False

    # --- Total game count: 4x15 regional + 2 FF + 1 Championship = 63 ---
    regional_total = sum(
        sum(len(w) for w in rp.values())
        for rp in picks.values()
    )
    total = regional_total + 3
    if total != 63:
        print(f"[FAIL] Total picks = {total}, expected 63")
        valid = False

    if valid:
        print(f"[OK] Bracket valid: {champion.name} "
              f"({champion.seed}-seed {champion.region})")
    return valid


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def print_bracket(bracket):
    """Print a human-readable bracket summary.

    Shows each region's picks by round, highlights the champion's path
    with asterisks (*), and shows Final Four / Championship results.
    """
    champion = bracket.champion
    picks = bracket.picks
    ff = bracket.final_four

    def fmt(team):
        """Format team with seed and champion marker."""
        marker = "*" if team.name == champion.name else " "
        return f"({team.seed:>2}){marker}{team.name}"

    print(f"\n{'='*80}")
    print(f"BRACKET: {champion.name} ({champion.seed}-seed, {champion.region}) "
          f"— Path value: {champion.seed * 63} pts")
    print(f"{'='*80}")

    round_labels = {1: "R64", 2: "R32", 3: "S16", 4: "E8 "}

    for region_name in ["East", "West", "Midwest", "South"]:
        region_picks = picks[region_name]
        tag = " [CHAMPION]" if region_name == champion.region else ""
        print(f"\n  {region_name}{tag}")

        for round_num in [1, 2, 3, 4]:
            label = round_labels[round_num]
            winners = region_picks[round_num]
            line = " | ".join(fmt(t) for t in winners)
            print(f"    {label}: {line}")

    # Final Four
    print(f"\n  Final Four")
    print(f"    SF1 (East vs South):   {fmt(ff['sf1_team1'])}  vs  {fmt(ff['sf1_team2'])}")
    print(f"      Winner: {fmt(ff['sf1_winner'])}")
    print(f"    SF2 (West vs Midwest): {fmt(ff['sf2_team1'])}  vs  {fmt(ff['sf2_team2'])}")
    print(f"      Winner: {fmt(ff['sf2_winner'])}")

    print(f"\n  Championship")
    print(f"    {fmt(ff['sf1_winner'])}  vs  {fmt(ff['sf2_winner'])}")
    print(f"    CHAMPION: {fmt(champion)}")

    # Count upset picks (lower seed beats higher seed) in R1
    upset_count = 0
    for region_picks in picks.values():
        # In R1, slots alternate between higher seed (top) and lower seed (bottom)
        # A pick is an "upset" if the winner has a higher seed number than the
        # team it was paired with. We track this by checking if the winner's seed
        # is higher than any possible opponent seed for that slot.
        pass  # Detailed upset tracking deferred to output.py (Sprint 4.1)

    regional_total = sum(sum(len(w) for w in rp.values()) for rp in picks.values())
    print(f"\n  Total picks: {regional_total + 3}")


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    teams = load_teams()
    bracket_structure = load_bracket_structure()

    print(f"\n{'#'*80}")
    print(f"# Sprint 2.2: Bracket Builder Demo")
    print(f"{'#'*80}")

    # --- Demo 1: Houston (2-seed South) ---
    houston_bracket = build_bracket("Houston", teams, bracket_structure)
    print_bracket(houston_bracket)
    print()
    validate_bracket(houston_bracket)

    # --- Demo 2: Duke (1-seed East) ---
    duke_bracket = build_bracket("Duke", teams, bracket_structure)
    print_bracket(duke_bracket)
    print()
    validate_bracket(duke_bracket)

    # --- Comparison: show differences ---
    print(f"\n{'='*80}")
    print("Bracket Comparison: Houston vs Duke")
    print(f"{'='*80}")

    for region_name in ["East", "West", "Midwest", "South"]:
        h_picks = houston_bracket.picks[region_name]
        d_picks = duke_bracket.picks[region_name]

        diffs = 0
        for round_num in [1, 2, 3, 4]:
            h_names = {t.name for t in h_picks[round_num]}
            d_names = {t.name for t in d_picks[round_num]}
            diffs += len(h_names - d_names)

        if diffs > 0:
            print(f"  {region_name}: {diffs} different picks")
        else:
            print(f"  {region_name}: identical")

    # Final Four comparison
    h_ff = houston_bracket.final_four
    d_ff = duke_bracket.final_four
    print(f"  Final Four: Houston bracket -> {h_ff['champion'].name} beats {h_ff['other_sf_winner'].name}")
    print(f"  Final Four: Duke bracket    -> {d_ff['champion'].name} beats {d_ff['other_sf_winner'].name}")
