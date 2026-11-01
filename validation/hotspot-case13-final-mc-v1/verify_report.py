"""Bounded, read-only replay of recorded case-13 MC arithmetic."""
import gzip
import importlib.util
import io
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
COMPRESSED_CAP=256*1024
PLAIN_CAP=256*1024
REPORT_CAP=32768


def need(ok,message):
    if not ok:raise ValueError(message)


def read(path,cap):
    with Path(path).open('rb') as f:b=f.read(cap+1)
    need(len(b)<=cap,'bounded read');return b


def same(a,b):
    if type(a) is not type(b):return False
    if isinstance(a,dict):return set(a)==set(b) and all(same(a[k],b[k]) for k in a)
    if isinstance(a,list):return len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
    return a==b


def main():
    source=ROOT/'tools/hotspot-case13-final-mc-audit-v1/audit_recorded_mc.py'
    spec=importlib.util.spec_from_file_location('_case13_saved_mc_audit',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    raw=read(HERE/'recorded-projection.jsonl.gz',COMPRESSED_CAP)
    with gzip.GzipFile(fileobj=io.BytesIO(raw),mode='rb') as f:plain=f.read(PLAIN_CAP+1)
    need(len(plain)<=PLAIN_CAP,'inflated input cap')
    parse=lambda b:json.loads(b,object_pairs_hook=module.pairs,
        parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
    projection=parse(plain)
    expected=parse(read(HERE/'recorded-audit.json',REPORT_CAP))
    actual=module.audit(projection)
    need(same(actual,expected),'recorded arithmetic report differs')
    print(json.dumps({'saved_projection_bytes':len(plain),'report_exact_same_runtime':True,
                      'historical_source_authenticated':False,
                      'full_paper_pass':False},sort_keys=True))


if __name__=='__main__':main()
