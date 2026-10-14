# Monad DEX Market Structure

**Onur Sener - Quantitative Researcher application sample**  
**Study window: 3-9 October 2026 UTC**

This focused study analyzes 402,062 Uniswap v4 Swap events across 267 pools,
with complete origin enrichment for all 301,134 distinct transactions. It
provides a manageable demonstration of extraction, dataset construction,
Python calculations, validation and quantitative interpretation. Longer
windows and additional venues are future extensions.

## Quick review

1. [Final research report](deliverables/Monad_Research_Report.pdf)
2. [Methodology](METHODOLOGY.md) and [data dictionary](DATA_DICTIONARY.md)
3. [Figures and supporting tables](results/)

Editable research report: [Word document](deliverables/Monad_Research_Report.docx). A [text version](REPORT.md) is provided for browsing on GitHub. 

## Findings

- **Trading is concentrated in a few pools:** The five busiest pools account for 72.32% of swaps and 85.95% of estimated dollar trading volume.
- **Uniswap v4 is the largest venue in this sample:** It represents 64.72% of Monad's DEX-category volume reported by DefiLlama for the same week. This comparison uses DefiLlama's reported venues.
- **Estimated trading volume is $157.56 million:** We calculated a dollar value for 393,605 swaps (97.90% of all recorded Swap events), using the pricing assumptions explained in the report.
- **Trading is concentrated among wallet addresses too:** We identified 7,801 distinct transaction-originating addresses. The five most active account addresses generated 29.82% of swaps; the five highest-volume addresses generated 47.15% of valued volume. Another 1,127 addresses traded on more than one day. Addresses are not necessarily individual people.
- **Buying/selling pressure slightly improves short-term price forecasts:** Adding order-flow data to a model based on recent price movements reduced mean squared prediction error by 1.96% for one-minute forecasts and 0.60% for five-minute forecasts on previously unseen data.
- **We tested nine combinations of order flow and liquidity:** We compared strong buying, strong selling and balanced trading under low, medium and high nearby liquidity. In the low-liquidity group, strong buying was followed by an average one-minute price rise of 3.20 basis points (0.032%); strong selling was followed by a fall of 3.72 basis points (0.0372%). These are observed averages, not guaranteed predictions. The groups had uneven sample sizes, so the results do not prove that lower liquidity caused larger price moves.
- **Adding liquidity data did not consistently help forecasting:** The combined buying/selling-and-liquidity model reduced one-minute prediction error by 1.50% across all eight pools but was 0.61% worse than the basic model at fifteen minutes.
- **Forecasting results depend on which pools are included:** The combined model was 0.12% worse at one minute for the busiest MON/USDC pool, while excluding that pool improved the one-minute result to 3.57%. This makes the results less reliable as a general forecasting method.

**Limitations:** The study covers seven days, with only three days of unseen data for forecasting tests. The findings show preliminary relationships between trading activity, liquidity and subsequent prices; they do not establish a profitable trading strategy.

## Reproduce offline

Tested with Python 3.12.14 and the supplied pinned dependencies. Use Python
3.11 or newer. No Goldsky, Neon, wallet or paid-data access is required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python verify_package.py
python run_research.py
```

The frozen large gzip inputs are distributed as five exact binary parts of
at most 20 MiB each. The first verification automatically assembles them and
checks SHA256. Keep `data_parts/` intact. The workflow then checks event keys,
canonical origins and independent samples and regenerates all analysis,
valuation, forecasting, account/cohort tables, sensitivities and six figures.
Large derivative tables are regenerated and ignored by Git. Allow several GB
of working memory and additional disk space for pandas outputs. Exact source
integer strings are preserved.

To regenerate the report and summary:

```bash
python -m pip install -r requirements_report.txt
python build_documents.py
```

The builder uses matplotlib's bundled DejaVu fonts and writes `deliverables/`.

## Code map

| File | Role |
|---|---|
| materialize_inputs.py | Assemble frozen parts and verify SHA256 |
| verify_package.py and validate_inputs.py | Full event/origin checks and independent ABI/sender samples |
| analyze.py | Normalize quantities, describe activity and run chronological forecasting |
| enrich_metrics.py | Value executions, decode liquidity changes and group provider venue families |
| final_metrics.py | Originating accounts, censored cohorts, sensitivities and final figures |
| run_research.py | Complete credential-free workflow |
| build_documents.py | Report and one-page summary generation |
| 01_token_metadata.sql / 02_module_a_swaps.sql / 03_pool_activity.sql | Versioned metadata and analytical views |

Optional refresh scripts are separate from offline reproduction. `fetch_data.py`
exports an existing Neon sample and does not collect a longer history.
`export_final_inputs.py` freezes completed origin records and ABI examples.
These require the reviewer's externally supplied connection. Public RPC
availability varies; selected checks cannot establish full feed completeness.
The SQL definitions assume existing raw/init source tables and decoding
functions; they document analytical views rather than a new-database bootstrap.
Offline Python reproduction is self-contained.

## Interpretation

Swap events are pool executions, not whole user orders. Callers differ from
transaction origins. Quote anchors are assumed at $1; indirect marks come
from v4. Missing valuations remain missing. All flagged records remain in
the source; flags do not prove manipulation. Observed active liquidity is not
full TVL or multi-tick executable depth. Venue totals are provider context.
Prediction-error reductions are not trading returns. Full qualifications
appear in METHODOLOGY.md and the report.

Cross-DEX leadership, lead-lag, arbitrage-convergence and Module B are excluded.
No longer-window or other-DEX event results are implied.

## GitHub publication

This is a repository-ready distribution; no published URL is claimed. Upload
the contents with subfolders preserved, or push using an authenticated Git
client. Upload `data_parts/` rather than the assembled gzip copies, which
`.gitignore` excludes. Every distributed file is below GitHub's 25 MiB browser
upload limit. See [GitHub's upload documentation](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository).

## Sources and verification

See SOURCE_NOTES.md and full links in METHODOLOGY.md. `data_manifest.json`
records all required input sizes and hashes. Validation and reproduction
receipts are in `results/`.


## Additional nine-group order-flow and liquidity analysis (14 October 2026)

Run `python regime_analysis.py` after `python run_research.py`; inspect `NINE_GROUP_METHODOLOGY.md` and `results/regime_tests/nine_group_results.csv`. This is a supplementary, exploratory analysis of pressure categories crossed with pool-relative liquidity levels; it does not change the original frozen data or forecasting baseline. The split is October 3–6 training / October 7–9 holdout. Groups differ markedly in pool mix and size, so do not interpret differences as causal price impact.

The PDF and DOCX in `deliverables/` reflect the latest human-edited research report, including the nine-group and per-pool reliability tables. Running `build_documents.py` generates the earlier automatically formatted report from the underlying analysis and may overwrite these edited presentation files; keep a copy if doing so.
