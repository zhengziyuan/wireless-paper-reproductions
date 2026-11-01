"""Check recorded event chains and stopping claims; does not run the solver."""
import base64
import gzip
import hashlib
import io
import json
import math
import sys
from pathlib import Path

EXPECTED=[('MIS',2),('SMS',1),('MIS',3),('MIS',4),('SMS',3),('MIS',5),
          ('MIS',6),('SMS',4),('MIS',7),('SMS',6),('MIS',8),('SMS',7),
          ('MIS',9),('SMS',11),('MIS',10),('SMS',12),('MIS',12),('SMS',13)]


def check(condition, message):
    if condition is not True: raise ValueError(message)


def canonical(obj):
    return (json.dumps(obj,sort_keys=True,separators=(',', ':'),allow_nan=False)+'\n').encode('ascii')


def main(root):
    root=Path(root)
    raw=(root/'evidence.json').read_bytes()
    check(len(raw)<=128*1024,'evidence size')
    evidence=json.loads(raw)
    check(evidence.get('schema')=='MIS_COMM_FIG11_POPULATION_BATCHES1TO3_PUBLIC_EVIDENCE_V1','schema')
    rows=evidence['completed_starts']
    check([(x['baseline'],x['start']) for x in rows]==EXPECTED,'start sequence')
    check(evidence['existing_artifacts_deferred']==[{'baseline':'SMS','start':2}],'deferred')
    claims=evidence['claims']
    check(set(claims)=={'independent_kkt_recomputation','independent_physical_feasibility',
                        'historical_provenance_authenticated','dual_language_validated',
                        'original_reference_agreement','all_6000_start_ranking_complete','full_paper_pass'} and
          all(v is False for v in claims.values()),'claims')
    batches=evidence['batches']
    check(len(batches)==3 and [b['batch_id'] for b in batches]==[1,2,3] and
          [b['skipped_existing'] for b in batches]==[1,0,0] and
          all(b['launches']==6 and b['all_6000_start_ranking_complete'] is False and
              b['scientific_or_full_paper_pass'] is False for b in batches) and
          batches[2]['lifetime_accounted_bytes']>batches[1]['lifetime_accounted_bytes']>batches[0]['lifetime_accounted_bytes'],
          'batch fields')
    stop_count=0
    for row in rows:
        b,n=row['baseline'],row['start']
        check(row['event_file']==f'events/{b}-{n:04d}.jsonl.gz','event path')
        compressed=(root/row['event_file']).read_bytes()
        check(len(compressed)<=512*1024,'compressed events bound')
        with gzip.GzipFile(fileobj=io.BytesIO(compressed),mode='rb') as stream:
            data=stream.read(512*1024+1)
        check(0<len(data)<=512*1024 and data.endswith(b'\n'),'events bound')
        events=[json.loads(line) for line in data.splitlines()]
        result=row['result']; guard=row['guard']
        check(result['status']=='finished' and len(events)==result['event_count'] and
              result['full_paper_pass'] is False and result['historical_content_reverified'] is False and
              result['experimental_floating_phase_mapping'] is True and
              result['replacement_is_separate_attempt'] is True,'result limitations')
        check(guard['guard_success'] is True and guard['returncode']==0 and
              guard['terminal_reason']=='natural_exit' and guard['resource_envelope_pass'] is True and
              guard['scientific_acceptance'] is False and guard['hard_filesystem_quota'] is False,
              'guard limitations')
        check(type(guard['minimum_E_free_bytes']) is int and guard['minimum_E_free_bytes']>101*1024**3 and
              type(guard['output_bytes_before_terminal']) is int and
              0<=guard['output_bytes_before_terminal']<=1024**2,'guard recorded resource boundary')
        prev=None; stops=[]
        for index,event in enumerate(events):
            digest=event.get('event_digest'); unsigned=dict(event); unsigned.pop('event_digest',None)
            check(event.get('sequence')==index and event.get('previous_digest')==prev and
                  event.get('context_id')==result['context_id'] and
                  digest==hashlib.sha256(canonical(unsigned)).hexdigest(),'event chain')
            cursor=event['cursor']; encoded=cursor.get('rcg_state_base64')
            if encoded:
                checkpoint=json.loads(base64.b64decode(encoded,validate=True))
                iteration=checkpoint.get('iteration')
                check(type(iteration) is int and 0<=iteration<=4000,'iteration cap record')
            if event['kind'] in ('mu_stage_end','final_stage_end'):
                stop=event['stop']; norm=stop.get('projected_kkt_norm')
                check(stop.get('reason')=='gradient_tolerance' and
                      type(norm) in (int,float) and math.isfinite(norm) and 0<=norm<=1e-6,
                      'reported stage stopping record')
                mu=float.fromhex(events[index-1]['cursor']['mu_hex'])
                stops.append((mu,norm)); stop_count+=1
            prev=digest
        first=events[0]
        check(first['kind']=='boundary' and first['baseline']==b and first['start']==n and
              first['replacement_stage_original_iteration_cap']==4000 and
              first['first_failed_mu_call']==result['first_failed_mu_call'] and
              first['original_failure_reason']==result['original_failure_reason'] and
              first['original_failed_stage_iterations']==result['original_failed_stage_iterations'] and
              first['successful_historical_mu_stages']==result['successful_historical_mu_stages'] and
              events[-1]['kind']=='final_stage_end' and prev==result['last_event_digest'],
              'boundary and recorded failure')
        gate=result['replacement_stage_stop_gate']; reported=gate['stage_stops']
        check(gate['required_mu_count']==gate['recorded_mu_count']==len(stops)==len(reported) and
              gate['all_replacement_stages_stopping_pass'] is True and
              gate['eligible_for_final_ranking'] is False and
              gate['independent_physical_feasibility_verified'] is False and
              gate['original_reference_agreement'] is False,'recorded gate')
        for (mu,norm), item in zip(stops,reported):
            check(item['mu']==mu and item['projected_kkt_norm']==norm and
                  item['reason']=='gradient_tolerance' and item['stopping_check_pass'] is True,
                  'stop record consistency')
    print(f'PASS: {len(rows)} event chains and {stop_count} recorded stage stops checked.')
    print('No independent KKT recomputation, feasibility, history, dual-language, ranking, or paper agreement verified.')


if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: python verify_public_batch1.py EVIDENCE_DIRECTORY')
    main(sys.argv[1])
