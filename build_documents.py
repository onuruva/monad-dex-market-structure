#!/usr/bin/env python3
"""Build the finished application report and one-page summary from verified outputs."""
import json,re,html
from pathlib import Path
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
from pypdf import PdfReader

BASE=Path(__file__).resolve().parent;ROOT=BASE/'repository' if (BASE/'repository').is_dir() else BASE;OUT=ROOT/'results';DEL=BASE/'output' if ROOT!=BASE else ROOT/'deliverables';DEL.mkdir(exist_ok=True)
from matplotlib.font_manager import findfont,FontProperties
for n,family,weight in [('Sans','DejaVu Sans','normal'),('SansBold','DejaVu Sans','bold'),('Serif','DejaVu Serif','normal')]:pdfmetrics.registerFont(TTFont(n,findfont(FontProperties(family=family,weight=weight))))
pdfmetrics.registerFontFamily('Sans',normal='Sans',bold='SansBold',italic='Sans',boldItalic='SansBold')
INK=colors.HexColor('#243047');ACCENT=colors.HexColor('#7155d9');LIGHT=colors.HexColor('#f3f1fa');GRAY=colors.HexColor('#5d6778')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyStudy',fontName='Sans',fontSize=9.3,leading=13.6,textColor=INK,spaceAfter=8))
styles.add(ParagraphStyle(name='SmallStudy',fontName='Sans',fontSize=8.1,leading=11.3,textColor=GRAY,spaceAfter=6))
styles.add(ParagraphStyle(name='TitleStudy',fontName='SansBold',fontSize=24,leading=29,textColor=INK,spaceAfter=10))
styles.add(ParagraphStyle(name='HeadingStudy',fontName='SansBold',fontSize=17,leading=22,textColor=INK,spaceAfter=12))
styles.add(ParagraphStyle(name='SubheadingStudy',fontName='SansBold',fontSize=11.2,leading=15,textColor=INK,spaceBefore=7,spaceAfter=6))
styles.add(ParagraphStyle(name='CellStudy',fontName='Sans',fontSize=8.2,leading=11.2,textColor=INK))
styles.add(ParagraphStyle(name='CardStudy',fontName='SansBold',fontSize=16,leading=22,textColor=ACCENT,spaceAfter=4))
styles.add(ParagraphStyle(name='SummaryBody',fontName='Sans',fontSize=9.4,leading=13.6,textColor=INK,spaceAfter=8))

def J(name):return json.loads((OUT/name).read_text())
Q=J('data_quality.json');M=J('market_structure.json');V=J('valuation_coverage.json');E=J('ecosystem_context.json');O=J('origin_activity_summary.json');L=J('liquidity_event_coverage.json');T=J('order_flow_tests.json');VALID=J('final_input_validation.json')
S=pd.read_csv(OUT/'valuation_sensitivity.csv');P=pd.read_csv(OUT/'pool_activity.csv');F=J('ecosystem_family_context.json')
fmt=lambda x:f'{x:,.0f}';pct=lambda x:f'{100*x:.2f}%';million=lambda x:f'${x/1e6:,.2f}m'
scope="For this application, I present a focused seven-day study of Monad DEX activity, covering 3-9 October 2026 UTC. I concentrate the event-level analysis on Uniswap v4, which accounted for <b>64.72% of the same week's DEX-category volume</b> in the frozen DefiLlama dataset. This produces a manageable research sample for review while retaining substantive data-engineering and quantitative work."
purpose="The aim is to demonstrate a reproducible workflow for extracting blockchain data, resolving token identities, building analytical datasets, calculating market-structure measures, validating results, and testing a research hypothesis in Python. The report supports a quick first review; the companion code, documented inputs and tables allow a deeper audit. The workflow can be extended to longer windows and additional venues upon request."

def h(text):return ('h',text)
def sub(text):return ('sub',text)
def p(text):return ('p',text)
def small(text):return ('small',text)
def table(rows,widths=None):return ('table',rows,widths)
def fig(name,caption):return ('fig',name,caption)
def box(text):return ('box',text)

