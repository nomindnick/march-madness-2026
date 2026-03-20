# March Madness 2026: AI-Assisted Bracket Portfolio Generator

## Overview

A Python system built with Claude that generates 10 strategically differentiated
March Madness brackets for an office pool (~30-60 people). The pool uses a
**Points x Seed** scoring system that creates unusual incentive structures. The
system combines team efficiency data, late-breaking injury adjustments, Monte Carlo
simulation, and portfolio-level diversification to maximize the probability that at
least one bracket finishes in the top 3.

---

## The Scoring System

The pool's scoring system multiplies base points by the winning team's seed number
in every round:

| Round         | Base Points | Formula          |
|---------------|-------------|------------------|
| Round of 64   | 1           | 1 x seed         |
| Round of 32   | 2           | 2 x seed         |
| Sweet 16      | 4           | 4 x seed         |
| Elite 8       | 8           | 8 x seed         |
| Final Four    | 16          | 16 x seed        |
| Championship  | 32          | 32 x seed        |

A team's entire champion path is worth **seed x 63** points:

| Champion Seed | Full Path Value | vs. 1-Seed |
|---------------|-----------------|------------|
| 1-seed        | 63 pts          | 1.0x       |
| 2-seed        | 126 pts         | 2.0x       |
| 3-seed        | 189 pts         | 3.0x       |
| 4-seed        | 252 pts         | 4.0x       |

This is very different from standard ESPN scoring. A 3-seed champion earns
**triple** the path points of a 1-seed champion. A correct 12-seed pick in
Round 1 is worth 12 points; a correct 1-seed pick is worth 1 point. The entire
system is built around optimizing for this multiplier.

---

## How It Works

### The Probability Engine

