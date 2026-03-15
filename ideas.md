# Factor Quality Ranker — Design Notes

## Concept
A cross-sectional ranking model for long-term portfolio construction.
Not predicting raw returns — ranking assets by the quality and reliability
of their factor exposures within a screened universe.

**Core question:** Given 50 candidates with the right factor profile,
which are the most reliable long-term holds?

---

## Target Variable
Risk-adjusted excess return over 63 or 126 days:
```
forward_return = cumulative_return_63d - rf_63d
target = forward_return / rolling_vol_63d
```
Aligns with monthly rebalancing. Rewards consistent outperformance over raw momentum.

---

## Features

### Factor Quality (from factor regression)
- `alpha` — excess return above factor model prediction
- `alpha_tstat` — statistical confidence in alpha
- `ir` — information ratio, consistency of alpha
- `r_squared` — systematic vs idiosyncratic variance
- `rmw_beta` — profitability tilt
- `hml_beta` — value tilt
- `smb_beta` — size tilt
- `alpha_stability` — rolling std of alpha over past 6 months
- `beta_stability` — how much betas drift over time

### Fundamental (from FMP enricher — build first)
- `pb_ratio` — value signal
- `roe` — return on equity, quality signal
- `profit_margin` — profitability
- `debt_to_equity` — financial risk
- `revenue_growth` — business momentum
- `dividend_yield` — income signal

### Momentum / Timing
- `mom_12_1` — 12 month minus 1 month momentum
- `mom_6_1` — 6 month minus 1 month
- `vol_63` — medium term volatility
- `proximity_52w` — price vs 52 week high

### Macro / Regime
- `yield_curve_slope` — 10y minus 2y spread
- `credit_spread` — HY minus IG spread
- `vix_level` — market fear gauge
- `regime` — macro regime classification

---

## Model
LightGBM lambdarank — same structure as existing return ranker but:
- **63 day forward return** target instead of 21 day
- **Group by region + date** — rank within region not globally
- **Quarterly rolling retraining** on expanding window
- **Regime conditioning** via macro features

---

## How It Fits the Pipeline
```
Factor screener
  → candidates matching factor gap criteria

Factor quality ranker
  → ranks candidates by alpha stability + fundamentals + timing

Portfolio builder
  → top N candidates fed into what-if page
```

---

## Differences vs Existing Return Ranker

| | Existing model | This model |
|--|--|--|
| Target | 21d raw return | 63d risk-adjusted excess return |
| Features | Price/momentum only | Factor quality + fundamentals + momentum |
| Ranking scope | Global | Within region |
| Primary signal | Momentum | Factor quality |
| Use case | Short-medium term | Monthly rebalancing |

---

## Prerequisites Before Building
- [ ] 100-200 tickers with history back to 2010
- [ ] FMP fundamental enricher built and populated
- [ ] Historical rolling factor regressions stored (not just current betas)
- [ ] Macro data pipeline (yield curve, VIX, credit spreads)

## Integration Point
`src/screening/ranker.py` — swap in model via `method` parameter:
```python
rank_candidates(candidates, gap, method="composite")  # now
rank_candidates(candidates, gap, method="model")       # later
```