pages=[]
pages.append([
 ('title','Monad DEX Market Structure'),p('<b>A seven day study of Uniswap v4</b>'),small('Onur Sener | Quantitative Researcher application sample | 13 October 2026'),
 table([['402,062','267','7,801'],['Pool Swap events','Active v4 pools','Originating accounts']], [159,159,159]),
 sub('Scope and purpose'),p(scope),p(purpose),
 sub('Principal findings'),
 p('<b>Activity is concentrated.</b> The five busiest pools account for '+pct(M['pool_swap_count_concentration']['top5_share'])+' of swaps. The five largest valued pools account for '+pct(V['pool_notional_concentration']['top5_share'])+' of estimated USD-equivalent volume.'),
 p('<b>Account activity is also uneven.</b> Five originating accounts account for '+pct(O['account_swap_concentration']['top5_share'])+' of swaps and '+pct(O['account_valued_volume_concentration']['top5_share'])+' of valued volume. '+fmt(O['active_on_two_or_more_days'])+' accounts appear on multiple days inside the sample.'),
 p('<b>Flow adds modest short-horizon information.</b> Adding signed flow to a recent-return baseline reduces holdout mean squared error by 1.96% at one minute and 0.60% at five minutes. The larger liquidity-interaction model does not consistently improve results.'),
 box('The collected sample supports a specific-week market-structure study and an exploratory forecasting exercise. Results are not estimates of persistent ecosystem-wide behavior or a demonstrated profitable strategy.'),
 small('Read pages 3-7 for findings. Page 2 describes validation; page 8 states limitations and reproduction steps. Full methodology, data definitions and statistical outputs accompany the report.')])

pages.append([
 h('Data and validation'),p('The study uses manager events from chain ID 143 with the fixed UTC filter <b>1790985600 &lt;= block_timestamp &lt; 1791590400</b>. The deployed manager address and event signatures are documented in the companion methodology and SQL.'),
 sub('From raw records to analytical data'),
 p('Historical Initialize events identify pool keys and their token contracts. Signed ABI amounts are decoded and scaled with onchain token decimals. Event order follows block number, transaction index and log index. Exact integers remain in the frozen inputs; floating-point values support aggregation and modeling.'),
 table([['Validation item','Verified outcome'],['Collected manager-event IDs','409,146 unique records'],['Observed Swap events and pool matching','402,062 Swaps; 267 of 267 pools matched'],['Token metadata','154 ERC-20 contracts plus native MON'],['Historical decimal checks','308 of 308 matched'],['Duplicates and tick-price inconsistencies','Zero in the frozen sample'],['Independent raw ABI sample','100 logs; 600 numeric and 200 identity matches'],['Transaction-origin enrichment','301,134 requested transactions; all resolved'],['Canonical swap-origin joins','402,062 matches; zero mismatches'],['Historical sender probe','51 independently obtained transactions matched']], [252,225]),
 p('Canonical sender matches require transaction hash, block hash, block number, transaction index and timestamp to agree. All matched receipts report success. The frozen Swap and other-event IDs reconcile to the 409,146 collected records.'),
 sub('Eligibility flags'),
 p('The sample contains 1,163 hooked swaps, 352 swaps without strictly opposite nonzero amount signs and 251 swaps reporting zero active liquidity. Counts overlap. The source retains these observations; valuation and forecasting apply explicit task-specific filters.'),
 box('These checks establish internal consistency and independently verify selected decoding and sender observations. Exhaustive whole-week capture against a second onchain indexer remains unverified. Aggregate provider-volume agreement is not a completeness test.')])

pages.append([
 h('Pool activity and trade sizes'),p('A small group of pools accounts for most observed executions. The largest MON/USDC pool alone accounts for '+pct(M['pool_swap_count_concentration']['top1_share'])+' of swaps. Activity peaks on 8 October with 84,165 Swap events.'),
 fig('01_pool_activity.png','Figure 1. Pool-level Swap counts and daily activity. One event is one pool execution; routed transactions can generate multiple events.'),
 table([['Measure','Swap-count universe','Valued-volume universe'],['Included pools','267 active pools','189 pools with valued volume'],['Top-five share',pct(M['pool_swap_count_concentration']['top5_share']),pct(V['pool_notional_concentration']['top5_share'])],['HHI on a 0-10,000 scale',f"{M['pool_swap_count_concentration']['hhi_10000']:,.1f}",f"{V['pool_notional_concentration']['hhi_10000']:,.1f}"],['Gini coefficient',f"{M['pool_swap_count_concentration']['gini']:.4f}",f"{V['pool_notional_concentration']['gini']:.4f}"]],[180,145,152]),
 sub('Execution sizes in the direct-quote subset'),
 p('There are 260,751 events with a leg in USDC, USDT0 or AUSD before valuation eligibility filters. In this subset, the median is <b>51.10 quote units</b>, the 90th percentile is 556.38 and the 99th percentile is 2,190.24. These quantities describe pool executions and this subset, rather than total user-order size or all swaps.'),
 p('The dominant pools differ between the count and valued-volume rankings. Event counts alone can give small trades the same weight as large trades; presenting both distributions provides a more informative view of activity.'),
 box('Interpretation: concentrated pool usage is a descriptive finding. It does not by itself show weak competition, manipulation or poor execution quality.')])

