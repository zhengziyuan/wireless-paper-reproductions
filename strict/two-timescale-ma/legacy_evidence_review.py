"""Read-only, scoped review of one saved MA result.

This never executes an optimizer, recomputes fingerprints, modifies evidence,
or proves the historical runtime/source or full-figure scientific acceptance.
Inputs are explicit existing JSON files; output is JSON on stdout only.
"""
import argparse
import json
import math
from pathlib import Path

SCHEMES = ('MA-MRT', 'MA-ZF', 'FPA-MRT', 'FPA-ZF', 'FPA-OPT')
CHECKS = ('mrt_converged', 'zf_converged',
          'mrt_nominal_design_spacing_feasible', 'zf_nominal_design_spacing_feasible',
          'mrt_nominal_design_box_feasible', 'zf_nominal_design_box_feasible')


def load_json(path):
    path = Path(path)
    if path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError('input exceeds 64 MiB limit')
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError('duplicate JSON key')
            out[key] = value
        return out
    with path.open('r', encoding='utf-8-sig') as stream:
        return json.load(stream, object_pairs_hook=unique,
                         parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def finite_real(x):
    return type(x) in (int, float) and math.isfinite(x)


def inspect(result, job, config, manifest, job_name):
    """Summarize one result's stored fields; never attest historical source."""
    if not all(type(x) is dict for x in (result, job, config, manifest)):
        raise ValueError('all four records must be JSON objects')
    matching = [e for e in manifest.get('files', [])
                if type(e) is dict and e.get('filename') == job_name]
    if len(matching) != 1:
        raise ValueError('exactly one matching manifest entry is required')
    entry = matching[0]
    identifiers = ('N', 'M', 'kappa', 'power', 'A', 'figure', 'point', 'realization')
    metadata = result.get('job_metadata')
    identity = (result.get('paper_id') == 'two-timescale-ma'
                and result.get('mode') == 'full_scenario'
                and result.get('status') != 'failed'
                and isinstance(result.get('input_fingerprint'), str)
                and result['input_fingerprint'] == entry.get('input_fingerprint')
                and type(metadata) is dict
                and all(k in metadata and k in job and metadata[k] == job[k] for k in identifiers)
                and entry.get('realization') == job.get('realization'))
    sample_count = config.get('nlos_realizations_per_geometry')
    if type(sample_count) is not int or sample_count <= 0:
        raise ValueError('configured sample count must be a positive integer')
    schemes = result.get('metrics', {}).get('schemes', {})
    rows = {}
    for name in SCHEMES:
        item = schemes.get(name, {})
        rates = item.get('sample_sum_rates', [])
        rates_ok = (type(rates) is list and len(rates) == sample_count
                    and all(finite_real(v) and v >= 0 for v in rates))
        mean = item.get('mean_sum_rate')
        mean_ok = (rates_ok and finite_real(mean)
                   and math.isclose(mean, math.fsum(rates)/sample_count, rel_tol=1e-10, abs_tol=1e-12))
        fpa_count = item.get('nonconverged_samples')
        convergence = (type(fpa_count) is int and fpa_count == 0) if name.startswith('FPA-') else None
        rows[name] = {'sample_count': len(rates) if type(rates) is list else None,
                      'rates_finite_nonnegative': rates_ok,
                      'stored_mean_matches_samples': mean_ok,
                      'minimum_sample_rate': min(rates) if rates_ok else None,
                      'fpa_reported_no_nonconverged_samples': convergence}
    stored_checks = {name: result.get('checks', {}).get(name) is True for name in CHECKS}
    all_rate_fields = all(row['rates_finite_nonnegative'] and row['stored_mean_matches_samples']
                          for row in rows.values())
    fpa_markers = all(rows[name]['fpa_reported_no_nonconverged_samples'] for name in SCHEMES if name.startswith('FPA-'))
    return {'scope': 'one saved record: metadata, rate arrays and stored flags only',
            'metadata_fields_consistent': identity,
            'stored_implementation_fingerprint': result.get('implementation_fingerprint'),
            'historical_source_identity_verified': False,
            'input_fingerprint_recomputed': False,
            'ao_and_geometry_stored_flags': stored_checks,
            'scheme_checks': rows,
            'stored_numerical_fields_consistent': bool(identity and all_rate_fields and fpa_markers and all(stored_checks.values())),
            'physical_feasibility_independently_verified': False,
            'mathematical_convergence_proven': False,
            'dual_language_verified': False,
            'original_reference_agreement_verified': False,
            'original_figure_complete': False,
            'limitations': ['fingerprint metadata matching does not certify actual loaded source or input bytes',
                            'stored flags are not independent feasibility or convergence checks',
                            'this reviews one record only and does not rerun the simulation']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('result', 'job', 'config', 'manifest'):
        parser.add_argument('--'+name, required=True, type=Path)
    args = parser.parse_args()
    report = inspect(load_json(args.result), load_json(args.job), load_json(args.config),
                     load_json(args.manifest), args.job.name)
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
