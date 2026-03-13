import pandas as pd
import numpy as np
import statsmodels.api as sm
from dataclasses import dataclass
from src.logger import get_logger

_logger = get_logger(__name__)

@dataclass
class FactorRegressionResult:
    ticker: str
    alpha: float
    alpha_tstat: float
    alpha_pvalue: float
    betas: dict[str, float]
    tstats: dict[str, float]
    pvalues: dict[str, float]
    r_squared: float
    r_squared_adj: float
    observations: int
    information_ratio: float
    
def run_regression(
    ticker: str,
    excess_returns: pd.Series,
    factors: pd.DataFrame,
) -> FactorRegressionResult:
    _logger.info(f"[{ticker}] Running OLS regression | obs={len(excess_returns)} factors={factors.columns.tolist()}")
    
    X = sm.add_constant(factors)
    model = sm.OLS(excess_returns, X, missing="drop")
    result = model.fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    
    factor_names = factors.columns.tolist()
    
    alpha = result.params['const']
    betas = {f: result.params[f] for f in factor_names}
    tstats = {f: result.tvalues[f] for f in factor_names}
    pvalues = {f: result.pvalues[f] for f in factor_names}
    
    freq_scale = 252 if len(excess_returns) > 500 else 12
    annualized_alpha = alpha*freq_scale
    tracking_error = result.resid.std()*np.sqrt(freq_scale)
    information_ratio = annualized_alpha / tracking_error if tracking_error > 0 else 0.0
    
    _logger.debug(
        f"[{ticker}] alpha={alpha:.6f} (t={result.tvalues['const']:.2f}, p={result.pvalues['const']:.3f})"
        f"R^2={result.rsquared:.3f} IR={information_ratio:.3f}"
    )
    _logger.debug(f"[{ticker}] betas={betas}")
    
    return FactorRegressionResult(
        ticker=ticker,
        alpha=alpha,
        alpha_tstat=result.tvalues["const"],
        alpha_pvalue=result.pvalues["const"],
        betas=betas,
        tstats=tstats,
        pvalues=pvalues,
        r_squared=result.rsquared,
        r_squared_adj=result.rsquared_adj,
        observations=int(result.nobs),
        information_ratio=information_ratio,
    )
    
def run_regressions(
    excess_returns: pd.DataFrame,
    factors: pd.DataFrame,
) -> dict[str, FactorRegressionResult]:
    tickers = excess_returns.columns.tolist()
    _logger.info(f"Running regressions for {tickers}")
    
    results = {}
    for ticker in tickers:
        try:
            results[ticker] = run_regression(ticker, excess_returns[ticker], factors)
        except Exception as e:
            _logger.error(f"[{ticker}] Regression failed: {e}")
    
    _logger.info(f"Completed {len(results)}/{len(tickers)} regressions")
    return results