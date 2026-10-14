# Monad DEX Market Structure - Report Text

> This is a text version of the final edited report. Figures and original formatting are in [the PDF](deliverables/Monad_Research_Report.pdf) and [Word document](deliverables/Monad_Research_Report.docx).

**A seven day study of Uniswap v4**

Onur Sener \| Monad Quantitative Researcher application sample \| 13
October 2026

| **402,062**      | **267**         | **7,801**                |
|------------------|-----------------|--------------------------|
| Pool Swap events | Active v4 pools | Trading wallet addresses |

## Scope and purpose

For this application, I present a deliberately focused seven-day study
of Monad DEX activity, covering the 3-9 October 2026 UTC period. The
study evaluates the quality and concentration of Monad on-chain swap
activity, describes liquidity events, and tests whether signed order
flow adds any short-horizon information beyond recent returns.  
  
I concentrated the event-level analysis on Uniswap v4, which accounted
for **64.72% of the same week's DEX-category volume** in the frozen
DefiLlama dataset. This produces a manageable research sample for
review, while demanding substantive data-engineering and quantitative
work.

The objective is to demonstrate a reproducible workflow for  
1. extracting blockchain data with ABI decoding,

2\. resolving token identities,

3\. building structured datasets,

4\. calculating market-structure metrics,

5\. validating results,

6\. and statistical-testing a research hypothesis using Python, SQL,
pandas, NumPy.

This report provides a quick first review. You can find the supporting
Python/SQL codes, CSV and JSON files, and a detailed methodology under
the GitHub repository, **whose link is provided in the Monad
Quantitative Researcher job application materials, as the answer to the
“What experience do you have in HFT or blockchain/crypto space?”
question.**  
  
The workflow can be extended to longer windows and additional venues
upon request.

## Principal findings

**Activity is concentrated:** The five busiest pools account for 72.32%
of Monad-chain swaps and 85.95% of estimated USD-equivalent volume.

**Wallet address activity is also uneven:** Five trading-wallet
addresses account for 29.82% of the swap count and 47.15% of volume.
1,127 addresses appear on multiple days inside the sample.

**Order flow analysis provides a small improvement in short-term price
predictions:** My price-prediction model predicts future price changes
using recent price movements and pool-specific adjustments.  
  
I then added buying and selling pressure data to see whether predictions
improved, by calculating the Mean Squared Error (MSE) for each model.
MSE is the average of the squared differences between predicted and
actual price changes.

Error reduction (%) = \[(Baseline MSE − New Model MSE) / Baseline MSE\]
× 100

Adding this buying and selling pressure data to my price-prediction
model reduced forecasting errors by 1.96% for one-minute predictions and
0.60% for five-minute predictions. However, including additional
liquidity measurements beyond 5-minutes did not consistently improve the
model's accuracy.

The collected sample uses a specific week’s market-structure and
performs an exploratory forecasting exercise. Results are by no means an
estimate for persistent ecosystem-wide behavior or demonstrated
profitable strategy.

Read pages 3-7 for findings. Page 2 describes validation, page 8 states
limitations and reproduction steps. Full methodology, data definitions,
and statistical outputs accompany the report.

# Data and validation

The study uses events from chain ID 143 (Monad mainnet's unique Chain
ID) with the fixed UTC filter **1790985600 \<= block_timestamp \<
1791590400**. The manager address and event signatures are documented in
the detailed methodology document.

## From raw records to analytical datasets

I used historical pool-creation records (“Initialize” events) to
identify each liquidity pool and the tokens traded in it.  
  
Following that, I decoded the raw transaction data and converted token
amounts into their actual values using each token's decimal settings.  
  
I arranged all events in chronological order using their block numbers,
transaction positions, and event positions. I preserved the original
numerical data in its exact form, while using decimal-based calculations
for statistical analysis and modeling.  
  
**Data lineage**

<table>
<colgroup>
<col style="width: 39%" />
<col style="width: 60%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>Stage</strong></th>
<th><strong>Observed/reproduced operation</strong></th>
</tr>
<tr class="odd">
<th>Collection</th>
<th><strong>Goldsky-sourced Monad Uniswap v4 logs in Neon</strong>;
frozen 7-day export saved in the accompanying reproducibility
archive.</th>
</tr>
<tr class="header">
<th>Interpretation</th>
<th>Decode Swap and ModifyLiquidity ABI fields;<br />
match Pool IDs to Initialize histories;<br />
attach token contracts and decimal scales.</th>
</tr>
<tr class="odd">
<th>Quality checks</th>
<th>Validate event/transaction-log uniqueness, pool joins, token scale
checks.</th>
</tr>
<tr class="header">
<th>Measurement</th>
<th>Build descriptive event/pool/volume tables, observe local liquidity
metrics and one-minute signed-flow figures.</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

