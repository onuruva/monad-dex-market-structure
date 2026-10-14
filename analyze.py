#!/usr/bin/env python3
"""Module A pilot. No venue leadership, lead-lag, or price-discovery tests.
Exact integers retained in source CSV; floats used only for statistical analysis.
"""
import json,gzip,hashlib,math,sys
from decimal import Decimal
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results';OUT.mkdir(exist_ok=True)
ZERO='0x'+'0'*40
STABLES={
 '0x754704bc059f8c67012fed69bc8a327a5aafb603':'USDC',
 '0xe7cd86e13ac4309349f30b3435a9d337750fc82d':'USDT0',
 '0x00000000efe302beaa2b3e6e1b18d08d69a9012a':'AUSD',
}

def save_json(name,x):
    def clean(v):
        if isinstance(v,dict):return {k:clean(a) for k,a in v.items()}
        if isinstance(v,list):return [clean(a) for a in v]
        if hasattr(v,'item'):v=v.item()
        if isinstance(v,float) and not math.isfinite(v):return None
        return v
    (OUT/name).write_text(json.dumps(clean(x),indent=2,allow_nan=False,default=str))

def concentration(values):
    x=np.sort(np.asarray(values,dtype=float));x=x[x>0]
    if not len(x):return {}
    s=x/x.sum();n=len(x)
    return {'n':n,'hhi':float(np.sum(s*s)),'hhi_10000':float(np.sum(s*s)*10000),'gini':float((2*np.arange(1,n+1)-n-1).dot(x)/(n*x.sum())),'top1_share':float(s[-1]),'top5_share':float(s[-5:].sum())}

def normalize():
    d=pd.read_csv(ROOT/'swaps.csv.gz',dtype=str)
    expected=json.loads((ROOT/'snapshot_manifest.json').read_text())['swaps']
    assert len(d)==expected==402062
    audit={'swaps':len(d),'duplicate_ids':int(d.id.duplicated().sum()),'duplicate_tx_log_keys':int(d.duplicated(['transaction_hash','log_index']).sum())}
    assert audit['duplicate_ids']==audit['duplicate_tx_log_keys']==0
    for c in ['block_number','block_timestamp','transaction_index','log_index','tick','swap_fee_pips']:d[c]=d[c].astype('int64')
    d=d.sort_values(['block_number','transaction_index','log_index']).reset_index(drop=True)
    pools=pd.DataFrame(json.loads((ROOT/'pools.json').read_text()))
    meta=pd.DataFrame(json.loads((ROOT/'token_metadata.json').read_text())).set_index('address')
    d=d.merge(pools,on='pool_id',how='left',validate='many_to_one')
    audit['unmatched_pools']=int(d.currency0.isna().sum());assert audit['unmatched_pools']==0
    for side in [0,1]:
        d['symbol'+str(side)]=d['currency'+str(side)].map(meta.symbol)
        decimals=d['currency'+str(side)].map(meta.decimals)
        d['decimals'+str(side)]=decimals
        # int -> float avoids parsing huge signed ABI amounts as int64.
        d['q'+str(side)]=d['amount'+str(side)+'_raw'].map(lambda x:float(Decimal(x)))/np.power(10.,decimals.astype(float))
    d['sqrt_ratio']=d.sqrt_price_x96.map(lambda x:float(Decimal(x)))/(2.**96)
    d['liquidity']=d.active_liquidity.map(lambda x:float(Decimal(x)))
    d['post_price_1_per_0']=d.sqrt_ratio**2*np.power(10.,d.decimals0.astype(float)-d.decimals1.astype(float))
    d['execution_price_1_per_0']=abs(d.q1/d.q0)
    d['opposite_signs']=np.sign(d.q0)*np.sign(d.q1)==-1
    d['has_hook']=d.hooks!=ZERO
    d['time']=pd.to_datetime(d.block_timestamp,unit='s',utc=True)
    d['pair']=d.symbol0.fillna('?')+'/'+d.symbol1.fillna('?')
    audit.update({'resolved_currencies':int(meta.decimals.notna().sum()),'currencies':len(meta),'fully_normalized_swaps':int((d.decimals0.notna()&d.decimals1.notna()).sum()),'nonstandard_signs':int((~d.opposite_signs).sum()),'hooked_swaps':int(d.has_hook.sum()),'pool_count':d.pool_id.nunique(),'start_utc':d.time.min().isoformat(),'end_utc':d.time.max().isoformat(),'zero_liquidity':int((d.liquidity<=0).sum()),'distinct_transactions':int(d.transaction_hash.nunique()),'distinct_swap_callers':int(d.swap_caller.nunique()),'bad_fee_range':int((~d.swap_fee_pips.between(0,1000000)).sum())})
    # Q96 and tick use raw units. Tick can be one less at an exact boundary.
    tick_diff=np.log(d.sqrt_ratio**2)/np.log(1.0001)-d.tick
    audit['tick_price_inconsistent']=int(((tick_diff<-.001)|(tick_diff>1.001)).sum())
    # Stablecoin-denominated values: explicitly a $1 peg assumption, not observed USD.
    d['stable_quote_address']=np.where(d.currency1.isin(STABLES),d.currency1,np.where(d.currency0.isin(STABLES),d.currency0,None))
    quote0=d.currency0==d.stable_quote_address
    d['stable_quote_notional']=np.where(d.stable_quote_address.notna(),np.where(quote0,abs(d.q0),abs(d.q1)),np.nan)
    d['base_address']=np.where(quote0,d.currency1,d.currency0)
    d['base_symbol']=np.where(quote0,d.symbol1,d.symbol0)
    d['base_delta']=np.where(quote0,d.q1,d.q0)
    d['signed_quote_flow']=d.stable_quote_notional*np.sign(d.base_delta)
    d['base_price']=np.where(quote0,1/d.post_price_1_per_0,d.post_price_1_per_0)
    # D = L sqrt(p_raw)/(2*10^d1) or L/(2*sqrt(p_raw)*10^d0).
    # Local quote-value slope per unit log-price change; NOT executable +/-1% depth.
    d['local_liquidity_scale']=np.where(quote0,.5*d.liquidity/d.sqrt_ratio/np.power(10.,d.decimals0.astype(float)),.5*d.liquidity*d.sqrt_ratio/np.power(10.,d.decimals1.astype(float)))
    audit['stable_quote_swaps']=int(d.stable_quote_address.notna().sum())
    save_json('data_quality.json',audit)
    # Keep normalized snapshot compressed, preserve raw integer columns as strings.
    d.to_csv(OUT/'swaps_normalized.csv.gz',index=False,compression='gzip')
    return d,audit

