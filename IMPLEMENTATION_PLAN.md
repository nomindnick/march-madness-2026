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
- [ ] Implement `src/ev_engine.py`:
  - `score_correct_pick(round, seed)` → base_points × seed
  - `ev_of_pick(round, team, opponent, win_prob)` → P(win) × score
  - `compare_ev(round, team_a, team_b, prob_a_wins)` → which pick has higher EV
  - Handle multi-round cumulative EV (advancing a team through R1 + R2)
- [ ] Build a demonstration: for each first-round matchup, show both teams'
      single-round EV and flag where the "upset" pick has higher EV than chalk
- [ ] Validate the key insight: in 5-vs-12 matchups, the 12-seed should
      frequently have higher Round 1 EV

**Acceptance Criteria:**
- For every R1 matchup, the engine identifies whether chalk or upset is higher EV
- The demo output matches the math from STRATEGY.md Section 6
- Multi-round EV correctly compounds probabilities

**Sprint Update:**
> _[To be completed by Claude Code]_

---

### Sprint 2.2: Backwards-Chaining Bracket Builder
**Estimated Time:** 1.5-2 hours

**Objective:** Given a champion assignment, generate a complete 63-game bracket
that is internally consistent and EV-optimized.

**Tasks:**
- [ ] Implement `src/bracket_builder.py`:
  - Accept a champion Team as input
  - Build the champion's path backward from Championship → R1
  - For the champion's region: pick opponents that maximize the champion's
    probability of advancing while also maximizing EV of the opponents' earlier
    games
  - For non-champion regions: use pure EV optimization at each node
  - Ensure internal consistency: no team can win a game after losing an earlier
    round
- [ ] Handle the bracket topology correctly:
  - 4 regions of 16 teams
  - Regional winners meet in Final Four (East vs South, West vs Midwest based
    on the 2026 bracket structure)
  - The champion's Final Four opponent is the highest-EV regional winner from
    the paired region
- [ ] Output a complete Bracket object with all 63 picks

**Acceptance Criteria:**
- Generate a bracket with Houston as champion — verify Houston wins every round
- Generate a bracket with Duke as champion — verify it's mostly chalk
- No internal inconsistencies (a team picked in Round 3 must also be picked
  in Rounds 1 and 2)
- Different champion assignments produce meaningfully different brackets

**Sprint Update:**
> _[To be completed by Claude Code]_

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

**Sprint Update:**
> _[To be completed by Claude Code]_

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
- [ ] Verify the Playwright-scraped KenPom data looks correct for top teams
- [ ] Update injury_overrides.json with any new developments (First Four
      results, last-minute injury news)

**Acceptance Criteria:**
- team_ratings.json has entries for all 68 teams
- Top 10 teams' ratings align with known KenPom rankings (Duke #1, Michigan #2,
  Arizona #3, etc.)

**Sprint Update:**
> _[To be completed]_

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

**Sprint Update:**
> _[To be completed]_

---

## Phase 4: Generation & Output

**Goal:** Generate all 10 brackets, review them, and prepare for submission.

### Sprint 4.1: Portfolio Generation
**Estimated Time:** 1-1.5 hours

**Objective:** Generate all 10 brackets with portfolio-level diversification.

**Tasks:**
- [ ] Implement `src/portfolio.py`:
  - Load the 10 champion assignments from portfolio_plan.json
  - Generate each bracket using bracket_builder
  - Apply correlation penalty: for each subsequent bracket, penalize picks that
    match previous brackets in close-call games (EV gap < threshold)
  - For the swing bracket (#10), identify the game with highest disagreement
    across the other 9 brackets and pick the opposite side
- [ ] Implement `src/output.py`:
  - Text-based bracket display for each of the 10 brackets
  - Highlight champion, Final Four, Elite 8
  - Flag upset picks (lower seed beating higher seed)
  - Portfolio summary with champion distribution, regional distribution,
    and correlation matrix
- [ ] Run `generate_brackets.py` to produce all output files

**Acceptance Criteria:**
- 10 complete brackets generated, each internally consistent
- No two brackets are identical
- Champions match the portfolio plan
- Regional distribution: no more than 3 brackets from any single region
- Output is human-readable and can be used to fill out CBS brackets manually

**Sprint Update:**
> _[To be completed by Claude Code]_

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
