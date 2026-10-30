"""Count saved D=3 prefix coverage; no search, rates or bound verification."""
from argparse import ArgumentParser
from itertools import combinations
from pathlib import Path
import json
import math

parser = ArgumentParser(description=__doc__)
parser.add_argument('fixture', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
with args.fixture.open('rb') as stream:
    raw = stream.read(32769)
if len(raw) > 32768:
    raise ValueError('fixture exceeds bound')
fixture = json.loads(raw)
if fixture['schema'] != 'MA20_D3G0_PREFIX_COVERAGE_FIXTURE_V1':
    raise ValueError('unexpected fixture')
job = fixture['job']
if (job['figure'], job['point'], job['realization'], job['N'], job['M'], job['brute_force_D']) != (20, 3, 0, 6, 5, 3):
    raise ValueError('unexpected grid case')
lower, upper, D = job['region_lower'], job['region_upper'], job['brute_force_D']
grid = [(lower[0] + i * (upper[0] - lower[0]) / (D - 1),
         lower[1] + j * (upper[1] - lower[1]) / (D - 1))
        for i in range(D) for j in range(D)]
spacing = float(fixture['minimum_distance'])
if not math.isfinite(spacing) or spacing <= 0:
    raise ValueError('invalid minimum spacing')
minimum_grid_distance = min(math.dist(a, b) for a, b in combinations(grid, 2))
if minimum_grid_distance < spacing:
    raise ValueError('this fixture requires all distinct grid points to satisfy spacing')
leaves = list(combinations(range(D * D), job['N']))
result = {}
for mode in ('MRT', 'ZF'):
    saved = fixture['modes'][mode]
    prefixes = [tuple(x) for x in saved['pruned_prefixes']]
    if not saved['completed'] or len(prefixes) != saved['saved_pruned_prefix_count']:
        raise ValueError('incomplete checkpoint or witness count mismatch')
    if any(not 0 < len(x) <= job['N'] or any(type(v) is not int or not 0 <= v < D * D for v in x)
           or tuple(sorted(set(x))) != x for x in prefixes):
        raise ValueError('invalid sorted grid prefix')
    coverage = [sum(leaf[:len(prefix)] == prefix for prefix in prefixes) for leaf in leaves]
    winner = tuple(saved['saved_winner'])
    if winner not in leaves:
        raise ValueError('winner is not a valid grid combination')
    row = {'all_feasible_grid_combinations': len(leaves), 'saved_pruned_prefixes': len(prefixes),
           'covered_combinations': sum(n > 0 for n in coverage),
           'multiply_covered_combinations': sum(n > 1 for n in coverage),
           'uncovered_combinations': sum(n == 0 for n in coverage),
           'saved_leaf_count': saved['saved_leaf_count'],
           'uncovered_count_matches_saved_leaves': sum(n == 0 for n in coverage) == saved['saved_leaf_count'],
           'winner_covered_by_pruned_prefix': any(winner[:len(x)] == x for x in prefixes)}
    result[mode] = row
report = {'schema': 'MA20_D3G0_PREFIX_COVERAGE_CHECK_V1', 'case': job,
          'minimum_grid_distance': minimum_grid_distance, 'minimum_required_spacing': spacing,
          'modes': result, 'full_figure_or_paper_pass': False,
          'scope': 'Combinatorial consistency of saved prefix lists and leaf counts only. This does not prove the values of pruning bounds, that every uncovered leaf was evaluated, MATLAB agreement, or the paper figure.'}
with args.output.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(report, stream, indent=2, allow_nan=False)
    stream.write('\n')
print('Saved D3 prefix-coverage check complete.')
