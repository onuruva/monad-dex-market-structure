# Methodology and scope

For this application, I present a focused seven-day study of Monad DEX activity, covering 3–9 October 2026 UTC. I concentrate the event-level analysis on Uniswap v4, which accounted for 64.72% of the same week's DEX-category volume in the frozen DefiLlama dataset. This produces a manageable research sample for review while retaining substantive data-engineering and quantitative work.

The aim is to demonstrate a reproducible workflow for extracting blockchain data, resolving token identities, building analytical datasets, calculating market-structure measures, validating results, and testing a research hypothesis in Python. The report is designed for a quick first review; the companion code, documented inputs, and supporting tables allow a deeper audit. The workflow can be extended to longer observation windows and additional venues upon request.

The scope is a descriptive case study of the observed week, with exploratory short-horizon forecasting tests. The venue share is a provider-defined volume measure, not a statement that the event dataset covers every Monad DEX, every transaction, or 64.72% of all ecosystem activity. Uniswap v4 receives complete analysis of its collected manager-event sample; it is not a random sample of all DEXs.

## Observation unit and identities

The event window is `1790985600 <= block_timestamp < 1791590400`, chain ID 143. The manager address is `0x188d586ddcf52439676ca21a244753fa19f9ea8e`. One Swap event is one pool execution. A routed order can generate multiple Swap events; user-order volume and pool-execution volume are different concepts.

The source contains 409,146 manager events, including 402,062 Swaps and 6,373 ModifyLiquidity events. Historical Initialize events supply pool identities; 267 pools have observed Swaps in this week. Contract addresses, rather than names or symbols, identify tokens. Metadata covers 154 ERC-20 contracts plus native MON. Exact raw integers are preserved; decimal-scaled floating-point values are used for aggregate calculations and modeling. Historical decimals at first observed use and the sample end matched in 308 checks.

Swap-event callers are kept separate from transaction senders. The origin snapshot contains all 301,134 requested transaction hashes. A swap-origin match requires transaction hash, block hash, block number, transaction index and timestamp to agree, and receipt success is verified. The matched accounts number 7,801; these are originating addresses, which may be relayers, bundlers, smart-account intermediaries, or automated strategies. They are not verified people or economic owners.

## Validation and coverage

Canonical event-key checks, unique IDs, pool matches and quantity normalization cover the complete frozen sample. A separately decoded seeded sample of 100 raw Swap logs matches all 600 numeric fields and 200 pool/caller identities. Fifty-one independently obtained historical RPC transaction probes also match the full sender snapshot. Frozen Swap and other-event IDs reconcile to all 409,146 collected records.

These checks establish consistency of the collected sample. An exhaustive reconciliation against an independent onchain indexer has not been completed. A bounded attempt to compare selected historical log fragments did not return usable independent data; no successful completeness check is claimed. The comparison with provider volume is an aggregate plausibility check, not proof of feed completeness.

Hooked, non-opposite-sign and zero-active-liquidity records remain in the source and are flagged. Their counts can overlap. A rounded-zero output or boundary state can be legitimate. The valuation and forecasting subsets apply separately documented eligibility rules; flags do not identify manipulation.

## Activity and concentration

Pool, originating-account and venue concentration are calculated separately. HHI is `10000 * sum(share_i ** 2)`. Gini uses the sorted positive activity or valued-volume distribution; missing/unvalued volume is not treated as zero. Pool HHI describes the distribution of observed v4 executions, not competition among firms. Origin-account HHI describes addresses, not beneficial ownership. Venue versions and provider parent families are both shown to illustrate sensitivity to aggregation.

First-observed-account cohorts start at the account's first activity inside this seven-day sample. Accounts can have traded before the sample. Later cohorts have fewer days in which to reappear; the last-day cohort has no follow-up and its repeat rate is undefined. Repeat activity is therefore reported as within-week observation, not long-term retention or evidence of newly acquired users.

## USD-equivalent valuation

