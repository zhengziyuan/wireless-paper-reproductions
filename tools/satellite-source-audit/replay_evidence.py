"""Replay the actual direction-pattern controls and diameter-only bound."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath

from audit_pattern_controls import audit as scalar_audit
from audit_diameter_family_bound import audit as family_audit


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(packet, M18_directory, input_bank, output):
    if output.exists():
        raise FileExistsError('Preserve previous physical-source replay')
    manifest=json.loads((packet/'manifest.json').read_bytes())
    for name,row in manifest['files'].items():
        p=PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or ':' in name or '\\' in name:
            raise ValueError('Unsafe source-evidence path')
        source=packet/name
        if source.stat().st_size!=row['bytes'] or sha(source)!=row['sha256']:
            raise ValueError('Actual source-evidence payload differs: '+name)
    if (manifest['actual_scalar_cases'],manifest['defined_standard_domain_cases'],manifest['endpoint_convention_cases'])!=(517,500,17):
        raise ValueError('Every actual scalar observation and convention must remain')
    output.mkdir(parents=True)
    scalar=scalar_audit(packet,output/'new-independent-scalar-MP80-MP100.json')
    if not (scalar['all500_defined_standard_domain_scalar_checks_pass'] and
            scalar['all17_explicit_endpoint_convention_checks_pass']):
        raise ValueError('An actual public scalar pattern observation failed')
    family=family_audit(M18_directory,input_bank,packet/'actual-geometry-controls.json',
        output/'new-independent-all-diameter-NoRIS-bound.json')
    with gzip.open(packet/'actual-all-diameter-NoRIS-bound-MP80-MP100.json.gz','rb') as stream:
        historical=json.load(stream)
    keys=('language','ordinal','scheme','source_reference','all_diameter_fixed_other_input_upper_bound',
          'source_exceeds_even_numeric_envelope_after_EPS_rounding')
    if [{k:r[k] for k in keys} for r in family['comparisons']] != [{k:r[k] for k in keys} for r in historical['comparisons']]:
        raise ValueError('Actual public whole-cohort diameter-bound comparisons differ')
    result=dict(actual_payload_files_byte_verified=len(manifest['files']),actual_scalar_observations=517,
        defined_domain_scalar_observations_verified=500,explicit_endpoint_conventions_verified=17,
        complete54_per_language_NoRIS_comparisons_exactly_replayed=True,
        all_source_and_numeric_input_bindings_pass=True,actual_new_optimizer_or_random_draw_calls=0,
        original_author_gains_or_full_source_scenario_or_original_curve_or_full_paper_pass=False)
    (output/'actual-public-replay.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('packet','M18-directory','input-bank','output-dir'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    replay(a.packet,a.M18_directory,a.input_bank,a.output_dir)