| **Validation item**                       | **Verified outcome**                           |
|-------------------------------------------|------------------------------------------------|
| Collected manager-event IDs               | 409,146 unique records                         |
| Observed swap events and pool matching    | 402,062 Swaps; 267 of 267 pools matched        |
| Token metadata                            | 154 ERC-20 contracts plus native MON           |
| Historical decimal checks                 | 308 of 308 matched                             |
| Duplicates and tick-price inconsistencies | Zero in the frozen sample                      |
| Independent raw ABI sample                | 100 logs; 600 numeric and 200 identity matches |
| Transaction-origin requests               | 301,134 requested transactions; all resolved   |
| Verified swap-origins                     | 402,062 matches; zero mismatches               |
| Historical sender probe                   | 51 independently obtained transactions matched |

We verified each blockchain address by checking that its transaction
details matched the original blockchain records, including transaction
IDs, block details, and timestamps.  
  
All verified transactions were successful. We also confirmed that our
saved swap and other event records matched the 409,146 events collected
in total.

## Data quality checks - swap data filters

The 7-day sample data contains 1,163 “hooked” swaps, 352 swaps without
matching opposite-amount signs, and 251 swaps reporting zero active
liquidity. The source retains these observations but excludes them from
trading-volume calculations and forecasting estimates.

# Pool activity and trade sizes

A small group of pools accounts for the highest number of executions.
The largest MON/USDC pool alone accounts for 32.64% of swaps. Activity
peaks on 8 October with 84,165 Swap events.

<img src="media/image1.png" style="width:7.59896in;height:2.72185in" />

Figure 1. Pool-level Swap counts and daily activity. Counts are decoded
Swap events, not users or completed wallet-level trades.

| **Leading pool**        | **Swap events** | **Share of all events** |
|-------------------------|-----------------|-------------------------|
| MON / USDC (0x18a9fc…)  | 131,215         | 32.64%                  |
| MON / WETH (0x3783b5…)  | 61,852          | 15.38%                  |
| MON / WBTC (0x1c93dd…)  | 46,820          | 11.65%                  |
| USDC / WETH (0xad4089…) | 31,438          | 7.82%                   |
| AUSD / USDC (0xd112fd…) | 19,461          | 4.84%                   |

| **Measure**                                          | **Swap-count universe** | **Transaction-volume universe** |
|------------------------------------------------------|-------------------------|---------------------------------|
| Included pools                                       | 267 active pools        | 189 pools with high volume      |
| Top-five share                                       | 72.32%                  | 85.95%                          |
| Herfindahl–Hirschman Index (HHI) on a 0-10,000 scale | 1,595.8                 | 2,107.8                         |
| Gini coefficient                                     | 0.9666                  | 0.9744                          |

## Median trade size in the subset

Out of the 402,062 swaps analyzed, 260,751 involved USDC, USDT0, and
AUSD stablecoins as one of the trading pairs. Among these stablecoin
swaps, the median trade size was 51.10 units. The largest 10% exceeded
556.38 units, while the largest 1% exceeded 2,190.24 units. These
figures represent individual executions within liquidity pools, not
necessarily the full size of a trader's order.

The pools with the most trades are not necessarily the ones with the
highest trading volumes. This is because a pool that processes many
small trades can have more transactions but less total volume, than a
pool processing fewer but larger trades. Therefore, examining both the
number of trades and their total value gives us a clearer picture of
trading activity.  
**Interpretation: Highly concentrated pool usage does not by itself show
weak competition, manipulation, or poor execution quality.**

# Ecosystem composition

The chart below shows each Monad DEX-venue’s total processed volume
throughout the seven-day period. Uniswap v4 represents **64.72%** of the
entire Monad DEX volume.  
<img src="media/image3.png" style="width:5.69444in;height:3.41667in" />

Figure 2. Provider-reported venue aggregates. Event-level decoding in
this study is confined to Uniswap v4; other venue totals provide
context. Source: DefiLlama

| **Item**                               | **Seven-day figure**       |
|----------------------------------------|----------------------------|
| Uniswap v4 eligible swap estimate      | \$157.56m USD-equivalent   |
| Eligible swap coverage                 | 393,605 / 402,062 = 97.90% |
| DefiLlama-reported Uniswap v4 volume   | \$159.88m                  |
| DefiLlama-reported Monad Dexs category | \$247.03m                  |
| Uniswap v4 share of that category      | 64.72%                     |

