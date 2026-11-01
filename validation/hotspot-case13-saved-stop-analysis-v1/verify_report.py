"""Replay a saved case13 analysis from bounded public projections, not the optimizer."""
import gzip
import importlib.util
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / 'tools/hotspot-case13-stop-consumer-v1/consume_saved_stops.py'
STREAM = ROOT / 'validation/hotspot-case13-saved-stop-history-v1/recorded-stop-history.jsonl.gz'
SUMMARY = ROOT / 'validation/hotspot-case13-saved-stop-history-v1/child-summary.json'
EXPECTED = HERE / 'recorded-analysis.json'
MAX_COMPRESSED = 512 * 1024
MAX_PLAIN = 512 * 1024
MAX_REPORT = 512 * 1024


def read_cap(path, cap):
    with path.open('rb') as stream:
        raw = stream.read(cap + 1)
    if len(raw) > cap:
        raise ValueError('input size bound exceeded')
    return raw


def decompress_limited(raw):
    if len(raw) > MAX_COMPRESSED:
        raise ValueError('compressed input size bound exceeded')
    with gzip.GzipFile(fileobj=io.BytesIO(raw), mode='rb') as stream:
        plain = stream.read(MAX_PLAIN + 1)
    if len(plain) > MAX_PLAIN:
        raise ValueError('decompressed stream size bound exceeded')
    return plain


def replay(raw, summary, consumer):
    plain = decompress_limited(raw)
    partial = bool(plain) and not plain.endswith(b'\n')
    lines = plain.splitlines()
    if partial:
        lines = lines[:-1]
    return consumer.consume([consumer.parse(line) for line in lines], summary, partial)


def exact_equal(left, right):
    """Preserve JSON types: Python's True == 1 must not validate a record."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(exact_equal(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(exact_equal(a, b) for a, b in zip(left, right))
    return left == right


def main():
    spec = importlib.util.spec_from_file_location('_case13_saved_stop_consumer', SOURCE)
    consumer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(consumer)
    recorded = consumer.parse(read_cap(EXPECTED, MAX_REPORT))
    summary = consumer.parse(read_cap(SUMMARY, 4096))
    computed = replay(read_cap(STREAM, MAX_COMPRESSED), summary, consumer)
    if not exact_equal(computed, recorded):
        changed = sorted(k for k in set(computed) | set(recorded)
                         if k not in computed or k not in recorded or
                         not exact_equal(computed[k], recorded[k]))
        raise ValueError('saved report mismatch in top-level fields: ' + ', '.join(changed))
    print(json.dumps({'saved_report_matches_exactly': True,
        'expected_events_and_histories_present': computed['expected_events_and_histories_present'],
        'no_detected_nested_interpretation_errors': computed['no_detected_nested_interpretation_errors'],
        'recorded_event_counts_by_action': computed['recorded_event_counts_by_action'],
        'full_paper_pass': False}, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
