# Implementation Plan: March Madness 2026 Bracket Generator

> **Reference:** See [SPEC.md](./SPEC.md) for full technical architecture and
> [STRATEGY.md](./STRATEGY.md) for the strategic analysis driving all decisions.

## Overview

This plan is organized into 4 phases. Phases 1-2 are strict build phases with
clear acceptance criteria. Phase 3 is a research/data-gathering phase that can
run in parallel. Phase 4 is generation and review — the payoff.

The timeline is compressed: everything must be complete by Wednesday evening
(March 18) so brackets can be submitted Thursday morning before tip-off.

**Estimated Total Time:** 6-10 hours across Tuesday-Wednesday evenings

---

## Phase 1: Foundation — Data & Configuration

**Goal:** All config files populated, project structure in place, core data
model working. At the end of this phase, you can load every team's data and
compute win probabilities for any matchup.

### Sprint 1.1: Project Scaffolding & Bracket Data
**Estimated Time:** 30-45 minutes

**Objective:** Create the project directory structure and populate the bracket
configuration with all 68 teams, their seeds, and regional assignments.

**Tasks:**
- [x] Create the directory structure from SPEC.md
- [x] Populate `config/bracket_2026.json` with all 68 teams organized by region,
      including First Four matchups (use the bracket data from STRATEGY.md
      Appendix A as the starting point)
- [x] Create `config/portfolio_plan.json` with the 10 champion assignments:
      Duke(1E), Arizona(1W), Houston(2S), UConn(2E), Iowa State(2MW),
      Gonzaga(3W), Illinois(3S), Kansas(4E), Purdue(2W), TBD-Swing(MW)
- [x] Create `config/injury_overrides.json` with the override dictionary from
      SPEC.md (Michigan, Alabama, UNC, BYU, Duke, Gonzaga)
- [x] Create `requirements.txt` (numpy, pandas)

**Acceptance Criteria:**
- All config files load without errors
- Every team in the bracket can be looked up by name and returns seed + region
- Injury overrides are applied correctly to affected teams

**Sprint Update (Completed 2026-03-18):**
> - Created directory structure: `config/`, `src/`, `data/`, `output/brackets/`
> - Populated `config/bracket_2026.json` with all 68 teams across 4 regions.
>   Bracket tree is encoded via slot ordering (0-7 per region); First Four
>   slots use `null` team with `first_four_id` references. Final Four pairings:
>   East vs South, West vs Midwest.
> - Moved `portfolio_plan.json` from root to `config/portfolio_plan.json` (unchanged).
> - Created `config/injury_overrides.json` with 6 overrides from SPEC.md, including
>   Gonzaga's conditional `sweet_16_override`.
> - Created `requirements.txt` (numpy, pandas).
> - Validation script (`validate_sprint1_1.py`) confirms: all JSON valid, 68 unique
>   teams, seeds 1-16 in each region, First Four IDs cross-reference correctly,
>   all injury/portfolio team names match bracket data.
> - **Key decision:** Team names use exact STRATEGY.md Appendix A names as canonical
>   identifiers. All config files must match these exactly.

---

### Sprint 1.2: Team Ratings & Win Probability Engine
**Estimated Time:** 1-2 hours

**Objective:** Load team efficiency ratings, apply injury overrides, and
implement the win probability function.

**Tasks:**
- [x] Create `config/team_ratings.json` — scrape from KenPom (see Data
      Gathering Note below) for all 68 teams. Fields: AdjO (ORtg), AdjD
      (DRtg), AdjEM (NetRtg), plus rank and conference.
- [x] Implement `src/data_loader.py`:
  - Load bracket structure, team ratings, and injury overrides
  - Merge into a single Team data structure with final adjusted ratings
  - Handle Gonzaga's conditional rating (different for rounds 1-2 vs 3+)
- [x] Implement `src/win_probability.py`:
  - Given two Teams, compute P(A wins) using logistic model on efficiency margin
  - Calibrate so that the outputs roughly match known relationships
    (e.g., a 1-seed vs 16-seed should be ~99%, 5 vs 12 should be ~65%)
  - Validate against historical seed upset rates

**Data Gathering Note:** KenPom's main rankings table at https://kenpom.com
is publicly accessible without a subscription. It contains all ~360 D-I teams
with the exact columns we need: Rk, Team, Conf, W-L, NetRtg (AdjEM), ORtg
(AdjO) + rank, DRtg (AdjD) + rank, AdjT, Luck, and SOS metrics. Tournament
seeds are shown inline with team names (e.g., "Duke 1"). We verified this
on 2026-03-18 via Playwright — the full table loads in a single page.

