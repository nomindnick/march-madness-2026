# STRATEGY.md — March Madness 2026: 10-Bracket Portfolio Strategy

## Executive Summary

We are entering 10 brackets in a firm bracket pool (~30-60 participants) with a
**Points × Seed** scoring system that massively rewards correctly predicting
higher-seeded teams advancing deep into the tournament. This scoring system
creates a structural edge for anyone who understands it: a 3-seed champion is
worth 3× a 1-seed champion across every round. Our 10-bracket portfolio is
designed to exploit this with a **2 Chalk / 4 Value Core / 3 Contrarian / 1
Swing** allocation, diversified across all four regions, concentrating on the
2-4 seed range where expected value peaks.

Late-breaking injuries have reshaped the bracket landscape: Duke (1-seed) is
missing its starting PG, Michigan (1-seed) lost a key guard, Alabama (4-seed)
lost its top shooter to suspension, and UNC (6-seed) lost its best player.
Meanwhile, Arizona (1-seed) is fully healthy and Gonzaga (3-seed) may get its
star forward back for the Sweet 16. These injury-adjusted probabilities,
combined with the scoring multiplier, create specific exploitable edges.

**Deadline:** Thursday, March 19, 2026 — before first game tip-off.

---

## 1. Scoring System Analysis

### The Rules

| Round         | Base Points | Bonus     | Formula            |
|---------------|-------------|-----------|---------------------|
| Round of 64   | 1           | × Seed    | 1 × seed value      |
| Round of 32   | 2           | × Seed    | 2 × seed value      |
| Sweet 16      | 4           | × Seed    | 4 × seed value      |
| Elite 8       | 8           | × Seed    | 8 × seed value      |
| Final Four    | 16          | × Seed    | 16 × seed value     |
| Championship  | 32          | × Seed    | 32 × seed value     |

Source: CBS pool settings page (confirmed — the email describing rounds 1-3 as
"points + seed" was incorrect; the actual system uses multiplication throughout).

### What This Means

The scoring is **perfectly linear in seed value.** A team's entire tournament
path is worth exactly `seed × 63` points if they win the championship. This
produces extreme incentives:

| Champion Seed | Full Path Value | vs. 1-Seed |
|---------------|-----------------|------------|
| 1-seed        | 63 pts          | 1.0×       |
| 2-seed        | 126 pts         | 2.0×       |
| 3-seed        | 189 pts         | 3.0×       |
| 4-seed        | 252 pts         | 4.0×       |
| 5-seed        | 315 pts         | 5.0×       |
| 7-seed        | 441 pts         | 7.0×       |
| 11-seed       | 693 pts         | 11.0×      |

**A correct 1-seed pick in Round 1 is worth 1 point.** This is nearly
worthless. Getting 1-seed picks right in early rounds barely matters. The entire
pool will be decided by who correctly identifies which higher-seeded teams make
deep runs.

### Strategic Implications

1. **Champion pick is the single highest-leverage decision.** The championship
   game alone is worth `32 × seed` points. A correct 3-seed champion = 96 pts
   from that one game. A correct 1-seed champion = 32 pts.

2. **Most pool participants will not understand this.** They'll pick 1-seeds to
   win, thinking those are the "safe" picks. Under standard ESPN scoring, that's
   correct. Under this system, it's leaving massive points on the table. If a
   2-seed wins it all, anyone with that pick earns double the championship
   points of everyone who picked a 1-seed.

3. **Early-round upsets have asymmetric value.** Missing a 1-seed Round 1 pick
   costs 1 point. Correctly calling a 12-over-5 upset earns 12 points. The
   expected value calculation often favors picking the upset even at 35%
   probability: `0.35 × 12 = 4.2` vs `0.65 × 5 = 3.25`.

4. **The optimal strategy with 10 brackets is portfolio diversification with a
   heavy tilt toward 2-4 seed champions.** We don't need to be right about
   which specific team wins — we need to have coverage across the most likely
   non-1-seed champions.

---

## 2. The 2026 Bracket

### Regional Structure

| Region   | 1-Seed   | 2-Seed     | 3-Seed        | 4-Seed   |
|----------|----------|------------|---------------|----------|
| East     | Duke     | UConn      | Michigan St.  | Kansas   |
| West     | Arizona  | Purdue     | Gonzaga       | Arkansas |
| Midwest  | Michigan | Iowa State | Virginia      | Alabama  |
| South    | Florida  | Houston    | Illinois      | Nebraska |

