#!/usr/bin/env python3
"""Out-of-sample nine-group order-flow x local-liquidity analysis, Monad v4, 3-9 Oct 2026.
Uses published frozen minute features and holdout predictions. No deeper tick-state or future information.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'results'
OUT=DATA/'regime_tests';OUT.mkdir(exist_ok=True)
SPLIT=pd.Timestamp('2026-10-07',tz='UTC')
HORIZONS=[1,5,15]
P=['Strong selling','Balanced trading','Strong buying']
L=['Low liquidity','Medium liquidity','High liquidity']

f=pd.read_csv(DATA/'minute_features.csv.gz',parse_dates=['time'])
existing=pd.read_csv(DATA/'holdout_predictions.csv.gz',parse_dates=['time'])
# Use only information available before the test period to define pool-relative liquidity regimes.
train_features=f[(f.time<SPLIT)&f.oi.notna()&f.ret_bps.notna()&f.log_depth.notna()].copy()
train_features=train_features[np.isfinite(train_features[['oi','ret_bps','log_depth']].to_numpy()).all(axis=1)]
thresholds=[]
for pid, g in train_features.groupby('pool_id'):
    q1,q2=g.log_depth.quantile([1/3,2/3]).to_numpy()
    if q1>=q2: raise ValueError(f'Non-unique liquidity thirds for {pid}')
    thresholds.append({'pool_id':pid,'pair':g.pair.iloc[0], 'train_observations':len(g),'low_cut_log_depth':float(q1),'high_cut_log_depth':float(q2),'low_cut_relative_depth':float(np.exp(q1)),'high_cut_relative_depth':float(np.exp(q2))})
tdf=pd.DataFrame(thresholds);tdf.to_csv(OUT/'liquidity_thresholds_by_pool.csv',index=False)

features=f.merge(tdf[['pool_id','low_cut_log_depth','high_cut_log_depth']],on='pool_id',validate='many_to_one',how='left')
features['pressure_group']=np.select([features.oi<-.5,features.oi>.5],['Strong selling','Strong buying'],default='Balanced trading')
features['liquidity_group']=np.select([features.log_depth<features.low_cut_log_depth,features.log_depth>features.high_cut_log_depth],['Low liquidity','High liquidity'],default='Medium liquidity')
# Keep only original eligible holdout observations (same training and test membership as published models).
outputs=[];comp=[]
for h in HORIZONS:
    yname=f'future_{h}'
    cols=['oi','ret_bps','log_depth','oi_x_depth']
    complete=f.dropna(subset=cols+[yname]);complete=complete[np.isfinite(complete[cols+[yname]].to_numpy()).all(axis=1)]
    train=complete[complete.time<SPLIT-pd.Timedelta(minutes=h)].copy()
    test=complete[complete.time>=SPLIT].copy()
    pools=sorted(train.pool_id.unique());test=test[test.pool_id.isin(pools)]
    cutoff=train.ret_bps.abs().quantile(.999)
    train=train[(train.ret_bps.abs()<=cutoff)&(train[yname].abs()<=cutoff*np.sqrt(h))]
    means=train[cols].mean();scales=train[cols].std().replace(0,1)
    def design(d,use):
        pool_feats=np.column_stack([(d.pool_id==p).to_numpy(dtype=float) for p in pools]);z=(d[use]-means[use])/scales[use]
        return np.column_stack([pool_feats,z.to_numpy()])
    beta_flow=np.linalg.lstsq(design(train,['ret_bps','oi']),train[yname],rcond=None)[0]
    beta_base=np.linalg.lstsq(design(train,['ret_bps']),train[yname],rcond=None)[0]
    beta_full=np.linalg.lstsq(design(train,cols),train[yname],rcond=None)[0]
    test=test.merge(features[['time','pool_id','pressure_group','liquidity_group','low_cut_log_depth','high_cut_log_depth']],on=['time','pool_id'],validate='one_to_one')
    test['prediction_flow']=design(test,['ret_bps','oi'])@beta_flow
    test['prediction_baseline_check']=design(test,['ret_bps'])@beta_base
    test['prediction_full_check']=design(test,cols)@beta_full
    saved=existing[existing.horizon_minutes==h].copy()
    test=test.merge(saved,on=['time','pool_id','pair'],validate='one_to_one')
    assert len(test)==len(saved),('join count mismatch',h,len(test),len(saved))
    assert np.allclose(test[yname],test.actual_return_bps,atol=1e-8)
    assert np.allclose(test.prediction_baseline_check,test.baseline_bps,atol=1e-8)
    assert np.allclose(test.prediction_full_check,test.prediction_bps,atol=1e-8)
    test['horizon_minutes']=h
    for c,pred in [('baseline','baseline_bps'),('flow','prediction_flow'),('full','prediction_bps')]:
        test[f'{c}_sq_error']=(test[yname]-test[pred])**2
    global_bl=test.baseline_sq_error.mean()
    global_flow=test.flow_sq_error.mean()
    global_full=test.full_sq_error.mean()
    comp.append({'horizon_minutes':h,'holdout_rows':len(test),'flow_only_mse_reduction_pct':100*(1-global_flow/global_bl),'full_model_mse_reduction_pct':100*(1-global_full/global_bl)})
    outputs.append(test[['time','pool_id','pair','horizon_minutes','pressure_group','liquidity_group','oi','log_depth','volume',yname,'baseline_bps','prediction_flow','prediction_bps','baseline_sq_error','flow_sq_error','full_sq_error']].rename(columns={yname:'actual_return_bps'}))
joined=pd.concat(outputs,ignore_index=True)
joined.to_csv(OUT/'holdout_regime_observations.csv.gz',index=False,compression='gzip')

summary=[]
for (h,p,l),g in joined.groupby(['horizon_minutes','pressure_group','liquidity_group'],sort=False):
    n=len(g);m0=g.baseline_sq_error.mean();mf=g.flow_sq_error.mean();mfull=g.full_sq_error.mean()
    summary.append({'horizon_minutes':h,'pressure_group':p,'liquidity_group':l,'holdout_minutes':n,'distinct_pools':g.pool_id.nunique(),'share_largest_pool_pct':100*g.pool_id.value_counts(normalize=True).iloc[0], 'mean_order_flow_imbalance':g.oi.mean(),'mean_future_return_bps':g.actual_return_bps.mean(),'median_future_return_bps':g.actual_return_bps.median(),'mean_abs_future_return_bps':g.actual_return_bps.abs().mean(), 'pct_positive_future_returns':100*(g.actual_return_bps>0).mean(), 'baseline_mse':m0,'flow_only_mse':mf,'flow_and_liquidity_mse':mfull,'flow_only_mse_reduction_pct':100*(1-mf/m0),'flow_and_liquidity_mse_reduction_pct':100*(1-mfull/m0)})
summary=pd.DataFrame(summary)
summary.pressure_group=pd.Categorical(summary.pressure_group,P,ordered=True)
summary.liquidity_group=pd.Categorical(summary.liquidity_group,L,ordered=True)
summary=summary.sort_values(['horizon_minutes','pressure_group','liquidity_group']);summary.to_csv(OUT/'nine_group_results.csv',index=False)
pool_summary=joined.groupby(['horizon_minutes','pool_id','pair','pressure_group','liquidity_group'],observed=True).agg(n=('oi','size'),mean_return_bps=('actual_return_bps','mean'),mean_flow=('oi','mean'),baseline_mse=('baseline_sq_error','mean'),flow_mse=('flow_sq_error','mean'),full_mse=('full_sq_error','mean')).reset_index()
pool_summary['flow_only_mse_reduction_pct']=100*(1-pool_summary.flow_mse/pool_summary.baseline_mse)
pool_summary['full_mse_reduction_pct']=100*(1-pool_summary.full_mse/pool_summary.baseline_mse)
pool_summary.to_csv(OUT/'nine_group_by_pool.csv',index=False)
# 4-hour block bootstrap, preserving the same time blocks across pools for paired differences.
# Uncertainty around conditional *mean return* and strong-buy minus strong-sell means at each liquidity level.
rng=np.random.default_rng(20261014)
boot_summary=[]
for h in HORIZONS:
    sub=joined[joined.horizon_minutes==h].copy();sub['block']=sub.time.dt.floor('4h')
    # Bootstrapping all 18 observed calendar blocks, not treating minutes as independent.
    blocks=sorted(sub.block.unique()); bidx=np.arange(len(blocks)); groups={b:sub[sub.block==b] for b in blocks}
    for l in L:
        sl=sub[sub.liquidity_group==l]
        buy=sl[sl.pressure_group=='Strong buying'];sell=sl[sl.pressure_group=='Strong selling']
        observed=float(buy.actual_return_bps.mean()-sell.actual_return_bps.mean()) if len(buy) and len(sell) else np.nan
        bs=[]
        # Faster aggregate numerators and denominators per block x pressure for paired bootstrap.
        bmat=np.zeros((len(blocks),4),dtype=float)
        for j,block in enumerate(blocks):
            k=groups[block];k=k[k.liquidity_group==l]
            for col,pressure in [(0,'Strong buying'),(2,'Strong selling')]:
                u=k.loc[k.pressure_group==pressure,'actual_return_bps'].to_numpy();bmat[j,col]=u.sum();bmat[j,col+1]=len(u)
        for _ in range(1500):
            z=bmat[rng.integers(0,len(blocks),len(blocks))].sum(axis=0)
            if z[1]>0 and z[3]>0:bs.append(z[0]/z[1]-z[2]/z[3])
        lo,hi=np.quantile(bs,[.025,.975]) if len(bs)>100 else (np.nan,np.nan)
        boot_summary.append({'horizon_minutes':h,'liquidity_group':l,'buy_minus_sell_mean_bps':observed,'ci95_low_bps':lo,'ci95_high_bps':hi,'n_buy':len(buy),'n_sell':len(sell),'bootstrap_blocks':len(blocks)})
pd.DataFrame(boot_summary).to_csv(OUT/'buy_vs_sell_liquidity_bootstrap.csv',index=False)
compare=pd.DataFrame(comp);compare.to_csv(OUT/'model_reproduction_check.csv',index=False)
source=pd.read_csv(DATA/'forecast_summary.csv')
assert np.allclose(compare.flow_only_mse_reduction_pct,source.flow_only_mse_reduction_pct,atol=1e-8)
assert np.allclose(compare.full_model_mse_reduction_pct,source.full_model_mse_reduction_pct,atol=1e-8)
manifest={'time_period':'2026-10-03 to 2026-10-09 UTC','train':'2026-10-03 through 2026-10-06 UTC','holdout':'2026-10-07 through 2026-10-09 UTC','pressure_group_rules':{'Strong selling':'OI < -0.50','Balanced trading':'-0.50 <= OI <= 0.50','Strong buying':'OI > 0.50'},'liquidity_group_rules':'pool-specific training period one-third and two-thirds cutoffs in log local liquidity; test data never defines thresholds','holdout_rows_by_horizon':{str(r.horizon_minutes):int(r.holdout_rows) for r in compare.itertuples()},'number_of_4h_blocks':18,'price_targets':'future observed pool-price log returns; not execution PnL','caution':'observational small 3-day holdout; multiple categories and thin cells; no causal inference','published_forecast_reproduction':'full, baseline, and flow-only metrics matched to included frozen results'}
(OUT/'nine_group_manifest.json').write_text(json.dumps(manifest,indent=2))
print('MODEL_CHECK\n'+compare.round(5).to_string(index=False))
for h in HORIZONS:
 print('\nHORIZON',h,'group sample sizes\n',summary[summary.horizon_minutes==h].pivot(index='pressure_group',columns='liquidity_group',values='holdout_minutes').to_string())
 print('\nMEAN FUTURE RETURN (bps)\n',summary[summary.horizon_minutes==h].pivot(index='pressure_group',columns='liquidity_group',values='mean_future_return_bps').round(3).to_string())
 print('\nFLOW MODEL MSE REDUCTION (%)\n',summary[summary.horizon_minutes==h].pivot(index='pressure_group',columns='liquidity_group',values='flow_only_mse_reduction_pct').round(2).to_string())
 print('\nFULL MODEL MSE REDUCTION (%)\n',summary[summary.horizon_minutes==h].pivot(index='pressure_group',columns='liquidity_group',values='flow_and_liquidity_mse_reduction_pct').round(2).to_string())
print('\nSTRONG_BUY_MINUS_SELL\n'+pd.DataFrame(boot_summary).round(3).to_string(index=False))
