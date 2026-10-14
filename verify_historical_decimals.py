#!/usr/bin/env python3
"""Check decimals at first observed use and end of sample using archive RPC."""
import csv,gzip,json,time
from fetch_data import ROOT,ZERO,rpc

def main():
    pools={p['pool_id']:p for p in json.loads((ROOT/'pools.json').read_text())}
    minimum={};last=0
    with gzip.open(ROOT/'swaps.csv.gz','rt') as f:
        for r in csv.DictReader(f):
            block=int(r['block_number']);last=max(last,block)
            for key in ['currency0','currency1']:
                a=pools[r['pool_id']][key];minimum[a]=min(block,minimum.get(a,block))
    meta={r['address']:r for r in json.loads((ROOT/'token_metadata.json').read_text())}
    tasks=[(a,point,b) for a in sorted(minimum) if a!=ZERO for point,b in [('first_observed_use',minimum[a]),('sample_end',last)]]
    records=[]
    for start in range(0,len(tasks),10):
        group=tasks[start:start+10]
        calls=[{'jsonrpc':'2.0','id':i,'method':'eth_call','params':[{'to':a,'data':'0x313ce567'},hex(b)]} for i,(a,point,b) in enumerate(group)]
        answer=rpc(calls,'https://rpc2.monad.xyz');byid={x['id']:x for x in answer}
        for i,(a,point,b) in enumerate(group):
            ans=byid.get(i,{});result=ans.get('result');value=int(result,16) if result and len(result)==66 else None
            records.append({'address':a,'point':point,'block_number':b,'current_decimals':meta[a]['decimals'],'historical_decimals':value,'matches':value==meta[a]['decimals'],'response':ans})
        if start%50==0:print('Historical decimal calls',start+len(group),'/',len(tasks),flush=True)
        time.sleep(.1)
    (ROOT/'historical_decimals_evidence.json').write_text(json.dumps(records,indent=2))
    summary={'calls':len(records),'matches':sum(r['matches'] for r in records),'unavailable':sum(r['historical_decimals'] is None for r in records),'mismatches':sum(r['historical_decimals'] is not None and not r['matches'] for r in records),'endpoint':'https://rpc2.monad.xyz'}
    (ROOT/'historical_decimals_summary.json').write_text(json.dumps(summary,indent=2));print(summary,flush=True)

if __name__=='__main__':main()
