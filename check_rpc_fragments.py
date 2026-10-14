#!/usr/bin/env python3
"""Bounded independent reconciliation of 14 selected 100-block fragments.
This is a spot check, not proof of complete upstream capture of the whole week.
No history expansion, transactions, or paid-provider calls are performed.
"""
import argparse,csv,gzip,json,time,urllib.request,hashlib
from collections import defaultdict
from pathlib import Path
from fetch_data import sql,ROOT
ADDRESS='0x188d586ddcf52439676ca21a244753fa19f9ea8e'
ENDPOINT='https://rpc2.monad.xyz'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--connection-file',required=True);a=ap.parse_args();url=Path(a.connection_file).read_text().strip()
    days=defaultdict(list)
    with gzip.open(ROOT/'swaps.csv.gz','rt') as f:
        for r in csv.DictReader(f):days[int(r['block_timestamp'])//86400].append(int(r['block_number']))
    ranges=[(b-49,b+50) for _,v in sorted(days.items()) for b in [min(v),max(v)]]
    evidence=[];counts=[];allkeys=set()
    for i,(lo,hi) in enumerate(ranges):
        payload={'jsonrpc':'2.0','id':i+1,'method':'eth_getLogs','params':[{'address':ADDRESS,'fromBlock':hex(lo),'toBlock':hex(hi)}]}
        request=urllib.request.Request(ENDPOINT,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(request,timeout=25) as response:ans=json.load(response)
        if 'result' not in ans:raise RuntimeError('Historical fragment response failed: '+str(ans.get('error',{})))
        logs=ans['result'];assert all('blockTimestamp' in x for x in logs),'Provider timestamp field missing'
        logs=[x for x in logs if 1790985600<=int(x['blockTimestamp'],16)<1791590400]
        db=sql(url,f'SELECT id,block_hash,block_number,block_timestamp,transaction_hash,transaction_index,log_index,topics,data FROM uniswap_v4_raw_logs_7d WHERE block_number BETWEEN {lo} AND {hi}')
        rpcmap={(x['blockHash'].lower(),int(x['logIndex'],16)):x for x in logs}
        dbmap={(x['block_hash'].lower(),int(x['log_index'])):x for x in db}
        assert rpcmap.keys()==dbmap.keys(),{'range':[lo,hi],'rpc_only':len(rpcmap.keys()-dbmap.keys()),'db_only':len(dbmap.keys()-rpcmap.keys())}
        for key,x in rpcmap.items():
            r=dbmap[key]
            assert x['transactionHash'].lower()==r['transaction_hash'].lower()
            assert x['data'].lower()==r['data'].lower() and ','.join(x['topics']).lower()==r['topics'].lower()
            for field,rfield in [('blockNumber','block_number'),('transactionIndex','transaction_index'),('blockTimestamp','block_timestamp')]:assert int(x[field],16)==int(r[rfield])
        allkeys.update(rpcmap);evidence.append({'range':[lo,hi],'rpc_logs':logs,'database_logs':db})
        counts.append({'start_block':lo,'end_block_inclusive':hi,'blocks':100,'rpc_logs':len(logs),'database_logs':len(db),'missing_keys':0,'field_mismatches':0})
        print('Fragment',i+1,'/',len(ranges),'passed;',len(logs),'logs',flush=True)
        time.sleep(.1)
    raw=ROOT/'independent_rpc_fragments.json.gz'
    with gzip.open(raw,'wt') as f:json.dump(evidence,f)
    result={'endpoint':ENDPOINT,'selection':'First and last observed Swap block per UTC day, each centered in 100 blocks; overlapping ranges may repeat logs. Not a random or population-completeness test.','date_start':'2026-10-03','date_end_exclusive':'2026-10-10','fragments':counts,'unique_logs_checked':len(allkeys),'evidence_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'complete_week_verified':False}
    (ROOT/'results'/'independent_coverage_check.json').write_text(json.dumps(result,indent=2));print('Selected-fragment reconciliation passed:',len(allkeys),'unique logs',flush=True)

if __name__=='__main__':main()
