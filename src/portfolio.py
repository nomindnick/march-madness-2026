"""Portfolio generation: 10 diversified March Madness brackets.

Builds on bracket_builder.py with a 3-tier pick strategy:
1. Locked picks: Consensus upsets (same in all 10 brackets)
2. Chalk picks: R2+ games pick by win probability (not EV)
3. Diversification: Close-call R1 games vary across brackets

The key insight from Monte Carlo simulation (Sprint 2.3): pure EV
optimization picks too many upsets in R2+, hurting total score.
Chalk (win probability) in R2+ outperforms by ~8.7 points because
cascading correctness matters more than per-game EV.
"""

import copy
import json

from src.data_loader import Team, load_teams, load_bracket_structure, get_adj_em
from src.win_probability import win_probability_teams
from src.ev_engine import compare_ev, BASE_POINTS
from src.bracket_builder import (
    Bracket, get_region_matchups, find_champion_slot,
    resolve_first_four_auto, validate_bracket
)


# ---------------------------------------------------------------------------
# Config loaders
# ---------------------------------------------------------------------------

def load_portfolio_plan(config_dir="config"):
    """Load the 10 champion assignments from portfolio_plan.json."""
    with open(f"{config_dir}/portfolio_plan.json") as f:
        data = json.load(f)
    return data["portfolio"]


def load_expert_data(data_dir="data"):
    """Load expert bracket picks from expert_picks.json."""
    with open(f"{data_dir}/expert_picks.json") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Locked picks: consensus upsets backed by EV + expert agreement
# ---------------------------------------------------------------------------

def find_matchup_slot(bracket_structure, region, team_a, team_b):
    """Find the R1 slot index for a matchup between two teams.

    Args:
        bracket_structure: Bracket JSON with First Four resolved.
        region: Region name ("East", "West", etc.).
        team_a: First team name.
        team_b: Second team name.

    Returns:
        int slot index (0-7) or None if not found.
    """
    region_data = bracket_structure["regions"][region]
    for matchup in region_data["matchups"]:
        top = matchup["top"]["team"]
        bot = matchup["bottom"]["team"]
        if ({top, bot} == {team_a, team_b}):
            return matchup["slot"]
    return None


def identify_locked_picks(teams, bracket_structure, expert_data):
    """Find R1 upset picks that should be locked into all 10 brackets.

    An upset is locked if:
    1. It's a Round 1 game
    2. Expert count >= 2 (at least 2 experts picked this upset)
    3. compare_ev picks the underdog OR the loser has an injury override

    Args:
        teams: dict[str, Team] from load_teams().
        bracket_structure: Bracket JSON with First Four already resolved.
        expert_data: dict from load_expert_data().

    Returns:
        dict: {(region, slot_index): winner_name} for forced R1 picks.
    """
    locked = {}

    # Gather all consensus upsets (near_unanimous + popular)
    all_upsets = (
        expert_data["consensus_upsets"]["near_unanimous"] +
        expert_data["consensus_upsets"]["popular"]
    )

    print("\n  Evaluating consensus upsets for locked picks:")

    for upset in all_upsets:
        # Only lock R1 picks — R2+ upsets cascade too aggressively
        if upset.get("round", 1) != 1:
            continue
        if upset["expert_count"] < 2:
            continue

        region = upset["region"]
        winner_name = upset["winner"]
        loser_name = upset["loser"]

        # Find the slot in the bracket
        slot = find_matchup_slot(bracket_structure, region, winner_name, loser_name)
        if slot is None:
            print(f"    WARNING: {winner_name}/{loser_name} not found in {region}")
            continue

        # Verify both teams exist
        if winner_name not in teams or loser_name not in teams:
            print(f"    WARNING: Team not found: {winner_name} or {loser_name}")
            continue

        winner = teams[winner_name]
        loser = teams[loser_name]
        ev_pick, _, _ = compare_ev(1, winner, loser)
        has_injury = loser.adj_em != loser.adj_em_base  # Injury override applied

        if ev_pick.name == winner_name or has_injury:
            locked[(region, slot)] = winner_name
            reason = "EV agrees" if ev_pick.name == winner_name else "injury override"
            print(f"    LOCKED: {winner_name} ({winner.seed}) over "
                  f"{loser_name} ({loser.seed}) — {region} slot {slot}, "
                  f"experts={upset['expert_count']}, {reason}")
        else:
            print(f"    SKIPPED: {winner_name} over {loser_name} — "
                  f"experts={upset['expert_count']}, EV disagrees, no injury")

    return locked