pages.append([
 h('Ecosystem context and valuation'),p('The frozen DefiLlama breakdown provides comparable daily aggregates for the same seven UTC dates. Protocols classified as <b>Dexs</b> total '+million(E['dex_category_volume'])+'. Uniswap v4 represents '+pct(E['uniswap_v4_share_dex_category'])+' of that source-defined volume universe.'),
 fig('02_venue_context.png','Figure 2. Provider-reported venue aggregates. Event-level decoding in this study is confined to Uniswap v4; other venue totals provide context.'),
 p('Universe definitions matter: including all provider categories raises the denominator to '+million(E['all_provider_volume'])+' and reduces the v4 share to 55.50%. Grouping protocol versions by provider parent labels puts the Uniswap family at '+pct(F['uniswap_family_share'])+'. These labels do not verify legal ownership.'),
 sub('USD equivalent valuation'),
 p('The primary valuation covers <b>393,605 events, or 97.90%</b>, with an estimated total of <b>'+million(V['total_usd_equivalent_notional'])+'</b>. USDC, USDT0 and AUSD are assumed at $1. Direct quote legs are used where present; otherwise eligible major assets receive chain-ordered v4 reference marks no more than 60 seconds old.'),
 p('One marked leg is counted once; two marked indirect legs are averaged, not summed. Indirect two-leg discrepancies above 5%, hooks and nonstandard signs are excluded. The unvalued 2.10% of events remain missing and are not assigned zero economic volume.'),
 box('The estimate is approximately 1.45% below DefiLlama\'s '+million(159880879)+' v4 aggregate. This is a useful plausibility comparison, with differences in eligibility, prices and counting conventions still unresolved. Stablecoin peg assumptions and reference-age sensitivity are tested on page 7.')])

pages.append([
 h('Originating accounts and repeat activity'),p('All 301,134 distinct Swap transactions have validated sender records. They identify <b>7,801 originating accounts</b>, compared with only 142 distinct Swap-event callers. The distinction matters because routers and intermediaries can execute for many accounts.'),
 fig('04_origin_activity.png','Figure 3. Originating-address activity and accounts observed on earlier days of the same sample. These addresses are not verified individuals.'),
 table([['Measure','Result'],['Top-five originating-account share of swaps',pct(O['account_swap_concentration']['top5_share'])],['Top-five originating-account share of valued volume',pct(O['account_valued_volume_concentration']['top5_share'])],['Swap-count HHI for originating accounts',f"{O['account_swap_concentration']['hhi_10000']:,.1f}"],['Accounts observed on at least two days','1,127'],['Accounts observed on all seven days','178']],[330,147]),
 sub('Within sample recurrence'),
 p('Of 1,454 accounts first observed on 3 October, 492 appear again on a later sample day: 33.84%, with six remaining days of follow-up. Later cohorts have fewer opportunities to reappear. The 9 October cohort has no follow-up and its repeat rate is undefined.'),
 p('First observed means first inside this dataset, not a new user or newly created wallet. Multi-address users, relayers, bundlers, smart-account intermediaries and automated strategies complicate interpretation.'),
 box('The defensible conclusion is uneven originating-account activity and measurable within-week recurrence. The data do not identify long-term retention, beneficial ownership or artificial-volume causation.')])