### Championship Odds (DraftKings, post-bracket)

| Team          | Seed | Odds     | Implied Prob | Pool Score Value |
|---------------|------|----------|--------------|------------------|
| Duke          | 1    | +325-350 | ~21-22%      | 63 pts           |
| Michigan      | 1    | +350-370 | ~20-21%      | 63 pts           |
| Arizona       | 1    | +380     | ~19-20%      | 63 pts           |
| Florida       | 1    | +700-750 | ~11-12%      | 63 pts           |
| Houston       | 2    | +1000    | ~9%          | 126 pts          |
| UConn         | 2    | +1700    | ~5-6%        | 126 pts          |
| Illinois      | 3    | +1900    | ~5%          | 189 pts          |
| Iowa State    | 2    | +2200    | ~4%          | 126 pts          |
| Michigan St.  | 3    | +2500    | ~4%          | 189 pts          |
| Purdue        | 2    | +3500    | ~3%          | 126 pts          |
| St. John's    | 5    | +5000    | ~2%          | 315 pts          |
| Gonzaga       | 3    | +7500    | ~1.3%        | 189 pts          |
| Virginia      | 3    | +7500    | ~1.3%        | 189 pts          |
| Vanderbilt    | 5    | +7500    | ~1.3%        | 315 pts          |

### Expected Value Under Pool Scoring (Prob × Path Value)

This is the key table. It combines the market's implied championship probability
with the scoring multiplier to identify the best value champion picks:

| Team          | Seed | Approx Prob | Path Value | Expected Value |
|---------------|------|-------------|------------|----------------|
| Duke          | 1    | 22%         | 63         | 13.9           |
| Michigan      | 1    | 20%         | 63         | 12.6           |
| Arizona       | 1    | 19%         | 63         | 12.0           |
| Houston       | 2    | 9%          | 126        | **11.3**       |
| Florida       | 1    | 12%         | 63         | 7.6            |
| UConn         | 2    | 5%          | 126        | **6.3**        |
| Illinois      | 3    | 5%          | 189        | **9.5**        |
| Iowa State    | 2    | 4%          | 126        | **5.0**        |
| Michigan St.  | 3    | 4%          | 189        | **7.6**        |
| Purdue        | 2    | 3%          | 126        | **3.8**        |
| St. John's    | 5    | 2%          | 315        | **6.3**        |
| Gonzaga       | 3    | 1.3%        | 189        | **2.5**        |
| Virginia      | 3    | 1.3%        | 189        | **2.5**        |
| Vanderbilt    | 5    | 1.3%        | 315        | **4.1**        |

**Reading this table:** Duke is still the single most likely champion, so it has
the highest EV. But look at how compressed the range is. Houston at 9% probability
has nearly the same EV as Arizona at 19% — because the scoring doubles its value.
Illinois at just 5% probability has EV comparable to Florida at 12%. Michigan
State at 4% beats Florida's EV.

**The 2-seeds and 3-seeds are where value concentrates.** They're credible
champions (real odds, not lottery tickets) AND the scoring multiplier amplifies
their value substantially. The 1-seeds have EV mostly from raw probability,
not from scoring leverage.

### KenPom Analytics Profile (Pre-Tournament)

The teams with elite two-way efficiency profiles (historically the strongest
predictor of deep runs):

| Team          | KenPom | Adj Off | Adj Def | Profile            |
|---------------|--------|---------|---------|--------------------|
| Duke          | #1     | #4      | #2      | Elite balanced     |
| Michigan      | #2     | #8      | #1      | Defense-first elite|
| Arizona       | #3     | #5      | #3      | Elite balanced     |
| Florida       | #4     | #9      | #6      | Strong balanced    |
| Houston       | #5     | #14     | #5      | Defense-first      |
| UConn         | ~#6    | —       | —       | Balanced           |
| Iowa State    | ~#7    | —       | —       | Balanced           |
| Michigan St.  | ~#9    | —       | —       | Balanced           |
| Illinois      | ~#10   | —       | —       | Offense-first      |
| Gonzaga       | ~#11   | —       | #8      | Defense-first*     |
| Virginia      | ~#13   | —       | —       | Defense-first      |

*Gonzaga's ranking dropped after losing Braden Huff (dislocated kneecap, Jan 15).
With Huff: top-15 offense. Without Huff: dropped to ~#68 offense. If he returns
for the Sweet 16 onward, Gonzaga could be significantly better than their
current ranking suggests. The model should use split ratings.

