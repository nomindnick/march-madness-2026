# CLAUDE.md

## Project Overview

Python system that generates 10 strategically differentiated March Madness brackets
optimized for a **Points x Seed** scoring system. Targets a ~30-60 person office pool.

**Deadline:** Thursday, March 19, 2026 — before first game tip-off.

## Key Documents

- `STRATEGY.md` — Strategic analysis, scoring math, portfolio allocation, all bracket matchups
- `SPEC.md` — Technical architecture, data model, component descriptions
- `IMPLEMENTATION_PLAN.md` — Sprint-by-sprint build plan with acceptance criteria

## Project Structure

```
config/
  bracket_2026.json     — 68 teams, 4 regions, First Four, Final Four pairings
  portfolio_plan.json   — 10 champion assignments (2 chalk / 4 value / 3 contrarian / 1 swing)
  injury_overrides.json — AdjEM deltas for injured/suspended players
  team_ratings.json     — KenPom efficiency ratings (AdjO, AdjD, AdjEM, rank, conf)
src/
  data_loader.py        — Team dataclass, load_teams() -> dict[str, Team], get_adj_em()
  win_probability.py    — P(A beats B) logistic model (K=0.1198, ~3%/pt)
  ev_engine.py          — [Sprint 2.1] Expected value under x Seed scoring
  bracket_builder.py    — [Sprint 2.2] Backwards-chaining bracket construction
  simulator.py          — [Sprint 2.3] Monte Carlo tournament simulation
  portfolio.py          — [Sprint 4.1] Diversification across 10 brackets
  output.py             — [Sprint 4.1] Bracket formatting and summaries
data/                   — Historical data, expert picks
output/brackets/        — Generated bracket files
generate_brackets.py    — [Sprint 4.1] Main entry point
```

## Sprint Status

- [x] Sprint 1.1 — Project scaffolding & bracket data (config files, directory structure)
- [x] Sprint 1.2 — Team ratings & win probability engine
- [ ] Sprint 2.1 — EV scoring engine
- [ ] Sprint 2.2 — Backwards-chaining bracket builder
- [ ] Sprint 2.3 — Monte Carlo simulator
- [ ] Sprint 4.1 — Portfolio generation & output
- [ ] Sprint 4.2 — Review, adjust, submit

## Critical Conventions

### Team Names

Team names must be **identical** across all config files. Canonical names come from
`bracket_2026.json`. Key names to get right:

- `Michigan State` (not "Michigan St." or "MSU")
- `St. John's` (abbreviated, with apostrophe)
- `Miami (FL)` and `Miami (OH)` (parenthetical qualifiers required)
- `Queens (NC)` (parenthetical qualifier)
- `Prairie View A&M` and `Texas A&M` (full names)
- `Saint Mary's` and `Saint Louis` (spelled out "Saint")
- `North Carolina` (not "UNC")

### Bracket Tree Structure

Matchups in each region are ordered: 1v16, 8v9, 5v12, 4v13, 6v11, 3v14, 7v10, 2v15
(slots 0-7). The tree is implicit in the array indices:

- Round 2: `slot // 2` (slots 0-1 -> game 0, slots 2-3 -> game 1, etc.)
- Sweet 16: `slot // 4`
- Elite 8: `slot // 8` (always 0 — regional final)

### First Four Handling

Four main-bracket slots have `"team": null` with a `"first_four_id"` reference.
The `first_four` array in bracket_2026.json lists the two candidate teams.
Data loader must resolve these before simulation.

### Gonzaga Conditional Rating

Gonzaga has different injury impact by round: `adj_em_delta: -4.0` for rounds 1-2,
`sweet_16_override: -1.0` from Sweet 16 onward (Braden Huff possible return).

### Scoring System

```
points = base_points[round] x seed
base_points = {R64: 1, R32: 2, S16: 4, E8: 8, FF: 16, Championship: 32}
Full champion path = seed x 63
```

A 3-seed champion path = 189 pts. A 1-seed champion path = 63 pts.
EV optimization picks higher-seed teams more aggressively than probability alone suggests.

## Commands

```bash
python validate_sprint1_1.py   # Validate config file integrity
python validate_sprint1_2.py   # Validate team ratings & win probability
python -m src.data_loader      # Print all 68 teams sorted by AdjEM
python -m src.win_probability  # Print East R1 matchups + calibration check
```

## Dependencies

Python 3.x, numpy, pandas. Install: `pip install -r requirements.txt`

## Style

Nick is a Python beginner. Code should be clean, well-commented, straightforward.
Standard library + numpy + pandas only. No clever patterns. Friendly error messages
(say which team name doesn't match, don't crash with KeyError).
