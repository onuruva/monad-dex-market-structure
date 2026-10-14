#!/usr/bin/env python3
"""Submission tables: valuation sensitivity, originating accounts, and figures.
Public originating addresses are accounts, not verified people or owners.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analyze import ROOT,OUT,STABLES,concentration,save_json
from enrich_metrics import MAJORS

PURPLE='#7155d9';TEAL='#2f8f83';GRAY='#9ba4b0';INK='#243047'

def valuation_sensitivity():
    cols=['id','pool_id','pair','block_number','transaction_index','log_index','block_timestamp','currency0','currency1','q0','q1','base_address','base_price','stable_quote_address','stable_quote_notional','opposite_signs','has_hook']
    d=pd.read_csv(OUT/'swaps_normalized.csv.gz',usecols=cols)
    d=d.sort_values(['block_number','transaction_index','log_index']).reset_index(drop=True)
    n=len(d);seq=np.arange(n);marks={};refs={}
    for a in MAJORS:
        g=d[(d.base_address==a)&d.stable_quote_notional.notna()&d.opposite_signs&~d.has_hook&(d.base_price>0)]
        if g.empty:continue
        pool=g.groupby('pool_id').stable_quote_notional.sum().idxmax();r=g[g.pool_id==pool]
        pos=np.searchsorted(r.index.to_numpy(),seq,side='right')-1;exists=pos>=0;idx=np.clip(pos,0,len(r)-1)
        marks[a]=(r.base_price.to_numpy()[idx],d.block_timestamp.to_numpy()-r.block_timestamp.to_numpy()[idx],exists,r.stable_quote_address.iloc[0]);refs[a]=pool
    def compute(stale=60,threshold=.05,peg=None):
        peg=peg or {};v=[]
        for side in [0,1]:
            px=np.full(n,np.nan);addresses=d['currency'+str(side)]
            for a,(price,age,exists,quote) in marks.items():
                mask=addresses.eq(a).to_numpy(); valid=exists&(age>=0)&(age<=stale)
                px[mask]=np.where(valid,price*peg.get(quote,1.),np.nan)[mask]
            for a in STABLES:px[addresses.eq(a)]=peg.get(a,1.)
            v.append(abs(d['q'+str(side)].to_numpy())*px)
        v0,v1=v;both=np.isfinite(v0)&np.isfinite(v1);denom=(v0+v1)/2
        discrepancy=np.where(both,abs(v0-v1)/np.maximum(denom,1e-15),np.nan)
        indirect=np.where(both,denom,np.where(np.isfinite(v0),v0,v1));direct=d.stable_quote_notional.notna().to_numpy()
        quote_factor=d.stable_quote_address.map(lambda a:peg.get(a,1.)).to_numpy()
        values=np.where(direct,d.stable_quote_notional.to_numpy()*quote_factor,indirect)
        eligible=d.opposite_signs.to_numpy()&~d.has_hook.to_numpy()&np.isfinite(values)&(values>=0)&(direct|~both|(discrepancy<=threshold))
        pools=pd.Series(values[eligible],index=d.pool_id[eligible]).groupby(level=0).sum()
        c=concentration(pools)
        return {'valued_events':int(eligible.sum()),'event_coverage_pct':100*float(eligible.mean()),'usd_equivalent_volume':float(values[eligible].sum()),'top5_volume_share_pct':100*c['top5_share'],'hhi_10000':c['hhi_10000']}
    rows=[]
    for label,stale,threshold,peg in [('Primary 60 seconds',60,.05,{}),('30 second marks',30,.05,{}),('120 second marks',120,.05,{}),('2 percent leg tolerance',60,.02,{}),('10 percent leg tolerance',60,.10,{}),('All quote anchors minus 1 percent',60,.05,{a:.99 for a in STABLES}),('All quote anchors plus 1 percent',60,.05,{a:1.01 for a in STABLES})]:
        rows.append({'scenario':label,**compute(stale,threshold,peg)})
    for a,label in STABLES.items():rows.append({'scenario':label+' minus 1 percent',**compute(peg={a:.99})})
    s=pd.DataFrame(rows);s.to_csv(OUT/'valuation_sensitivity.csv',index=False)
    base=json.loads((OUT/'valuation_coverage.json').read_text())
    assert rows[0]['valued_events']==base['valued_events']
    assert np.isclose(rows[0]['usd_equivalent_volume'],base['total_usd_equivalent_notional'],rtol=1e-12)
    save_json('valuation_sensitivity_summary.json',{'scenarios':rows,'note':'Peg scenarios are hypothetical stresses, not observed independent USD prices. Reference pools selected retrospectively by seven-day direct-quote volume for descriptive valuation, not used to predict trades.'})
    return s

def origin_activity():
    s=pd.read_csv(ROOT/'swaps.csv.gz',usecols=['id','transaction_hash','block_number','transaction_index','log_index','block_timestamp','pool_id','swap_caller'],dtype={'id':str,'transaction_hash':str,'pool_id':str,'swap_caller':str})
    t=pd.read_csv(ROOT/'transaction_origins.csv.gz',dtype={'transaction_hash':str,'block_hash':str,'tx_from':str,'tx_to':str})
    assert len(t)==301134 and not t.transaction_hash.duplicated().any()
    d=s.merge(t[['transaction_hash','tx_from','tx_to']],on='transaction_hash',how='left',validate='many_to_one');assert d.tx_from.notna().all()
    d['day']=pd.to_datetime(d.block_timestamp,unit='s',utc=True).dt.strftime('%Y-%m-%d')
    v=pd.read_csv(OUT/'trade_valuation.csv.gz',usecols=['id','usd_equivalent_notional','eligible']);d=d.merge(v,on='id',validate='one_to_one')
    d['valued_notional']=d.usd_equivalent_notional.where(d.eligible,np.nan)
    accounts=d.groupby('tx_from').agg(swap_events=('id','size'),transactions=('transaction_hash','nunique'),active_days=('day','nunique'),pools=('pool_id','nunique'),usd_equivalent_notional=('valued_notional',lambda x:x.sum(min_count=1)),first_day=('day','min'),last_day=('day','max')).sort_values('swap_events',ascending=False)
    accounts.to_csv(OUT/'origin_account_activity.csv')
    daily=d.groupby('day').agg(swap_events=('id','size'),transactions=('transaction_hash','nunique'),origin_accounts=('tx_from','nunique'),usd_equivalent_notional=('valued_notional','sum'))
    active={day:set(g.tx_from) for day,g in d.groupby('day')};first=accounts.first_day.value_counts();daily['first_observed_accounts']=daily.index.map(first).fillna(0).astype(int)
    daily['previously_observed_accounts']=daily.origin_accounts-daily.first_observed_accounts
    daily['also_active_previous_day']=[len(active[day]&active.get((pd.Timestamp(day)-pd.Timedelta(days=1)).strftime('%Y-%m-%d'),set())) for day in daily.index]
    daily.to_csv(OUT/'origin_daily_activity.csv')
    cohort=[]
    for day,g in accounts.groupby('first_day'):
        members=set(g.index);later=[k for k in active if k>day];returned=len({a for k in later for a in active[k]}&members)
        cohort.append({'first_observed_day':day,'accounts':len(members),'days_remaining_in_sample':len(later),'observed_again_later':returned,'observed_again_pct':100*returned/len(members) if later else None})
    pd.DataFrame(cohort).to_csv(OUT/'origin_within_week_cohorts.csv',index=False)
    addresses={x['tx_from']:x for x in json.loads((ROOT/'independent_sender_probe.json').read_text())}
    summary={'distinct_originating_accounts':len(accounts),'distinct_transactions':len(t),'swap_events':len(d),'origin_coverage_pct':100.,'active_on_two_or_more_days':int((accounts.active_days>=2).sum()),'active_on_all_seven_days':int((accounts.active_days==7).sum()),'account_swap_concentration':concentration(accounts.swap_events),'account_valued_volume_concentration':concentration(accounts.usd_equivalent_notional.dropna()),'account_transaction_concentration':concentration(accounts.transactions),'cohorts':cohort,'note':'Origin accounts are not verified people or economic owners. First observed means first within this dataset; repeat activity is sample-censored and not long-term retention.'}
    save_json('origin_activity_summary.json',summary)
    assert int(daily.swap_events.sum())==402062 and int(accounts.transactions.sum())==301134
    return accounts,daily,summary

def charts():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':INK,'text.color':INK,'axes.titleweight':'bold','savefig.facecolor':'white'})
    charts_dir=OUT/'figures';charts_dir.mkdir(exist_ok=True)
    p=pd.read_csv(OUT/'pool_activity.csv'); pv=pd.read_csv(OUT/'pool_valued_volume.csv');day=pd.read_csv(OUT/'daily_activity.csv')
    fig,ax=plt.subplots(1,2,figsize=(10.6,3.8));top=p.head(7).iloc[::-1]
    labels=top['pair']+' '+top.pool_id.str.slice(0,8)
    ax[0].barh(labels,100*top.swaps/402062,color=PURPLE);ax[0].set_xlabel('Share of all Swap events (%)');ax[0].set_title('Pool activity concentration',loc='left')
    x=np.arange(len(day));ax[1].bar(x,day.swaps/1000,color=TEAL);ax[1].set_xticks(x,['Oct '+str(i) for i in range(3,10)]);ax[1].set_ylabel('Swap events (thousands)');ax[1].set_title('Activity by UTC day',loc='left');fig.tight_layout();fig.savefig(charts_dir/'01_pool_activity.png',dpi=230);plt.close(fig)
    e=pd.read_csv(OUT/'ecosystem_venue_shares.csv');fig,ax=plt.subplots(figsize=(10.6,3.3));q=e.head(7).iloc[::-1]
    ax.barh(q.protocol,q.reported_usd_volume/1e6,color=[PURPLE if x=='Uniswap V4' else GRAY for x in q.protocol]);ax.set_xlabel('Provider-reported DEX-category volume (USD millions)');ax.set_title('Same-week Monad venue context',loc='left')
    fig.tight_layout();fig.savefig(charts_dir/'02_venue_context.png',dpi=230);plt.close(fig)
    s=pd.read_csv(OUT/'valuation_sensitivity.csv');fig,ax=plt.subplots(1,2,figsize=(10.6,3.3));top=pv.head(6).iloc[::-1]
    ax[0].barh(top.pair+' '+top.pool_id.str[:8],top.usd_equivalent_notional/1e6,color=PURPLE);ax[0].set_xlabel('Estimated USD-equivalent volume (millions)');ax[0].set_title('Largest valued pools',loc='left')
    r=s.iloc[:5];ax[1].barh(['60 sec primary','30 sec marks','120 sec marks','2% leg tolerance','10% leg tolerance'][::-1],r.usd_equivalent_volume.iloc[::-1]/1e6,color=TEAL);ax[1].set_xlabel('Estimated volume (USD millions)');ax[1].set_title('Valuation sensitivity',loc='left');fig.tight_layout();fig.savefig(charts_dir/'03_valuation.png',dpi=230);plt.close(fig)
    a=pd.read_csv(OUT/'origin_account_activity.csv');daily=pd.read_csv(OUT/'origin_daily_activity.csv');fig,ax=plt.subplots(1,2,figsize=(10.6,3.3))
    ranked=a.swap_events.to_numpy();ax[0].plot(np.arange(1,len(ranked)+1),100*np.cumsum(ranked)/ranked.sum(),color=PURPLE,lw=2);ax[0].set_xscale('log');ax[0].set_xlabel('Originating accounts ranked by activity (log scale)');ax[0].set_ylabel('Cumulative share of swaps (%)');ax[0].set_title('Originating-account concentration',loc='left');ax[0].set_ylim(0,102)
    x=np.arange(7);ax[1].bar(x,daily.first_observed_accounts,label='First observed in sample',color=TEAL);ax[1].bar(x,daily.previously_observed_accounts,bottom=daily.first_observed_accounts,label='Observed on an earlier day',color=PURPLE);ax[1].set_xticks(x,['Oct '+str(i) for i in range(3,10)]);ax[1].set_ylabel('Active originating accounts');ax[1].set_title('Within-week repeat activity',loc='left');ax[1].legend(fontsize=8);fig.tight_layout();fig.savefig(charts_dir/'04_origin_activity.png',dpi=230);plt.close(fig)
    tests=json.loads((OUT/'order_flow_tests.json').read_text());fig,ax=plt.subplots(figsize=(10.6,3.2));x=np.arange(3)
    ax.bar(x-.18,[100*r['flow_only_oos_r2_vs_autoregression'] for r in tests],.36,color=TEAL,label='Recent return plus flow');ax.bar(x+.18,[100*r['oos_r2_vs_autoregression'] for r in tests],.36,color=PURPLE,label='Flow plus liquidity and interaction');ax.axhline(0,color=INK,lw=.8);ax.set_xticks(x,['1 minute','5 minutes','15 minutes']);ax.set_ylabel('Holdout MSE reduction (%)');ax.set_title('Small short-horizon gains with uneven pool performance',loc='left');ax.legend(fontsize=9);fig.tight_layout();fig.savefig(charts_dir/'05_forecast.png',dpi=230);plt.close(fig)
    d=pd.read_csv(OUT/'swaps_normalized.csv.gz',usecols=['stable_quote_notional']);v=d.stable_quote_notional.dropna();positive=v[v>0];fig,ax=plt.subplots(figsize=(10.6,3.1));ax.hist(np.log10(positive),bins=60,color=TEAL);ax.axvline(np.log10(v.median()),color=PURPLE,label=f'Median {v.median():.2f} quote units');ax.set_xlabel('Log10 direct quote-leg quantity');ax.set_ylabel('Swap events');ax.set_title('Trade-size distribution in the direct-quote subset',loc='left');ax.legend(fontsize=9);fig.tight_layout();fig.savefig(charts_dir/'06_trade_sizes.png',dpi=230);plt.close(fig)

def main():
    s=valuation_sensitivity();a,d,summary=origin_activity();charts()
    tests=json.loads((OUT/'order_flow_tests.json').read_text())
    table=pd.DataFrame([{'horizon_minutes':r['horizon_minutes'],'training_rows':r['train_n'],'holdout_rows':r['test_n'],'flow_only_mse_reduction_pct':100*r['flow_only_oos_r2_vs_autoregression'],'full_model_mse_reduction_pct':100*r['oos_r2_vs_autoregression'],'baseline_rmse_bps':r['baseline_rmse_bps'],'full_model_rmse_bps':r['rmse_bps'],'without_largest_pool_full_mse_reduction_pct':100*r['exclude_largest_pool_oos_r2_vs_autoregression'],'flow_increment_ci95_lower_bps_squared':r['flow_increment_block_bootstrap']['ci95'][0],'flow_increment_ci95_upper_bps_squared':r['flow_increment_block_bootstrap']['ci95'][1],'holdout_time_blocks':r['flow_increment_block_bootstrap']['blocks']} for r in tests]);table.to_csv(OUT/'forecast_summary.csv',index=False)
    print('Submission metrics complete:',summary['distinct_originating_accounts'],'originating accounts;',len(s),'valuation scenarios',flush=True)

if __name__=='__main__':main()