def descriptive(d):
    bypool=d.groupby('pool_id').agg(pair=('pair','first'),swaps=('id','size'),transactions=('transaction_hash','nunique'),callers=('swap_caller','nunique'),stable_quote_notional=('stable_quote_notional',lambda x:x.sum(min_count=1)),hook=('has_hook','first'),fee_pips=('fee_pips','first'))
    bypool=bypool.sort_values('swaps',ascending=False)
    bypool.to_csv(OUT/'pool_activity.csv')
    day=d.assign(day=d.time.dt.floor('D')).groupby('day').agg(swaps=('id','size'),transactions=('transaction_hash','nunique'),pools=('pool_id','nunique'),stable_quote_notional=('stable_quote_notional','sum'))
    day.to_csv(OUT/'daily_activity.csv')
    caller=d.groupby('swap_caller').agg(swaps=('id','size'),transactions=('transaction_hash','nunique'),pools=('pool_id','nunique')).sort_values('swaps',ascending=False)
    caller.to_csv(OUT/'swap_caller_activity.csv')
    out={'pool_swap_count_concentration':concentration(bypool.swaps),'stable_quote_pool_notional_concentration':concentration(bypool.stable_quote_notional.dropna()),'caller_swap_count_concentration':concentration(caller.swaps),'stable_quote_notional_total':float(d.stable_quote_notional.sum()),'swap_count_top5_pairs':bypool.head(5).reset_index().to_dict('records'),'stable_quote_size_quantiles':d.stable_quote_notional.dropna().quantile([.01,.25,.5,.75,.9,.95,.99]).to_dict()}
    save_json('market_structure.json',out)
    fig,axes=plt.subplots(1,2,figsize=(12,4.6))
    t=bypool.head(10).iloc[::-1];axes[0].barh(t.pair+' '+t.index.str[:8],t.swaps,color='#2864ad');axes[0].set_xlabel('Swap events');axes[0].set_title('Top pools by activity')
    axes[1].bar(day.index.strftime('%b %d'),day.swaps,color='#309c91');axes[1].set_title('Daily activity (UTC)');axes[1].set_ylabel('Swap events');fig.tight_layout();fig.savefig(OUT/'activity.png',dpi=180);plt.close(fig)
    return out

