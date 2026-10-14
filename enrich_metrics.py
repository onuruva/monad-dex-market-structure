#!/usr/bin/env python3
"""Additional Module A descriptive valuation and liquidity-event audits.
Indirect marks are lagged within v4, not an independent USD benchmark.
No interpolation, future marks, assumed obscure-token prices, or volume doubling.
"""
import json,gzip
import numpy as np
import pandas as pd
from analyze import ROOT,OUT,ZERO,STABLES,concentration,save_json

MAJORS={ZERO,'0x3bd359c1119da7da1d913d1c4d2b7c461115433a','0x0555e30da8f98308edb960aa94c0db47230d2b9c','0xd18b7ec58cdf4876f6afebd3ed1730e4ce10414b','0xee8c0e9f1bffb4eb878d8f15f368a02a35481242'}

def value_trades():
    d=pd.read_csv(OUT/'swaps_normalized.csv.gz',usecols=['id','pool_id','block_number','transaction_index','log_index','block_timestamp','currency0','currency1','q0','q1','base_address','base_price','stable_quote_notional','opposite_signs','has_hook','pair'])
    d=d.sort_values(['block_number','transaction_index','log_index']).reset_index(drop=True)
    n=len(d);sequence=np.arange(n);marks={};ages={};refs={}
    for a in MAJORS:
        g=d[(d.base_address==a)&d.stable_quote_notional.notna()&d.opposite_signs&~d.has_hook&(d.base_price>0)]
        if g.empty:continue
        pool=g.groupby('pool_id').stable_quote_notional.sum().idxmax();r=g[g.pool_id==pool]
        pos=np.searchsorted(r.index.to_numpy(),sequence,side='right')-1;exists=pos>=0
        idx=np.clip(pos,0,len(r)-1);age=d.block_timestamp.to_numpy()-r.block_timestamp.to_numpy()[idx]
        valid=exists&(age>=0)&(age<=60)
        marks[a]=np.where(valid,r.base_price.to_numpy()[idx],np.nan);ages[a]=np.where(valid,age,np.nan);refs[a]=pool
    value=[]
    for side in [0,1]:
        px=np.full(n,np.nan)
        for a,prices in marks.items():
            mask=d['currency'+str(side)].eq(a).to_numpy();px[mask]=prices[mask]
        # $1 is a stated quote-anchor peg assumption, not a measured USD mark.
        px[d['currency'+str(side)].isin(STABLES)]=1.
        value.append(abs(d['q'+str(side)].to_numpy())*px)
    v0,v1=value;both=np.isfinite(v0)&np.isfinite(v1)
    denom=(v0+v1)/2;discrepancy=np.where(both,abs(v0-v1)/np.maximum(denom,1e-15),np.nan)
    indirect=np.where(both,denom,np.where(np.isfinite(v0),v0,v1))
    direct=d.stable_quote_notional.notna().to_numpy()
    valuation=np.where(direct,d.stable_quote_notional.to_numpy(),indirect)
    # Retain flagged data; exclude abnormal/hooked/stale/dislocated marks from totals.
    eligible=d.opposite_signs.to_numpy()&~d.has_hook.to_numpy()&np.isfinite(valuation)&(valuation>=0)&(direct|~both|(discrepancy<=.05))
    result=d[['id','pool_id','pair']].copy();result['usd_equivalent_notional']=valuation;result['direct_quote']=direct;result['two_leg_mark_discrepancy']=discrepancy;result['eligible']=eligible
    result.to_csv(OUT/'trade_valuation.csv.gz',index=False,compression='gzip')
    p=result[result.eligible].groupby('pool_id').agg(pair=('pair','first'),usd_equivalent_notional=('usd_equivalent_notional','sum'),events=('id','size')).sort_values('usd_equivalent_notional',ascending=False)
    p.to_csv(OUT/'pool_valued_volume.csv')
    summary={'reference_pools':refs,'max_reference_staleness_seconds':60,'valued_events':int(eligible.sum()),'event_coverage':float(eligible.mean()),'direct_quote_events':int((eligible&direct).sum()),'indirect_valued_events':int((eligible&~direct).sum()),'total_usd_equivalent_notional':float(valuation[eligible].sum()),'pool_notional_concentration':concentration(p.usd_equivalent_notional),'indirect_leg_discrepancy_above_5pct':int((~direct&both&(discrepancy>.05)).sum()),'interpretation':'One pool leg or average of two available lagged marks, never sum of both legs. Quote anchors assumed at $1; indirect marks come from same-venue reference pools.'}
    save_json('valuation_coverage.json',summary);print('Valuation',summary,flush=True)

def liquidity_events():
    raw=json.load(gzip.open(ROOT/'non_swap_events.json.gz','rt'));pools={p['pool_id'] for p in json.loads((ROOT/'pools.json').read_text())}
    rows=[]
    def signed(word):
        n=int(word,16);return n-(1<<256) if n>=(1<<255) else n
    for r in raw:
        topics=r['topics'].lower().split(',')
        if topics[0]!='0xf208f4912782fd25c7f114ca3723a2d5dd6f3bcc3ac8db5af63baa85f711d5ec':continue
        data=r['data'][2:];assert len(data)==256 and len(topics)==3
        words=[data[i:i+64] for i in range(0,len(data),64)]
        lower,upper,delta=signed(words[0]),signed(words[1]),signed(words[2]);assert -887272<=lower<upper<=887272
        rows.append({'id':r['id'],'block_number':int(r['block_number']),'transaction_index':int(r['transaction_index']),'log_index':int(r['log_index']),'pool_id':topics[1],'liquidity_caller':'0x'+topics[2][-40:],'tick_lower':lower,'tick_upper':upper,'liquidity_delta':str(delta),'salt':'0x'+words[3],'matches_swap_pool':topics[1] in pools,'action':'add' if delta>0 else 'remove' if delta<0 else 'zero_delta'})
    d=pd.DataFrame(rows);d.to_csv(OUT/'liquidity_changes.csv.gz',index=False,compression='gzip')
    summary={'modify_liquidity_events':len(d),'matching_active_swap_pools':int(d.matches_swap_pool.sum()),'pools':int(d.pool_id.nunique()),'actions':d.action.value_counts().to_dict(),'note':'Changes only; opening positions and tick liquidity distribution have not been reconstructed. Zero-delta calls are not liquidity additions or removals.'}
    save_json('liquidity_event_coverage.json',summary);print('Liquidity',summary,flush=True)

def venue_families():
    x=json.loads((ROOT/'ecosystem_dex_volume_snapshot.json').read_text());families={p['name']:p.get('parentProtocol') or p['name'] for p in x['protocols']}
    d=pd.read_csv(OUT/'ecosystem_daily_venue_volume.csv');d=d[d.category=='Dexs'];d['family']=d.protocol.map(families)
    agg=d.groupby('family').reported_usd_volume.sum().sort_values(ascending=False);pd.DataFrame({'reported_usd_volume':agg,'share':agg/agg.sum()}).to_csv(OUT/'ecosystem_family_shares.csv')
    summary={'concentration':concentration(agg),'uniswap_family_share':float(agg.get('parent#uniswap',0)/agg.sum()),'classification':'Protocol parent labels from the provider; missing parent retained separately. Distinct versions pooled by parent, not legal ownership verification.'};save_json('ecosystem_family_context.json',summary);print('Families',summary,flush=True)

if __name__=='__main__':value_trades();liquidity_events();venue_families()
