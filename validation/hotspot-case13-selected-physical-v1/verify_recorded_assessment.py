"""Replay retained binary64 values; no original trajectory or optimizer read."""
import gzip
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def need(ok, why):
    if not ok:
        raise ValueError(why)


def read(path, cap):
    with path.open('rb') as f:
        data = f.read(cap+1)
    need(len(data) <= cap, 'bounded input')
    return data


def parse(raw):
    def pairs(items):
        result = {}
        for k, v in items:
            need(k not in result, 'duplicate JSON key')
            result[k] = v
        return result
    return json.loads(raw, object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def strict_equal(a, b):
    # Canonical JSON comparison distinguishes booleans from numbers.
    return json.dumps(a, sort_keys=True, separators=(',', ':'), allow_nan=False) == \
           json.dumps(b, sort_keys=True, separators=(',', ':'), allow_nan=False)


def run():
    archive = read(HERE/'selected-input.jsonl.gz', 512*1024)
    # Cap expanded bytes before parsing; no decompressed file is created.
    import io
    with gzip.GzipFile(fileobj=io.BytesIO(archive)) as f:
        expanded = f.read(512*1024+1)
    need(len(expanded) <= 512*1024 and expanded.endswith(b'\n'), 'compressed input bound or truncation')
    rows = [parse(line) for line in expanded.splitlines()]
    need(len(rows) == 3, 'three selected inputs required')
    moment = parse(read(ROOT/'tools/hotspot-case13-evidence-v1/moment_projection.json', 32768))
    saved_raw = read(HERE/'recorded-assessment.jsonl', 512*1024)
    need(saved_raw.endswith(b'\n'), 'truncated assessment')
    saved = [parse(line) for line in saved_raw.splitlines()]
    need(len(saved) == 4 and saved[-1].get('kind') == 'terminal' and
         saved[-1].get('schema') == 'CASE13_SELECTED_PHYSICAL_STREAM_V1' and
         saved[-1].get('completed') is True and saved[-1].get('schemes_durably_confirmed') == 3,
         'recorded terminal')
    path = ROOT/'tools/hotspot-case13-selected-feasibility-v1/prepared_exact_assessment.py'
    spec = importlib.util.spec_from_file_location('_selected_exact_replay', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    need(module.ENABLED is False, 'unexpected worker default')
    computed = []
    try:
        module.ENABLED = True
        overall = module.assess(rows, moment, computed.append)
    finally:
        module.ENABLED = False
    need(overall['full_paper_pass'] is False and len(computed) == 3, 'unexpected result')
    for want, got in zip(saved[:3], computed):
        need(want.get('kind') == 'scheme', 'record kind')
        need(strict_equal(want, dict(got, kind='scheme')), 'saved computation mismatch')
    return {'schema': 'CASE13_SELECTED_PHYSICAL_REPLAY_V1',
            'recorded_scheme_results_reproduced': 3,
            'original_trajectory_read': False, 'optimizer_rerun': False,
            'historical_source_authenticated': False, 'full_paper_pass': False}


if __name__ == '__main__':
    print(json.dumps(run(), sort_keys=True, separators=(',', ':')))
