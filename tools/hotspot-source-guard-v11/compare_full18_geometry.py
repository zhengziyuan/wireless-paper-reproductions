"""Bounded fixed-geometry equivalence evidence, never a full-paper certificate.

Uses the 18 already saved native case configurations and the unchanged frozen
geometry/formula sources. No optimizer, random channel, Monte Carlo bank, trace
archive extraction, or historical worker is launched. An external caller must
enforce the admitted wall-clock limit. Completed case records are flushed.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import time

from call_only_numeric_source_guard import CallOnlyNumericSourceGuard, file_sha256
from test_call_only_numeric_source_guard import load_legacy_class

LANES = ('full_physical_MP_pi', 'literal_binary64_constants_point')
MAX_OUTPUT = 1024 * 1024


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exact_payload(value):
    """Compare the actual MP mantissa/exponent words, not rounded strings."""
    if hasattr(value, '_mpf_'):
        return ('mpf', value._mpf_)
    if hasattr(value, '_mpc_'):
        return ('mpc', value._mpc_)
    if hasattr(value, 'rows') and hasattr(value, 'cols'):
        return ('matrix', value.rows, value.cols,
                tuple(exact_payload(value[i, j]) for i in range(value.rows)
                      for j in range(value.cols)))
    if isinstance(value, dict):
        return tuple((k, exact_payload(v)) for k, v in sorted(value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(exact_payload(v) for v in value)
    return value


def canonical_set(guard):
    return sorted((row['path'], row['canonical_SHA256'])
                  for row in guard.raw_diagnostics)


def main(args):
    if not args.execute_bounded_component or not sys.dont_write_bytecode:
        raise ValueError('Explicit bounded component admission and Python -B required')
    if sys.gettrace() is not None:
        raise ValueError('Fresh untraced validation process required')
    output = args.output.resolve()
    if not output.is_relative_to(Path('E:/ZiyuanZhengProject/paper-reproduction-data')):
        raise ValueError('Evidence must remain under the E data root')
    if output.exists() or shutil.disk_usage(output.parent).free <= 101 * 2**30:
        raise ValueError('Fresh small evidence path and reserve required')
    spec = json.loads(args.manifest.read_text(encoding='utf-8-sig'))
    pins = {Path(row['path']).resolve().as_posix(): row['sha256'] for row in spec['files']}
    rows = [row for row in spec['files'] if
            '/full-paper-banks/hotspot-statistical-validated18-matlab-20261004-v1/case-' in row['path']
            and row['path'].endswith('-config.json')]
    rows.sort(key=lambda row: row['path'])
    if len(rows) != 18:
        raise ValueError('All 18 original saved case configurations required')
    configs = []
    for row in rows:
        path = Path(row['path'])
        if path.stat().st_size != row['bytes'] or file_sha256(path) != row['sha256']:
            raise ValueError('Saved configuration differs from its existing binding')
        configs.append(json.loads(path.read_text(encoding='utf-8-sig')))
    grid = [(c['reported']['U'], c['reported']['kappa_satellite_db']) for c in configs]
    if grid != [(u, beta) for beta in (0, 10, 20) for u in range(1, 7)]:
        raise ValueError('Exact original full18 geometry grid required')
    for cfg in configs:
        p = cfg['reported']
        if (p['N'], p['J'], p['M'], p['K'], p['kappa_ground_db']) != (16, 16, 25, 16-p['U'], 20):
            raise ValueError('Original full geometry dimensions required')
    root = Path('E:/ZiyuanZhengProject/academic-homepage')
    kernel_path = root / 'work/hotspot-full18-complete-typedstream-science-checker-prepared-v1/independent_geometry_kernels_sourceonly_v1.py'
    formula_path = Path(spec['closed_authority']['original_independent_formula_path'])
    mp_root = Path(spec['closed_authority']['MP_source_root'])
    for path in (kernel_path, formula_path, args.canonical.resolve(), args.legacy_entry.resolve()):
        key = path.resolve().as_posix()
        if key not in pins or file_sha256(path) != pins[key]:
            raise ValueError('An exact existing source binding is missing or changed: ' + key)
    sys.path.insert(0, str(mp_root.parent))
    import mpmath
    if Path(mpmath.__file__).resolve() != (mp_root / '__init__.py').resolve():
        raise ValueError('Selected frozen MP package required')
    canonical = load(args.canonical, 'original_bound_canonical')
    kernel = load(kernel_path, 'independent_geometry_kernels_sourceonly_v1')
    formula = load(formula_path, 'full18_bound_frozen_formulas')
    Legacy = load_legacy_class(args.legacy_entry, canonical)
    numeric_paths = [p for p in pins if Path(p).is_relative_to(mp_root)] + [kernel_path.as_posix(), formula_path.as_posix()]
    before_own = {p.name: file_sha256(p) for p in
                  (Path(__file__), Path(__file__).with_name('call_only_numeric_source_guard.py'),
                   Path(__file__).with_name('test_call_only_numeric_source_guard.py'))}
    metadata = dict(schema='ACTUAL_FULL18_FIXED_GEOMETRY_SOURCE_BINDER_COMPARISON_V1',
                    scope='18 saved full-size deterministic geometries only; not random channels, optimizer, projector quadrature, all events or original-reference agreement',
                    python=sys.version, mpmath_version=mpmath.__version__,
                    configs=[dict(path=r['path'], sha256=r['sha256']) for r in rows],
                    new_validation_sources=before_own, original_precisions=[80, 100],
                    constructor_lanes=list(LANES), paper_reproduction_pass=False)
    used = 0
    def emit(stream, value):
        nonlocal used
        line = (json.dumps(value, ensure_ascii=False, sort_keys=True) + '\n').encode('utf-8')
        used += len(line)
        if used > MAX_OUTPUT or shutil.disk_usage(output.parent).free <= 101 * 2**30:
            raise RuntimeError('Bounded evidence size or free-space threshold reached')
        stream.write(line); stream.flush()
    completed = 0
    executed_sources = set()
    with output.open('xb') as stream:
        emit(stream, metadata)
        for number, config in enumerate(configs, 1):
            case = dict(case=number, U=config['reported']['U'], beta=config['reported']['kappa_satellite_db'], comparisons=[])
            for precision in (80, 100):
                for lane in LANES:
                    payloads, counts, bindings, elapsed = [], [], [], []
                    for implementation in ('v10', 'v11'):
                        context = mpmath.mp.clone(); context.dps = precision
                        guard = Legacy(pins, numeric_paths) if implementation == 'v10' else CallOnlyNumericSourceGuard(pins, numeric_paths, canonical)
                        start = time.perf_counter()
                        if implementation == 'v10':
                            sys.settrace(guard.trace)
                            try:
                                result = kernel.deterministic_geometry(context, formula, config, lane)
                            finally:
                                sys.settrace(None)
                        else:
                            with guard.armed():
                                result = kernel.deterministic_geometry(context, formula, config, lane)
                        elapsed.append(time.perf_counter()-start)
                        if context.dps != precision:
                            raise ValueError('Original precision changed')
                        payloads.append(exact_payload(result))
                        counts.append(guard.calls); bindings.append(canonical_set(guard))
                        executed_sources.update(p for p, _ in bindings[-1])
                    equal = payloads[0] == payloads[1]
                    same_bindings = bindings[0] == bindings[1]
                    case['comparisons'].append(dict(precision=precision, lane=lane,
                        exact_all_output_words_equal=equal, numeric_calls=counts,
                        same_canonical_code_set=same_bindings, seconds=elapsed))
                    # Library caches may make two successive fresh contexts
                    # take different internal calls. Both bind every actual
                    # selected call; fixture tests cover identical-call paths.
                    if not equal or not all(counts) or not all(bindings):
                        emit(stream, dict(failed_case=case, component_pass=False, paper_reproduction_pass=False))
                        raise ValueError('Legacy/new geometry values differ or numerical binding was absent')
            emit(stream, case); completed += 1
            print(json.dumps(dict(completed_geometry_cases=completed, target=18)), flush=True)
        for path in executed_sources:
            if file_sha256(path) != pins[path]:
                raise ValueError('Executed selected source changed during the component check')
        after_own = {p.name: file_sha256(p) for p in
                     (Path(__file__), Path(__file__).with_name('call_only_numeric_source_guard.py'),
                      Path(__file__).with_name('test_call_only_numeric_source_guard.py'))}
        if before_own != after_own:
            raise ValueError('Validation source changed during this check')
        emit(stream, dict(completed_geometry_cases=completed, paired_geometry_comparisons=72,
                          component_pass=True, original_frozen_sources_checked_unchanged=True,
                          all_original_event_audit_pass=False, paper_reproduction_pass=False))
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--legacy-entry', type=Path, required=True)
    parser.add_argument('--canonical', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--execute-bounded-component', action='store_true')
    raise SystemExit(main(parser.parse_args()))