pages.append([
 h('Observed liquidity and flow testing'),p('The source includes 6,373 ModifyLiquidity events across 133 pools: 2,913 positive changes, 2,551 negative changes and 909 zero-delta calls. Opening positions and the complete initialized-tick distribution have not been reconstructed.'),
 p('Swap events supply post-swap active liquidity. I use a local quote-value slope within the current range as a control, documented in the methodology. It is distinct from TVL, reserves and executable depth over a multi-tick move.'),
 sub('A chronological forecasting exercise'),
 p('The question is whether signed quote-flow imbalance adds information about subsequent last-observed pool-price returns beyond the latest return. Eight pools qualify using only 3-6 October activity. Training uses those dates; testing uses 7-9 October, with overlapping training targets removed. Scaling and cutoffs use training data; missing prices are not filled.'),
 fig('05_forecast.png','Figure 4. Relative holdout MSE reduction. Positive values mean lower prediction error, not positive trading returns. The baseline includes pool intercepts and the most recent return.'),
 table([['Horizon','Train rows','Holdout rows','Flow only','Full model'],*[ [f"{r['horizon_minutes']} min",fmt(r['train_n']),fmt(r['test_n']),f"{100*r['flow_only_oos_r2_vs_autoregression']:+.2f}%",f"{100*r['oos_r2_vs_autoregression']:+.2f}%"] for r in T]],[66,92,100,103,116]),
 p('The full model adds flow, log observed local liquidity and their interaction. At one minute its RMSE is 15.08 basis points versus 15.19 for the baseline. At fifteen minutes it performs worse than the baseline. The flow-only model retains a small positive aggregate improvement at that horizon.'),
 small('Eight selected pools include MON, BTC wrappers, WETH and mUSD against quote anchors. This is not a MON-only test. Targets are last-traded pool prices; no executable strategy or profitability simulation is presented.')])

pages.append([
 h('Robustness and interpretation'),
 fig('03_valuation.png','Figure 5. Largest valued pools and sensitivity to reference-price eligibility. Peg stresses are hypothetical assumptions, not observed independent USD benchmarks.'),
 table([['Valuation setting','Valued events','Estimated volume','Top-five share'],*[ [r['scenario'].replace('Primary 60 seconds','60 sec primary').replace('30 second marks','30 sec marks').replace('120 second marks','120 sec marks'),fmt(r['valued_events']),million(r['usd_equivalent_volume']),f"{r['top5_volume_share_pct']:.2f}%"] for r in S.iloc[:3].to_dict('records')]],[165,101,109,102]),
 p('Changing the age limit from 30 to 120 seconds moves estimated volume from $155.90m to $159.48m and top-five volume concentration from 86.47% to 85.03%. The qualitative concentration finding persists. Simultaneously moving all three assumed anchor prices by +/-1% changes total value proportionally while preserving concentration.'),
 sub('Statistical evidence remains exploratory'),
 p('Four-hour bootstrap blocks jointly resample pools to preserve contemporaneous dependence. There are only 18 holdout blocks. Comparing the full model with the recent-return-plus-liquidity control, loss-reduction intervals are positive at one and five minutes and cross zero at fifteen minutes. Short coverage and overlapping returns limit the strength of inference.'),
 p('The full model does not improve one-minute forecasts for the largest MON/USDC pool. Separately, excluding the largest training-volume pool changes the fifteen-minute full-model result from -0.61% to +0.77%. Shared slopes perform poorly for the low-volatility mUSD pool. The liquidity interaction itself does not consistently improve performance.'),
 box('For Monad: prioritize review of high-activity pools and distinguish event counts, execution volume and originating-account activity. For further research: extend time coverage, test asset-specific or volatility-normalized models, and reconstruct opening liquidity state. These are research priorities rather than causal or trading recommendations.')])

sources=[
 ('1','Primary event and origin snapshots','User-owned Goldsky-to-Neon exports; exact integers, canonical keys and frozen metadata are included.'),
 ('2','Monad official token list','https://github.com/monad-crypto/token-list'),
 ('3','Monad Uniswap deployment registry','https://github.com/monad-crypto/protocols/blob/main/mainnet/uniswap.jsonc'),
 ('4','Uniswap v4 event definitions','https://github.com/Uniswap/v4-core/blob/main/src/interfaces/IPoolManager.sol'),
 ('5','Uniswap v4 pool implementation','https://github.com/Uniswap/v4-core/blob/main/src/libraries/Pool.sol'),
 ('6','Monad RPC documentation','https://docs.monad.xyz/reference/json-rpc/overview'),
 ('7','DefiLlama API documentation','https://api-docs.defillama.com/')]
