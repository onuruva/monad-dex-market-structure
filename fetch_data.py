#!/usr/bin/env python3
"""Freeze a Neon v4 research snapshot and resolve token metadata without guesses.
Uses stdlib HTTPS, no database passwords in output or saved research artifacts.
Set DATABASE_URL, or use --connection-file outside the deliverable directory.
"""
import argparse,csv,gzip,hashlib,json,os,time,urllib.request,urllib.parse
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parent
ZERO='0x'+'0'*40
SWAP='0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f'
TOKEN_LIST='https://raw.githubusercontent.com/monad-crypto/token-list/refs/heads/main/tokenlist-mainnet.json'

def http_json(url,payload=None,headers=None):
    req=urllib.request.Request(url,data=None if payload is None else json.dumps(payload).encode(),headers={'User-Agent':'MonadModuleAResearch/1.0',**(headers or {})})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req,timeout=90) as response:return json.load(response)
        except Exception:
            if attempt==3:raise
            time.sleep(1+attempt)

def sql(url,query):
    host=urllib.parse.urlparse(url).hostname
    ans=http_json('https://'+host+'/sql',{'query':query,'params':[]},{'Content-Type':'application/json','Neon-Connection-String':url,'Neon-Raw-Text-Output':'true'})
    if 'rows' not in ans:raise ValueError('SQL response has no rows')
    return ans['rows']

def rpc(calls,endpoint='https://rpc.monad.xyz'):
    return http_json(endpoint,calls,{'Content-Type':'application/json'})

def abi_string(result):
    if not result or not result.startswith('0x'):return None
    b=bytes.fromhex(result[2:])
    if len(b)==32:return b.rstrip(b'\0').decode('utf-8','replace') or None
    if len(b)<64:return None
    offset=int.from_bytes(b[:32],'big')
    if offset+32>len(b):return None
    size=int.from_bytes(b[offset:offset+32],'big')
    if size>4096 or offset+32+size>len(b):return None
    return b[offset+32:offset+32+size].decode('utf-8','replace') or None

