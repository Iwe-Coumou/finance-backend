# Portfolio Management System — TO-DO

## 1. Data & Infrastructure
- [ ] Add `region` column to asset table (underlying asset region, not listing country)
- [ ] Add `region_override` column for manual corrections (ETFs, ADRs)
- [ ] Build asset data cleaner to derive region from country + asset type
- [ ] Investigate OpenFIGI / FMP for more accurate region data

## 2. Factor Model
- [ ] Build `loader.py` — fetch and align asset returns with regional factor returns
- [ ] Build `regression.py` — OLS with Newey-West standard errors
- [ ] Build `service.py` — orchestrate loader + regression with Redis caching
- [ ] Support both single asset and portfolio-level regression

## 3. Portfolio Monitoring
### 3a. Drift Detection
- [ ] Compute current portfolio factor exposure (weighted average of asset betas)
- [ ] Define target factor exposure profiles (static base + optional macro overlay)
- [ ] Compute gap between current and target exposure
- [ ] Flag factors where gap exceeds drift threshold

### 3b. Rebalancing Check
- [ ] Run constrained optimization to find optimal weights with current assets
- [ ] Apply maximum number of transactions constraint to limit costs
- [ ] Compute residual gap after optimal reweighting
- [ ] If residual gap < threshold → recommend rebalance, output target weights + trades
- [ ] Check if transaction costs outweigh the benefit before recommending trades

### 3c. Structural Change — Sell Candidates
If reweighting is insufficient:
- [ ] Compute per-asset factor contribution (weight × beta per factor)
- [ ] Identify assets with high negative contribution across multiple underweight factors
- [ ] Flag assets with insignificant, zero, or negative alpha (not earning enough to justify drift)
- [ ] Identify redundant assets — similar factor loadings but worse alpha/IR than another holding
- [ ] Run "what if removed" test — recheck residual gap after hypothetically removing candidate
- [ ] Tax check — estimate cost of realizing gains vs benefit of closing factor gap, flag if drift tolerance is cheaper

### 3d. Structural Change — Buy Candidates
If portfolio after selling still cannot reach target through reweighting:
- [ ] Translate remaining factor gap into fundamental screening criteria
- [ ] Run screener with criteria + region/exchange constraints to generate candidate universe
- [ ] Fetch and store price/return data for candidates not yet in DB
- [ ] Run factor model on candidates
- [ ] Rank candidates by: gap fill score, alpha significance, information ratio
- [ ] Run "what if added" test — verify candidate closes gap sufficiently before recommending

### 3e. Combined Sell + Buy
- [ ] Profile of sold asset defines criteria for replacement
- [ ] Ensure buy candidate fills the factor gap vacated by sell
- [ ] Verify full portfolio gap closes after hypothetical sell + buy

## 4. Universe & Screening
- [ ] Build FMP screener fetcher
- [ ] Map factor gaps to fundamental screening criteria (HML → low P/B, RMW → high ROE etc.)
- [ ]