**Historical filter:** 23 of the last 24 national champions ranked in the top 21
of KenPom adjusted offensive efficiency. This effectively eliminates pure
defense-first teams without strong offenses from serious championship
consideration — which is relevant for teams like Virginia and Tennessee.

---

## 3. Key Injuries and Situational Factors

These are the factors that the probability model alone won't capture and that
the research phase needs to investigate deeply:

### Injuries That Meaningfully Change Team Ceilings

- **Duke — Caleb Foster (broken foot, LIKELY OUT) & Patrick Ngongba II (foot
  soreness, QUESTIONABLE):** The #1 overall seed is missing its starting point
  guard and may be without its starting center. Foster broke his foot March 7
  and won't return unless Duke makes a deep run. Ngongba could suit up for the
  opener against Siena. Duke is still elite but meaningfully weakened — expect
  them to be heavily over-picked by the public. **This makes the East Region a
  goldmine for value picks.**

- **Michigan — L.J. Cason (torn ACL, OUT):** Key guard, team hasn't looked the
  same without him. They went 5-0 after the injury but were blitzed by Purdue
  in the Big Ten Tournament final. Despite being a 1-seed, Michigan is more
  vulnerable than their record suggests. However, they still have the #1
  defense in the country.

- **BYU — Richie Saunders (torn ACL, OUT):** BYU's best shooter and top two-way
  guard is out. BYU went 4-6 after the injury in regular season, but rallied
  with a strong Big 12 Tournament showing. AJ Dybantsa (25.3 PPG, nation's
  leading scorer, likely #1 NBA pick) can carry them, but the supporting cast
  is thin. BYU is a 6-seed, meaning high scoring multiplier if they advance.
  **NOTE: An earlier draft of this document incorrectly attributed Saunders and
  Dybantsa to Arizona. Arizona is fully healthy.**

- **Arizona — HEALTHY.** Despite being a 1-seed, Arizona has no significant
  injuries. Elite two-way efficiency (AdjO #5, AdjD #3), six potential NBA
  players on the roster. Arizona is the strongest 1-seed by health status.

- **Gonzaga — Braden Huff (dislocated kneecap, OUT opening weekend, POSSIBLE
  Sweet 16 return):** Huff has not played since January 15 (9 weeks). Mark Few
  confirmed he is out for the opening weekend but said he is "jogging and
  shooting, and I think that's a real positive sign." If Gonzaga reaches the
  Sweet 16, they'd have a full week off and Huff could potentially return.
  Before his injury, Huff averaged 17.8 PPG shooting 69.7% from inside the arc.
  Gonzaga went 13-2 without him and still won the WCC. **This makes Gonzaga a
  conditional value play: limited ceiling for rounds 1-2, dramatically higher
  ceiling from round 3 onward if Huff returns.** The model should use different
  efficiency ratings for rounds 1-2 vs. rounds 3+.

- **North Carolina — Caleb Wilson (broken thumb, OUT):** Best player and likely
  top-5 NBA pick, season-ending surgery March 5. UNC ranks outside the top 30
  in both offensive and defensive efficiency without him. They're a 6-seed but
  may play like an 8-9 seed. **This significantly boosts 11-seed VCU's path.**

- **Alabama — Aden Holloway (felony marijuana possession, SUSPENDED
  INDEFINITELY):** Confirmed arrested Monday March 16. Top 3-point shooter,
  Alabama is down to 9 scholarship players. This is a severe blow to a 4-seed
  that was already inconsistent. **13-seed Hofstra upset becomes a high-leverage
  play: 13 points for a correct pick, and Hofstra has a real path now.**

- **Kansas — Darryn Peterson (HEALTHY):** Confirmed healthy. Played 37 minutes
  in the Big 12 Tournament and declared himself fully recovered from cramping
  issues. At full strength, Kansas at 4-seed is a credible champion pick with
  252-point path value. His health was the key research question — now answered.

### Situational/Momentum Factors

- **BYU/Dybantsa factor:** AJ Dybantsa is the nation's leading scorer (25.3
  PPG), AP First Team All-American, and likely #1 NBA pick. He broke Kevin
  Durant's freshman Big 12 Tournament scoring record with 93 points in three
  games. But BYU lost Saunders and went under .500 since the injury. High
  variance — could flame out or could go on a star-driven run. As a 6-seed,
  the scoring multiplier is excellent if they advance.

- **Duke's compounding vulnerabilities:** #1 overall seed but missing Foster,
  potentially without Ngongba, AND in the toughest region (UConn 2-seed,
  Michigan State 3-seed, Kansas 4-seed). Duke will be the most popular champion
  pick in the pool. Under × Seed scoring, this means picking Duke has the
  lowest differentiation value — everyone else picked them too, so you don't
  gain separation.

- **Midwest Region is crumbling for the 1-seed:** Michigan lost Cason, Alabama
  lost Holloway. Iowa State (2-seed) is the primary beneficiary — their path
  to the Elite 8 just got significantly easier.

- **Miami (OH) at 31-1:** Undefeated in regular season but lost in MAC
  tournament. Made the field as one of the last four teams in. They play in a
  First Four game. If they win, they're an 11-seed in the Midwest — high
  scoring multiplier, but quality concerns.

- **Florida defending champions:** Defending their title as the 1-seed in the
  South. Path could go through Houston in the Elite 8 (in Houston). A "road
  game" for the defending champs in the regional final.

- **South Region is the weakest:** Florida as 1-seed has the most favorable
  path according to KenPom aggregate difficulty. Houston as the 2-seed is the
  biggest threat but plays effectively at home in the Sweet 16/Elite 8.

---

## 4. Historical Upset Rates

These base rates should inform our probability model and bracket construction:

### First Round Win Rates (Higher Seed), 1985-2025

| Matchup  | Higher Seed Win % | Upset Rate | Expected Upsets/Year |
|----------|-------------------|------------|----------------------|
| 1 vs 16  | 99.3%             | 0.7%       | ~0.03                |
| 2 vs 15  | 94.3%             | 5.7%       | ~0.23                |
| 3 vs 14  | 85.0%             | 15.0%      | ~0.60                |
| 4 vs 13  | 79.3%             | 20.7%      | ~0.83                |
| 5 vs 12  | 64.3%             | 35.7%      | ~1.43                |
| 6 vs 11  | 62.9%             | 37.1%      | ~1.49                |
| 7 vs 10  | 60.7%             | 39.3%      | ~1.57                |
| 8 vs 9   | 49.3%             | 50.7%      | ~2.03                |

### Key Historical Patterns

- **At least one 12-over-5 upset has occurred in 34 of the last 40 tournaments.**
  In the last 15 years, 12-seeds win ~39% of games against 5-seeds.

- **A 2-seed loses in the second round to a 7 or 10 seed about 1.2 times per
  tournament.**

- **A 1-seed has lost in the second round about once every other year.**

- **Annual upset count (using 5+ seed-line difference): average ~8 per
  tournament.** Range: 3 (2007) to 14 (2021, 2022). 2025 had only 4 — the
  lowest in years.

- **14 of the last 18 national champions have been 1-seeds.** But under our
  scoring system, this statistic is less relevant because the scoring penalty
  for missing on a non-1-seed champion is much smaller than the reward for
  hitting one.

- **No 5-seed has ever won the national championship.** Three have reached the
  title game. This is relevant when considering how far to push the seed
  boundary for champion picks.

---

## 5. Portfolio Construction: The 10-Bracket Plan

### Design Philosophy

In a pool of ~30-60 participants, most will submit 1-3 brackets with 1-seed
champions. With 10 brackets, we can cover significantly more of the outcome
space. The goal isn't to have every bracket be independently optimal — it's to
maximize the probability that at least one bracket finishes in the top 3 (70%,
20%, or 10% of the pot).

This means we want:
- **Coverage:** Different champions across brackets so that many outcomes
  produce a high-scoring bracket for us.
- **Correlation management:** Brackets that share a champion should diverge
  elsewhere (different upset picks, different Final Four).
- **Scoring optimization:** Each bracket should maximize expected points under
  the × Seed system, not just pick the most likely winners.
- **Regional diversification:** No more than 3 brackets should require the same
  region's champion to win the title. Since only one team emerges from each
  region, overloading a single region means multiple brackets are guaranteed
  dead by the Final Four.

### The "Runner-Up Paradox"

A critical insight for chalk brackets: under this scoring system, a 1-seed
champion's full path is only 63 points. However, a 3-seed merely *reaching*
the championship game (and losing) earns 93 points from that team's games
alone. A 4-seed reaching the Final Four earns 60 points.

This means: **to win the pool with a 1-seed champion bracket, you MUST also
correctly pick high-seed teams making deep runs elsewhere in that bracket.**
Simply picking all chalk with a 1-seed champion produces a mediocre score.
The chalk brackets must still aggressively advance 4-6 seeds to the Final Four
on the other side of the bracket to separate from the field.

### Final Allocation: 2 Chalk / 4 Value Core / 3 Contrarian / 1 Swing

**Tier 1 — Chalk Insurance (2 brackets)**

| Bracket | Champion | Seed | Region | Path Value |
|---------|----------|------|--------|------------|
| 1       | Duke     | 1    | East   | 63         |
| 2       | Arizona  | 1    | West   | 63         |

- **Duke bracket:** #1 overall seed but weakened (Foster out, Ngongba
  questionable). Still the most likely champion per market odds. Most people
  in the pool will pick Duke, so this bracket only wins if we differentiate
  with aggressive high-seed picks elsewhere (apply Runner-Up Paradox).