pages.append([
 h('Limits and reproducibility'),
 p('<b>Time coverage.</b> Seven days support a bounded case study, not persistent behavior across market regimes. Hundreds of thousands of events do not provide the independence of hundreds of thousands of separate experiments.'),
 p('<b>Coverage and identity.</b> Whole-week capture has not been exhaustively reconciled with a second indexer. Other venues have aggregate context only. Originating addresses are not identified people or beneficial owners; repeat observations are censored by the sample window.'),
 p('<b>Prices and liquidity.</b> USD-equivalent values rely on $1 quote-anchor assumptions and same-venue major-asset marks. Independent contemporaneous USD prices are not fully benchmarked. Full TVL and executable depth require additional opening state and tick reconstruction.'),
 p('<b>Prediction.</b> The holdout covers three days, results vary by pool and no profitability after fees, gas or slippage is assessed. A small reduction in forecast error is not an investment return or established trading edge.'),
 sub('Reproduce and review'),
 p('The companion repository contains frozen inputs, Python and SQL, six figures, supporting CSV/JSON tables, exact input checksums and a full methodology. Run <b>python verify_package.py</b> and <b>python run_research.py</b> after installing requirements.txt. Reproduction is offline and does not require Goldsky, Neon credentials or a paid data subscription.'),
 p('The quick-review path is this report and the one-page summary. Detailed review can follow METHODOLOGY.md, DATA_DICTIONARY.md, validation outputs and per-pool holdout tables. Larger derivative tables are regenerated rather than bundled.'),
 sub('Sources and observation window'),
 *[small(f'[{num}] <b>{title}.</b> '+(f'<link href="{url}" color="#7155d9">Open source</link>' if url.startswith('https://') else url)) for num,title,url in sources],
 small('The frozen DefiLlama daily-volume breakdown and its complete endpoint are documented in METHODOLOGY.md. All venue comparisons align to 3-9 October 2026 UTC. Prepared 13 October 2026.'),
 box('Future extension: longer observation windows and additional venue records can be compiled upon request. They are not required to inspect or reproduce this version of the application sample.')])

WIDTH=477
def footer(c,doc):
    c.saveState();w,height=A4;c.setFont('Sans',7.4);c.setFillColor(GRAY);c.drawString(59,30,'Onur Sener | Monad research sample | 3-9 October 2026 UTC');c.drawRightString(w-59,30,str(doc.page));c.restoreState()

def flows(blocks):
    result=[]
    for b in blocks:
        typ=b[0]
        if typ in ['p','small','h','sub','title']:
            style={'p':'BodyStudy','small':'SmallStudy','h':'HeadingStudy','sub':'SubheadingStudy','title':'TitleStudy'}[typ];result.append(Paragraph(b[1],styles[style]))
        elif typ=='table':
            rows=b[1];widths=b[2] or [WIDTH/len(rows[0])]*len(rows[0]);cells=[]
            for i,row in enumerate(rows):cells.append([Paragraph(('<b>'+str(x)+'</b>') if i==0 else str(x),styles['CellStudy']) for x in row])
            tab=Table(cells,colWidths=widths,hAlign='LEFT');tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,0),.4,colors.HexColor('#d7d4e4')),('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#e6e8ed'))]));result.extend([tab,Spacer(1,10)])
        elif typ=='fig':
            path=OUT/'figures'/b[1];w,height=PILImage.open(path).size
            result.extend([Image(str(path),width=WIDTH,height=WIDTH*height/w),Spacer(1,4),Paragraph(b[2],styles['SmallStudy']),Spacer(1,4)])
        elif typ=='box':
            para=Paragraph(b[1],styles['SmallStudy']);tab=Table([[para]],colWidths=[WIDTH]);tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LIGHT),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),8),('LEFTPADDING',(0,0),(-1,-1),11),('RIGHTPADDING',(0,0),(-1,-1),11)]));result.extend([tab,Spacer(1,8)])
    return result

