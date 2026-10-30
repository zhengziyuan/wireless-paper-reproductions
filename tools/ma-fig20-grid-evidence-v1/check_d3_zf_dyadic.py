"""Check saved ZF tangent weights against the D3 hypersimplex only."""
from argparse import ArgumentParser
from pathlib import Path
import json

parser = ArgumentParser(description=__doc__)
parser.add_argument('prefix_fixture', type=Path)
parser.add_argument('dyadic_fixture', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()

def read_small(path):
    with path.open('rb') as stream:
        raw = stream.read(32769)
    if len(raw) > 32768:
        raise ValueError('fixture too large')
    return json.loads(raw)

prefixes = read_small(args.prefix_fixture)
fixture = read_small(args.dyadic_fixture)
if prefixes['schema'] != 'MA20_D3G0_PREFIX_COVERAGE_FIXTURE_V1' or fixture['schema'] != 'MA20_D3G0_ZF_DYADIC_FIXTURE_V1':
    raise ValueError('unexpected fixture schema')
job = prefixes['job']
if (job['figure'], job['point'], job['realization'], job['N'], job['brute_force_D']) != (20, 3, 0, 6, 3):
    raise ValueError('unexpected grid case')
q = fixture['denominator']
if type(q) is not int or q != 2**32:
    raise ValueError('unexpected dyadic denominator')
rows = fixture['rows']
expected = prefixes['modes']['ZF']['pruned_prefixes']
if len(rows) != len(expected) or [r['prefix'] for r in rows] != expected:
    raise ValueError('saved prefix sequence mismatch')
checks = []
for row in rows:
    prefix = row['prefix']
    counts = row['counts']
    if not prefix or any(type(i) is not int or not 0 <= i < 9 for i in prefix) or sorted(set(prefix)) != prefix:
        raise ValueError('invalid saved prefix')
    remaining = list(range(prefix[-1] + 1, 9))
    needed = 6 - len(prefix)
    if not 0 <= needed <= len(remaining) or not isinstance(counts, list) or len(counts) != len(remaining):
        raise ValueError('wrong remaining candidate dimensions')
    if any(type(x) is not int or not 0 <= x <= q for x in counts):
        raise ValueError('weight outside [0,1]')
    if sum(counts) != needed * q:
        raise ValueError('weights do not sum to the remaining cardinality')
    checks.append({'prefix': prefix, 'remaining_candidates': len(remaining),
                   'remaining_placements': needed, 'feasible_hypersimplex_weights': True})
report = {'schema': 'MA20_D3G0_ZF_DYADIC_WEIGHT_CHECK_V1', 'checked_saved_prefixes': len(checks),
          'checks': checks, 'all_weights_in_saved_hypersimplex': True,
          'scope': 'Exact integer feasibility of stored dyadic tangent points only; no objective, tangent bound, historical incumbent, MATLAB or figure is verified.',
          'full_figure_or_paper_pass': False}
with args.output.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(report, stream, indent=2, allow_nan=False)
    stream.write('\n')
print('Saved D3 ZF dyadic-weight check complete.')
