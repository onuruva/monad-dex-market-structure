# Monad DEX Market Structure

**Onur Sener - Quantitative Researcher application sample**  
**Study window: 3-9 October 2026 UTC**

This focused study analyzes 402,062 Uniswap v4 Swap events across 267 pools,
with complete origin enrichment for all 301,134 distinct transactions. It
provides a manageable demonstration of extraction, dataset construction,
Python calculations, validation and quantitative interpretation. Longer
windows and additional venues are future extensions.

## Quick review

1. [One-page executive summary](deliverables/Monad_Executive_Summary.pdf)
2. [Final research report](deliverables/Monad_Research_Report.pdf)
3. [Methodology](METHODOLOGY.md) and [data dictionary](DATA_DICTIONARY.md)
4. [Figures and supporting tables](results/)

Editable research report: [Word document](deliverables/Monad_Research_Report.docx). A [text version](REPORT.md) is provided for browsing on GitHub. The executive-summary text is in [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md).

## Findings

- Top-five pools account for 72.32% of swaps and 85.95% of eligible valued volume.
- Estimated USD-equivalent pool-execution volume is $157.56m; valuation covers 97.90% of events under documented assumptions.
- V4 accounts for 64.72% of same-week provider DEX-category volume, a source-defined universe.
- There are 7,801 originating accounts; 1,127 appear on multiple sample days. These are not verified people or long-term retention measures.
- Adding flow to a recent-return baseline reduces holdout MSE by 1.96% at one minute and 0.60% at five minutes. Gains are small and uneven; the liquidity interaction does not consistently help.

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