The system scrapes [KenPom](https://kenpom.com) efficiency ratings for all 68
tournament teams using Playwright browser automation. KenPom provides tempo-free,
opponent-adjusted metrics:

- **Adjusted Offensive Efficiency (AdjO):** Points scored per 100 possessions
- **Adjusted Defensive Efficiency (AdjD):** Points allowed per 100 possessions
- **Adjusted Efficiency Margin (AdjEM):** AdjO - AdjD (the overall power rating)

Win probability for any matchup uses a logistic model:

```
P(A beats B) = 1 / (1 + exp(-0.1198 x (AdjEM_A - AdjEM_B)))
```

The constant K = 0.1198 is calibrated so that 1 point of efficiency margin shifts
win probability ~3% from 50%. This is the standard model used by KenPom, BartTorvik,
and most serious college basketball analytics.

Sample outputs: Duke vs Siena (1v16) = 99.1%. A typical 8v9 game = ~50%. A typical
5v12 = ~65-85% depending on the specific teams (not the historical seed average —
the model uses actual team ratings).

### Injury Overrides

Season-long KenPom ratings don't reflect late-breaking injuries. The system includes
an injury override config that adjusts team ratings before any simulation:

- **Duke (1-seed, #1 overall):** Starting PG Caleb Foster broke his foot March 7.
  Center Ngongba questionable with foot soreness. Override: **-1.0 AdjEM**.

- **Alabama (4-seed):** Top 3-point shooter arrested for felony marijuana
  possession March 16, suspended indefinitely. Down to 9 scholarship players.
  Override: **-4.0 AdjEM**. This made 13-seed Hofstra a high-leverage upset pick
  worth 13 points.

- **North Carolina (6-seed):** Best player (likely top-5 NBA pick) out with broken
  thumb, season-ending surgery. Override: **-6.0 AdjEM**. UNC effectively played
  like an 8-9 seed, making 11-seed VCU a strong upset pick.

- **Texas Tech (5-seed):** Star player (21.8 PPG) torn ACL in February. Override:
  **-6.5 AdjEM**.

- **Gonzaga (3-seed):** Star center Braden Huff was
  out for opening weekend but potentially returning for the Sweet 16. The system
  used **conditional ratings**: -4.0 AdjEM for rounds 1-2 and only -1.0 from
  Sweet 16 onward. The model natively handles this through a `get_adj_em(team,
  round_number)` function.

- **Michigan (1-seed):** Key guard L.J. Cason torn ACL. Override: **-3.0 AdjEM**.
  Still had the #1 defense in the country.

These overrides were cross-validated against Vegas lines. The overrides are 2-4
points more aggressive than Vegas for injured teams — intentionally, because under
x Seed scoring, pushing more upset picks is strategically desirable.

### The Expected Value Engine

For every game, instead of asking "who wins?", the system asks "which pick
maximizes expected points?":

```
EV(pick team) = P(team wins) x base_points[round] x seed
```

Example — a 5-seed vs 12-seed at historical base rates:
- `EV(pick 5-seed) = 0.65 x 1 x 5 = 3.25`
- `EV(pick 12-seed) = 0.35 x 1 x 12 = 4.20`

The 12-seed is the better *pick* even though it's the worse *bet*. The seed
multiplier flips the calculus. The system found this pattern in 8v9 games (almost
always pick the 9-seed), 6v11 games, and some 5v12 games.

With team-specific KenPom ratings (not just seed averages), 4 of 28 first-round
matchups had "upset EV" — where the underdog had higher expected value than the
favorite. These were concentrated in 6v11, 7v10, and 8v9 matchups where injury
overrides compressed the probability gap.

### The Backwards-Chaining Bracket Builder

Each bracket starts from a pre-assigned champion and builds backward:

1. **Champion wins the championship game**
2. **Champion wins the Final Four** — opponent is the highest-EV team from the
   paired region
3. **Champion wins the Elite 8** — regional final
4. **Fill the champion's region** — champion wins every game; all other games
   optimized by EV
5. **Fill the other three regions** — pure EV optimization at every node

This guarantees internal consistency — the champion is never picked to lose in
an earlier round.

### The Monte Carlo Simulator (10,000 Tournaments)

This is where it gets interesting. [Monte Carlo simulation](https://en.wikipedia.org/wiki/Monte_Carlo_method)
is a technique where you simulate random outcomes thousands of times to understand
probability distributions that are too complex to calculate directly.

**How it works:**

For each of 10,000 simulated tournaments:
1. Play all 63 games, with each outcome decided by a weighted coin flip based on
   our win probability model. Duke beats Siena in ~9,910 of 10,000 sims. A 5v12
   game might split 6,500/3,500.
2. Score every one of our brackets against that simulated outcome using the x Seed
   scoring formula.
3. Record the champion, the scores, everything.

After 10,000 runs, we have a full probability distribution for each bracket: mean
score, median, 10th percentile (bad luck), 90th percentile (good luck). This runs
in ~1.8 seconds on a laptop — pure Python with numpy for random number generation.

**Championship probability calibration:**

The simulator's championship frequencies were compared against Vegas odds as a
sanity check:

| Team       | Simulator | Vegas  |
|------------|-----------|--------|
| Duke       | 23.8%     | ~22%   |
| Arizona    | 22.4%     | ~19%   |
| Michigan   | 13.3%     | ~20%   |
| Houston    | 6.8%      | ~9%    |
| Iowa State | 6.3%      | ~4.5%  |
| UConn      | 1.6%      | ~5.6%  |

Most numbers are in the right ballpark, which validates the model. Where they
diverge is informative — Michigan is lower than Vegas (13.3% vs 20%), suggesting
the injury override might be too harsh. UConn is way low, likely because our
aggressive injury overrides reshaped the East region.

**The big discovery:**

We built two Duke-champion brackets — one picking favorites everywhere ("chalk"),
one using pure EV optimization (which favors upsets because of the seed multiplier):

- **Chalk Duke: mean 224.4 points**
- **EV Duke: mean 215.6 points**

The "smarter" EV bracket scored *worse* by 8.7 points. Why? The EV engine
correctly identifies that a 9-seed in Round 2 is worth 9 x 2 = 18 points while
a 1-seed is worth 1 x 2 = 2 points. So at even modest upset probabilities, the
9-seed has higher single-game EV. But the 9-seed almost never *actually wins*
Round 2. When you pick the 9-seed and they lose, you also lose credit for them
in every subsequent round. The 1-seed keeps winning round after round, earning
compounding points — the **cascading correctness** of chalk picks outweighs
the per-game EV advantage of upset picks.

The EV math is correct for each game in isolation. But bracket scoring isn't
isolated — your Round 3 pick only scores if your Round 2 pick was right.

This led to the **3-tier pick strategy:**
- **Round 1:** Use EV optimization (upsets are isolated, low base points, no cascade)
- **Round 2+, safe brackets:** Pick by win probability ("chalk") — cascading
  correctness wins
- **Round 2+, contrarian brackets:** Use EV optimization — lower expected score
  but much higher ceiling (90th percentile up to 294 pts vs ~260 for chalk)

Without the simulator, I would have submitted 10 pure-EV brackets and left ~9
points per bracket on the table for the safe ones.

---

## The Portfolio: 10 Brackets, One Strategy

### Design Philosophy

With 10 brackets, the system can cover significantly more of the outcome space
than a single bracket. The goal isn't to have every bracket independently win —
it's to maximize the probability that **at least one bracket finishes in the
top 3**.

Expert brackets were collected from ESPN (60-analyst poll), CBS Sports, Fox,
SI, and Vegas odds. This identified:
- **Consensus upset picks** locked into all 10 brackets
- **High-disagreement games** where picks are varied across brackets
- **Pool popularity data** to measure differentiation from the field

### The 10 Brackets

**2 Chalk / 4 Value / 3 Contrarian / 1 Swing**

| #  | Champion   | Seed | Region  | Tier        | Path Value | Rationale |
|----|------------|------|---------|-------------|------------|-----------|
| 1  | Duke       | 1    | East    | Chalk       | 63 pts     | #1 overall seed, insurance if chalk holds |
| 2  | Arizona    | 1    | West    | Chalk       | 63 pts     | Healthiest 1-seed, elite two-way profile |
| 3  | Houston    | 2    | South   | Value       | 126 pts    | Best 2-seed by odds, elite defense, home court for Sweet 16 |
| 4  | UConn      | 2    | East    | Value       | 126 pts    | Must beat weakened Duke, Dan Hurley's pedigree, 2x multiplier |
| 5  | Iowa State | 2    | Midwest | Value       | 126 pts    | Biggest beneficiary of Michigan + Alabama injuries |
| 6  | Gonzaga    | 3    | West    | Value       | 189 pts    | The "Trojan Horse" — if Huff returns for Sweet 16, different team. 3x multiplier |
| 7  | Illinois   | 3    | South   | Contrarian  | 189 pts    | +1900 odds, manageable South path, 3x multiplier |
| 8  | Kansas     | 4    | East    | Contrarian  | 252 pts    | Peterson healthy, Duke weakened, 4x multiplier, Kansas pedigree |
| 9  | Purdue     | 2    | West    | Contrarian  | 126 pts    | Big Ten Tournament winners, hot team, West diversification |
| 10 | Michigan   | 1    | Midwest | Swing       | 63 pts     | #1 defense, maximum upset picks elsewhere for differentiation |

**Regional distribution:** East 3, West 3, South 2, Midwest 2. No region exceeds
3 brackets, so no single regional upset wipes out more than 30% of the portfolio.

### Locked Picks (All 10 Brackets)

Five upset picks appeared in every bracket — games where expert consensus, EV
analysis, AND injury data all agreed:

1. **South Florida over Louisville (11v6)** — Louisville's star questionable
2. **Akron over Texas Tech (12v5)** — Texas Tech's star had torn ACL
3. **VCU over North Carolina (11v6)** — UNC's best player done for season
4. **Texas over BYU (11v6)** — BYU lost their best shooter
5. **Iowa over Clemson (9v8)** — Clemson's second-leading scorer torn ACL

### Diversification

Six close-call first-round games were rotated across brackets so different brackets
hit different outcomes. Chalk brackets (#1-2) took no extra upsets. Value brackets
(#3-6) rotated 2-3 upset picks each. Contrarian brackets (#7-10) took all
close-call upsets plus aggressive EV-based Round 2+ picks.

The correlation structure: chalk brackets correlated at 0.84-0.98 with each other,
contrarian brackets at 0.76-0.90, and cross-cluster correlation dropped to
0.54-0.68. The contrarian brackets were genuinely exploring different outcome
spaces.

---

## The Technical Stack

~800 lines of Python across 7 modules, plus JSON config files:

```
src/
  data_loader.py        — Team dataclass, loads bracket + ratings + injuries
  win_probability.py    — Logistic model: P(A beats B) from efficiency margins
  ev_engine.py          — Expected value scoring under Points x Seed rules
  bracket_builder.py    — Backwards-chaining bracket construction from champion
  simulator.py          — 10,000-tournament Monte Carlo simulation
  portfolio.py          — 3-tier pick strategy, 10-bracket diversification
  output.py             — CBS-entry bracket display, correlation matrix
config/
  bracket_2026.json     — 68 teams, 4 regions, First Four, Final Four pairings
  team_ratings.json     — KenPom efficiency ratings for all 68 teams
  injury_overrides.json — AdjEM adjustments for 9 injured/suspended players
  portfolio_plan.json   — 10 champion assignments with tier and rationale
```

Dependencies: Python 3.x, numpy, pandas. That's it.

The whole system runs in under 15 seconds: generate 10 brackets, simulate 10,000
tournaments, validate everything, write output files.

---

## Key Design Decisions

1. **Injury overrides as first-class config.** A JSON file where you adjust team
   AdjEM with a note explaining why. Late-breaking injuries (March arrests, broken
   feet, torn ACLs) meaningfully change team ceilings, and season-long stats
   don't reflect them.

2. **EV optimization, not probability optimization.** Every pick maximizes
   expected *points*, not expected *correctness*. These are very different
   objectives under x Seed scoring.

3. **The simulator teaching restraint.** Pure EV was too aggressive in later
   rounds. The 3-tier strategy (EV for Round 1, chalk for later rounds in safe
   brackets, full EV in contrarian brackets) was discovered empirically through
   10,000 simulations, not assumed upfront.

4. **Portfolio thinking over single-bracket thinking.** The system covers the
   outcome space so that many possible tournament results produce a high-scoring
   bracket — with 2-seeds (126 pts), 3-seeds (189 pts), and a 4-seed (252 pts)
   as champions, not just 1-seeds (63 pts).

5. **Human strategy, automated execution.** The human picks which team each
   bracket champions, based on strategic analysis of the scoring system, injury
   landscape, and expert data. The algorithm handles the tedious optimization of
   the other 62 games per bracket.

6. **Gonzaga's conditional rating.** One team had different strength levels
   depending on how deep they went (injured star potentially returning for
   Sweet 16). The model handles this natively with round-dependent efficiency
   ratings rather than forcing a single number.

---

## The Theory

The intended edge comes from three compounding factors:

**Optimizing for the actual scoring system.** The x Seed multiplier makes this
a fundamentally different game than standard bracket pools. Every pick is
optimized for expected *points*, not expected *wins*.

**Incorporating late-breaking information.** Injuries and suspensions that
happened in the final week before the tournament meaningfully changed team
ceilings. The system quantifies these as AdjEM adjustments and feeds them into
the probability model.

**Portfolio diversification.** With 10 brackets covering different champions
across the 1-4 seed range, the system has coverage for many possible tournament
outcomes. If a 2-seed or 3-seed wins it all, a bracket is earning 2-3x the
champion path points. If chalk holds, two 1-seed brackets are in play. The
downside is capped (entry fees); the upside is multiplied.

---

## Tools Used

- **Claude Code** — AI pair programmer for the entire build, from strategy
  analysis through code generation and debugging
- **KenPom** — Team efficiency ratings (scraped via Playwright)
- **Expert brackets** — ESPN 60-analyst poll, CBS Sports, Fox, SI, Vegas odds
- **Python** — numpy for simulation, pandas for data handling
- **~2 evenings of work** — Designed and built in roughly 6-10 hours across two
  evenings before the submission deadline

---

*Built March 2026. System designed and coded with Claude Code (Claude Opus 4.6).*