def markdown(blocks):
    out=[]
    def clean(s):
        s=re.sub(r'<link href="([^"]+)"[^>]*>(.*?)</link>',r'[\2](\1)',s);s=s.replace('<b>','**').replace('</b>','**');return html.unescape(s)
    for b in blocks:
        if b[0] in ['p','small','box']:out.append(clean(b[1]))
        elif b[0] in ['title','h','sub']:out.append(('# ' if b[0]=='title' else '## ' if b[0]=='h' else '### ')+clean(b[1]))
        elif b[0]=='table':
            rows=b[1];out.append('\n'.join(['| '+' | '.join(map(str,rows[0]))+' |','|'+'|'.join(['---']*len(rows[0]))+'|']+['| '+' | '.join(map(str,r))+' |' for r in rows[1:]]))
        elif b[0]=='fig':out.append(f'![{b[2]}](results/figures/{b[1]})\n\n{b[2]}')
    return '\n\n'.join(out)

def build():
    report=DEL/'Monad_Research_Report.pdf';doc=SimpleDocTemplate(str(report),pagesize=A4,rightMargin=59,leftMargin=59,topMargin=45,bottomMargin=48,title='Monad DEX Market Structure',author='Onur Sener')
    story=[]
    for i,page in enumerate(pages):
        if i:story.append(PageBreak())
        story+=flows(page)
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    (ROOT/'REPORT.md').write_text('\n\n'.join(markdown(x) for x in pages))
    summary=[('title','Monad DEX Market Structure'),p('<b>Executive summary | Seven day Uniswap v4 study</b>'),small('Onur Sener | Quantitative Researcher application sample | 13 October 2026'),
      p('This application sample examines <b>402,062 Swap events across 267 pools</b> during 3-9 October 2026 UTC. Its central finding is concentrated pool usage and originating-account activity, alongside small, uneven short-horizon forecasting gains from order flow.'),
      table([['72.32%','85.95%','7,801'],['Top-five pool share of swaps','Top-five share of valued volume','Originating accounts']], [159,159,159]),
      sub('Why this scope'),p('I use a focused seven-day sample for a manageable first review. Uniswap v4 accounted for <b>64.72% of provider-reported Monad DEX-category volume</b> during the same week, making it a substantive venue for event-level analysis. The purpose is to demonstrate extraction, dataset construction, Python calculations, validation and quantitative interpretation. The workflow can be extended to longer windows and additional venues upon request.'),
      sub('Findings'),
      p('<b>Market structure.</b> Estimated USD-equivalent pool-execution volume is <b>$157.56m</b>, covering 97.90% of events under documented valuation rules. Top-five volume concentration remains between 85.03% and 86.47% when reference-price age limits vary from 120 to 30 seconds.'),
      p('<b>Originating-account activity.</b> All 301,134 transactions have validated sender records. Five accounts account for 29.82% of swaps and 47.15% of valued volume; 1,127 accounts appear on multiple days. Addresses are not verified people, and repeat observations are not long-term retention.'),
      p('<b>Quantitative testing.</b> A chronological holdout finds 1.96% and 0.60% lower prediction MSE at one and five minutes when flow is added to a recent-return baseline. The liquidity interaction does not consistently help. Gains are small and vary across pools.'),
      sub('Validation and interpretation'),
      p('The frozen sample has no duplicate event keys or unmatched pools. All 155 currencies have resolved metadata; 308 historical decimal checks match. Independent samples validate raw ABI decoding and sender records. Whole-week upstream capture and independent contemporaneous USD pricing are not exhaustively reconciled. Observed liquidity is local active liquidity, rather than full TVL or executable depth.'),
      small('Read the eight-page report for methods, findings and limits. The companion repository supplies documented frozen inputs, Python and SQL, checksums, six figures and supporting tables. Offline reproduction requires no paid data subscription. Forecast-error improvements are not trading returns or proof of profitability.')]
    executive=DEL/'Monad_Executive_Summary.pdf';doc=SimpleDocTemplate(str(executive),pagesize=A4,rightMargin=59,leftMargin=59,topMargin=42,bottomMargin=44,title='Monad DEX Market Structure Executive Summary',author='Onur Sener');doc.build(flows(summary),onFirstPage=footer,onLaterPages=footer)
    (ROOT/'EXECUTIVE_SUMMARY.md').write_text(markdown(summary))
    counts={report.name:len(PdfReader(report).pages),executive.name:len(PdfReader(executive).pages)}
    print(json.dumps(counts))
    assert counts[report.name]==8,counts
    assert counts[executive.name]==1,counts

if __name__=='__main__':build()
