#!/usr/bin/env python3
"""Exactly enumerate rowwise candidates in a saved approximate SINR table.

Only a 9x25 serialized table and retained eta are compared. No physical
forward model, optimizer, or new phase is evaluated. Additional constraints
can only reduce the row-only set; they are not checked here.
"""
import argparse
import json
import math
from fractions import Fraction
from pathlib import Path


def evaluate(path):
    obj = json.loads(path.read_text(encoding='utf-8'))
    if obj.get('schema') != 'MIS_NATIVE4736_FIXED_STATE_225_GAMMA_DIAGNOSTIC_V1':
        raise ValueError('wrong saved diagnostic schema')
    if obj.get('original_start', 4736) != 4736 or obj.get('original_argmax_X_matches_stored_binary_schedule') is not True:
        raise ValueError('wrong original state or schedule binding')
    if obj.get('dimensions', {}).get('targets') != 9 or obj['dimensions'].get('positions') != 25:
        raise ValueError('wrong dimensions')
    eta = Fraction(obj['original_eta_exact_binary64'])
    original = obj['original_argmax_X_columns_zero_based']
    if len(original) != 9 or any(type(c) is not int or not 0 <= c < 25 for c in original):
        raise ValueError('invalid original selection')
    output = {}
    for precision in ('80', '100'):
        lane = obj['lanes'][precision]
        tolerance_text = lane['same_eta_feasibility_threshold_exact_binary64']
        # The diagnostic label says binary64, but its decimal formatter emits
        # a rounded 60-digit string. Compare the literal stored decimal and
        # the binary64 value recovered by rounding that string separately.
        tolerance_serialized = Fraction(tolerance_text)
        tolerance_float = float(tolerance_text)
        if not math.isfinite(tolerance_float):
            raise ValueError('nonfinite recovered binary64 tolerance')
        tolerance_binary64 = Fraction.from_float(tolerance_float)
        if tolerance_serialized < 0 or tolerance_binary64 < 0:
            raise ValueError('negative tolerance')
        rows = [[Fraction(v) for v in row] for row in lane['Gamma_9x25']]
        if len(rows) != 9 or any(len(row) != 25 for row in rows) or any(v < 0 for row in rows for v in row):
            raise ValueError('invalid Gamma shape or value')
        strict = [[j for j, v in enumerate(row) if v >= eta] for row in rows]
        within_serialized = [[j for j, v in enumerate(row) if eta - v <= tolerance_serialized] for row in rows]
        within_binary64 = [[j for j, v in enumerate(row) if eta - v <= tolerance_binary64] for row in rows]
        counts = [len(v) for v in within_binary64]
        unique = [v[0] for v in within_binary64] if all(n == 1 for n in counts) else None
        difference = tolerance_serialized - tolerance_binary64
        output[precision] = {
            'strict_candidate_columns_zero_based': strict,
            'serialized_tolerance_text': tolerance_text,
            'recovered_binary64_tolerance_hex': tolerance_float.hex(),
            'serialized_minus_binary64_fraction': [difference.numerator, difference.denominator],
            'serialized_tolerance_candidate_columns_zero_based': within_serialized,
            'recovered_binary64_tolerance_candidate_columns_zero_based': within_binary64,
            'candidate_sets_equal_between_tolerances': within_serialized == within_binary64,
            'strict_row_only_schedule_count': math.prod(map(len, strict)),
            'serialized_tolerance_row_only_schedule_count': math.prod(map(len, within_serialized)),
            'recovered_binary64_tolerance_row_only_schedule_count': math.prod(counts),
            'unique_row_only_recovered_binary64_schedule_zero_based': unique,
            'original_selected_column_in_recovered_binary64_set': [original[i] in v for i, v in enumerate(within_binary64)],
            'different_rows_zero_based': [i for i, c in enumerate(original) if unique is not None and c != unique[i]],
        }
    return {
        'schema': 'MIS_4736_SERIALIZED_GAMMA_SCHEDULE_ENUMERATION_V2',
        'original_start': 4736,
        'original_schedule_zero_based': original,
        'criterion': 'For each target k compare saved linear Gamma[k,j] directly to the same saved eta; compare eta-Gamma separately with the serialized decimal tolerance and its reconstructed binary64 value. No row-wise normalization.',
        'lanes': output,
        'scope': 'Exact rational comparisons of serialized approximate Gamma values; schedule counts assume only one-hot rows. No claim that any schedule satisfies other physical, temporal or assignment constraints.',
        'physical_forward_interval_or_author_recovery_verified': False,
        'original_failed_record_replaced': False,
        'new_optimizer_or_new_phase': False,
        'full_paper_pass': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('saved_diagnostic', type=Path)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    report = evaluate(args.saved_diagnostic)
    with args.report.open('x', encoding='utf-8', newline='\n') as file:
        json.dump(report, file, indent=2, ensure_ascii=False)
        file.write('\n')


if __name__ == '__main__':
    main()
