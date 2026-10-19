"""Read every public domain-evidence part/member and compare a complete replay."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile

import audit_both183_QT_domains_v1 as checker


def normalized_sources(value):
    rows={name.replace('\\','/').rsplit('/',1)[-1]:digest for name,digest in value.items()}
    checker.require(len(rows)==len(value),'Duplicated original oracle source name')
    return rows


def verify(packet,fresh,output):
    checker.require(not output.exists(),'Preserve every verification epoch')
    manifest=checker.read(packet/'archive-manifest.json')
    checker.require(manifest['scope']=='complete-both183-all12344-QT-primal-domain-and-before-feasibility-v1' and
        manifest['actual_original_cases_per_language']==183 and manifest['actual_QT_updates']==12344,
        'The complete two-language original domain population is required')
    spec=manifest['archive'];pieces=[];expected_bytes=0
    for n,part in enumerate(spec['parts']):
        name=part['file']
        checker.require(name==f'complete-domain-reports.tar.gz.part{n:03d}' and checker.helper.safe(name),
                        'A complete, safe, ordered domain archive part is required')
        raw=(packet/name).read_bytes()
        checker.require(len(raw)==part['bytes'] and len(raw)<=512*1024 and
            hashlib.sha256(raw).hexdigest()==part['sha256'],'An original domain evidence part differs')
        pieces.append(raw);expected_bytes+=len(raw)
    checker.require(expected_bytes==spec['bytes'] and expected_bytes<=32*1024*1024,
                    'The complete bounded evidence archive is required')
    archive=b''.join(pieces)
    checker.require(hashlib.sha256(archive).hexdigest()==spec['sha256'],'The whole original domain archive differs')
    wanted={'native-all183-QT-domains.json','python-all183-QT-domains.json',
        'actual-complete-both-language-summary.json','actual-all12-negative-domain-controls.json',
        'actual-portable-domain-terminal-exit0.json'}
    checker.require(set(manifest['files'])==wanted,'A full original domain/control/terminal report is missing')
    reports={}
    with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as tar:
        for item in tar:
            checker.require(item.isfile() and checker.helper.safe(item.name) and item.name in wanted and
                item.name not in reports,'Unsafe, duplicated or substituted original domain member')
            prior=manifest['files'][item.name]
            checker.require(item.size==prior['bytes'] and item.size<=32*1024*1024,'The full original domain member size differs')
            raw=tar.extractfile(item).read()
            checker.require(hashlib.sha256(raw).hexdigest()==prior['sha256'],'An original full domain report byte differs')
            reports[item.name]=json.loads(raw)
    checker.require(set(reports)==wanted,'A full original domain report is missing')
    original=reports['actual-complete-both-language-summary.json'];actual=checker.read(fresh/'summary.json')
    for summary in (original,actual):
        checker.require(summary['actual_original_QT_updates']==12344 and summary['actual_original_cases_per_language']==183 and
            summary['all_original_QT_before_candidate_domains_and_constraints_pass'] and
            summary['actual_fresh_MP100_contractions']==0 and summary['source_before']==summary['source_after'],
            'Require all original QT domains with explicit reuse of complete MP100 contractions')
    checker.require(normalized_sources(original['source_after'])==normalized_sources(actual['source_after']),
                    'A current domain/physical reader differs from the sealed full result')
    for name,digest in actual['source_after'].items():
        checker.require(checker.sha(Path(name))==digest,'A replay source changed after completion')
    controls=reports['actual-all12-negative-domain-controls.json']
    checker.require(controls['actual_negative_controls']==12 and
        controls['all_expected_invalid_primal_or_physical_domains_rejected'] and
        controls['checker_sha256']==checker.sha(Path(checker.__file__)) and
        reports['actual-portable-domain-terminal-exit0.json']['actual_terminal_exit_code']==0,
        'The actual original control/source/terminal closure is required')
    cases=updates=0;rows=[]
    for language,expected in [('native',6181),('python',6163)]:
        name=language+'-all183-QT-domains.json';path=fresh/name
        checker.require(checker.sha(path)==manifest['files'][name]['sha256'],
                        'A fresh complete domain/feasibility result differs from the original full evidence')
        report=reports[name]
        checker.require(report['actual_QT_candidates']==expected and [c['ordinal'] for c in report['cases']]==list(range(183)) and
            report['all_exact_primal_domains_and_both_before_candidate_original_tolerance_constraints_pass'] and
            report['actual_domain_or_before_candidate_constraint_events']==[], 'A full original domain population failed')
        count=0
        for case in report['cases']:
            candidates=case['all_original_candidates']
            checker.require([r['index'] for r in candidates]==list(range(case['actual_QT_candidates'])),
                            'An original complete QT candidate domain row is missing')
            for row in candidates:
                checker.require(row['before_domain']['passed_strict_domain'] and row['candidate_domain']['passed_strict_domain'] and
                    row['independent_MP100_before_feasibility']['passed_original1e_minus5_constraints'] and
                    row['independent_MP100_candidate_feasibility']['passed_original1e_minus5_constraints'],
                    'An original primal domain or before/candidate physical constraint failed')
            count+=len(candidates)
        checker.require(count==expected,'An original full QT population is incomplete')
        cases+=183;updates+=count
        rows.append(dict(language=language,actual_cases=183,actual_QT_updates=count,actual_full_report_SHA256=checker.sha(path)))
    result=dict(actual_original_language_cases=cases,actual_original_QT_updates=updates,
        every_archive_part_and_full_original_member_byte_verified=True,
        actual_complete_current_replay_reports_byte_equal_original=True,
        actual_negative_controls=12,all_original_before_candidate_primal_and_physical_constraints_pass=True,
        actual_fresh_MP100_physical_contractions=0,actual_portable_domain_and_physical_sources_unchanged=True,
        archive_SHA256=spec['sha256'],verifier_SHA256=checker.sha(Path(__file__)),populations=rows,
        every_inner_state_dual_KKT_original_reference_or_full_paper_pass=False)
    checker.save(output,result)
    print(json.dumps({k:v for k,v in result.items() if k!='populations'}),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('packet','fresh-domain-output','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();verify(a.packet,a.fresh_domain_output,a.output)