## Estimating trading volume in US dollars

I calculated the trading volume in US dollars for the eligible 393,605
swaps (97.90% of all swaps). Together, these trades were worth an
estimated \$157.56 million.  
  
I assumed that USDC, USDT0, and AUSD are worth exactly \$1, so for swaps
involving these stablecoins, I directly used their exact amounts. For
other major tokens, I used prices recorded on Uniswap v4 within the
previous 60 seconds, always using prices from before the swap.  
  
When calculating trading volume, I counted each swap only once.  
  
For example, if someone swapped \$100 worth of MON for \$100 worth of
USDC, I counted it as a \$100 trade, not \$200. When I could calculate
the dollar value of both tokens, I used the average of the two values.  
  
If the two estimated values differed by more than 5%, I excluded that
swap from the volume calculation because the price estimate might be
unreliable. I also excluded swaps using special contract features
("hooks") or showing unusual token movements.

For the remaining 2.10% of swaps, I couldn't calculate a reliable dollar
value. I kept these transactions in our dataset but excluded them from
our estimated trading volume.

My \$157.56 million Uniswap v4 estimate is 1.45% below DefiLlama's
reported \$159.88 million for the same week. That difference may come
from how trades are priced and counted. Later in this report, I test how
our results change when we use different **price limits and stablecoin
assumptions**.

# Trading wallets and repeat trading

I matched all 301,134 unique swap transactions with the addresses that
originally sent them, which were only 7,801 distinct wallet addresses.  
  
The Swap events themselves showed only 142 different caller addresses.
**This is because routers and other services can place trades on behalf
of many wallets.**

<img src="media/image2.png" style="width:7.57813in;height:2.35332in" />

Figure 3. How trading activity is spread across wallet addresses, and
how many wallets traded again during the seven-day period. A wallet
address does not necessarily represent one single person.

| **Measure**                                               | **Result** |
|-----------------------------------------------------------|------------|
| Share of swaps from five most active blockchain addresses | 29.82%     |
| Share of volume from five highest-volume addresses        | 47.15%     |
| Address concentration score (HHI)                         | 304.7      |
| Addresses active on two or more days                      | 1,127      |
| Addresses active on all seven days                        | 178        |

## How often did wallet addresses trade again?

Of the 1,454 addresses we first saw on October 3rd, 492 traded again on
a later day (33.84%). I could track these addresses for six more days.
Addresses first seen later had less time to return. I could not measure
repeat activity for wallets first seen on October 9 as the study ends
that day.  
  
"First seen" means the first time we recorded a wallet address during
this seven-day study. It does not mean the wallet was newly created or
had never traded before. One person may control multiple wallets, and
bots or trading services may also be involved.

The results show that a small number of accounts were responsible for a
large share of trading, while some accounts traded on multiple days. We
cannot tell who owns these addresses, whether they kept trading after
the study, or whether any of the volume was artificial.

# Liquidity changes and orderflow pressure

I found 6,373 liquidity-change events across 133 pools. Of these, 2,913
added liquidity, 2,551 removed liquidity, and 909 recorded no net
liquidity change. I did not reconstruct how much liquidity existed at
the start of the week or how liquidity was spread across all price
levels.  
  
Each swap event records the liquidity left in its pool immediately after
the trade. I used that figure to estimate how much more trading the pool
could absorb right around its current price. The formula is in the
METHODOLOGY.md file in the GitHub research package.

## Can order flows help predict short-term price changes?

I wanted to know if buying and selling activity helps predict a pool's
price over the next 1, 5, or 15 minutes.

1.  I first used recent prices alone.

2.  Then I added buying/selling pressure.

3.  Finally, I also added **pool liquidity** to see if the same buying
    pressure moves prices more, in pools with less liquidity.

I trained the models on October 3–6 and tested them on October 7–9 using
eight pools.

<img src="media/image4.png" style="width:7.74362in;height:2.34332in" />

Figure 4. How much each model lowered prediction error compared to
forecasts using recent prices alone. Positive = better; negative =
worse. These figures are NOT trading profits.

| **Minutes ahead** | **Examples for training** | **Examples for testing** | **With buying/selling data** | **With buying/selling and liquidity data** |
|-------------------|---------------------------|--------------------------|------------------------------|--------------------------------------------|
| 1 min             | 8,296                     | 7,634                    | +1.96%                       | +1.50%                                     |
| 5 min             | 7,781                     | 7,193                    | +0.60%                       | +0.60%                                     |
| 15 min            | 7,680                     | 7,171                    | +0.20%                       | -0.61%                                     |