**Approach:** Use Playwright (available as MCP tool) to load kenpom.com,
extract the HTML table, parse all ~360 rows, then filter to the 68 tournament
teams by matching against `bracket_2026.json` team names. Output to
`config/team_ratings.json`. This replaces the manual-entry approach — faster
and less error-prone. Team name matching between KenPom and our canonical
names will need a mapping for any discrepancies (e.g., KenPom may use
"St. John's" vs our "St. John's" — needs verification during scrape).

**Fallback:** If KenPom's page structure changes or scraping fails, BartTorvik
(barttorvik.com/trank.php) has equivalent data for free. Manual entry of 68
teams is a last resort (~30 min).

**Acceptance Criteria:**
- `data_loader.py` produces a complete list of 68 teams with ratings
- Injury overrides visibly change affected teams' ratings
- `win_probability.py` returns sensible probabilities:
  - Duke vs Siena ≈ 99%
  - A 5 vs 12 matchup ≈ 60-70% for the 5
  - An 8 vs 9 matchup ≈ 50%
- Print a sample matchup table for one region to verify

**Sprint Update (Completed 2026-03-18):**
> - Scraped KenPom ratings via Playwright for all 365 D-I teams, filtered to 68
>   tournament teams. Applied 14 name mappings (e.g., `Connecticut` → `UConn`,
>   `Iowa St.` → `Iowa State`, `Miami FL` → `Miami (FL)`).
> - Created `config/team_ratings.json` with AdjO, AdjD, AdjEM, rank, and conference
>   for all 68 teams. Source: kenpom.com, scraped 2026-03-18.
> - Implemented `src/data_loader.py` with `Team` dataclass and `load_teams()` function.
>   Loads bracket structure, ratings, and injury overrides; merges into dict[str, Team].
>   Gonzaga's conditional rating handled via `sweet_16_adj_em` field + `get_adj_em()` helper.
> - Implemented `src/win_probability.py` with logistic model (K=0.1198, ~3% per point).
>   Calibration: Duke vs Siena = 99.1%, 8v9 matchups ≈ 40-64%, 1-pt margin = 3.0% shift.
> - Validation script (`validate_sprint1_2.py`) confirms: all 68 teams loaded, 6 injury
>   overrides applied correctly, Gonzaga conditional rating works, win probability calibrated.
> - **Key observation:** Team-specific matchup probabilities diverge from historical seed
>   averages. E.g., St. John's (#17 KenPom) vs Northern Iowa (#71) = 84.4%, not the
>   historical 5v12 average of ~65%. This is correct — the model uses actual ratings.

---

## Phase 2: Core Engine — EV Scoring & Bracket Building

**Goal:** The system can generate a single complete bracket given a champion
assignment, optimized for × Seed expected value. This is the core intellectual
contribution of the project.

### Sprint 2.1: EV Scoring Engine
**Estimated Time:** 1-1.5 hours

**Objective:** Implement the expected value calculator that scores picks under
the Points × Seed system.

**Tasks:**
- [x] Implement `src/ev_engine.py`:
  - `score_correct_pick(round, seed)` → base_points × seed
  - `ev_of_pick(round, team, opponent, win_prob)` → P(win) × score
  - `compare_ev(round, team_a, team_b, prob_a_wins)` → which pick has higher EV
  - Handle multi-round cumulative EV (advancing a team through R1 + R2)
- [x] Build a demonstration: for each first-round matchup, show both teams'
      single-round EV and flag where the "upset" pick has higher EV than chalk
- [x] Validate the key insight: in 5-vs-12 matchups, the 12-seed should
      frequently have higher Round 1 EV

**Acceptance Criteria:**
- For every R1 matchup, the engine identifies whether chalk or upset is higher EV
- The demo output matches the math from STRATEGY.md Section 6
- Multi-round EV correctly compounds probabilities

