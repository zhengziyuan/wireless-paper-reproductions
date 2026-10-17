"""Retry transient Windows checkpoint replacement without changing audit math.

The original auditor bytes, source-bound plan and completed per-start results
stay unchanged, permitting exact reuse of an interrupted saved-state audit.
"""
import argparse
from pathlib import Path
import time

import audit_population as audit


def run(bank, output, starts=None):
    ordinary = audit.write
    source_before = audit.sha(Path(__file__).read_bytes()); retries = 0

    def write(path, value):
        nonlocal retries
        for attempt in range(100):
            try:
                return ordinary(path, value)
            except PermissionError:
                if attempt == 99:
                    raise
                retries += 1; time.sleep(.05)

    audit.write = write
    result = audit.audit(bank, output, starts)
    unchanged = audit.sha(Path(__file__).read_bytes()) == source_before
    write(output/'io-wrapper-receipt.json', dict(scope='Atomic checkpoint I/O retries only; actual auditor and mathematical source unchanged',
        wrapper_sha256=source_before, wrapper_source_unchanged=unchanged, checkpoint_permission_retries=retries,
        completed_source_bound_audits_reused=True, mathematical_controls_or_old_result_flags_changed=False,
        actual_auditor_sha256=result['input_sha256']['auditor'], audit_pass=result['all_checked_saved_fields_KKT_flags_and_stop_decisions_match']))
    if not unchanged or not result['all_checked_saved_fields_KKT_flags_and_stop_decisions_match']:
        raise SystemExit(1)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--bank', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True); p.add_argument('--starts', type=int, nargs='+')
    a = p.parse_args(); run(a.bank, a.output_dir, a.starts)
