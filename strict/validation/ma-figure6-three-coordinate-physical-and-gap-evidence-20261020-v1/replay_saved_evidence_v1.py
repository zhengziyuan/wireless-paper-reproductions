"""Inspect the six-capture capsule, or explicitly recheck saved data only.

No optimizer, coordinate solver, root solver, MC, or RNG is called. Published
MP numerical function bodies are unchanged. Public replay first use is pending.
"""
import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent


def sha(raw):return hashlib.sha256(raw).hexdigest()


def read_json(path):
    raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def write_new(path,value):
    payload=json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n'
    with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(payload)


def verify():
    manifest=read_json(HERE/'MANIFEST.json')
    for item in manifest['files']:
        p=(HERE/item['path']).resolve()
        if not p.is_relative_to(HERE) or not p.is_file():raise ValueError('invalid capsule path')
        raw=p.read_bytes()
        if len(raw)!=item['bytes'] or sha(raw)!=item['SHA256']:raise ValueError('capsule file changed: '+item['path'])
    return manifest


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


def materialize(item,destination):
    raw=(HERE/item['path']).read_bytes()
    if item.get('gzip'):raw=gzip.decompress(raw)
    if sha(raw)!=item['uncompressed_SHA256']:raise ValueError('decoded capture digest mismatch')
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('xb') as stream:stream.write(raw)
    return {'path':str(destination.resolve()),'SHA256':sha(raw),'bytes':len(raw)}


def local_aggregate(inventory,root):
    aggregate=copy.deepcopy(read_json(HERE/inventory['capture_aggregate']))
    rows={r['case']+'-'+r['mode'].lower():r for r in aggregate['rows']}
    for point in inventory['points']:
        row=rows[point['key']]
        row['fixture']=materialize(point['fixture'],root/point['key']/'fixture.json')
        for lane,entry in point['lanes'].items():
            target=root/point['key']/lane
            row['lanes'][lane]['actual_report']=materialize(entry['report'],target/'report.json')
            row['lanes'][lane]['held_journal']=materialize(entry['journal'],target/'actual-original-held-journal.json')
            row['lanes'][lane]['actual_numeric_capture']=materialize(entry['numeric'],target/('capture.npz' if lane=='python' else 'capture.mat'))
    return aggregate


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=['inspect','fixed-coeff','physical-coeff'],default='inspect')
    parser.add_argument('--output-dir',type=Path)
    args=parser.parse_args();before=verify();scope=read_json(HERE/'SCOPE.json')
    if args.stage=='inspect':
        print(json.dumps({'capsule_files_verified':len(before['files']),
              'saved_inputs':scope['saved_inputs'],'actual_results':scope['actual_results'],
              'limits':scope['limits'],'no_MP_or_solver_executed':True},indent=2))
        return 0
    if args.output_dir is None or args.output_dir.exists():raise ValueError('explicit fresh --output-dir required')
    args.output_dir.mkdir(parents=True,exist_ok=False)
    try:
        inventory=read_json(HERE/'CAPTURE_INVENTORY.json')
        aggregate=local_aggregate(inventory,args.output_dir/'inputs')
        sys.path.insert(0,str(HERE/'sources'))
        fixed=module('published_fixed_coeff_MP_functions',HERE/'sources/audit_only_six_captured_coordinate_coefficients_MP80_MP100_v3.py')
        physical=(module('published_physical_coeff_MP_functions',HERE/'sources/audit_only_three_saved_prestate_physical_coefficients_v1.py')
                  if args.stage=='physical-coeff' else None)
        rows=[];passed=True
        for row in aggregate['rows']:
            models={lane:fixed.load_lane(row,lane) for lane in ['python','native']}
            output={'case':row['case'],'mode':row['mode'],'lanes':{}}
            fixture=read_json(Path(row['fixture']['path']))
            for lane,model in models.items():
                if args.stage=='fixed-coeff':
                    vertices=fixed.exact_certificate_vertices(model['A'],model['b'])
                    other=models['native' if lane=='python' else 'python']['winner']
                    results=[fixed.audit_precision(model,dps,vertices,other) for dps in [80,100]]
                    passed=passed and all(r['fixed_coeff_original_gap_and_primal_pass'] for r in results)
                else:
                    actual=fixed.one_event(model['events'],'actual_complete_design_and_whole_saved_prestate')
                    c=physical.normalized_c(actual['c']);t=physical.np.asarray(actual['t'],dtype=physical.np.float64)
                    expected=physical.np.asarray(fixture['actual_pre_state'],dtype=physical.np.float64)
                    if t.shape!=(6,2) or t.tobytes(order='F')!=expected.tobytes(order='F'):raise ValueError('saved prestate binding failed')
                    results=[physical.audit_precision(model,c,t,fixture['antenna_zero_based'],fixture['selected_original_job'],dps) for dps in [80,100]]
                    passed=passed and all(all(r['existing_independent_consistency_checks'].values()) for r in results)
                output['lanes'][lane]=results
            if args.stage=='fixed-coeff':output['cross_lane_saved_readset_diagnostic_only']=fixed.compare_lanes(models)
            rows.append(output)
        after=verify()
        result={'schema':'portable-saved-only-MA6-three-coordinate-evidence-replay-v1','stage':args.stage,
                'capsule_before_and_after_identical':before==after,'rows':rows,
                'scoped_original_checks_pass':bool(passed),'scope_and_limits':scope['limits'],
                'recorded_original_epochs_not_new_coordinate_execution':True,
                'all_coefficients_or_curvatures_or_reference_PASS_claimed':False,
                'no_optimizer_coordinate_root_MC_RNG_or_trajectory_calls':True,
                'actual_exit_code':0 if passed else 2}
        write_new(args.output_dir/'portable-saved-only-result.json',result)
        print(json.dumps({'output':str(args.output_dir),'stage':args.stage,'scoped_checks_pass':passed,'exit':result['actual_exit_code']}))
        return result['actual_exit_code']
    except Exception as error:
        write_new(args.output_dir/'portable-host-failure.json',{'error':repr(error),'no_automatic_retry':True})
        raise


if __name__=='__main__':raise SystemExit(main())