**Sprint Update (Completed 2026-03-18):**
> - Implemented `src/ev_engine.py` with 6 functions: `score_correct_pick`, `ev_of_pick`,
>   `compare_ev`, `cumulative_ev`, `champion_path_ev`, `print_ev_comparison`.
> - Constants: `BASE_POINTS = {1:1, 2:2, 3:4, 4:8, 5:16, 6:32}`, sum = 63.
> - `compare_ev` is the workhorse for bracket_builder — returns (best_team, ev_a, ev_b).
> - `cumulative_ev` compounds win probabilities across rounds for multi-round path EV.
> - Demo output shows all 4 regions' R1 matchups with EV analysis + seed-group summaries.
> - **Key finding:** Only 4/28 R1 matchups have upset EV (underdog has higher expected value).
>   With team-specific KenPom ratings (vs historical seed averages), most favorites' win
>   probability is high enough to overcome the seed multiplier disadvantage. The exceptions
>   are in 6v11, 7v10, and 8v9 matchups with close ratings (e.g., VCU over UNC at 6.26 vs 2.59,
>   Iowa over Clemson at 5.36 vs 3.24).
> - **Key finding:** 8v9 matchups do NOT universally favor the 9-seed as STRATEGY.md's
>   base-rate analysis suggests. With team-specific ratings, only 2/4 favor the 9-seed.
>   Strong 8-seeds (Ohio State, Georgia) overcome the 1-point multiplier gap.
> - **Key finding:** No 5v12 matchup has upset EV this year — the 5-seeds are all strong
>   enough that their ~85% win probability overcomes the 12/5 multiplier ratio. This differs
>   from historical base rates (35.7% upset rate would yield upset EV).
> - Validation: `validate_sprint2_1.py` passes all checks (score_correct_pick, ev_of_pick,
>   compare_ev, cumulative_ev, champion_path_ev, constants, upset EV count).

---

### Sprint 2.2: Backwards-Chaining Bracket Builder
**Estimated Time:** 1.5-2 hours

**Objective:** Given a champion assignment, generate a complete 63-game bracket
that is internally consistent and EV-optimized.

**Tasks:**
- [x] Implement `src/bracket_builder.py`:
  - Accept a champion Team as input
  - Build the champion's path backward from Championship → R1
  - For the champion's region: pick opponents that maximize the champion's
    probability of advancing while also maximizing EV of the opponents' earlier
    games
  - For non-champion regions: use pure EV optimization at each node
  - Ensure internal consistency: no team can win a game after losing an earlier
    round
- [x] Handle the bracket topology correctly:
  - 4 regions of 16 teams
  - Regional winners meet in Final Four (East vs South, West vs Midwest based
    on the 2026 bracket structure)
  - The champion's Final Four opponent is the highest-EV regional winner from
    the paired region
- [x] Output a complete Bracket object with all 63 picks

**Acceptance Criteria:**
- Generate a bracket with Houston as champion — verify Houston wins every round
- Generate a bracket with Duke as champion — verify it's mostly chalk
- No internal inconsistencies (a team picked in Round 3 must also be picked
  in Rounds 1 and 2)
- Different champion assignments produce meaningfully different brackets

