#!/usr/bin/env python3
"""Assemble browser-upload-sized frozen input parts and validate SHA256."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def ensure():
    manifest=json.loads((ROOT/'data_manifest.json').read_text())
    for item in manifest['inputs']:
        path=ROOT/item['path']
        if not path.is_file() and item.get('parts'):
            tmp=path.with_suffix(path.suffix+'.assembling')
            with open(tmp,'wb') as out:
                for part in item['parts']:
                    partpath=ROOT/part['path'];assert sha(partpath)==part['sha256'],part['path']
                    with open(partpath,'rb') as source:
                        for chunk in iter(lambda:source.read(1024*1024),b''):out.write(chunk)
            assert sha(tmp)==item['sha256'],item['path'];tmp.replace(path)
        assert path.is_file() and sha(path)==item['sha256'],item['path']
    return manifest

if __name__=='__main__':
    m=ensure();print('Verified',len(m['inputs']),'frozen inputs')