def metadata():
    pools=json.loads((ROOT/'pools.json').read_text())
    currencies=sorted({p[k] for p in pools for k in ['currency0','currency1']})
    listing=http_json(TOKEN_LIST)
    (ROOT/'official_tokenlist_snapshot.json').write_text(json.dumps(listing,indent=2))
    byaddr={t['address'].lower():t for t in listing['tokens'] if t['chainId']==143}
    chain=rpc({'jsonrpc':'2.0','id':1,'method':'eth_chainId','params':[]})
    assert int(chain['result'],16)==143
    block=rpc({'jsonrpc':'2.0','id':1,'method':'eth_blockNumber','params':[]})['result']
    selectors={'symbol':'0x95d89b41','token_name':'0x06fdde03','decimals':'0x313ce567'}
    records={ZERO:{'address':ZERO,'token_name':'Monad','symbol':'MON','decimals':18,'metadata_source':'native','lookup_block':block,'tokenlist_match':True}}
    evidence=[]
    # Verify EVERY ERC20, including list entries. Names are labels, never identity.
    tasks=[(a,k,s) for a in currencies if a!=ZERO for k,s in selectors.items()]
    for start in range(0,len(tasks),10):
        group=tasks[start:start+10]
        calls=[{'jsonrpc':'2.0','id':i,'method':'eth_call','params':[{'to':a,'data':sel},block]} for i,(a,k,sel) in enumerate(group)]
        ans=rpc(calls)
        if not isinstance(ans,list):raise ValueError('RPC batch returned a non-list')
        lookup={v['id']:v for v in ans}
        for i,(a,k,sel) in enumerate(group):
            result=lookup.get(i,{})
            evidence.append({'address':a,'field':k,'block':block,'response':result})
            entry=records.setdefault(a,{'address':a,'token_name':None,'symbol':None,'decimals':None,'metadata_source':'onchain_erc20','lookup_block':block,'tokenlist_match':a in byaddr})
            raw=result.get('result')
            if k=='decimals':
                if raw and len(raw)==66:
                    n=int(raw,16);entry[k]=n if 0<=n<=255 else None
            else:entry[k]=abi_string(raw)
        if start%50==0:print('Metadata fields checked',start+len(group),'/',len(tasks),flush=True)
        time.sleep(.15)
    conflicts=[]
    for a,entry in records.items():
        listed=byaddr.get(a)
        if listed:
            for field,lk in [('symbol','symbol'),('token_name','name'),('decimals','decimals')]:
                if entry[field] is None:entry[field]=listed.get(lk);entry['metadata_source']='official_list_fallback'
                elif entry[field]!=listed.get(lk):conflicts.append({'address':a,'field':field,'onchain':entry[field],'listed':listed.get(lk)})
    (ROOT/'token_metadata.json').write_text(json.dumps(list(records.values()),indent=2))
    with open(ROOT/'token_metadata.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[ZERO]));w.writeheader();w.writerows(records.values())
    (ROOT/'metadata_evidence.json').write_text(json.dumps(evidence))
    (ROOT/'metadata_conflicts.json').write_text(json.dumps(conflicts,indent=2))
    print('Metadata resolved',sum(r['decimals'] is not None for r in records.values()),'/',len(currencies),'conflicts',len(conflicts),flush=True)

def export(url):
    audit=sql(url,"SELECT count(*) AS raw_events,count(DISTINCT (block_hash,log_index)) AS unique_log_keys,count(DISTINCT id) AS unique_ids,min(block_number) AS min_block,max(block_number) AS max_block,min(block_timestamp) AS min_ts,max(block_timestamp) AS max_ts FROM uniswap_v4_raw_logs_7d")
    topics=sql(url,"SELECT lower(split_part(topics,',',1)) AS topic0,count(*) AS events FROM uniswap_v4_raw_logs_7d GROUP BY 1 ORDER BY 2 DESC")
    (ROOT/'raw_audit.json').write_text(json.dumps({'audit':audit,'topics':topics,'snapshot_utc':datetime.now(timezone.utc).isoformat()},indent=2))
    # Each batch is keyset-paginated by unique event id. Python restores chain order.
    last=''; total=0
    cols=['id','block_number','block_timestamp','transaction_hash','transaction_index','log_index','pool_id','swap_caller','amount0_raw','amount1_raw','sqrt_price_x96','active_liquidity','tick','swap_fee_pips']
    with gzip.open(ROOT/'swaps.csv.gz','wt',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=cols);writer.writeheader()
        while True:
            where="AND id > '"+last.replace("'","''")+"'" if last else ''
            q=f"""SELECT id,block_number,block_timestamp,transaction_hash,transaction_index,log_index,
            lower(split_part(topics,',',2)) AS pool_id,
            '0x'||right(lower(split_part(topics,',',3)),40) AS swap_caller,
            monad_v4_signed128(substr(data,3,64)) AS amount0_raw,
            monad_v4_signed128(substr(data,67,64)) AS amount1_raw,
            monad_v4_uint160(substr(data,131,64)) AS sqrt_price_x96,
            monad_v4_uint160(substr(data,195,64)) AS active_liquidity,
            (('x'||right(substr(data,259,64),6))::bit(24)::bigint - CASE WHEN substr(right(substr(data,259,64),6),1,1) ~* '[89a-f]' THEN 16777216 ELSE 0 END) AS tick,
            ('x'||right(substr(data,323,64),6))::bit(24)::bigint AS swap_fee_pips
            FROM uniswap_v4_raw_logs_7d WHERE lower(split_part(topics,',',1))='{SWAP}' {where} ORDER BY id LIMIT 20000"""
            rows=sql(url,q)
            if not rows:break
            writer.writerows(rows);total+=len(rows);last=rows[-1]['id'];print('Exported swaps',total,flush=True)
    for table in ['uniswap_v4_initialize_history']:
        rows=sql(url,'SELECT * FROM '+table+' ORDER BY block_number,transaction_index,log_index')
        with gzip.open(ROOT/(table+'.json.gz'),'wt') as f:json.dump(rows,f)
    # Additional events may update liquidity between swaps; retain their raw form.
    rows=sql(url,f"SELECT * FROM uniswap_v4_raw_logs_7d WHERE lower(split_part(topics,',',1))<>'{SWAP}' ORDER BY block_number,transaction_index,log_index")
    with gzip.open(ROOT/'non_swap_events.json.gz','wt') as f:json.dump(rows,f)
    (ROOT/'snapshot_manifest.json').write_text(json.dumps({'swaps':total,'sha256':hashlib.sha256((ROOT/'swaps.csv.gz').read_bytes()).hexdigest(),'exported_utc':datetime.now(timezone.utc).isoformat()},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--connection-file');p.add_argument('--metadata-only',action='store_true');p.add_argument('--export-only',action='store_true');a=p.parse_args()
    if not a.export_only:metadata()
    if not a.metadata_only:
        url=Path(a.connection_file).read_text().strip() if a.connection_file else os.environ['DATABASE_URL'];export(url)
