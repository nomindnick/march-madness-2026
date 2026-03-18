# March Madness 2026: 10-Bracket Portfolio Generator

## Overview

A Python-based system that generates 10 strategically differentiated March
Madness brackets optimized for a Points × Seed scoring system. The system
combines team efficiency data, injury adjustments, Monte Carlo simulation, and
portfolio-level diversification to maximize the probability that at least one
bracket finishes in the top 3 of a ~30-60 person office pool.

## Problem Statement

Our firm's bracket pool uses a Points × Seed scoring system where every round
multiplies base points by the winning team's seed number. This creates extreme
incentives that most participants won't understand: a 3-seed champion's full
path is worth 3× a 1-seed's path (189 vs 63 points). With 10 bracket slots
available, we can exploit this by building a diversified portfolio of brackets
with different champion picks weighted toward the 2-4 seed range where expected
value peaks.

Filling out 10 brackets by hand — each internally consistent, scoring-optimized,
and strategically differentiated — is impractical. This system automates the
generation while preserving human strategic control over champion assignments
and injury adjustments.

## Goals & Success Criteria

- **Primary:** Generate 10 complete, valid, internally consistent brackets
  before Thursday March 19 tip-off
- **Secondary:** Each bracket should maximize expected points under the × Seed
  scoring system given its assigned champion
- **Tertiary:** The 10-bracket portfolio should have low correlation — different
  brackets should pick different upsets and paths, covering more of the outcome
  space
- **Stretch:** Produce analysis output showing the expected value of our
  portfolio vs. naive chalk brackets

## Target Users

Nick (the developer) — Python beginner, working in Claude Code. The system
should be straightforward to run, with clear configuration files for adjusting
inputs (champion assignments, injury overrides) and readable output (printable
bracket summaries).

## Core Components

### 1. Team Data & Efficiency Ratings

Pull or manually enter team-level efficiency data for all 68 tournament teams.
The key metrics per team:

- **Adjusted Offensive Efficiency (AdjO):** Points scored per 100 possessions,
  adjusted for opponent quality
- **Adjusted Defensive Efficiency (AdjD):** Points allowed per 100 possessions,
  adjusted for opponent quality
- **Adjusted Efficiency Margin (AdjEM):** AdjO - AdjD (the overall power rating)
- **Seed** and **Region** assignment

**Primary data source:** BartTorvik.com (free alternative to KenPom). The T-Rank
ratings provide the same core metrics. If web scraping is problematic, manually
enter the top ~40 teams and use seed-based estimates for the rest.

**Fallback:** Use the 1-68 seed list combined with historical seed-based
performance averages as a simpler (less accurate) baseline.

### 2. Efficiency Override Dictionary

**This is architecturally critical.** Season-long efficiency metrics do not
reflect late-season injuries. The system must include a configuration dictionary
where we manually adjust team ratings before running simulations.

```python
# Example structure
INJURY_OVERRIDES = {
    "Michigan": {"adj_em_delta": -3.0, "note": "L.J. Cason torn ACL, key guard out"},
    "Alabama": {"adj_em_delta": -4.0, "note": "Aden Holloway suspended, top 3pt shooter"},
    "North Carolina": {"adj_em_delta": -6.0, "note": "Caleb Wilson broken thumb, best player out"},
    "BYU": {"adj_em_delta": -3.5, "note": "Richie Saunders ACL, went 4-6 since injury"},
    "Duke": {"adj_em_delta": -2.0, "note": "Caleb Foster broken foot, Ngongba foot soreness"},
    "Gonzaga": {
        "adj_em_delta": -4.0,
        "note": "Braden Huff out opening weekend, possible Sweet 16 return",
        "sweet_16_override": -1.0  # Reduced penalty if they reach S16
    },
}
```

These overrides are applied after loading base ratings and before any
simulation runs. They should be easy to edit in a single config file.

### 3. Win Probability Engine

Given two teams' adjusted efficiency margins, estimate P(Team A wins).

The standard approach (used by KenPom) models game outcomes as:

```
Expected margin = AdjEM_A - AdjEM_B + home_court_adjustment
P(A wins) = function of expected margin (logistic or normal CDF)
```

Since all tournament games are neutral site, home court = 0. The conversion
from expected margin to win probability uses a logistic function calibrated
to college basketball (roughly: every 1 point of expected margin ≈ 3% win
probability shift from 50%).

The engine must be able to compute P(A beats B) for any pair of teams in the
field, not just the actual first-round matchups.