# ---------------------------------------------------------------------------
# Close-call games: diversification candidates
# ---------------------------------------------------------------------------

def identify_close_calls(teams, bracket_structure, locked_picks, expert_data=None):
    """Find R1 games suitable for diversification across brackets.

    A game is a close call if it's NOT locked and any of:
    - Win probability is between 35-65% (competitive game), or
    - compare_ev picks the upset (underdog by seed has higher EV), or
    - Expert consensus picked the upset (expert_count >= 2)

    Uses a wider threshold (35-65%) than pure toss-ups to generate enough
    diversification candidates for meaningful portfolio variety.

    Args:
        teams: dict[str, Team].
        bracket_structure: Bracket JSON with First Four resolved.
        locked_picks: dict from identify_locked_picks().
        expert_data: Optional dict from load_expert_data().

    Returns:
        list of dicts: {region, slot, favorite, underdog, win_prob_fav,
                        ev_pick, ev_picks_upset}.
    """
    # Build set of expert-backed upsets for wider inclusion
    expert_upsets = set()  # (region, winner_name)
    if expert_data:
        for upset in (expert_data["consensus_upsets"]["near_unanimous"] +
                      expert_data["consensus_upsets"]["popular"]):
            if upset.get("round", 1) == 1:
                expert_upsets.add((upset["region"], upset["winner"]))

    close_calls = []

    for region_name in bracket_structure["regions"]:
        matchups = get_region_matchups(region_name, bracket_structure, teams)

        for slot_idx, (top, bot) in enumerate(matchups):
            # Skip locked picks — those are already decided
            if (region_name, slot_idx) in locked_picks:
                continue

            prob_top = win_probability_teams(top, bot, 1)
            ev_pick, _, _ = compare_ev(1, top, bot)

            # Top team always has the better (lower) seed number
            favorite, underdog = top, bot

            is_close = 0.35 <= prob_top <= 0.65
            ev_picks_upset = (ev_pick.name == underdog.name)
            expert_backs_upset = (region_name, underdog.name) in expert_upsets

            if is_close or ev_picks_upset or expert_backs_upset:
                close_calls.append({
                    "region": region_name,
                    "slot": slot_idx,
                    "favorite": favorite,
                    "underdog": underdog,
                    "win_prob_fav": prob_top,
                    "ev_pick": ev_pick.name,
                    "ev_picks_upset": ev_picks_upset,
                    "expert_backed": expert_backs_upset,
                })

    print(f"\n  Found {len(close_calls)} close-call games for diversification:")
    for cc in close_calls:
        tags = []
        if cc["ev_picks_upset"]:
            tags.append("EV upset")
        if cc.get("expert_backed"):
            tags.append("expert")
        tag = f" [{', '.join(tags)}]" if tags else ""
        print(f"    {cc['region']} slot {cc['slot']}: "
              f"{cc['favorite'].name} ({cc['favorite'].seed}) vs "
              f"{cc['underdog'].name} ({cc['underdog'].seed}) "
              f"P(fav)={cc['win_prob_fav']:.1%}{tag}")

    return close_calls


# ---------------------------------------------------------------------------
# Region-fill functions (3-tier strategy)
# ---------------------------------------------------------------------------

def _pick_game(team_a, team_b, round_number, use_ev):
    """Pick a game winner by either EV or chalk (win probability).

    Args:
        team_a, team_b: The two teams.
        round_number: Tournament round (for Gonzaga conditional).
        use_ev: If True, use compare_ev. If False, pick by win probability.

    Returns:
        Team: The picked winner.
    """
    if use_ev:
        winner, _, _ = compare_ev(round_number, team_a, team_b)
        return winner
    else:
        prob_a = win_probability_teams(team_a, team_b, round_number)
        return team_a if prob_a >= 0.5 else team_b