The basic model uses recent prices and allows for differences between
pools. Adding buying and selling pressure improved its forecasts
slightly. Adding pool liquidity too means checking whether the pool has
enough liquidity near its current price to absorb trades, and whether
that changes how strongly buying or selling moves the price.  
  
At one minute, buying/selling data lowered mean squared prediction error
(MSE) by 1.96% compared to the basic model. Adding liquidity too lowered
it by 1.50%. At five minutes, both versions improved MSE by 0.60%. At
fifteen minutes, the combined model was 0.61% worse than the basic
model.  
  
In short, buying/selling pressure helped a little, but the liquidity
data did not consistently improve predictions.

The eight pools included MON, Bitcoin-linked tokens, WETH, and mUSD
traded against selected stablecoins. These results measure how well the
models predicted later pool prices. I did not test real trading
strategies or calculate profits after trading costs.

## How does order flow pressure behave under different liquidity levels?

I divided trading into three groups:

1.  strong buying (more than 75% buying),

2.  strong selling (more than 75% selling),

3.  balanced trading (neither side above 75%).

I also grouped the liquidity near each pool’s current price into low,
medium, and high levels, using only the October 3–6 training data to set
the boundaries.

I then checked the average price change over the following 1, 5 and 15
minutes on October 7–9. The results below show what happened for each
combination. A positive number means the price rose on average while a
negative number means it fell.

| **Liquidity** | **Buy/sell activity** | **1 minute** | **5 minutes** | **15 minutes** | **1-min samples** |
|---------------|-----------------------|--------------|---------------|----------------|-------------------|
| Low           | Strong selling        | -3.72 bps    | -5.38 bps     | -7.63 bps      | 2,526             |
| Low           | Balanced              | -1.25 bps    | -0.59 bps     | +0.06 bps      | 1,344             |
| Low           | Strong buying         | +3.20 bps    | +1.95 bps     | -1.41 bps      | 2,230             |
| Medium        | Strong selling        | -2.70 bps    | -9.58 bps     | -14.03 bps     | 157               |
| Medium        | Balanced              | -3.74 bps    | -17.65 bps    | -56.35 bps     | 42                |
| Medium        | Strong buying         | +0.98 bps    | -2.13 bps     | -7.33 bps      | 198               |
| High          | Strong selling        | -2.70 bps    | -6.11 bps     | -11.48 bps     | 548               |
| High          | Balanced              | -0.97 bps    | -3.46 bps     | -11.28 bps     | 120               |
| High          | Strong buying         | +1.84 bps    | +1.20 bps     | -4.03 bps      | 469               |

**Example:** With low liquidity, strong buying was followed by an
average 1-minute rise of 3.20 basis points, while strong selling was
followed by a fall of 3.72 basis points. (One basis point = 0.01%.)

**Important:** This does not prove that low liquidity caused a larger
price move. About 80% of the test observations fell in the low-liquidity
group, and several pools had too few observations in other groups for a
fair comparison. The results are preliminary, not a tested trading
strategy.

**The last column on the table above shows the number of observations
for the 1-minute test whereas the 5- and 15-minute tests have slightly
different counts.** Full counts, results by pool, and the Python test
are included in NINE_GROUP_METHODOLOGY.md and results/regime_tests/ in
the GitHub research package.

# Checking the reliability of results

<img src="media/image5.png" style="width:7.55729in;height:2.34857in" />

Figure 5. Pools with the highest trading volume, and how our totals
change when we allow newer or older token prices. The stablecoin price
changes are hypothetical tests, not observed market moves.

| **Price age limit** | **Swaps valued** | **Estimated volume** | **Share of top five pools** |
|---------------------|------------------|----------------------|-----------------------------|
| 60 sec (main)       | 393,605          | \$157.56m            | 85.95%                      |
| 30 sec              | 388,606          | \$155.90m            | 86.47%                      |
| 120 sec             | 396,980          | \$159.48m            | 85.03%                      |

I wanted to see whether using newer or older token prices would
significantly change my trading-volume estimates.

When I used token prices recorded within the previous 30 seconds, the
estimated trading volume was \$155.90 million, with the five largest
pools accounting for 86.47% of it.

When I allowed prices from up to 120 seconds earlier, the estimated
volume increased to \$159.48 million, while the five largest pools
accounted for 85.03%.