### 4. Custom EV Scoring Engine

The scoring formula for our pool:

```
points_for_correct_pick(round, seed) = base_points[round] × seed

where base_points = {1: 1, 2: 2, 3: 4, 4: 8, 5: 16, 6: 32}
```

The EV engine calculates, for every game node in the bracket:

```
EV(pick team A) = P(A wins) × base_points[round] × seed_A
EV(pick team B) = P(B wins) × base_points[round] × seed_B
```

**Critical:** This is NOT the same as picking the most likely winner. Under
× Seed scoring, a team with 35% win probability but a 12-seed often has
higher EV than the 65% favorite with a 5-seed.

The EV engine must also account for cascading rounds — picking a team to win
in Round 2 requires them to first win Round 1. The cumulative EV of advancing
a team through multiple rounds must be computed correctly.

### 5. Backwards-Chaining Bracket Builder

Each bracket is built starting from a pre-assigned champion and working backward:

1. **Championship game:** Champion is assigned (e.g., Houston, 2-seed South)
2. **Final Four:** Champion's opponent is the highest-EV team from the opposing
   semifinal pairing (East/West vs South/Midwest based on bracket structure)
3. **Elite 8:** Champion must win their regional final. Pick their most likely
   opponent and the champion wins.
4. **Sweet 16 → Round 1:** Fill in the champion's region to create a consistent
   path. Then fill the remaining three regions using pure EV optimization.

The backward chain ensures no bracket ever has a team winning the championship
after being eliminated in an earlier round (a common bug in naive generators).

For the non-champion regions, the algorithm should optimize for maximum expected
points at each node, not just pick the most likely winner.

### 6. Monte Carlo Tournament Simulator

Simulate the entire tournament N times (default: 10,000) using the win
probability engine. For each simulation:

1. Resolve First Four games probabilistically
2. Play each round, advancing winners based on probabilities
3. Record the full bracket outcome
4. Score every candidate bracket against the simulated outcome using the
   × Seed scoring formula

This produces:
- Distribution of expected scores for each bracket
- Championship frequency per team (for validation against market odds)
- Identification of high-value "sleeper" paths the model discovers

### 7. Portfolio Diversifier

The 10 brackets should not all pick the same first-round upsets. The diversifier
enforces differentiation:

- **Champion constraint:** Each bracket has a pre-assigned champion (from the
  portfolio plan in STRATEGY.md)
- **Correlation penalty:** When generating brackets 2-10, penalize picks that
  duplicate earlier brackets in the same round. The penalty doesn't prevent
  duplication (sometimes the EV is so strong that all brackets should agree)
  but biases toward variety in close-call games.
- **Implementation:** For each game, compute EV for both sides. If the gap is
  small (< threshold), alternate the pick across brackets. If the gap is large,
  all brackets pick the same way.

### 8. Output: Printable Bracket Summaries

