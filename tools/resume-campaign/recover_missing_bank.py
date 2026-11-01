"""Execute only absent full MA/ISAC jobs; retain every old failed outcome.

The immutable full input bank supplies every channel, original scheme and
numerical budget. This recovery never changes settings or replaces solvers.
Schema/convergence checks below are not independent physics/reference audits.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
from datetime import datetime, timezone


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def utc():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, allow_nan=False) + '\n', encoding='utf-8')
    temporary.replace(path)


def execute(paper, bank, output, workers):
    repo = Path(__file__).resolve().parents[2]
    package = repo / 'strict' / paper
    sys.path.insert(0, str(package))
    metadata = importlib.import_module('isac_metadata' if paper == 'rotatable-isac' else 'ma_metadata')
    bank, output = bank.resolve(), output.resolve()
    if output.exists():
        raise ValueError('Choose a fresh recovery directory; preserve every previous attempt')
    if output == bank or bank in output.parents:
        raise ValueError('Recovery output must be outside the original bank')
    if not 1 <= workers <= 3:
        raise ValueError('Use one to three workers without changing scientific budgets')
    configuration = (bank / 'run_config.json').read_bytes()
    config = json.loads(configuration)
    manifest = load(bank / 'manifest.json')
    if manifest.get('realizations_per_case') != 100 or not metadata.bank_complete(bank / 'jobs', manifest, configuration):
        raise ValueError('Complete original 100-realization-per-point bank required')
    if paper == 'two-timescale-ma' and (config.get('geometry_realizations') != 100 or config.get('nlos_realizations_per_geometry') != 1000):
        raise ValueError('Original complete MA 100 geometry x 1000 NLoS policy required')
    files = manifest['files']
    if len(files) != manifest['expected_jobs'] or len({entry['filename'] for entry in files}) != len(files):
        raise ValueError('Duplicate/missing manifest slots')
    current_source = metadata.implementation_fingerprint()
    output.mkdir(parents=True)
    (output / 'results').mkdir()
    (output / 'logs').mkdir()
    records, absent = [], []
    lock = threading.Lock()
    active = {}
    started = utc()

    def valid(path, entry):
        try:
            if paper == 'rotatable-isac':
                return bool(metadata.reusable(path, entry['input_fingerprint']))
            return bool(metadata.reusable(path, entry['input_fingerprint'], load(bank / 'jobs' / entry['filename']), config))
        except (OSError, ValueError, KeyError, TypeError):
            return False

    def receipt():
        successful = sum(record['status'] in ('reused_converged', 'recovered_converged') for record in records)
        return {
            'paper_id': paper, 'scope': 'only_absent_jobs_from_unchanged_complete_original_input_bank',
            'started_utc': started, 'updated_utc': utc(), 'source_bank': str(bank),
            'implementation_fingerprint': current_source, 'expected_jobs': len(files),
            'recorded_jobs': len(records), 'successful_jobs': successful,
            'retained_failed_or_unverified_jobs': sum(record['status'] == 'retained_failed_or_unverified' for record in records),
            'new_attempts_finished': sum(record.get('new_attempt', False) for record in records),
            'active_jobs': dict(active), 'workers': workers, 'all_input_slots_retained': True,
            'original_algorithms_or_budgets_changed': False, 'old_results_overwritten': False,
            'full_population_recorded': len(records) == len(files),
            'all_schema_and_stored_convergence_checks_passed': len(records) == len(files) and successful == len(files),
            'independent_physics_or_dual_language_or_reference_pass': False,
            'records': sorted(records, key=lambda record: record['filename']),
        }

    for entry in files:
        name = Path(entry['filename']).stem + '-python.json'
        original = bank / name
        if original.exists():
            records.append(dict(entry, result=str(original), status='reused_converged' if valid(original, entry) else 'retained_failed_or_unverified', new_attempt=False))
        else:
            absent.append(entry)
    write(output / 'progress.json', receipt())
    print(json.dumps({'expected': len(files), 'existing_preserved': len(records), 'absent_full_jobs': len(absent)}), flush=True)

    def job(entry):
        key = entry['filename']
        result = output / 'results' / (Path(key).stem + '-python.json')
        if shutil.disk_usage(output).free < 16 * 1024**3:
            return dict(entry, status='deferred_disk_below_16GiB', new_attempt=False, result=str(result))
        if metadata.implementation_fingerprint() != current_source:
            return dict(entry, status='blocked_scientific_source_changed', new_attempt=False, result=str(result))
        command = [sys.executable, '-B', str(package / 'run.py'), '--config', str(bank / 'run_config.json'),
                   '--scenario' if paper == 'rotatable-isac' else '--job', str(bank / 'jobs' / key), '--output', str(result)]
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
                           OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
        before = utc()
        try:
            with (output / 'logs' / (Path(key).stem + '.stdout.log')).open('wb') as stdout, \
                    (output / 'logs' / (Path(key).stem + '.stderr.log')).open('wb') as stderr:
                process = subprocess.Popen(command, stdout=stdout, stderr=stderr, env=environment,
                                           cwd=str(repo), creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                with lock:
                    active[key] = {'pid': process.pid, 'started_utc': before, 'command': command}
                    write(output / 'progress.json', receipt())
                code = process.wait()
            unchanged = metadata.implementation_fingerprint() == current_source
            passed = code == 0 and unchanged and valid(result, entry)
            return dict(entry, status='recovered_converged' if passed else 'executed_failed_or_unverified',
                        result=str(result), new_attempt=True, started_utc=before, completed_utc=utc(),
                        process_exit_code=code, scientific_sources_unchanged=unchanged)
        except Exception as error:
            return dict(entry, status='host_or_transport_error', new_attempt=True, result=str(result),
                        started_utc=before, completed_utc=utc(), error=repr(error))
        finally:
            with lock:
                active.pop(key, None)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for future in as_completed([pool.submit(job, entry) for entry in absent]):
            row = future.result()
            with lock:
                records.append(row)
                write(output / 'progress.json', receipt())
            print(json.dumps({'recorded': len(records), 'expected': len(files), 'latest': row['filename'], 'status': row['status']}), flush=True)
    final = receipt()
    write(output / 'summary.json', final)
    return 0 if final['all_schema_and_stored_convergence_checks_passed'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paper', required=True, choices=['rotatable-isac', 'two-timescale-ma'])
    parser.add_argument('--bank', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--workers', default=1, type=int, choices=[1, 2, 3])
    args = parser.parse_args()
    raise SystemExit(execute(args.paper, args.bank, args.output_dir, args.workers))
