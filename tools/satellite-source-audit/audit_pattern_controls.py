"""Replay actual Python/MATLAB pattern scalars against independent MP80/100."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import mpmath as mp
import numpy as np

from itu1428_oracle import binary, linear


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def audit(directory, output):
    if output.exists():
        raise FileExistsError('Preserve actual earlier numerical audit')
    names = ('scalar-cases.json','scalar-inputs.csv','actual-Python-scalar-observations.csv',
        'actual-native-scalar-observations.csv','actual-native-scalar-execution.json',
        'prepare-receipt.json','native-copy-source-proof.json','itu1428_native_copy.m',
        'original-scenario.py.source','original-strict_satcom_scenario.m.source',
        'actual-native-runner.m.source','original-configuration.json')
    paths = [directory/name for name in names] + [Path(__file__),Path(__file__).with_name('itu1428_oracle.py')]
    before = {p.name:sha(p) for p in paths}
    cases = read(directory/'scalar-cases.json')['cases']
    inputs = np.loadtxt(directory/'scalar-inputs.csv',delimiter=',',ndmin=2)
    observed = {language:np.loadtxt(directory/f'actual-{language}-scalar-observations.csv',delimiter=',',ndmin=2)
                for language in ('Python','native')}
    if len(cases)!=517 or inputs.shape!=(517,2):
        raise ValueError('All517 actual prescribed scalar probes are required')
    for language,a in observed.items():
        if a.shape!=(517,3) or not np.array_equal(a[:,:2],inputs) or not np.isfinite(a).all() or np.any(a[:,2]<=0):
            raise ValueError('A numerical scalar return/input round trip differs: '+language)
    execution = read(directory/'actual-native-scalar-execution.json')
    if not (execution['actual_cases']==517 and execution['actual_scalar_execution_complete'] and
            execution['source_and_inputs_unchanged'] and execution['source_before']==execution['source_after'] and
            execution['output_csv_sha256']==before['actual-native-scalar-observations.csv'] and
            execution['source_before']['input_csv']==before['scalar-inputs.csv'] and
            execution['source_before']['runner']==before['actual-native-runner.m.source']):
        raise ValueError('No complete source-bound actual native scalar execution')
    proof = read(directory/'native-copy-source-proof.json')
    native = (directory/'original-strict_satcom_scenario.m.source').read_bytes()
    marker = b'function gain=itu1428(angle,q)'
    unit = native[native.index(marker):]
    adapted = (directory/'itu1428_native_copy.m').read_bytes()
    if not (sha(directory/'original-strict_satcom_scenario.m.source')==proof['original_source_sha256'] and
            hashlib.sha256(unit).hexdigest()==proof['original_function_unit_sha256'] and
            sha(directory/'itu1428_native_copy.m')==proof['adapted_function_sha256'] and
            adapted.replace(b'function gain=itu1428_native_copy(angle,q)',marker,1)==unit and
            execution['source_before']['original_native']==proof['original_source_sha256'] and
            execution['source_before']['native_function']==proof['adapted_function_sha256']):
        raise ValueError('Native scalar copy is not an exact invertible original-function extraction')
    preparation = read(directory/'prepare-receipt.json')
    py_hashes = [v for k,v in preparation['source_sha256'].items() if k.replace('\\','/').rsplit('/',1)[-1]=='scenario.py']
    if py_hashes != [sha(directory/'original-scenario.py.source')] or not preparation['source_and_configuration_unchanged']:
        raise ValueError('Actual Python source interval differs from the frozen source')
    for name in ('scalar-inputs.csv','scalar-cases.json','actual-Python-scalar-observations.csv',
                 'original-configuration.json','native-copy-source-proof.json','itu1428_native_copy.m'):
        if preparation['output_sha256'][name]!=sha(directory/name):
            raise ValueError('Actual prepared Python output/input changed: '+name)
    started = time.perf_counter()
    lanes,values = {},{}
    for digits in (80,100):
        rows,all_values = [],[]
        with mp.workdps(digits):
            for n,case in enumerate(cases):
                if case['index']!=n or not np.array_equal(inputs[n],[case['q'],case['angle_deg']]):
                    raise ValueError('Missing/reordered scalar source case')
                theta = (mp.mpf(case['exact_named_decimal_angle']) if case['probe']=='fixed_decimal'
                         else abs(binary(case['angle_deg'])))
                q = binary(case['q'])
                domain = ('continuous_boresight_convention' if theta==0 else
                    ('printed_small_q_33_1_gap_left_extension' if q<=25 and theta==mp.mpf('33.1')
                     else 'defined_standard_clause'))
                if domain!=case['source_domain']:
                    raise ValueError('A source-domain gap was hidden or relabelled')
                expected = linear(q,theta,conventions=domain!='defined_standard_clause')
                checks = {}
                for language,actual in observed.items():
                    error = abs(binary(actual[n,2])-expected)
                    checks[language] = dict(absolute_error=mp.nstr(error,105),
                        relative_error=mp.nstr(error/expected,105),
                        passed=bool(error<=mp.mpf('1e-12')+mp.mpf('1e-12')*abs(expected)))
                rows.append(dict(index=n,source_domain=domain,reference=mp.nstr(expected,105),checks=checks,
                    all_numeric_checks_pass=all(c['passed'] for c in checks.values())))
                all_values.append(expected)
        lanes[str(digits)] = rows
        values[digits] = all_values
    with mp.workdps(110):
        precision_gap = max(abs(x-y) for x,y in zip(values[80],values[100]))
        precision_pass = precision_gap<=mp.mpf('1e-50')
    defined = [r for r in lanes['100'] if r['source_domain']=='defined_standard_clause']
    conventions = [r for r in lanes['100'] if r['source_domain']!='defined_standard_clause']
    if len(defined)!=500 or len(conventions)!=17:
        raise ValueError('Every printed-domain and convention probe must remain separate')
    after = {p.name:sha(p) for p in paths}
    report = dict(scope='Actual517 scalar Python/native observations, independent official-pattern MP80/100 replay',
        actual_cases=517,defined_standard_domain_cases=500,declared_endpoint_convention_cases=17,
        source_input_sha256=before,source_and_inputs_unchanged=before==after,
        precisions=[80,100],scalar_linear_absolute_tolerance=1e-12,scalar_linear_relative_tolerance=1e-12,
        maximum_MP80_MP100_difference=mp.nstr(precision_gap,105),precision_absolute_bound='1e-50',
        all500_defined_standard_domain_scalar_checks_pass=bool(precision_pass and before==after and
            all(r['all_numeric_checks_pass'] for lane in lanes.values() for r in lane if r['source_domain']=='defined_standard_clause')),
        all17_explicit_endpoint_convention_checks_pass=bool(all(r['all_numeric_checks_pass'] for lane in lanes.values()
            for r in lane if r['source_domain']!='defined_standard_clause')),
        maximum_observed_Python_native_relative_gap=float(np.max(abs(observed['Python'][:,2]-observed['native'][:,2])/
            observed['native'][:,2])),lanes=lanes,
        fixed_named_decimal_angles_are_declared_boundary_probes_encoded_as_binary64=True,
        algebraic_thresholds_tested_on_strict_sides_not_unrepresentable_exact_equalities=True,
        boresight_uses_declared_continuous_Gmax_extension=True,
        small_q_exact33_1_printed_gap_uses_explicit_left_extension=True,
        full_continuum_interval_or_author_parameter_or_original_curve_or_paper_pass=False,
        optimizer_or_random_draw_calls=0,elapsed_seconds=time.perf_counter()-started)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('lanes','source_input_sha256')}))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    r=audit(a.directory,a.output)
    if not (r['all500_defined_standard_domain_scalar_checks_pass'] and r['all17_explicit_endpoint_convention_checks_pass']):
        raise SystemExit(1)