def fill_region_portfolio(matchups, locked_picks=None, diversify_picks=None,
                          use_ev_r2=False):
    """Fill a region: R1 by EV with overrides, R2+ by chalk or EV.

    For chalk brackets (use_ev_r2=False): R2+ picks by win probability,
    because the simulator showed chalk outperforms EV by ~8.7 pts.
    For contrarian brackets (use_ev_r2=True): R2+ picks by EV,
    creating aggressive upset-heavy brackets for portfolio variety.

    Args:
        matchups: 8 (top_team, bottom_team) tuples from get_region_matchups().
        locked_picks: dict {slot_index: winner_name} for forced R1 picks.
        diversify_picks: dict {slot_index: winner_name} for extra R1 flips.
        use_ev_r2: If True, use EV for R2+ (more upsets). Default False (chalk).

    Returns:
        dict: {round_number: [Team winners]}.
    """
    if locked_picks is None:
        locked_picks = {}
    if diversify_picks is None:
        diversify_picks = {}

    picks = {}

    # --- Round 1: 8 games — EV default, with locked/diversify overrides ---
    r1 = []
    for slot_idx, (top, bot) in enumerate(matchups):
        if slot_idx in locked_picks:
            name = locked_picks[slot_idx]
            r1.append(top if top.name == name else bot)
        elif slot_idx in diversify_picks:
            name = diversify_picks[slot_idx]
            r1.append(top if top.name == name else bot)
        else:
            winner, _, _ = compare_ev(1, top, bot)
            r1.append(winner)
    picks[1] = r1

    # --- Round 2: 4 games ---
    r2 = []
    for i in range(0, 8, 2):
        r2.append(_pick_game(r1[i], r1[i + 1], 2, use_ev_r2))
    picks[2] = r2

    # --- Sweet 16: 2 games ---
    s16 = []
    for i in range(0, 4, 2):
        s16.append(_pick_game(r2[i], r2[i + 1], 3, use_ev_r2))
    picks[3] = s16

    # --- Elite 8: 1 game ---
    picks[4] = [_pick_game(s16[0], s16[1], 4, use_ev_r2)]

    return picks


def fill_region_champion_portfolio(matchups, champion, champion_slot,
                                   locked_picks=None, use_ev_r2=False):
    """Fill champion's region: champion wins all, others by chalk/EV + overrides.

    Like fill_region_champion() from bracket_builder.py, but non-champion
    R2+ games can use either chalk (win probability) or EV optimization.

    Args:
        matchups: 8 (top, bot) tuples.
        champion: Team object.
        champion_slot: R1 slot index (0-7).
        locked_picks: dict {slot_index: winner_name} for forced non-champion R1.
        use_ev_r2: If True, use EV for non-champion R2+ games.

    Returns:
        dict: {round_number: [Team winners]}.
    """
    if locked_picks is None:
        locked_picks = {}

    picks = {}

    # --- Round 1 ---
    r1 = []
    for slot_idx, (top, bot) in enumerate(matchups):
        if slot_idx == champion_slot:
            r1.append(champion)
        elif slot_idx in locked_picks:
            name = locked_picks[slot_idx]
            r1.append(top if top.name == name else bot)
        else:
            winner, _, _ = compare_ev(1, top, bot)
            r1.append(winner)
    picks[1] = r1

    # --- Round 2: champion wins their game, others by chalk/EV ---
    champ_r2 = champion_slot // 2
    r2 = []
    for game_idx in range(4):
        if game_idx == champ_r2:
            r2.append(champion)
        else:
            a, b = r1[game_idx * 2], r1[game_idx * 2 + 1]
            r2.append(_pick_game(a, b, 2, use_ev_r2))
    picks[2] = r2

    # --- Sweet 16: champion wins their game, other by chalk/EV ---
    champ_s16 = champion_slot // 4
    s16 = []
    for game_idx in range(2):
        if game_idx == champ_s16:
            s16.append(champion)
        else:
            a, b = r2[game_idx * 2], r2[game_idx * 2 + 1]
            s16.append(_pick_game(a, b, 3, use_ev_r2))
    picks[3] = s16

    # --- Elite 8: champion wins ---
    picks[4] = [champion]

    return picks


# ---------------------------------------------------------------------------
# Diversification assignment
# ---------------------------------------------------------------------------