def ecosystem():
    x=json.loads((ROOT/'ecosystem_dex_volume_snapshot.json').read_text())
    cats={p['name']:p.get('category') for p in x['protocols']}
    rows=[]
    for ts,breakdown in x['totalDataChartBreakdown']:
        for protocol,volume in breakdown.items():
            # Some feeds nest protocol versions. Flatten only numeric entries.
            if isinstance(volume,(int,float)):rows.append({'day':pd.to_datetime(ts,unit='s',utc=True),'protocol':protocol,'category':cats.get(protocol),'reported_usd_volume':volume})
    d=pd.DataFrame(rows)
    # Align context to the EXACT seven UTC dates of the v4 pilot.
    d=d[(d.day>=pd.Timestamp('2026-10-03',tz='UTC'))&(d.day<pd.Timestamp('2026-10-10',tz='UTC'))]
    d.to_csv(OUT/'ecosystem_daily_venue_volume.csv',index=False)
    total=d.groupby('protocol').reported_usd_volume.sum().sort_values(ascending=False)
    spot=d[d.category=='Dexs'].groupby('protocol').reported_usd_volume.sum().sort_values(ascending=False)
    result={'source':'DefiLlama daily volume breakdown; provider-reported, not independently event-reconciled','start':'2026-10-03','end_exclusive':'2026-10-10','days':int(d.day.nunique()),'all_provider_categories':concentration(total),'dex_category_only':concentration(spot),'all_provider_volume':float(total.sum()),'dex_category_volume':float(spot.sum()),'uniswap_v4_share_dex_category':float(spot.get('Uniswap V4',0)/spot.sum()),'top_dex_category_venues':spot.head(12).reset_index().to_dict('records')}
    pd.DataFrame({'reported_usd_volume':spot,'share':spot/spot.sum()}).to_csv(OUT/'ecosystem_venue_shares.csv')
    save_json('ecosystem_context.json',result)
    fig,ax=plt.subplots(figsize=(8,4.8));top=spot.head(10).iloc[::-1];ax.barh(top.index,top/1e6,color='#2864ad');ax.set_xlabel('Provider-reported volume (USD millions)');ax.set_title('Monad DEX category — 3–9 October 2026 UTC');fig.tight_layout();fig.savefig(OUT/'ecosystem.png',dpi=180);plt.close(fig)
    return result

def minute_series(d):
    split=pd.Timestamp('2026-10-07',tz='UTC')
    valid=d[d.stable_quote_address.notna()&d.opposite_signs&~d.has_hook&(d.liquidity>0)&np.isfinite(d.base_price)&(d.base_price>0)].copy()
    # Exclude pairs between the three selected quote anchors; other base assets
    # (including mUSD) remain identifiable in pool-level results.
    valid=valid[~valid.base_address.isin(STABLES)]
    ranks=valid[valid.time<split].groupby('pool_id').agg(n=('id','size'),notional=('stable_quote_notional','sum'))
    chosen=ranks[ranks.n>=1000].sort_values('notional',ascending=False).head(10).index
    rows=[]
    for pool,g in valid[valid.pool_id.isin(chosen)].groupby('pool_id'):
        g=g.set_index('time').sort_index(kind='stable')
        # Data was chain sorted before stable timestamp sorting; ties keep log order.
        b=g.resample('1min',label='right',closed='left').agg(volume=('stable_quote_notional','sum'),net_flow=('signed_quote_flow','sum'),price=('base_price','last'),depth=('local_liquidity_scale','last'),n=('id','size'))
        # Require observed trades at both origin and target; never unlimited fills.
        b['oi']=b.net_flow/b.volume.replace(0,np.nan)
        b['ret_bps']=1e4*np.log(b.price/b.price.shift(1))
        median=b.loc[b.index<split,'depth'].median()
        b['log_depth']=np.log(b.depth/median)
        b['oi_x_depth']=b.oi*b.log_depth
        for h in [1,5,15]:b['future_'+str(h)]=1e4*np.log(b.price.shift(-h)/b.price)
        b['pool_id']=pool;b['pair']=g.pair.iloc[0];rows.append(b.reset_index())
    result=pd.concat(rows,ignore_index=True) if rows else pd.DataFrame()
    result.to_csv(OUT/'minute_features.csv.gz',index=False,compression='gzip')
    return result,split