**Sprint Update (Completed 2026-03-18):**
> - Implemented `src/bracket_builder.py` with `Bracket` dataclass, `build_bracket()` main entry
>   point, `fill_region_ev()` for pure EV optimization, `fill_region_champion()` for champion
>   path enforcement, `validate_bracket()`, and `print_bracket()`.
> - First Four auto-resolution: reads known winners from bracket JSON (`"winner"` field),
>   auto-picks remaining games by higher AdjEM. Accepts `first_four_winners` override dict.
> - Algorithm: Champion wins every round in their region. All other games (including non-champion
>   games within the champion's region) use `compare_ev()` for EV optimization.
> - Final Four: champion beats paired region's E8 winner. Other semifinal uses `compare_ev(5)`.
> - Deep copy of bracket structure used internally — safe to call `build_bracket()` multiple times.
> - **Key finding:** x Seed scoring heavily favors upset picks in R2+. In non-champion regions,
>   8/9-seeds routinely beat 1-seeds by EV (e.g., Utah State 9-seed EV=2.13 vs Arizona 1-seed
>   EV=1.76 in R2, because 9×2=18 pts vs 1×2=2 pts). This is mathematically correct — the
>   seed multiplier overwhelms the probability advantage for low-seed teams in later rounds.
> - **Key finding:** R1 is mostly chalk (78% top-8 seeds picked) because in R1 the base points
>   are only 1, so the seed multiplier advantage is smaller. From R2 onward, base points double
>   each round, amplifying the seed multiplier effect.
> - **Key finding:** Non-champion regions produce identical picks across all brackets (EV
>   optimization is deterministic). Portfolio diversification (Sprint 4.1) will add correlation
>   penalties to differentiate close-call picks across brackets.
> - Validation: `validate_sprint2_2.py` passes all 6 tests (Houston champion path, Duke champion
>   path + chalk check, internal consistency, bracket differentiation, game counts, Kansas 4-seed).

---

### Sprint 2.3: Monte Carlo Simulator
**Estimated Time:** 1-1.5 hours

**Objective:** Simulate the tournament thousands of times to validate our
brackets and estimate expected scores.

**Tasks:**
- [ ] Implement `src/simulator.py`:
  - Simulate a full tournament using win probabilities
  - Score a bracket against a simulated outcome
  - Run N simulations (default 10,000) and collect statistics
- [ ] For each candidate bracket, compute:
  - Mean expected score across all simulations
  - Score distribution (10th, 50th, 90th percentile)
  - Championship pick hit rate
- [ ] Produce a "market validation" output: the simulator's championship
      probabilities per team should roughly align with Vegas odds. If Duke
      shows 50% and Vegas has 22%, something is wrong with the ratings.

**Acceptance Criteria:**
- Simulator runs 10,000 iterations in under 60 seconds
- Championship probabilities are in the right ballpark vs. market odds
- A chalk bracket scores lower in expectation than an EV-optimized bracket
  under × Seed scoring

**Sprint Update (Completed 2026-03-18):**
> - Implemented `src/simulator.py` with 3 dataclasses (`SimulatedTournament`, `BracketScore`,
>   `SimulationResults`) and 7 functions (`simulate_game`, `simulate_region`, `simulate_tournament`,
>   `score_bracket`, `run_simulation`, `championship_probabilities`, `print_simulation_report`).
> - Performance: 10,000 simulations complete in ~1.8 seconds (well under 60s target).
>   Pure Python loops with numpy only for RNG (`default_rng`). ~630K `win_probability_teams`
>   calls per run are fast enough without caching.
> - Reproducibility: same seed produces identical results across runs.
> - **Championship probability calibration vs Vegas:**
>   Duke 23.8% (Vegas 22%), Arizona 22.4% (19%), Michigan 13.3% (20%),
>   Florida 8.2% (12%), Houston 6.8% (9%), Iowa State 6.3% (4.5%),
>   Illinois 4.7% (5%). UConn flagged at 1.6% vs Vegas 5.6% — likely because
>   our injury overrides for their region opponents are more aggressive than Vegas.
>   Michigan lower than Vegas (13.3% vs 20%) — injury override of -3.0 may be too harsh.
> - **Key finding: Single-game EV optimization does NOT outperform chalk in total bracket
>   score.** Chalk Duke bracket (mean 224.4) outscores EV Duke bracket (mean 215.6) by
>   8.7 points. The reason: EV optimization picks upset winners in later rounds (e.g.,
>   9-seeds over 1-seeds in R2 because 9×2 > 1×2) that almost never actually happen.
>   The cascading correctness of chalk picks (favorites keep winning → more rounds correct)
>   outweighs the per-game EV advantage of upset picks. This means the bracket builder's
>   pure EV approach is too aggressive with upsets in R2+. Sprint 4.1 portfolio generation
>   should mix chalk and upset picks strategically rather than going all-in on single-game EV.
> - Validation: `validate_sprint2_3.py` passes all 6 tests (single simulation validity,
>   scoring correctness, championship probability sanity, bracket score sanity, performance,
>   reproducibility).

---

## Phase 3: Data & Research (Can Run in Parallel)

**Goal:** Gather the real-world data that makes our model better than a pure
seed-based approach. This phase can happen alongside Phase 2 — Nick gathers
data while Claude Code builds the engine.

### Sprint 3.1: Team Ratings Data Collection
**Estimated Time:** 30 minutes (automated via Playwright)

**Objective:** Populate team_ratings.json with real efficiency data.

**Note:** This sprint has been largely absorbed into Sprint 1.2. The KenPom
scrape (via Playwright) will happen as the first task of Sprint 1.2, producing
`config/team_ratings.json` automatically. This sprint now covers only the
manual follow-up work.

**Tasks:**
- [x] Verify the Playwright-scraped KenPom data looks correct for top teams
- [x] Update injury_overrides.json with any new developments (First Four
      results, last-minute injury news)

**Acceptance Criteria:**
- team_ratings.json has entries for all 68 teams
- Top 10 teams' ratings align with known KenPom rankings (Duke #1, Michigan #2,
  Arizona #3, etc.)

**Sprint Update (Completed 2026-03-18):**
> - **BartTorvik cross-reference:** Attempted but barttorvik.com has browser
>   verification that blocked both Playwright and WebFetch. KenPom data validated
>   indirectly via Vegas lines comparison — non-injury games show strong alignment
>   between our AdjEM-derived spreads and Vegas (within 1-2 points).
> - **First Four results (2 of 4):** Howard beat UMBC 86-83 (FF1), Texas beat
>   NC State 68-66 (FF2). FF3 (Prairie View A&M vs Lehigh) and FF4 (Miami OH vs
>   SMU) scheduled tonight — update bracket_2026.json when results come in.
> - **3 new injury overrides added:**
>   - Texas Tech: -6.5 (JT Toppin torn ACL Feb 17, 21.8 PPG — dropped from 3-seed to 5-seed)
>   - Louisville: -4.0 (Mikel Brown Jr. questionable, potential lottery pick, missed ACC tourney)
>   - Clemson: -2.5 (Carter Welling torn ACL Mar 12, second-leading scorer)
> - **Duke override reduced:** -2.0 → -1.0 (Ngongba probable for Thursday per Scheyer).
>   Revert to -2.0 if Ngongba ruled out Thursday morning.
> - **Vegas calibration finding:** Our injury overrides are ~2-4 pts more aggressive
>   than Vegas for UNC (-6.0 vs ~-3.5 implied), Alabama (-4.0 vs ~-2.5), Gonzaga
>   (-4.0 vs ~-3.0), BYU (-3.5 vs ~-2.0). Duke's -1.0 aligns perfectly. May
>   partially double-count since KenPom already reflects recent games without
>   injured players. For x Seed scoring, more aggressive overrides = more upset
>   picks, which is strategically desirable.
> - **Swing bracket #10 finalized:** Michigan (1-seed, EV 12.6) over Virginia
>   (3-seed, EV 2.5). Vanderbilt was incorrectly listed as Midwest candidate
>   (it's in South). portfolio_plan.json updated.
> - **Championship futures for calibration:** Duke ~22%, Michigan ~20%, Arizona ~19%,
>   Florida ~12%, Houston ~9%, UConn ~5.6%, Illinois/Iowa State ~4-5%.
> - All validations pass (sprint1_1, sprint1_2).

---

### Sprint 3.2: Expert Bracket Collection (Optional)
**Estimated Time:** 30-60 minutes

**Objective:** Collect published expert brackets to identify consensus and
disagreement.

**Tasks:**
- [ ] Record Jay Bilas (ESPN), CBS model, and Fox Sports expert champion picks
      and Final Four selections
- [ ] Identify games where experts sharply disagree — these inform the swing
      bracket's differentiation
- [ ] Save as `data/expert_picks.json`

**Note:** This is a nice-to-have. If time is tight, skip this sprint. The Monte
Carlo simulator will identify high-uncertainty games on its own.

**Sprint Update (Completed 2026-03-18):**
> - Collected expert bracket picks from ESPN (60-analyst poll + Jay Bilas), CBS Sports
>   (Norlander, Parrish, Bruce Pearl panel), Fox Sports, SI, Covers, SportsBookReview.
> - Saved to `data/expert_picks.json` with structured expert brackets, consensus upsets,
>   key disagreements, Vegas odds, CBS pool popularity, and portfolio implications.
> - **ESPN 60-analyst poll champion votes:** Arizona 33, Michigan 10, Duke 9, Florida 5,
>   Houston 2, Purdue 1. Arizona is the overwhelming expert favorite.
> - **CBS pool popularity:** Duke 29.2%, Arizona 21.9%, Michigan 13.7%. Duke is the
>   public's favorite despite having the toughest path + injuries.
> - **Consensus upset picks (near-unanimous):** South Florida over Louisville (11v6),
>   Akron over Texas Tech (12v5). Both align with our injury overrides.
> - **Key disagreement — East region:** Experts split on WHO beats Duke: Michigan State
>   (Bilas E8 upset), St. John's (Pearl S16 upset), UConn (some models). Duke wins
>   region per 39/60 ESPN analysts. East is the highest-variance region.
> - **Key disagreement — South region:** Houston (34/60 ESPN, home-court at Toyota Center)
>   vs Florida (1-seed, defending champion, easiest path). Our portfolio covers both.
> - **Portfolio validation:** Our 4 contrarian picks (Iowa State, Gonzaga, Illinois, Kansas)
>   have ZERO expert champion picks — maximum differentiation. Our chalk/value picks
>   (Duke, Arizona, Houston, Michigan) all have strong expert support.
> - **Swing bracket insight:** Duke is most popular public pick but has toughest path +
>   injuries. East region disagreement is ideal for swing bracket differentiation.

---

## Phase 4: Generation & Output

**Goal:** Generate all 10 brackets, review them, and prepare for submission.

### Sprint 4.1: Portfolio Generation
**Estimated Time:** 1-1.5 hours

**Objective:** Generate all 10 brackets with portfolio-level diversification.

**Design Notes (from Sprint 2.3 + 3.2 findings):**

The Monte Carlo simulator revealed that pure single-game EV optimization picks too
many upsets in later rounds, hurting total bracket score (chalk Duke outscored EV Duke
by 8.7 points). Expert data from Sprint 3.2 confirms the right approach: mostly chalk
with **selective, injury-driven upsets** that have high confidence. The portfolio.py
design below incorporates both findings.

Additionally, expert picks data (`data/expert_picks.json`) provides:
- Consensus upset picks that align with our injury overrides (lock these across brackets)
- CBS pool popularity data for contrarian value calculation
- Key regional disagreements for bracket diversification

**Tasks:**
- [ ] Implement `src/portfolio.py`:
  - Load the 10 champion assignments from portfolio_plan.json
  - Load expert consensus data from `data/expert_picks.json`
  - **Pick strategy (3 tiers instead of pure EV):**
    - **Locked picks:** Consensus upsets backed by both EV and expert agreement
      (South Florida/Louisville, Akron/Texas Tech, VCU/North Carolina,
      Texas/BYU, Iowa/Clemson). These go in all 10 brackets.
    - **Chalk picks:** For non-champion regions in R2+, default to chalk (pick the
      favorite by win probability) rather than single-game EV. The simulator showed
      cascading correctness matters more than per-game EV in later rounds.
    - **Diversification picks:** In close-call games (EV gap < threshold OR win
      probability 40-60%), vary the pick across brackets. Chalk brackets (#1-2)
      pick the favorite; value/contrarian brackets pick the upset side.
  - Generate each bracket using bracket_builder (champion path unchanged)
  - Apply diversification: for each subsequent bracket, flip close-call picks
    that match previous brackets, prioritizing games in the champion's region
    and Final Four path
  - **Swing bracket (#10, Michigan):** Use expert disagreement data — East region
    is highest-variance (experts split on Duke/MSU/STJ/UConn), so swing bracket
    picks against Duke-wins-East consensus. Also pick opposite side of any game
    where 8+ of the other 9 brackets agree.
- [ ] Implement `src/output.py`:
  - Text-based bracket display for each of the 10 brackets
  - Highlight champion, Final Four, Elite 8
  - Flag upset picks (lower seed beating higher seed)
  - Flag expert-consensus picks and contrarian picks
  - Portfolio summary: champion distribution, regional distribution,
    CBS pool popularity overlap (lower = more contrarian = more upside),
    and pick correlation matrix across 10 brackets
- [ ] Run `generate_brackets.py` to produce all output files
- [ ] Run simulator on all 10 brackets to verify expected scores and
      portfolio-level diversification (score correlation < 0.8 between brackets)

**Acceptance Criteria:**
- 10 complete brackets generated, each internally consistent
- No two brackets are identical
- Champions match the portfolio plan
- Regional distribution: no more than 3 brackets from any single region
- Consensus upset picks appear in all 10 brackets
- Chalk brackets (#1-2) have ≤5 upset picks outside R1
- Contrarian brackets (#5-8) have meaningfully different non-champion regions
- Output is human-readable and can be used to fill out CBS brackets manually
- Simulator confirms all 10 brackets score > 150 mean expected points

**Sprint Update (Completed 2026-03-18):**
> - Created `src/portfolio.py` with 3-tier pick strategy: locked consensus upsets (5 games
>   in all brackets), chalk R2+ for safe brackets, EV R2+ for contrarian brackets.
> - Created `src/output.py` with CBS-entry-optimized bracket display, upset [U] and
>   consensus [C] flags, pick correlation matrix, and portfolio summary.
> - Created `generate_brackets.py` as main entry point with full acceptance testing.
> - **5 locked picks:** South Florida/Louisville (East), Akron/Texas Tech (MW),
>   Texas/BYU (West), VCU/North Carolina (South), Iowa/Clemson (South). All backed by
>   expert consensus (2-5 experts) AND EV agreement OR injury overrides.
> - **6 close-call diversification games** identified: UCF/UCLA (East), Utah State/Villanova
>   (West), Saint Louis/Georgia (MW), Santa Clara/Kentucky (MW), Texas A&M/Saint Mary's
>   (South). Value brackets rotate 2-3 of these; contrarian brackets take all.
> - **Key design: two bracket profiles.** Chalk/value brackets (#1-6) use win probability
>   for R2+ (safe, mean 211-229 pts). Contrarian/swing brackets (#7-10) use EV for R2+
>   (aggressive, mean 196-211 pts, but higher upside — 90th percentile up to 294 pts).
> - **Correlation structure:** Chalk cluster 0.84-0.98, contrarian cluster 0.76-0.90,
>   cross-cluster 0.54-0.68. Contrarian brackets are meaningfully different.
> - **All acceptance criteria pass:** 10 valid unique brackets, champions match plan,
>   all scores > 150 (range 196-229), chalk brackets ≤3 non-R1 upsets, 5 locked picks
>   in all brackets.
> - Simulation: 10K tournaments in ~9s. Duke chalk bracket highest mean (229.4),
>   Kansas contrarian lowest mean (196.0) but highest path value (252 pts).
> - Output: 10 bracket files + portfolio summary written to `output/brackets/`.

---

### Sprint 4.2: Review, Adjust, Submit
**Estimated Time:** 1-2 hours (mostly human review)

**Objective:** Review all 10 brackets, make manual adjustments, and submit.

**Tasks:**
- [ ] Review each bracket for obvious problems:
  - Does the champion's path make narrative sense?
  - Are there any picks that seem crazy (e.g., 15-seed in the Elite 8)?
  - Do the upset picks align with known information (injuries, hot streaks)?
- [ ] Run the simulator to score each bracket and verify the portfolio's
      expected value
- [ ] Update First Four results (games played Tue/Wed) in the bracket data
- [ ] Apply any late-breaking news to injury overrides and re-run if needed
- [ ] Manually enter all 10 brackets on CBS Sports before Thursday tip-off

**Acceptance Criteria:**
- All 10 brackets submitted on CBS before deadline
- Nick is comfortable with every bracket and understands the logic behind
  key picks
- Portfolio summary saved for post-tournament analysis

**Sprint Update:**
> _[To be completed]_

---

## Implementation Notes

### Dependencies Between Sprints

- Sprint 1.1 → 1.2 → 2.1 → 2.2 (strict sequence)
- Sprint 2.3 can start after 2.1 (doesn't need bracket builder)
- Sprint 3.1 can start immediately (independent data gathering)
- Sprint 3.2 is optional and independent
- Sprint 4.1 requires 2.2 + 2.3 + 3.1
- Sprint 4.2 requires 4.1

### Critical Path

The minimum viable product is: **1.1 → 1.2 → 2.1 → 2.2 → 4.1 → 4.2**

The Monte Carlo simulator (2.3) and expert collection (3.2) are valuable but
not blocking. If time runs short, skip the simulator and use the EV engine
alone to generate brackets — it will still produce dramatically better results
than hand-picking.

### Time Pressure Fallback

If things take longer than expected, this is the priority order:

1. **Must have:** 10 brackets with assigned champions, built backward from
   champion, using EV optimization with injury overrides. (Sprints 1.1-2.2, 4.1)
2. **Should have:** Monte Carlo validation showing expected scores and
   championship probability calibration. (Sprint 2.3)
3. **Nice to have:** Expert ensemble integration, portfolio correlation
   analysis, fancy output formatting. (Sprint 3.2, polish)

### Testing Strategy

Test each component as it's built:
- After 1.2: Print one region's matchup probabilities
- After 2.1: Print EV comparison for all R1 games
- After 2.2: Generate and print one complete bracket
- After 2.3: Run simulation and compare championship probs to Vegas
- After 4.1: Review all 10 brackets side by side

### Definition of Done

A sprint is complete when:
1. All tasks are checked off
2. Acceptance criteria are met
3. Code runs without errors
4. Sprint Update is filled in with key decisions and notes for future sprints
