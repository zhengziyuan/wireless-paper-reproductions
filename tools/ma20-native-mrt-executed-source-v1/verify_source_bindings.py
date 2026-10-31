"""Check the published native source bindings; this does not run MATLAB."""
import argparse
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent

def need(condition,message):
    if not condition:raise ValueError(message)

def digest(raw):return hashlib.sha256(raw).hexdigest()

def body(source,name):
    start=re.search(r'(?m)^function [^\r\n]*\b'+re.escape(name)+r'\(',source)
    need(start is not None,'missing MATLAB function '+name)
    end=re.search(r'(?m)^function ',source[start.end():])
    return source[start.start():start.end()+end.start()] if end else source[start.start():]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True)
    ap.add_argument('--original-driver',type=Path);args=ap.parse_args();repo=args.repo.resolve()
    pins=json.loads((HERE/'source_bindings.json').read_text(encoding='utf-8'))
    first_manifest=(HERE/'execution_first_manifest.json').read_bytes()
    need(digest(first_manifest)==pins['execution_first_manifest_sha256'],'first manifest pin')
    recorded=json.loads(first_manifest);recorded_sources=recorded['source_sha256']
    for source,key in (('original','native_helper_sha256'),('exact','exact_coordinate_sha256'),
                       ('generator','dispatch_generator_sha256'),('driver','actual_driver_sha256')):
        need(recorded_sources[source]==pins[key],'manifest source pin mismatch: '+source)
    helper=(HERE/'ma_original_statistical_components_native_v1.m').read_bytes()
    generator=(HERE/'generate_component_dispatch_prepared_v1.py').read_bytes()
    portable=(HERE/'ma20_mrt_segment_prepared_v1.m').read_bytes()
    exact=(repo/'strict/two-timescale-ma/ma_exact_coordinate.m').read_bytes()
    for data,key in ((helper,'native_helper_sha256'),(generator,'dispatch_generator_sha256'),
                     (portable,'portable_driver_sha256'),(exact,'exact_coordinate_sha256')):
        need(digest(data)==pins[key],key+' mismatch')
    actual=helper.decode('utf-8');v4=(repo/'strict/two-timescale-ma/run_strict_two_timescale_ma_full_v4.m').read_text(encoding='utf-8')
    names=('ma_scenario','ma_los','ma_mrt','ma_zf','ma_zf_surrogate','ma_coordinate')
    need(all(body(actual,n)==body(v4,n) for n in names),'component body mismatch')
    need(body(actual,'ma_optimize')!=body(v4,'ma_optimize') and 'ma_fractional_stop_v3' in body(v4,'ma_optimize'),
         'expected stopping-semantics distinction not found')
    relation_checked=False
    if args.original_driver:
        original=args.original_driver.read_bytes();need(digest(original)==pins['actual_driver_sha256'],'original driver pin')
        a=original.splitlines(keepends=True);b=portable.splitlines(keepends=True)
        changed=[i for i in range(min(len(a),len(b))) if a[i]!=b[i]]
        need(len(a)==len(b) and len(changed)==1,'portable driver changed more than one line')
        idx=changed[0]
        need(a[idx].startswith(b'assert(startsWith(string(eventsPath),')
             and b[idx].startswith(b"outputRoot=getenv('MA20_NATIVE_OUTPUT_ROOT');"),'unexpected changed line')
        relation_checked=True
    print(json.dumps({'first_manifest_source_pins_match':True,'helper_and_generator_pinned':True,'exact_coordinate_pinned':True,
        'six_v4_numeric_bodies_match':True,'v4_stopping_semantics_differ':True,
        'portable_original_driver_relation_checked':relation_checked,
        'historical_content_reverified':False,'full_paper_pass':False},separators=(',',':')))

if __name__=='__main__':main()