- **Arizona bracket:** Healthiest 1-seed, elite two-way profile. Favorable
  West Region draw. Pair with aggressive upset picks from other regions to
  maximize total score.

**Tier 2 — Value Core (4 brackets)**

| Bracket | Champion   | Seed | Region  | Path Value |
|---------|------------|------|---------|------------|
| 3       | Houston    | 2    | South   | 126        |
| 4       | UConn      | 2    | East    | 126        |
| 5       | Iowa State | 2    | Midwest | 126        |
| 6       | Gonzaga    | 3    | West    | 189        |

- **Houston:** Best 2-seed by odds (+1000). Elite defense. Plays second weekend
  effectively at home in Houston. Path through South is favorable.
- **UConn:** Must navigate Duke (weakened) in the East. High risk but 2×
  multiplier makes it worthwhile. Dan Hurley's tournament pedigree is real.
- **Iowa State:** Biggest beneficiary of the Midwest's injury carnage.
  Michigan lost Cason, Alabama lost Holloway. Iowa State's path to the Elite 8
  has opened up dramatically.
- **Gonzaga:** Conditional value play — the "Trojan Horse." Huff out for opening
  weekend but possible Sweet 16 return. If Gonzaga survives rounds 1-2 in
  Portland (favorable venue) and gets Huff back, they become a different team
  for the multiplier rounds. 3× multiplier on the full path. Use different
  efficiency ratings for rounds 1-2 vs. rounds 3+.