def bootstrap_hourly_loss(test,loss_diff,hours=1):
    # Resample time blocks jointly across pools, preserving contemporaneous links.
    z=pd.DataFrame({'time':test.time,'diff':loss_diff}).assign(block=lambda x:x.time.dt.floor(str(hours)+'h')).groupby('block')['diff'].agg(['sum','count'])
    rng=np.random.default_rng(20261012);values=z.to_numpy();boot=[]
    for _ in range(1000):
        sample=values[rng.integers(0,len(values),len(values))];boot.append(sample[:,0].sum()/sample[:,1].sum())
    return {'blocks':len(values),'ci95':list(np.quantile(boot,[.025,.975])),'ci9833_three_horizon_adjustment':list(np.quantile(boot,[.05/6,1-.05/6])),'mean_loss_reduction':float(np.mean(loss_diff))}

def research(features,split):
    if features.empty:return []
    results=[];predictions=[]
    for h in [1,5,15]:
        yname='future_'+str(h);cols=['oi','ret_bps','log_depth','oi_x_depth']
        complete=features.dropna(subset=cols+[yname])
        complete=complete[np.isfinite(complete[cols+[yname]].to_numpy()).all(axis=1)]
        train=complete[complete.time<split-pd.Timedelta(minutes=h)]
        test=complete[complete.time>=split]
        # Remove pools with no usable training observations.
        pools=sorted(train.pool_id.unique());test=test[test.pool_id.isin(pools)]
        if len(train)<100 or len(test)<100:continue
        # Outlier limits estimated only on training data, applied symmetrically.
        cutoff=train.ret_bps.abs().quantile(.999)
        train=train[(train.ret_bps.abs()<=cutoff)&(train[yname].abs()<=cutoff*np.sqrt(h))]
        test_raw=test.copy()
        # Main test keeps extreme realized outcomes; robustness removes separately.
        means=train[cols].mean();scales=train[cols].std().replace(0,1)
        def design(a,full):
            fe=np.column_stack([(a.pool_id==p).astype(float) for p in pools])
            if full:return np.column_stack([fe,((a[cols]-means)/scales).to_numpy()])
            return np.column_stack([fe,((a.ret_bps-means.ret_bps)/scales.ret_bps).to_numpy()])
        beta=np.linalg.lstsq(design(train,True),train[yname],rcond=None)[0]
        beta0=np.linalg.lstsq(design(train,False),train[yname],rcond=None)[0]
        pred=design(test,True)@beta;baseline=design(test,False)@beta0;y=test[yname].to_numpy()
        loss=(y-pred)**2;bloss=(y-baseline)**2;zero=y*y
        def nested_design(a,features_to_use):
            fe=np.column_stack([(a.pool_id==p).astype(float) for p in pools])
            return np.column_stack([fe,((a[features_to_use]-means[features_to_use])/scales[features_to_use]).to_numpy()])
        nested={}
        for name,cc in [('depth_control',['ret_bps','log_depth']),('flow_only',['ret_bps','oi']),('no_interaction',['ret_bps','log_depth','oi'])]:
            coefficient=np.linalg.lstsq(nested_design(train,cc),train[yname],rcond=None)[0]
            forecast=nested_design(test,cc)@coefficient;nested[name]=(y-forecast)**2
        raw_coefs=dict(zip(cols,beta[len(pools):]/scales.to_numpy()))
        r={'horizon_minutes':h,'train_n':len(train),'test_n':len(test),'pools':len(pools),'pool_pairs':train.groupby('pool_id').pair.first().to_dict(),'train_end':train.time.max().isoformat(),'test_start':test.time.min().isoformat(),'test_end':test.time.max().isoformat(),'train_target_cutoff_bps':float(cutoff*np.sqrt(h)),'coefficients_raw_units':raw_coefs,'oos_r2_vs_zero':float(1-loss.mean()/zero.mean()),'oos_r2_vs_autoregression':float(1-loss.mean()/bloss.mean()),'rmse_bps':float(np.sqrt(loss.mean())),'baseline_rmse_bps':float(np.sqrt(bloss.mean())),'hour_block_bootstrap':bootstrap_hourly_loss(test,bloss-loss,1),'four_hour_block_bootstrap':bootstrap_hourly_loss(test,bloss-loss,4)}
        r['oos_r2_vs_depth_control']=float(1-loss.mean()/nested['depth_control'].mean())
        r['flow_only_oos_r2_vs_autoregression']=float(1-nested['flow_only'].mean()/bloss.mean())
        r['interaction_oos_r2_vs_no_interaction']=float(1-loss.mean()/nested['no_interaction'].mean())
        r['flow_increment_block_bootstrap']=bootstrap_hourly_loss(test,nested['depth_control']-loss,4)
        perpool=pd.DataFrame({'pool_id':test.pool_id,'full_loss':loss,'ar_loss':bloss,'depth_loss':nested['depth_control']}).groupby('pool_id').mean()
        perpool['r2_vs_ar']=1-perpool.full_loss/perpool.ar_loss
        perpool['r2_vs_depth_control']=1-perpool.full_loss/perpool.depth_loss
        r['per_pool_holdout']=perpool.reset_index().to_dict('records')
        # Predefined robustness: remove outcome tail and remove largest pool.
        robust=(np.abs(y)<=cutoff*np.sqrt(h))&(test.ret_bps.abs().to_numpy()<=cutoff)
        r['trimmed_oos_r2_vs_autoregression']=float(1-loss[robust].mean()/bloss[robust].mean()) if robust.any() else None
        largest=train.groupby('pool_id').volume.sum().idxmax();other=(test.pool_id!=largest).to_numpy()
        r['exclude_largest_pool_oos_r2_vs_autoregression']=float(1-loss[other].mean()/bloss[other].mean()) if other.any() else None
        byday=pd.DataFrame({'date':test.time.dt.date,'full_loss':loss,'base_loss':bloss}).groupby('date').mean();r['daily_loss']=byday.reset_index().to_dict('records')
        p=test[['time','pool_id','pair']].copy();p['horizon_minutes']=h;p['actual_return_bps']=y;p['prediction_bps']=pred;p['baseline_bps']=baseline;predictions.append(p)
        results.append(r)
    if predictions:pd.concat(predictions,ignore_index=True).to_csv(OUT/'holdout_predictions.csv.gz',index=False,compression='gzip')
    save_json('order_flow_tests.json',results)
    if results:
        fig,ax=plt.subplots(figsize=(7,4));xs=np.arange(len(results));ax.bar(xs-.18,[r['rmse_bps'] for r in results],.36,label='Order flow + liquidity');ax.bar(xs+.18,[r['baseline_rmse_bps'] for r in results],.36,label='Recent-return baseline');ax.set_xticks(xs,[str(r['horizon_minutes'])+' min' for r in results]);ax.set_ylabel('Holdout RMSE (basis points)');ax.set_title('Chronological holdout — 7–9 October UTC');ax.legend();fig.tight_layout();fig.savefig(OUT/'order_flow_holdout.png',dpi=180);plt.close(fig)
    return results

def main():
    d,audit=normalize();print('Quality',json.dumps(audit),flush=True)
    descriptive(d);ec=ecosystem();print('Ecosystem',json.dumps(ec),flush=True)
    f,split=minute_series(d);r=research(f,split);print('Research',json.dumps(r,default=str),flush=True)
    save_json('analysis_manifest.json',{'source_sha256':hashlib.sha256((ROOT/'swaps.csv.gz').read_bytes()).hexdigest(),'seed':20261012,'scope':'Seven-day Uniswap v4 application study; complete origin enrichment and separate provider venue aggregates','train_split':split.isoformat(),'runtime_versions':{'python':sys.version.split()[0],'numpy':np.__version__,'pandas':pd.__version__,'matplotlib':matplotlib.__version__}})

if __name__=='__main__':main()
