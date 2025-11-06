# Evolution from `getTeamElo.py` to `getTeamEloV2.py`

## Plain-Language Concept (What Elo Is)
Elo is a running strength score for each team. Before a match, the two ratings (plus a home edge) produce expected probabilities for win/draw/loss. After the match:
- If a team does better than expected, it gains points; if worse, it loses points.
- The size of the change (K) controls how fast ratings react. [2010]

In football we adjust classic Elo because:
- Draws are common (need explicit draw probability). [2024]
- Goal margins carry information but shouldn’t explode ratings. [2010, 2024]
- Home advantage is systematic. [2010]
- Recent form should count more than older results. [2024]
- Ratings drift over seasons unless gently regressed toward the league average. [2024]

V2 adds these football-specific refinements in a structured, tunable way so ratings become both more realistic and more predictive.

## High-Level Shift
| Aspect | V1 (`getTeamElo.py`) | V2 (`getTeamEloV2.py`) | Intent |
|-------|----------------------|------------------------|--------|
| Core model | 2-way Elo (draw = 0.5) | Davidson-style 3-way probs (Win/Draw/Loss) | Better draw calibration [2024] |
| K dynamics | Upset + log margin multiplier | Base K × MOV × recency decay | Standard, tunable volatility [2010, 2024] |
| Home advantage | Fixed 35 | Tunable (default 60) | League-level calibration [2010] |
| Season handling | None | Preseason regression to mean | Prevent drift/inflation [2024] |
| Time weighting | None | Exponential recency decay | Emphasize recent form [2024] |
| Draw handling | Implicit | Drawness parameter ν | Control draw frequency [2024] |
| MOV logic | log1p(goal_diff) | World Football Elo MOV with gap damping | Realistic blowout scaling [2010, 2024] |
| Caps / safety | None | MOV cap, half-life, scale | Prevent extremes [2024] |
| Update symmetry | Separate per-team deltas | Single delta, inverse applied | Conserve total rating [2010] |
| Diagnostics | Minimal | Full probs + effective K | Better transparency [2024] |
| Data ingestion | Single aggregate | Robust: merge team CSVs | Pipeline robustness (engineering) |

---

## Deep Dive: Concepts Added in V2

1) 3‑way outcome probabilities (Win/Draw/Loss) with drawness ν [2024]  
- What: Converts rating difference into three probabilities (P(Home), P(Draw), P(Away)) instead of forcing draw = 0.5.  
- How:
  - dr = (R_home + H) − R_away
  - q = 10^(dr / s), r = 10^(−dr / s)
  - mid = ν · sqrt(q · r)
  - P(H) = q / (1 + q + mid), P(D) = mid / (1 + q + mid), P(A) = r / (1 + q + mid)
  - s = SCALE, H = HOME_ADVANTAGE, ν = DRAW_NU
  - For rating updates we use E2 = P(H) + 0.5·P(D).  
- Why: Football’s high draw rate requires explicit tie modeling for calibration.  
- Effect: More realistic probabilities and improved predictive sharpness around even matchups.

2) Margin‑of‑victory (MOV) with rating‑gap damping [2010, 2024]  
- What: Larger wins move ratings more, but the effect shrinks when the stronger team beats a weaker team.  
- How:
  - gd = |goal_diff| (optionally capped)
  - MOV = ln(gd + 1) × [2.2 / (2.2 + 0.001·|dr|)]  
- Why: 4–0 carries more signal than 1–0, but not linearly; mismatches shouldn’t cause huge jumps.  
- Effect: Sensible reaction to margins, controlled volatility in mismatches.

3) Recency decay (exponential time weighting) [2024]  
- What: Older matches count less than recent ones.  
- How:
  - weight = exp(−Δdays / HALF_LIFE_DAYS), multiplied into the effective K.  
- Why: Squads/strength evolve; recency improves responsiveness.  
- Effect: Faster adaptation to current form with smooth memory of history.

4) Preseason regression to league mean [2024]  
- What: At each season boundary, ratings are nudged toward the league average.  
- How:
  - R_team ← (1 − γ)·R_team + γ·LeagueMean, γ = REGRESS_GAMMA.  