Both calculations showed the same general result: Most trading volume
was concentrated in just a few pools.

## How reliable are our price predictions?

I wanted to check whether the small improvements in price predictions
were consistent across different pools, or whether the results depended
on which pools we tested.

I repeated the statistical checks using 18 four-hour blocks from our
three-day testing period. This is a small sample, so the findings are
preliminary.

**The table below compares the detailed model (recent prices, buy/sell
pressure and nearby liquidity) with the basic model (recent price
changes, with an adjustment for each pool).**

| **Pools included**    | **1 minute** | **5 minutes** | **15 minutes** |
|-----------------------|--------------|---------------|----------------|
| All eight pools       | +1.50%       | +0.60%        | −0.61%         |
| Busiest MON/USDC pool | −0.12%       | +0.19%        | −1.37%         |
| Without busiest pool  | +3.57%       | +1.18%        | +0.77%         |

A positive percentage means that the detailed model made more accurate
predictions, while a negative percentage means it performed worse. These
are changes in mean squared prediction error, not trading profits.

The busiest MON/USDC pool showed weaker results at one and fifteen
minutes. The model also struggled with the relatively stable USDC/mUSD
pool. Our separate statistical tests found that the fifteen-minute
improvements were particularly uncertain.

Overall, buying/selling pressure offered a small improvement, but adding
liquidity did not consistently help. The results changed considerably
depending on which pools we included.

For Monad, it is useful to track the busiest pools and compare swap
counts, total dollar volume, and wallet addresses separately. Future
research could cover more trading days, test models for specific tokens,
and rebuild the pools' full liquidity data. These are research
suggestions, not proven causes or trading recommendations.

# Limitations and how to reproduce the study

**Time period:** We studied only seven days. Trading behavior may change
over weeks, months and under different market conditions. Even with
hundreds of thousands of swaps, we do not have hundreds of thousands of
independent tests.

**Data coverage and wallet identities:** We have not checked every event
against a second blockchain-data provider. For other DEXs, we used
reported total volumes rather than individual trades. One wallet address
may represent a person, bot, or service. The short observation period
also limits what we can say about how often wallets return.

**Prices and liquidity:** We assumed USDC, USDT0, and AUSD were worth
\$1 each. For some other tokens, we used recent prices from Uniswap v4,
without fully checking them against independent USD market prices. More
historical pool data is needed to calculate total value locked (TVL) and
exactly how much could be traded at different prices.

**Price predictions:** We tested the models on just three days of new
data, and accuracy differed across pools. We did not calculate trading
fees, gas costs, slippage or actual profits. A small reduction in
prediction error does not prove a profitable strategy.

## How to check or repeat the research

The GitHub repository includes saved data, Python and SQL code, six
charts, supporting CSV and JSON tables, file checksums to confirm the
inputs have not changed, and a detailed methodology.  
  
To reproduce the analysis, install the Python packages in
**requirements.txt**, then run python **verify_package.py** and python
**run_research.py**. Everything runs offline: no Goldsky account, Neon
access or paid data subscription is needed.

For a quick overview, start with this report.  
  
For more detail, see METHODOLOGY.md, DATA_DICTIONARY.md, the
data-validation results, and the forecast results for each pool. Some
larger tables are created when the code runs.

## Sources and dates covered

\[1\] Main swap and wallet datasets. Exported from the Goldsky-to-Neon
workflow. The package includes the original numerical values, verified
transaction identifiers and saved token information.

\[2\] **Monad official token list.** [Open
source](https://github.com/monad-crypto/token-list)

\[3\] **Monad Uniswap deployment registry.** [Open
source](https://github.com/monad-crypto/protocols/blob/main/mainnet/uniswap.jsonc)

\[4\] **Uniswap v4 event definitions.** [Open
source](https://github.com/Uniswap/v4-core/blob/main/src/interfaces/IPoolManager.sol)

\[5\] **Uniswap v4 pool implementation.** [Open
source](https://github.com/Uniswap/v4-core/blob/main/src/libraries/Pool.sol)

\[6\] **Monad RPC documentation.** [Open
source](https://docs.monad.xyz/reference/json-rpc/overview)

\[7\] **DefiLlama API documentation.** [Open
source](https://api-docs.defillama.com/)

The saved daily DefiLlama volume figures and the full data link are
listed in METHODOLOGY.md. All DEX comparisons cover October 3–9, 2026
(UTC). This report was prepared on October 13, 2026.

The same methods can be used to study longer time periods and additional
DEXs if needed. The data and code already included are enough for
someone else to check and reproduce this report.