USDC, USDT0 and AUSD are quote anchors with an explicit $1 assumption. A direct quote leg is used where present, with token1 taking precedence when both legs are anchors. Otherwise, MON, WBTC, cbBTC and WETH may be marked from eligible v4 reference pools. Reference pools are chosen retrospectively by seven-day direct-quote volume for this descriptive valuation. Indirect marks respect chain order and are at most 60 seconds old. No future indirect observations or unlimited price fills are used.

One available marked leg is counted once; two available indirect marked legs are averaged rather than summed. Indirect executions with a two-leg discrepancy above 5%, hooks or nonstandard signs are excluded. The primary valued subset contains 393,605 events. Missing values remain missing. Reference-age limits of 30 and 120 seconds, discrepancy limits of 2% and 10%, and hypothetical anchor-price shocks are tested. Peg stresses are assumptions, not independently observed stablecoin USD prices. Wrappers can deviate from their underlying assets; same-venue marks are not an independent fair-value benchmark.

## Liquidity

ModifyLiquidity events retain signed changes, tick ranges and position salts. They describe changes during the sample; opening positions and the complete initialized-tick distribution have not been reconstructed. A zero-delta call is not an addition or removal.

Swap events supply post-swap active liquidity L and raw square-root price s. For token0 as base and token1 as quote, the local quote-value slope per unit log-price change is `D = L*s/(2*10**decimals1)`. With token0 as quote it is `D = L/(2*s*10**decimals0)`. This is a local within-range measure. It is not TVL, total reserves or executable depth over a multi-tick move. Liquidity changes between swaps also limit the freshness of last-observed swap state.

## Forecasting design

One-minute bins aggregate direct quote-leg notional and its signed flow. A positive base-token delta represents a base purchase. Order-flow imbalance is `OI = signed_quote_notional / total_quote_notional`. The target is the future last-observed pool-price log return at 1, 5 or 15 minutes, in basis points. Both origin and target need actual trade observations; missing minutes are not filled.

Pool selection uses only 3–6 October activity: at least 1,000 eligible training swaps, ranked by direct quote notional, capped at ten pools. Eight qualify. They include MON, BTC wrappers, WETH and mUSD; this is not a MON-only sample. Forecast eligibility requires a quote anchor, opposite nonzero amount signs, positive observed active liquidity and no hook, and excludes pairs between the selected quote anchors.

Training is 3–6 October; holdout is 7–9 October. Training targets overlapping the boundary are removed. Scaling, liquidity medians and outlier cutoffs use training data. Extreme holdout outcomes remain in the primary evaluation. The baseline includes pool intercepts and the most recent return. Nested models add flow, log local liquidity relative to each pool's training median, and the flow-liquidity interaction. Least squares is implemented with NumPy.

Performance means relative reduction in holdout mean squared error, not a trading return. Four-hour calendar-block bootstraps jointly resample pools to retain contemporaneous dependence; there are only 18 holdout time blocks. Tail trimming, largest-pool exclusion, nested models and per-pool results reveal sensitivity. No executable trading strategy, causal identification, external-price target or profitability after fees, gas and slippage is claimed.

## Sources

- Frozen user-owned Goldsky-to-Neon manager-event and enriched-transaction snapshots, supplied in the companion package.
- Monad official token list: https://github.com/monad-crypto/token-list
- Monad Uniswap deployment registry: https://github.com/monad-crypto/protocols/blob/main/mainnet/uniswap.jsonc
- Uniswap v4 event definitions: https://github.com/Uniswap/v4-core/blob/main/src/interfaces/IPoolManager.sol
- Uniswap v4 pool implementation: https://github.com/Uniswap/v4-core/blob/main/src/libraries/Pool.sol
- Monad RPC documentation: https://docs.monad.xyz/reference/json-rpc/overview
- DefiLlama API documentation: https://api-docs.defillama.com/
- Frozen venue endpoint: https://api.llama.fi/overview/dexs/Monad?excludeTotalDataChart=false&excludeTotalDataChartBreakdown=false&dataType=dailyVolume

Version 1 deliberately uses seven days and one venue's event records. Longer windows and additional DEX events are future extensions, not collected inputs to this report.
