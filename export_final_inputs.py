#!/usr/bin/env python3
"""Freeze completed origin records and independent raw ABI examples from Neon.
Read-only. Credentials are supplied externally and never included in outputs.
"""
import argparse,csv,gzip,json,random
from pathlib import Path
from fetch_data import sql,ROOT

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--connection-file',required=True);a=ap.parse_args()
    url=Path(a.connection_file).read_text().strip()
    cols=['chain_id','transaction_hash','block_hash','block_number','transaction_index','block_timestamp','tx_from','tx_to','transaction_type','input_selector','receipt_status','receipt_gas_used','receipt_effective_gas_price','provenance']
    last='';count=0
    with gzip.open(ROOT/'transaction_origins.csv.gz','wt',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        while True:
            query='SELECT '+','.join(cols)+' FROM monad_module_a_transactions'
            if last:query+=" WHERE transaction_hash > '"+last+"'"
            query+=' ORDER BY transaction_hash LIMIT 10000'
            rows=sql(url,query)
            if not rows:break
            w.writerows(rows);count+=len(rows);last=rows[-1]['transaction_hash']
            if count%50000==0:print('Origin rows exported',count,flush=True)
    assert count==301134,count
    with gzip.open(ROOT/'swaps.csv.gz','rt') as f:sample=random.Random(20261012).sample(list(csv.DictReader(f)),100)
    ids=','.join("'"+x['id'].replace("'","''")+"'" for x in sample)
    rows=sql(url,'SELECT id,address,block_hash,block_number,block_timestamp,transaction_hash,transaction_index,log_index,topics,data FROM uniswap_v4_raw_logs_7d WHERE id IN ('+ids+') ORDER BY id')
    assert len(rows)==100
    (ROOT/'independent_raw_swap_sample.json').write_text(json.dumps(rows,indent=2))
    print('Export complete',count,'origins and',len(rows),'raw ABI examples',flush=True)

if __name__=='__main__':main()
