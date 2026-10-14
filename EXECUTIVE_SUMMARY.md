# Monad DEX Market Structure

**Executive summary | Seven day Uniswap v4 study**

Onur Sener | Quantitative Researcher application sample | 13 October 2026

This application sample examines **402,062 Swap events across 267 pools** during 3-9 October 2026 UTC. Its central finding is concentrated pool usage and originating-account activity, alongside small, uneven short-horizon forecasting gains from order flow.

| 72.32% | 85.95% | 7,801 |
|---|---|---|
| Top-five pool share of swaps | Top-five share of valued volume | Originating accounts |

### Why this scope

I use a focused seven-day sample for a manageable first review. Uniswap v4 accounted for **64.72% of provider-reported Monad DEX-category volume** during the same week, making it a substantive venue for event-level analysis. The purpose is to demonstrate extraction, dataset construction, Python calculations, validation and quantitative interpretation. The workflow can be extended to longer windows and additional venues upon request.

### Findings

**Market structure.** Estimated USD-equivalent pool-execution volume is **$157.56m**, covering 97.90% of events under documented valuation rules. Top-five volume concentration remains between 85.03% and 86.47% when reference-price age limits vary from 120 to 30 seconds.

**Originating-account activity.** All 301,134 transactions have validated sender records. Five accounts account for 29.82% of swaps and 47.15% of valued volume; 1,127 accounts appear on multiple days. Addresses are not verified people, and repeat observations are not long-term retention.

**Quantitative testing.** A chronological holdout finds 1.96% and 0.60% lower prediction MSE at one and five minutes when flow is added to a recent-return baseline. The liquidity interaction does not consistently help. Gains are small and vary across pools.

### Validation and interpretation

The frozen sample has no duplicate event keys or unmatched pools. All 155 currencies have resolved metadata; 308 historical decimal checks match. Independent samples validate raw ABI decoding and sender records. Whole-week upstream capture and independent contemporaneous USD pricing are not exhaustively reconciled. Observed liquidity is local active liquidity, rather than full TVL or executable depth.

Read the eight-page report for methods, findings and limits. The companion repository supplies documented frozen inputs, Python and SQL, checksums, six figures and supporting tables. Offline reproduction requires no paid data subscription. Forecast-error improvements are not trading returns or proof of profitability.