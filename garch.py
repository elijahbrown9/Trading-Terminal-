"""Dependency-free GARCH(1,1) fitted by Gaussian maximum likelihood.

Input bars are expected to originate from the broker/MCP snapshot boundary.
No market data is fetched by this module.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import exp, isfinite, log, pi, sqrt
from statistics import fmean
from typing import Iterable, Sequence

TRADING_DAYS = 252


@dataclass(frozen=True)
class GarchResult:
    symbol: str
    observations: int
    omega: float
    alpha: float
    beta: float
    log_likelihood: float
    next_day_expected_move_pct: float
    current_annualized_vol_pct: float
    long_run_annualized_vol_pct: float
    forecast_21d_annualized_vol_pct: float
    storm_ratio: float
    regime: str

    def to_dict(self) -> dict:
        return asdict(self)


def log_returns(closes: Sequence[float]) -> list[float]:
    clean = [float(x) for x in closes if x is not None and float(x) > 0]
    if len(clean) < 31:
        raise ValueError("At least 31 positive closes are required")
    return [log(clean[i] / clean[i - 1]) for i in range(1, len(clean))]


def _variance(values: Sequence[float]) -> float:
    mean = fmean(values)
    return max(1e-12, sum((x - mean) ** 2 for x in values) / len(values))


def _params(raw: Sequence[float]) -> tuple[float, float, float]:
    """Map unconstrained values to omega>0, alpha>=0, beta>=0, alpha+beta<1."""
    omega = exp(max(-30.0, min(5.0, raw[0])))
    ea = exp(max(-15.0, min(15.0, raw[1])))
    eb = exp(max(-15.0, min(15.0, raw[2])))
    denom = 1.0 + ea + eb
    alpha = 0.999 * ea / denom
    beta = 0.999 * eb / denom
    return omega, alpha, beta


def _raw_from_params(omega: float, alpha: float, beta: float) -> list[float]:
    remaining = max(1e-8, 0.999 - alpha - beta)
    return [log(max(omega, 1e-18)), log(max(alpha, 1e-8) / remaining), log(max(beta, 1e-8) / remaining)]


def _filter_variance(returns: Sequence[float], omega: float, alpha: float, beta: float) -> list[float]:
    unconditional = omega / max(1e-8, 1.0 - alpha - beta)
    variances = [max(unconditional, _variance(returns))]
    for i in range(1, len(returns)):
        value = omega + alpha * returns[i - 1] ** 2 + beta * variances[-1]
        variances.append(max(1e-14, value))
    return variances


def _negative_log_likelihood(raw: Sequence[float], returns: Sequence[float]) -> float:
    omega, alpha, beta = _params(raw)
    variances = _filter_variance(returns, omega, alpha, beta)
    value = 0.5 * sum(log(2.0 * pi) + log(h) + (r * r / h) for r, h in zip(returns, variances))
    return value if isfinite(value) else 1e100


def _nelder_mead(fn, start: Sequence[float], max_iter: int = 900, tolerance: float = 1e-9) -> tuple[list[float], float]:
    """Small deterministic Nelder-Mead implementation for three parameters."""
    n = len(start)
    simplex = [list(start)]
    for i in range(n):
        point = list(start)
        point[i] += 0.15 if abs(point[i]) < 1 else abs(point[i]) * 0.08
        simplex.append(point)

    values = [fn(point) for point in simplex]
    for _ in range(max_iter):
        ranked = sorted(zip(values, simplex), key=lambda item: item[0])
        values = [item[0] for item in ranked]
        simplex = [item[1] for item in ranked]
        if max(abs(v - values[0]) for v in values) < tolerance:
            break
        centroid = [sum(simplex[j][i] for j in range(n)) / n for i in range(n)]
        worst = simplex[-1]
        reflected = [centroid[i] + (centroid[i] - worst[i]) for i in range(n)]
        reflected_value = fn(reflected)
        if values[0] <= reflected_value < values[-2]:
            simplex[-1], values[-1] = reflected, reflected_value
            continue
        if reflected_value < values[0]:
            expanded = [centroid[i] + 2.0 * (reflected[i] - centroid[i]) for i in range(n)]
            expanded_value = fn(expanded)
            if expanded_value < reflected_value:
                simplex[-1], values[-1] = expanded, expanded_value
            else:
                simplex[-1], values[-1] = reflected, reflected_value
            continue
        contracted = [centroid[i] + 0.5 * (worst[i] - centroid[i]) for i in range(n)]
        contracted_value = fn(contracted)
        if contracted_value < values[-1]:
            simplex[-1], values[-1] = contracted, contracted_value
            continue
        best = simplex[0]
        simplex = [best] + [[best[i] + 0.5 * (point[i] - best[i]) for i in range(n)] for point in simplex[1:]]
        values = [fn(point) for point in simplex]
    best_index = min(range(len(values)), key=values.__getitem__)
    return simplex[best_index], values[best_index]


def fit_garch(symbol: str, closes: Iterable[float]) -> GarchResult:
    close_list = list(closes)[-501:]
    returns = log_returns(close_list)
    sample_variance = _variance(returns)
    starts = [
        (sample_variance * 0.05, 0.05, 0.90),
        (sample_variance * 0.10, 0.10, 0.80),
        (sample_variance * 0.02, 0.03, 0.95),
    ]
    fitted = []
    for omega, alpha, beta in starts:
        raw, nll = _nelder_mead(lambda x: _negative_log_likelihood(x, returns), _raw_from_params(omega, alpha, beta))
        fitted.append((nll, raw))
    nll, raw = min(fitted, key=lambda item: item[0])
    omega, alpha, beta = _params(raw)
    variances = _filter_variance(returns, omega, alpha, beta)
    next_variance = omega + alpha * returns[-1] ** 2 + beta * variances[-1]
    long_run = omega / (1.0 - alpha - beta)
    persistence = alpha + beta
    forecast_variances = [long_run + (persistence ** horizon) * (next_variance - long_run) for horizon in range(1, 22)]
    forecast_21 = fmean(forecast_variances)
    current_vol = sqrt(next_variance * TRADING_DAYS)
    long_vol = sqrt(long_run * TRADING_DAYS)
    ratio = current_vol / max(long_vol, 1e-12)
    regime = "STORM" if ratio >= 1.25 else "ELEVATED" if ratio >= 1.10 else "NORMAL"
    return GarchResult(
        symbol=symbol.upper(),
        observations=len(returns),
        omega=omega,
        alpha=alpha,
        beta=beta,
        log_likelihood=-nll,
        next_day_expected_move_pct=sqrt(next_variance) * 100,
        current_annualized_vol_pct=current_vol * 100,
        long_run_annualized_vol_pct=long_vol * 100,
        forecast_21d_annualized_vol_pct=sqrt(forecast_21 * TRADING_DAYS) * 100,
        storm_ratio=ratio,
        regime=regime,
    )


def fit_from_bars(symbol: str, bars: Sequence[dict]) -> GarchResult:
    closes = [float(bar["close_price"] if "close_price" in bar else bar["close"]) for bar in bars]
    return fit_garch(symbol, closes)