For each of the 10 brackets, produce:
- A text-based bracket showing all picks by round
- The champion, Final Four, and Elite 8 picks highlighted
- Total expected points (from Monte Carlo simulation)
- Key upset picks flagged
- A brief narrative summary ("This bracket bets on Houston navigating the
  South and Iowa State emerging from a weakened Midwest")

Also produce a portfolio summary:
- Champion distribution across brackets
- Regional champion distribution
- Total portfolio expected value vs. a naive all-chalk baseline
- Correlation matrix showing how similar each pair of brackets is

## Technical Architecture

### Technology Stack

- **Language:** Python 3.x
- **Key Libraries:** numpy (simulation), pandas (data handling), json (config)
- **Optional:** matplotlib or a simple text-based visualization for bracket output
- **No external APIs required** — all data can be manually entered or scraped
  from free sources

### Data Model

```
Team:
  - name: str
  - seed: int
  - region: str ("East", "West", "Midwest", "South")
  - adj_o: float (adjusted offensive efficiency)
  - adj_d: float (adjusted defensive efficiency)
  - adj_em: float (adjusted efficiency margin, after overrides)

BracketSlot:
  - round: int (1-6)
  - region: str
  - position: int (slot within region)
  - team_picked: Team

Bracket:
  - champion: Team
  - slots: list[BracketSlot] (63 total game picks)
  - expected_points: float
  - tier: str ("chalk", "value", "contrarian", "swing")

Portfolio:
  - brackets: list[Bracket] (10 total)
  - correlation_matrix: 10×10 float matrix
```

### Project Structure

```
march-madness-2026/
├── STRATEGY.md              # Strategic analysis and portfolio plan
├── SPEC.md                  # This document
├── IMPLEMENTATION_PLAN.md   # Sprint-by-sprint build plan
├── config/
│   ├── bracket_2026.json    # Full bracket structure (teams, seeds, regions)
│   ├── team_ratings.json    # Efficiency ratings per team
│   ├── injury_overrides.json# Manual efficiency adjustments
│   └── portfolio_plan.json  # Champion assignments per bracket
├── data/
│   ├── historical_upsets.csv# Seed-vs-seed historical win rates
│   └── expert_picks.json    # Collected expert brackets (optional)
├── src/
│   ├── data_loader.py       # Load and merge config/data files
│   ├── win_probability.py   # P(A beats B) calculator
│   ├── ev_engine.py         # Expected value under × Seed scoring
│   ├── bracket_builder.py   # Backwards-chaining bracket construction
│   ├── simulator.py         # Monte Carlo tournament simulation
│   ├── portfolio.py         # Diversification and portfolio analysis
│   └── output.py            # Bracket formatting and summaries
├── output/
│   ├── brackets/            # Individual bracket files
│   ├── portfolio_summary.md # Overall portfolio analysis
│   └── simulation_stats.md  # Monte Carlo results
├── generate_brackets.py     # Main entry point
└── requirements.txt
```

## Key Design Decisions

1. **Manual data entry over web scraping:** Given time pressure (2 days) and
   that we only need ~68 teams' ratings, manual entry from BartTorvik is more
   reliable than building a scraper. The config files make this easy to update.

2. **Pre-assigned champions:** The human (Nick) decides which team each bracket
   picks as champion, based on STRATEGY.md analysis. The algorithm optimizes
   the rest of each bracket given that constraint. This keeps strategic control
   with the human while automating the tedious 63-game optimization.

3. **Injury overrides as a first-class feature:** Season-long metrics are stale
   for injured teams. The override dictionary is not a hack — it's a core
   architectural requirement that makes the model's output meaningfully better
   than raw KenPom predictions.

4. **EV optimization over most-likely-winner:** Every pick in every bracket is
   chosen to maximize expected points under the × Seed system, not to maximize
   the number of correct picks. These are very different objectives.

5. **Portfolio diversification as a constraint, not a separate step:** The
   diversifier runs during bracket generation, not after. This ensures variety
   is baked into the process rather than applied as a post-hoc adjustment.

## Constraints & Considerations

### Known Challenges

- **Data availability:** KenPom requires a subscription. BartTorvik is free but
  may require manual transcription. If neither is accessible, the system should
  degrade gracefully to seed-based probability estimates.
- **Gonzaga conditional rating:** Huff's possible Sweet 16 return creates a
  team whose strength changes mid-tournament. The model should handle this
  (different AdjEM for rounds 1-2 vs rounds 3+).
- **First Four uncertainty:** Four matchups are played tonight/tomorrow before
  we generate brackets. The system should be able to update these results.

### Out of Scope

- Live updating during the tournament
- Automated web scraping (manual data entry is fine)
- Women's tournament brackets
- Betting or wagering integration

## Scoring System Reference

| Round         | Base Points | Formula              | Example (5-seed correct) |
|---------------|-------------|----------------------|--------------------------|
| Round of 64   | 1           | 1 × seed             | 5 pts                    |
| Round of 32   | 2           | 2 × seed             | 10 pts                   |
| Sweet 16      | 4           | 4 × seed             | 20 pts                   |
| Elite 8       | 8           | 8 × seed             | 40 pts                   |
| Final Four    | 16          | 16 × seed            | 80 pts                   |
| Championship  | 32          | 32 × seed            | 160 pts                  |
| **Full path** |             |                      | **315 pts**              |

## Notes for Claude Code

- Nick is a Python beginner. Code should be clean, well-commented, and avoid
  overly clever patterns. Straightforward is better than elegant.
- Use standard library + numpy + pandas only. Minimize dependencies.
- Config files (JSON) should be human-readable and easy to edit by hand.
- The system should produce useful output even if only partially complete —
  e.g., generating one bracket is valuable even if the portfolio diversifier
  isn't finished yet.
- Print clear progress messages so Nick can see what's happening during
  simulation runs.
- Error handling should be friendly — if a team name doesn't match between
  files, say which one instead of crashing with a KeyError.
- Test each component independently before integrating.
- The whole system needs to run and produce output by Wednesday evening.