def assign_diversification(bracket_number, tier, close_calls):
    """Assign close-call upset picks for a specific bracket.

    Chalk brackets (1-2): no extra upsets beyond locked picks.
    Value brackets (3-5): 2-3 close-call upsets, rotated across brackets.
    Contrarian brackets (6-9): take ALL close-call upsets (EV R2+ already
        creates major differentiation; R1 upsets add more variety).

    Args:
        bracket_number: 1-10.
        tier: "chalk", "value_core", "contrarian", or "swing".
        close_calls: list from identify_close_calls().

    Returns:
        dict: {(region, slot): underdog_name} for this bracket's extra R1 upsets.
    """
    if tier == "chalk" or not close_calls:
        return {}

    if tier == "contrarian":
        # Contrarian brackets take ALL close-call upsets. Combined with
        # EV R2+ optimization, this creates maximally different brackets.
        overrides = {}
        for cc in close_calls:
            overrides[(cc["region"], cc["slot"])] = cc["underdog"].name
        return overrides

    # Value brackets: rotate through 2-3 close-call upsets
    count = min(3, len(close_calls))
    n = len(close_calls)
    offset = ((bracket_number - 3) * 2) % n if n > 0 else 0

    selected = []
    for i in range(count):
        idx = (offset + i) % n
        cc = close_calls[idx]
        if (cc["region"], cc["slot"]) not in {(s["region"], s["slot"]) for s in selected}:
            selected.append(cc)

    overrides = {}
    for cc in selected:
        overrides[(cc["region"], cc["slot"])] = cc["underdog"].name

    return overrides


def compute_swing_diversification(brackets_so_far, bracket_structure, teams,
                                  locked_picks, close_calls, entry):
    """Compute diversification for the swing bracket (#10).

    Strategy: take ALL close-call upsets for R1 variety. The swing bracket
    also uses EV R2+ (via tier="swing"), so it naturally creates very
    different R2-R4 picks from chalk/value brackets.

    Previous approach of flipping ALL 8+/9 agreement games was too
    aggressive — it created an unrealistic bracket. Now we only flip
    close-call games, which are games that are genuinely uncertain.

    Args:
        brackets_so_far: list of 9 Bracket objects already built.
        bracket_structure: Bracket JSON with First Four resolved.
        teams: dict[str, Team].
        locked_picks: dict of forced picks (respected, not flipped).
        close_calls: list of close-call games.
        entry: portfolio_plan entry for the swing bracket.

    Returns:
        dict: {(region, slot): team_name} for swing bracket R1 overrides.
    """
    champion = teams[entry["champion"]]
    champion_region = champion.region
    overrides = {}

    # Take ALL close-call upsets for maximum R1 differentiation
    for cc in close_calls:
        key = (cc["region"], cc["slot"])
        if key not in locked_picks and cc["region"] != champion_region:
            overrides[key] = cc["underdog"].name

    return overrides


# ---------------------------------------------------------------------------
# Main bracket builder (portfolio version)
# ---------------------------------------------------------------------------

