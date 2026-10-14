# Nine-group buying/selling pressure and liquidity study

**Scope:** Exploratory extension of the Monad Uniswap v4 study covering October 3–9, 2026 UTC. Only October 7–9 is used to evaluate results. Eight selected pools. No reconstruction of ±2%, ±5% or ±10% executable depth.

## The two inputs

1. **Buying/selling pressure:** For each one-minute period, `order_flow_imbalance = (buying_notional - selling_notional)/(buying_notional + selling_notional)`. Strong selling: below −0.50 (over 75% selling); balanced: −0.50 through +0.50; strong buying: above +0.50 (over 75% buying).
2. **Liquidity near current price:** The existing `log_depth` measure, derived from liquidity reported immediately after a swap and the local quote-price slope. For each pool, the boundaries for low/medium/high are calculated using the bottom/middle/top third of its **October 3–6 training-period distribution**. No test-period observations are used to select boundaries. This is **local liquidity near the observed price**, not full executable depth or TVL.

Each of the nine combinations is then evaluated against the **realized next 1-, 5-, and 15-minute returns**. Minute observations enter only if original forecasting eligibility permits them, which requires observed prices at origin and future target (without filling empty minutes). Results also include per-group forecast errors for the original baseline and both fitted models.

## One-minute headline result

| Liquidity | Strong selling | Balanced | Strong buying |
| --- | ---: | ---: | ---: |
| Low | -3.72 bps (n=2,526) | -1.25 bps (n=1,344) | +3.20 bps (n=2,230) |
| Medium | -2.70 bps (n=157) | -3.74 bps (n=42) | +0.98 bps (n=198) |
| High | -2.70 bps (n=548) | -0.97 bps (n=120) | +1.84 bps (n=469) |

In the pooled sample, strong buying was followed by a higher average one-minute return than strong selling in each measured liquidity group. The same relative ordering is present at 5 and 15 minutes, **but strong buying does not always predict an absolute positive 15-minute return**. These are *observed conditional averages*, not an executable strategy, controlled causal price impact or statistical proof of differences across liquidity levels.

**Important distribution warning:** Liquidity groups are defined relative to each pool's *training* levels. Of the 7,634 one-minute test observations, 6,100 (79.9%) are low liquidity, 397 (5.2%) medium, and 1,137 (14.9%) high. Many pools contribute to only one group in the three-day test. In particular, the high-liquidity observations are much more concentrated in USDC/cbBTC, while several MON pools appear only at low liquidity. **Direct low-vs-high liquidity causal comparisons are not supported by this test.** The smallest one-minute group has just 42 observations; 18 four-hour resampling blocks make uncertainty material.

Original forecast performance is exactly reproduced: 1-minute flow-only MSE reduction 1.96247%, 5-minute 0.60100%, 15-minute 0.19939%, and full-model changes 1.49989%, 0.59895%, −0.60731% (all relative to the recent-price baseline on the three-day holdout). These are aggregate MSE changes, not gains from trading.

## File guide

- `nine_group_results.csv`: 9 groups × 3 forecast horizons, counts, pool concentration, observed price changes, and within-cell forecasting MSE.
- `nine_group_by_pool.csv`: same analysis by individual pool for comparability and to spot sparse groups.
- `holdout_regime_observations.csv.gz`: the individual eligible minute observations with model predictions, actual prices, and regime labels.
- `liquidity_thresholds_by_pool.csv`: the precise training-only liquidity breakpoints per pool.
- `buy_vs_sell_liquidity_bootstrap.csv`: four-hour block resampling intervals for the strong-buy minus strong-sell *difference* within each liquidity group. Blocks are shared across pools but cannot remove selection bias.
- `model_reproduction_check.csv`: confirms exact reproduction of the original forecast summary.
- `nine_group_price_changes.png`: visual overview of all 27 cells.
- `nine_group_manifest.json`: definitions, sources, and primary caveats.

## Reproduce

Run `python regime_analysis.py` at the repository root **after** running the original `run_research.py`; it reads `results/minute_features.csv.gz` and `results/holdout_predictions.csv.gz`. The script checks its calculated baseline and full-model predictions against the previously frozen holdout predictions, and its aggregate results against `results/forecast_summary.csv`. Nothing in the frozen original data or models is altered.

### Interpretation limits

This research is descriptive and has a short out-of-sample period, highly uneven group sizes, pool-mix differences, and overlapping multi-minute returns. Large differences in group means **do not prove a stable strategy or a liquidity-driven price-impact effect**. An adequate within-pool causal or robust interaction test would need a longer test interval with comparable liquidity regimes for the same pools and additional controls.