- Why: Prevents multi‑season drift/inflation; stabilizes early season predictions.  
- Effect: Keeps the ecosystem centered and reduces early‑season noise.

5) Tunable scale (S) and home advantage (H) [2010]  
- What:
  - SCALE controls steepness from rating difference to probabilities.
  - HOME_ADVANTAGE adds Elo points to home team before computing probs.  
- Why: Leagues differ in parity and home edge; tuning improves calibration.  
- Effect: Better probability calibration and ranking stability per league.

6) Symmetric update with conserved rating mass [2010]  
- What: Apply one delta to home and the opposite to away.  
- How:
  - K_eff = K_BASE × MOV × Recency
  - delta = K_eff × (S_home − E2)
  - R_home += delta, R_away −= delta  
- Why: Clean conservation; avoids inflation/deflation from asymmetric updates.  
- Effect: Stable long‑run ratings; interpretable K.

7) Safety controls and caps (MOV cap, half‑life) [2024]  
- What: Clamp extremes and ensure bounded time influence.  
- Why: Outlier matches (red cards, rotations) shouldn’t dominate history.  
- Effect: Robustness and smoother trajectories.

8) Enhanced diagnostics and outputs [2024]  
- What: Store p_home/p_draw/p_away, pre‑match dr, K_eff, and post‑elos.  
- Why: Enables calibration checks (RPS/log loss), backtests, and transparency.  
- Effect: Easier tuning and stakeholder communication.

9) Flexible data ingestion (engineering)  
- What: Build matches by merging team CSVs by match_id and venue.  
- Why: Works whether you have a single aggregate file or multiple team files.  
- Effect: Less brittle pipeline across leagues.

---

## Technical Changes Summary
- Probability engine: 2‑way expectation replaced by 3‑way probs with drawness; updates use E2 = P(H) + 0.5·P(D). [2024]
- Dynamic K: K_BASE × MOV × recency_weight (no ad‑hoc upset factor). [2010, 2024]
- Season hook: regression to league mean at season boundaries. [2024]
- Update rule: single antisymmetric delta (home +delta, away −delta). [2010]
- Tunables surfaced: SCALE, HOME_ADVANTAGE, DRAW_NU, HALF_LIFE_DAYS, REGRESS_GAMMA, MOV_CAP. [2010, 2024]

## Rationale and Expected Effects
- Explicit draw modeling improves calibration and predictive accuracy in draw‑heavy football. [2024]
- MOV with gap damping captures margin information without explosive jumps. [2010, 2024]
- Recency and preseason regression keep ratings current and prevent drift. [2024]
- Tuned S, H, ν yield better league‑specific calibration; symmetric updates conserve rating mass. [2010, 2024]

## Tuning Priorities
- Per‑league time‑series CV optimizing RPS/log‑loss:
  - HOME_ADVANTAGE (H): 50–80 typical. [2010]
  - SCALE (s): 250–350 common. [2010]
  - DRAW_NU (ν): 1.0–1.6 to match draw rates. [2024]
  - K_BASE: 20–35 depending on desired volatility. [2010]
  - HALF_LIFE_DAYS: 180–540 (faster vs smoother). [2024]
  - REGRESS_GAMMA: 0.1–0.3 for preseason resets. [2024]

## Summary
`getTeamEloV2.py` implements best‑practice upgrades inspired by modern Elo‑in‑football literature: explicit draw modeling, MOV with gap damping, recency decay, preseason regression, and tunable core parameters. The result is a more stable, interpretable, and better‑calibrated rating system with stronger predictive performance. [2010, 2024]

---

## References
- [2010] Lars Magnus Hvattum and Halvard Arntzen. Using ELO ratings for match result prediction in association football. International Journal of Forecasting, 26(3):460–470. DOI: 10.1016/j.ijforecast.2009.10.002. (Provided as project attachment: “Elo In football 2010.pdf”)
- [2024] Elo in Football (2024). (Provided as project attachment: “Elo in football 2024.pdf”)