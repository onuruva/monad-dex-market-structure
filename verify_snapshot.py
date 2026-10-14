#!/usr/bin/env python3
"""Independently compare a seeded sample of exported values with raw ABI logs."""
import argparse,csv,gzip,json,random,os
from pathlib import Path
from decimal import Decimal
from fetch_data import ROOT,sql

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--connection-file');a=ap.parse_args()
    url=Path(a.connection_file).read_text().strip() if a.connection_file else os.environ['DATABASE_URL']
    rng=random.Random(20261012)
    with gzip.open(ROOT/'swaps.csv.gz','rt') as f:allrows=list(csv.DictReader(f))
    sample=rng.sample(allrows,100);lookup={r['id']:r for r in sample}
    literals=','.join("'"+s.replace("'","''")+"'" for s in lookup)
    source=sql(url,'SELECT id,data,topics FROM uniswap_v4_raw_logs_7d WHERE id IN ('+literals+')')
    checked=0
    for r in source:
        words=[r['data'][i:i+64] for i in range(2,len(r['data']),64)]
        def signed(word):
            v=int(word,16);return v-(1<<256) if v>=(1<<255) else v
        expected={'amount0_raw':signed(words[0]),'amount1_raw':signed(words[1]),'sqrt_price_x96':int(words[2],16),'active_liquidity':int(words[3],16),'tick':signed(words[4]),'swap_fee_pips':int(words[5],16)}
        for k,v in expected.items():assert Decimal(lookup[r['id']][k])==v,(r['id'],k)
        assert lookup[r['id']]['pool_id']==r['topics'].split(',')[1].lower()
        assert lookup[r['id']]['swap_caller']=='0x'+r['topics'].split(',')[2][-40:].lower()
        checked+=1
    assert checked==100
    (ROOT/'sample_abi_validation.json').write_text(json.dumps({'seed':20261012,'sampled_rows':checked,'numeric_field_comparisons':checked*6,'pool_and_caller_comparisons':checked*2,'mismatches':0},indent=2))
    print('Independent ABI validation passed for',checked,'events')

if __name__=='__main__':main()