**Tier 3 — Contrarian/High-Upside (3 brackets)**

| Bracket | Champion | Seed | Region  | Path Value |
|---------|----------|------|---------|------------|
| 7       | Illinois | 3    | South   | 189        |
| 8       | Kansas   | 4    | East    | 252        |
| 9       | Purdue   | 2    | West    | 126        |

- **Illinois:** Strong 3-seed at +1900 odds. South Region path is manageable.
  Would likely need to beat Houston (or upset Houston's path). 3× multiplier.
- **Kansas:** Peterson is healthy. 4-seed in an East Region where Duke is
  weakened. 4× multiplier = 252-point path. Kansas has the pedigree and now the
  health to make this a legitimate longshot champion pick.
- **Purdue:** Just won the Big Ten Tournament, jumped from 3-seed to 2-seed.
  Hot team with momentum. Provides West Region diversification.

**Tier 4 — Swing/Differentiation (1 bracket)**

| Bracket | Champion | Seed | Region  | Path Value |
|---------|----------|------|---------|------------|
| 10      | TBD      | —    | Midwest | TBD        |

Targets the Midwest for regional balance. Candidates: Michigan (1-seed, 63 pts
— vulnerable but still #1 defense), Virginia (3-seed, 189 pts — defense-first
but deep), or Vanderbilt (5-seed, 315 pts — hot team, beat Florida in SEC
Tournament). Finalize after data collection and First Four results.

### Regional Distribution Check

| Region  | Brackets | Champions                     |
|---------|----------|-------------------------------|
| East    | 3        | Duke (1), UConn (2), Kansas (4)|
| West    | 3        | Arizona (1), Gonzaga (3), Purdue (2)|
| South   | 2        | Houston (2), Illinois (3)      |
| Midwest | 2        | Iowa State (2), TBD swing      |

No region exceeds 3 brackets. Each region has at least 2 brackets. The East
and West have 3 each because they contain the most credible champion candidates
across multiple seeds.

---

## 6. Within-Bracket Optimization Principles

Beyond the champion pick, every game in every bracket should be optimized for
expected points under the × Seed system. Key principles:

### Early Rounds: Pick Upsets Aggressively Where EV Supports It

For any first-round game, the expected value of picking the upset is:

    EV(upset) = P(upset) × (1 × higher_seed)
    EV(chalk) = P(chalk) × (1 × lower_seed)

Example — 12 vs 5 matchup at historical base rate (35.7% upset):

    EV(pick 12) = 0.357 × 12 = 4.28
    EV(pick 5)  = 0.643 × 5  = 3.22

**Picking the 12-seed is higher EV even at base rates.** When the specific
12-seed is strong (e.g., McNeese with 28-5 record, third consecutive
tournament appearance), the EV gap widens further.

This pattern holds for many first-round matchups:
- **8 vs 9:** Almost always pick the 9-seed (9 pts vs 8 pts, near coin flip)
- **6 vs 11:** Favors the 11-seed by EV (11 × 0.371 = 4.08 vs 6 × 0.629 = 3.77)
- **5 vs 12:** Favors the 12-seed by EV (12 × 0.357 = 4.28 vs 5 × 0.643 = 3.22)
- **7 vs 10:** Favors the 7-seed by EV at base rates (7 × 0.607 = 4.25 vs
  10 × 0.393 = 3.93) — this is close but chalk is correct at baseline
- **4 vs 13:** Closer — depends on specific matchup (13 × 0.207 = 2.69 vs
  4 × 0.793 = 3.17 at base rates — chalk wins unless the 13 is strong)
- **3 vs 14:** Favors the 3-seed (3 × 0.85 = 2.55 vs 14 × 0.15 = 2.10)
- **2 vs 15:** Always favors the 2-seed
- **1 vs 16:** Always favors the 1-seed (but only worth 1 pt either way)

### The Cascading Effect: A Myth in Most Cases

A natural concern: if you pick a 12-seed in Round 1 and they lose, don't you
also lose points in Round 2? The answer depends on bracket construction:

**If you don't advance the upset winner:** Your bracket has the 4-seed beating
whoever wins the 5/12 game. The 12-seed's Round 1 pick is an isolated +1.06 EV
gain with zero cascade. Pick the 12-seed.

**If you do advance the upset winner to the Sweet 16:** The cumulative EV still
favors the 12-seed through two rounds. A 12-seed reaching the Sweet 16 earns
12 + 24 = 36 points. A 5-seed reaching the Sweet 16 earns 5 + 10 = 15 points.
Even at lower advancement probability, the math works:
- Cumulative EV of 5-seed to S16: 3.22 (R1) + [10 × 0.35] = 6.72
- Cumulative EV of 12-seed to S16: 4.28 (R1) + [24 × 0.15] = 7.88

**The principle: "Chaos Early, Chalk Late."** The only point where the 5-seed
mathematically overtakes the 12-seed is if you project them to the Elite 8 or
beyond — which is rare for either seed.

**However:** This applies to each bracket independently. Across 10 brackets, we
don't want all of them picking the same upsets. The portfolio should vary which
specific upsets are picked in each bracket.

### Late Rounds: Build Around the Champion

Once the champion is chosen, the bracket should be constructed backward:
1. Champion wins the title game
2. Champion wins the Final Four game (against whom?)
3. Champion wins the Elite 8 (against whom?)
4. Fill in the champion's half of the bracket to be consistent
5. Then optimize the other half independently

This ensures internal consistency — no bracket should have a team winning the
championship if that team was picked to lose in an earlier round (obvious, but
a common automated-generation bug).

### The 8/9 Games: Almost Always Pick the 9-Seed

Under × Seed scoring, the 9-seed is worth 9 pts per correct pick and the 8-seed
is worth 8 pts. Since 8/9 games are essentially coin flips historically (49.3%
for the 8-seed), the 9-seed is always higher EV. The only exception is if the
specific 8-seed is meaningfully stronger per KenPom.

---

## 7. Research Agenda

The probability model and expert analysis need to answer these questions before
bracket generation:

### Must-Answer Before Generating Brackets

1. **What are current KenPom ratings for all 68 teams?** We need adjusted
   offensive and defensive efficiency to estimate game-by-game win probabilities.
   Source: kenpom.com (subscription), or BartTorvik (free alternative).

2. ~~**Gonzaga's Braden Huff — playing or not?**~~ **RESOLVED:** Out for opening
   weekend, possible Sweet 16 return. Mark Few: "jogging and shooting." Model
   should use split ratings — lower AdjEM for rounds 1-2, higher for rounds 3+.

3. ~~**Alabama's Aden Holloway status?**~~ **RESOLVED:** Arrested March 16 for
   felony marijuana possession, suspended indefinitely. Alabama is down to 9
   scholarship players. Severe downgrade.

4. ~~**Kansas's Darryn Peterson health?**~~ **RESOLVED:** Fully healthy. Played
   37 minutes in Big 12 Tournament. Kansas is a credible 4-seed champion pick.

5. **What are the specific first-round point spreads?** These are the market's
   best estimate of game-by-game probabilities and will inform our upset picks.
   **Still needed — gather before bracket generation.**

6. **Duke's injury updates — game-time decisions:** Monitor Ngongba's status
   for the opener. If he sits, Duke's vulnerability increases further.

### Expert Ensemble Collection

Gather complete brackets from at least 5 sources:
- Jay Bilas (ESPN) — published
- CBS Sports model — published  
- Fox Sports experts — published
- Action Network — published
- The Ringer — published
- KenPom-derived bracket (if available)

For each, record: champion pick, Final Four, Elite 8, and any notable upset
picks. Identify consensus picks (most experts agree) and high-disagreement
games (experts split). The high-disagreement games are where we should vary
picks across our 10 brackets.

### Data Sources for Probability Model

- **BartTorvik.com** (free KenPom alternative): Team efficiency ratings,
  game-by-game win probability calculator
- **ESPN BPI** tournament projections: Published win probabilities per team
- **Vegas odds/spreads**: First-round lines provide market-derived probabilities
- **Historical seed-matchup data**: Base rates for upset frequency by round

---

## 8. Bracket Generation Process

### Step 1: Build Win Probability Matrix
For every possible matchup (team A vs team B), estimate P(A wins) using a
combination of KenPom/BartTorvik ratings, injury adjustments, and historical
seed base rates. This produces a 68×68 matrix.

### Step 2: Simulate Tournament Outcomes
Run Monte Carlo simulation (10,000+ iterations) where each game is decided
probabilistically. This produces:
- Championship probability per team
- Final Four probability per team
- Expected points per team under × Seed scoring
- Variance in scoring outcomes

### Step 3: Generate Candidate Brackets
For each champion pick in our portfolio plan, generate a bracket that maximizes
expected points given that champion. The bracket construction works backward
from the champion through each round, picking the highest-EV winner at each
node.

### Step 4: Diversify Across Brackets
Review the 10 brackets as a portfolio. Identify which games have the same pick
across all brackets — these represent correlation risk. For high-uncertainty
games, deliberately vary the picks across brackets.

### Step 5: Human Review and Adjustment
Before submission, review all 10 brackets for:
- Internal consistency (no team winning after being eliminated earlier)
- Reasonable paths (does the narrative make sense, or is it pure noise?)
- Any late-breaking news (injuries, suspensions, etc.)
- Strategic check: Does our portfolio actually cover the most likely outcomes?

---

## 8.5. High-Leverage Tactical Plays

Based on the injury landscape and scoring system, these specific plays should
be evaluated by the model and considered across the portfolio:

### "Cannon Fodder" Optimization

When a team is destined to lose to your champion in a later round, maximize
the scoring value of the *loser*. For example, in a Houston-champion bracket,
if Houston faces the 3/6/11/14 pod winner in the Sweet 16, consider advancing
11-seed VCU (11 × 1 + 11 × 2 = 33 pts) rather than 3-seed Illinois (3 × 1 +
3 × 2 = 9 pts) to lose to Houston. This only works if VCU has a credible path,
which UNC's Wilson injury makes plausible. **The model should discover this
organically through EV optimization, not through hardcoding.**

### Hammer the 13-over-4 in Alabama's Game

With Holloway suspended and Alabama down to 9 scholarship players, 13-seed
Hofstra's upset probability rises meaningfully above the 20.7% base rate. A
correct 13-seed Round 1 pick = 13 points. This should appear in most brackets
where Alabama's game doesn't affect the champion's path.

### Target Weakened 6-Seeds' Opponents

Both 6-seeds with injured stars (BYU without Saunders, UNC without Wilson) face
11-seeds (Texas/NC State and VCU respectively). 11-seeds historically upset
6-seeds 37.1% of the time at base rates. With these specific 6-seeds weakened,
the 11-seed probability rises further — and 11-seed picks earn 11 pts vs 6 pts
for the 6-seed. Feature these across multiple brackets.

---

## 9. Risk Assessment and Blind Spots

### What Could Go Wrong

- **All-chalk tournament:** If all four 1-seeds reach the Final Four (happened
  in 2025), our Tier 2-4 brackets underperform and we're relying on our two
  chalk brackets plus early-round upset picks to compete. Mitigation: the chalk
  brackets still benefit from higher-seed early-round picks.

- **Extreme chaos:** A 7-seed or higher wins it all. We likely don't have that
  specific team as a champion pick. Mitigation: our Tier 3 brackets push to
  4-5 seeds; going further is too low-probability to justify.

- **Model overfit to base rates:** Historical upset rates are averages. This
  year's 12-seeds might be collectively weaker than average. Mitigation: use
  KenPom/spread data to adjust team-specific probabilities, not just seed-based
  base rates.

- **Pool size dynamics:** In a smaller pool (30 people), differentiation matters
  more. If only 2-3 other people submit 10 brackets, our coverage advantage is
  larger. If many people submit max brackets, we need quality over quantity.
  **Research question: estimate pool size from firm participation.**

### Things We Don't Know

- Exact pool size (affects strategy — larger pools favor more contrarian picks)
- How sophisticated other participants are (do they understand the scoring
  system's multiplication, or will they play it like standard ESPN scoring?)
- Individual team motivation, chemistry, and intangible factors
- Game-day shooting variance (the fundamental irreducible uncertainty of March)

---

## 10. Success Criteria

**Primary goal:** At least one bracket finishes in the top 3, winning money.

**Secondary goal:** Demonstrate that systematic AI-assisted bracket construction
meaningfully outperforms naive approaches — a nice parallel to the CASBO
presentation themes about AI as a force multiplier.

**Stretch goal:** Win the pool outright.

---

## Appendix A: Full Bracket Matchups

### East Region
| Seed | Team          | vs Seed | Opponent          |
|------|---------------|---------|-------------------|
| 1    | Duke          | 16      | Siena             |
| 8    | Ohio State    | 9       | TCU               |
| 5    | St. John's    | 12      | Northern Iowa     |
| 4    | Kansas        | 13      | California Baptist|
| 6    | Louisville    | 11      | South Florida     |
| 3    | Michigan State| 14      | North Dakota State|
| 7    | UCLA          | 10      | UCF               |
| 2    | UConn         | 15      | Furman            |

### West Region
| Seed | Team          | vs Seed | Opponent          |
|------|---------------|---------|-------------------|
| 1    | Arizona       | 16      | LIU               |
| 8    | Villanova     | 9       | Utah State        |
| 5    | Wisconsin     | 12      | High Point        |
| 4    | Arkansas      | 13      | Hawaii            |
| 6    | BYU           | 11      | Texas/NC State    |
| 3    | Gonzaga       | 14      | Kennesaw State    |
| 7    | Miami (FL)    | 10      | Missouri          |
| 2    | Purdue        | 15      | Queens (NC)       |

### Midwest Region
| Seed | Team          | vs Seed | Opponent          |
|------|---------------|---------|-------------------|
| 1    | Michigan      | 16      | UMBC/Howard       |
| 8    | Georgia       | 9       | Saint Louis       |
| 5    | Texas Tech    | 12      | Akron             |
| 4    | Alabama       | 13      | Hofstra           |
| 6    | Tennessee     | 11      | Miami (OH)/SMU    |
| 3    | Virginia      | 14      | Wright State      |
| 7    | Kentucky      | 10      | Santa Clara       |
| 2    | Iowa State    | 15      | Tennessee State   |

### South Region
| Seed | Team          | vs Seed | Opponent          |
|------|---------------|---------|-------------------|
| 1    | Florida       | 16      | Prairiew View/Lehigh |
| 8    | Clemson       | 9       | Iowa              |
| 5    | Vanderbilt    | 12      | McNeese           |
| 4    | Nebraska      | 13      | Troy              |
| 6    | North Carolina| 11      | VCU               |
| 3    | Illinois      | 14      | Idaho             |
| 7    | Saint Mary's  | 10      | Texas A&M         |
| 2    | Houston       | 15      | Penn              |

### First Four (Dayton, March 17-18)
- UMBC vs Howard (16-seed, Midwest)
- Texas vs NC State (11-seed, West)
- Prairie View A&M vs Lehigh (16-seed, South)
- Miami (OH) vs SMU (11-seed, Midwest)
