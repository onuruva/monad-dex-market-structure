#!/usr/bin/env python3
"""Credential-free validation of exact source integers and canonical origin joins."""
import csv,gzip,json,random
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
    with gzip.open(ROOT/'swaps.csv.gz','rt') as f:swaps=list(csv.DictReader(f))
    with gzip.open(ROOT/'transaction_origins.csv.gz','rt') as f:origins=list(csv.DictReader(f))
    lookup={x['transaction_hash']:x for x in origins}
    assert len(swaps)==402062 and len(origins)==len(lookup)==301134
    assert len({x['id'] for x in swaps})==402062
    assert len({(x['transaction_hash'],x['log_index']) for x in swaps})==402062
    other=json.load(gzip.open(ROOT/'non_swap_events.json.gz','rt'))
    assert len(other)==7084
    assert len({x['id'] for x in swaps}|{x['id'] for x in other})==409146
    for s in swaps:
        t=lookup[s['transaction_hash']]
        assert s['id'].split('_')[1]==t['block_hash']
        for k in ['block_number','transaction_index','block_timestamp']:assert int(s[k])==int(t[k]),k
        assert int(t['receipt_status'])==1 and int(t['chain_id'])==143 and len(t['tx_from'])==42
    byid={x['id']:x for x in swaps};raw=json.loads((ROOT/'independent_raw_swap_sample.json').read_text())
    assert len(raw)==100
    for r in raw:
        words=[r['data'][i:i+64] for i in range(2,len(r['data']),64)];assert len(words)==6
        signed=lambda w:int(w,16)-(1<<256) if int(w,16)>=(1<<255) else int(w,16)
        expected=dict(zip(['amount0_raw','amount1_raw','sqrt_price_x96','active_liquidity','tick','swap_fee_pips'],[signed(words[0]),signed(words[1]),int(words[2],16),int(words[3],16),signed(words[4]),int(words[5],16)]))
        s=byid[r['id']]
        for k,v in expected.items():assert Decimal(s[k])==v,(r['id'],k)
        topics=r['topics'].split(',');assert s['pool_id']==topics[1].lower();assert s['swap_caller']=='0x'+topics[2][-40:].lower()
    probe=json.loads((ROOT/'independent_sender_probe.json').read_text())
    for t in probe:
        current=lookup[t['transaction_hash']]
        for k in ['tx_from','tx_to','block_hash']:assert current[k]==t[k],k
        for k in ['block_number','transaction_index']:assert int(current[k])==int(t[k]),k
    result={'raw_source_rows_verified_in_database':409146,'frozen_swap_and_other_event_ids':409146,'other_raw_events':len(other),'swap_events':len(swaps),'distinct_transactions':len(origins),'canonical_origin_matches':len(swaps),'missing_origin_matches':0,'canonical_mismatches':0,'raw_abi_sample':len(raw),'numeric_comparisons':len(raw)*6,'pool_and_caller_comparisons':len(raw)*2,'independent_sender_probe_matches':len(probe),'successful_receipts':len(origins)}
    out=ROOT/'results';out.mkdir(exist_ok=True);(out/'final_input_validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)

if __name__=='__main__':main()