def build_bracket_portfolio(champion_name, teams, bracket_structure,
                            locked_picks, diversify_overrides=None,
                            bracket_number=1, tier="chalk"):
    """Build a bracket using the 3-tier pick strategy.

    Like build_bracket() from bracket_builder.py but uses:
    - fill_region_champion_portfolio() for champion's region
    - fill_region_portfolio() for other regions
    - Chalk or EV for R2+ depending on tier:
        - chalk/value_core: chalk R2+ (safe, higher mean score)
        - contrarian/swing: EV R2+ (aggressive, more upsets, better upside)

    The champion's path is unchanged: champion wins every round.

    Args:
        champion_name: Assigned champion team name.
        teams: dict[str, Team].
        bracket_structure: Bracket JSON with First Four already resolved.
        locked_picks: dict {(region, slot): winner_name} (all brackets).
        diversify_overrides: dict {(region, slot): winner_name} (this bracket).
        bracket_number: 1-10 for metadata.
        tier: "chalk", "value_core", "contrarian", or "swing".

    Returns:
        Bracket with picks, final_four, and metadata.
    """
    if diversify_overrides is None:
        diversify_overrides = {}

    if champion_name not in teams:
        raise ValueError(
            f"Champion '{champion_name}' not found in teams dict. "
            f"Check spelling against bracket_2026.json."
        )

    champion = teams[champion_name]
    bs = copy.deepcopy(bracket_structure)

    # Contrarian and swing brackets use EV for R2+ (more aggressive upsets)
    # Chalk and value brackets use win probability (chalk) for R2+
    use_ev_r2 = tier in ("contrarian", "swing")

    # Build region matchups
    region_matchups = {}
    for region_name in bs["regions"]:
        region_matchups[region_name] = get_region_matchups(region_name, bs, teams)

    # Find champion's slot
    champion_slot = find_champion_slot(champion, bs)

    # Helper: extract locked/diversify picks for a specific region
    def locked_for(region):
        return {slot: name for (r, slot), name in locked_picks.items()
                if r == region}

    def diversify_for(region):
        return {slot: name for (r, slot), name in diversify_overrides.items()
                if r == region}

    # --- Fill all 4 regions ---
    picks = {}

    # Champion's region: champion wins every round, others by chalk/EV + locked
    picks[champion.region] = fill_region_champion_portfolio(
        region_matchups[champion.region], champion, champion_slot,
        locked_picks=locked_for(champion.region),
        use_ev_r2=use_ev_r2,
    )

    # Other 3 regions: R1 by EV + overrides, R2+ by chalk or EV
    for region_name in bs["regions"]:
        if region_name != champion.region:
            picks[region_name] = fill_region_portfolio(
                region_matchups[region_name],
                locked_picks=locked_for(region_name),
                diversify_picks=diversify_for(region_name),
                use_ev_r2=use_ev_r2,
            )

    # --- Final Four + Championship ---
    sf1_regions = bs["final_four"]["semifinal_1"]   # ["East", "South"]
    sf2_regions = bs["final_four"]["semifinal_2"]   # ["West", "Midwest"]

    # Which semifinal has the champion?
    if champion.region in sf1_regions:
        champ_sf_regions = sf1_regions
        other_sf_regions = sf2_regions
    else:
        champ_sf_regions = sf2_regions
        other_sf_regions = sf1_regions

    # Champion beats paired region's E8 winner
    paired_region = [r for r in champ_sf_regions if r != champion.region][0]
    champ_ff_opponent = picks[paired_region][4][0]

    # Other semifinal: pick by chalk or EV based on tier
    other_team_1 = picks[other_sf_regions[0]][4][0]
    other_team_2 = picks[other_sf_regions[1]][4][0]
    other_sf_winner = _pick_game(other_team_1, other_team_2, 5, use_ev_r2)

    # Assemble final_four dict (same structure as bracket_builder)
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

    bracket = Bracket(
        champion=champion,
        picks=picks,
        final_four=final_four,
        metadata={
            "bracket_number": bracket_number,
            "tier": tier,
            "champion_seed": champion.seed,
            "path_value": champion.seed * 63,
        },
    )

    return bracket


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def generate_portfolio(teams, bracket_structure):
    """Generate all 10 diversified brackets.

    Orchestrates:
    1. First Four resolution
    2. Locked pick identification (consensus upsets)
    3. Close-call identification (diversification candidates)
    4. Bracket generation with tier-based diversification
    5. Swing bracket with maximum differentiation

    Args:
        teams: dict[str, Team] from load_teams().
        bracket_structure: dict from load_bracket_structure().

    Returns:
        list[Bracket]: 10 complete, validated brackets.
    """
    # Resolve First Four once (shared across all bracket builds)
    bs = copy.deepcopy(bracket_structure)
    print("Resolving First Four games:")
    resolve_first_four_auto(bs, teams)

    # Load configuration
    plan = load_portfolio_plan()
    expert_data = load_expert_data()

    # Identify locked picks (consensus upsets for ALL brackets)
    locked_picks = identify_locked_picks(teams, bs, expert_data)

    # Identify close-call games (for bracket-specific diversification)
    close_calls = identify_close_calls(teams, bs, locked_picks, expert_data)

    # Generate all 10 brackets
    brackets = []
    print(f"\n{'='*60}")
    print("Generating 10 brackets...")
    print(f"{'='*60}")

    for entry in plan:
        bn = entry["bracket_number"]
        tier = entry["tier"]
        champ = entry["champion"]

        if tier == "swing":
            # Swing bracket: compute AFTER brackets 1-9
            diversify = compute_swing_diversification(
                brackets, bs, teams, locked_picks, close_calls, entry
            )
        else:
            diversify = assign_diversification(bn, tier, close_calls)

        bracket = build_bracket_portfolio(
            champ, teams, bs, locked_picks, diversify, bn, tier
        )

        # Validate internal consistency
        valid = validate_bracket(bracket)
        if not valid:
            print(f"  [ERROR] Bracket #{bn} ({champ}) FAILED validation!")

        brackets.append(bracket)

        n_diversify = len(diversify)
        print(f"  #{bn} {champ} ({champion_seed_str(bracket)}, {tier}) — "
              f"{n_diversify} diversification picks")

    return brackets


def champion_seed_str(bracket):
    """Format champion seed string, e.g. '2-seed South'."""
    c = bracket.champion
    return f"{c.seed}-seed {c.region}"
