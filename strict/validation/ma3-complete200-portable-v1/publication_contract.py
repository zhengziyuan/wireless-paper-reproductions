"""Publication/layout/complete-evidence gates ONLY; no numerical imports."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path, PurePosixPath

INDEX_SHA = 'ee9576d69eb634b2843f0be8e01c4bbe19e2926741dac89a2d76d2f744634c24'
V1_FREEZE_SHA = '6b3de8c78f36d4ba4bd2fddfbc8c978a37895f06b2c5dfca8faedeb0adf90612'
NUMERIC_SUFFIX_SHA = '71eb5fd75e0c188a4b9fe16f881303ca984b2ae6e3424df28e00b401bb5eccbb'
SLOTS = tuple(f'case-{case:03d}-mc-{draw:03d}' for case in range(2) for draw in range(100))
AUDIT_NAMES = tuple(slot + '-independent-dual.json' for slot in SLOTS)
SCHEMES = ('MA-MRT', 'MA-ZF', 'FPA-MRT', 'FPA-ZF', 'FPA-OPT')


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024**2):
            value.update(block)
    return value.hexdigest()


def load(path):
    return json.loads(Path(path).read_bytes())


def safe_relative(root, name):
    if not isinstance(name, str) or '\\' in name or ':' in name:
        raise ValueError('One canonical relative POSIX bundle path required')
    pure = PurePosixPath(name)
    if pure.is_absolute() or pure.as_posix() != name or any(part in ('.', '..') for part in pure.parts):
        raise ValueError('No absolute/traversal/ambiguous public bundle path')
    path = (Path(root) / name).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError('Resolved public evidence/source path escaped bundle')
    return path


def verify_relative_pins(root, pins):
    for name, expected in pins.items():
        if sha(safe_relative(root, name)) != expected:
            raise ValueError('An immutable bundle source/evidence changed: ' + name)


def full200_gate(summary, completion, start, proofs):
    """No mock/partial/survivor flag alone promotes an incomplete population."""
    if any(type(summary.get(key)) is not int or summary[key] != required for key, required in
        (('expected_cases', 200), ('attempted_cases', 200), ('passed_cases', 200), ('failed_cases', 0))):
        raise ValueError('Exactly ALL200 required; no boolean counts/partial/survivors')
    if (summary.get('full200_independent_numeric_pass') is not True
        or summary.get('all_source_input_and_both_raw_bytes_unchanged') is not True
        or summary.get('original_curve_agreement_claimed') is not False
        or summary.get('all_failures') != []):
        raise ValueError('All original physical/stop/source gates must pass without reclassification')
    if (completion.get('all1044_original_evidence_bytes_unchanged') is not True
        or completion.get('portable_source_bytes_unchanged') is not True
        or completion.get('actual_numeric_summary_available') is not True
        or start.get('trusted_whole_archive_index_sha256') != INDEX_SHA
        or start.get('numeric_body_proof', {}).get('literal_numeric_suffix_text_sha256') != NUMERIC_SUFFIX_SHA
        or start.get('numeric_body_proof', {}).get('original_numeric_AST_exactly_equal') is not True):
        raise ValueError('Actual unchanged-body full200 byte/source completion required')
    if set(summary.get('all200_case_audit_sha256', {})) != set(AUDIT_NAMES) or set(proofs) != set(AUDIT_NAMES):
        raise ValueError('Every actual200 complete independently checked per-case proof required')
    for slot, name in zip(SLOTS, AUDIT_NAMES, strict=True):
        proof = proofs[name]
        if proof.get('passed') is not True or proof.get('case') != slot or set(proof.get('languages', {})) != {'python', 'matlab'}:
            raise ValueError('An original slot/language case failed/missing: ' + slot)
        for language in ('python', 'matlab'):
            own = proof['languages'][language]
            if own.get('all_independent_physical_stop_and_coordinate_gates') is not True or set(own.get('schemes', {})) != set(SCHEMES):
                raise ValueError('Original five terminal families and own-state gates required')
            for scheme in SCHEMES:
                result = own['schemes'][scheme]
                if type(result.get('sample_count')) is not int or result['sample_count'] != 1000 or result.get('all_terminal_samples_independently_recomputed') is not True or result.get('all1000_original_benchmark_stops_and_power_constraints_verified') is not True:
                    raise ValueError('No terminal draw or original benchmark stop may be dropped')
            # BEGIN V2 explicit original coordinate metadata completeness gate
            # This reads already-computed independent receipts, never recomputes
            # a coordinate objective or claims a new certificate calculation.
            certificates = own.get('independent_global_coordinate_certificates')
            if not isinstance(certificates, dict) or set(certificates) != {'mrt', 'zf'}:
                raise ValueError('Both explicit original independent coordinate certificate branches required')
            for coordinate_mode in ('mrt', 'zf'):
                history = own['histories'][coordinate_mode]
                certificate = certificates[coordinate_mode]
                accepted = history.get('accepted_position_count')
                coordinates = history.get('coordinate_count')
                if (type(accepted) is not int or accepted < 2 or type(coordinates) is not int
                    or coordinates != 6 * (accepted - 1) or type(certificate.get('coordinate_count')) is not int
                    or certificate['coordinate_count'] != coordinates):
                    raise ValueError('Every original N6 ordered coordinate/accepted-position count must agree')
                if (certificate.get('all_global_concave_tangent_gap_bounds_independently_recomputed') is not True
                    or certificate.get('all_spacing_box_polygon_vertices_enumerated') is not True):
                    raise ValueError('Original independent gap and complete polygon predicates required')
                for key in ('maximum_gap_to_original_tolerance_ratio', 'maximum_primal_to_original_tolerance_ratio'):
                    value = certificate.get(key)
                    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
                        raise ValueError('Finite original inclusive coordinate gap/primal ratios required')
                error = certificate.get('maximum_minorant_increment_abs_error')
                if (type(error) not in (int, float) or not math.isfinite(error) or not 0 <= error < 1e-9
                    or certificate.get('original_minorant_atol') != 1e-9):
                    raise ValueError('Original strict minorant error <1e-9 remains unchanged')
            # END V2 explicit original coordinate metadata completeness gate
            for mode in ('mrt', 'zf'):
                if own['histories'][mode].get('actual_source_stop_verified') is not True:
                    raise ValueError('Original actual fractional stopping gate required')
                physical = own['accepted_position_physics'][mode]
                if type(physical.get('draw_count_per_position')) is not int or physical['draw_count_per_position'] != 1000 or physical.get('every_accepted_position_all1000_physical_samples_recomputed') is not True:
                    raise ValueError('All accepted saved geometries/full1000 draws required')
                count = physical.get('accepted_position_count')
                if type(count) is not int or count <= 0 or count != own['histories'][mode].get('accepted_position_count') or count != len(physical.get('fresh_mean_rates', [])):
                    raise ValueError('Every saved accepted position must have its own full1000 mean')
    return True


def read_actual_complete_audit(audit):
    """Reads completed JSON/SHA evidence only; does NOT rerun its arithmetic."""
    audit = Path(audit)
    summary = load(audit / 'actual-full200-dual-summary.json')
    completion = load(audit / 'portable-audit-completion-byte-binding.json')
    start = load(audit / 'portable-audit-start-identity.json')
    names = {path.name for path in (audit / 'case-audits').glob('*.json')}
    if names != set(AUDIT_NAMES):
        raise ValueError('All200 actual case proof files, no additions or survivors')
    proofs = {}
    for name in AUDIT_NAMES:
        path = audit / 'case-audits' / name
        if sha(path) != summary['all200_case_audit_sha256'].get(name):
            raise ValueError('Actual full200 case proof bytes changed: ' + name)
        proofs[name] = load(path)
    full200_gate(summary, completion, start, proofs)
    return summary


def actual_supervision_gate(boundary):
    boundary = Path(boundary)
    parent = load(boundary / 'parent-v2-source-binding-after.json')
    exit_record = load(boundary / 'actual-child-exit-and-streams.json')
    worker = load(boundary / 'worker-entry/outer-completion.json')
    if (type(parent.get('actual_child_return_code')) is not int or parent['actual_child_return_code'] != 0
        or parent.get('v2_and_v1_sources_unchanged') is not True
        or parent.get('v2_sources_sha256_before') != parent.get('v2_sources_sha256_after')
        or type(exit_record.get('actual_child_return_code')) is not int or exit_record['actual_child_return_code'] != 0 or exit_record.get('parent_exception') is not None
        or worker.get('outer_status') != 'original_call_returned' or worker.get('exception') is not None
        or worker.get('outer_sources_unchanged') is not True):
        raise ValueError('Actual completed root child/source interval required, not exit/flag inference')
    return True


def verify_ready_bundle(root):
    root = Path(root).resolve()
    manifest = load(root / 'bundle-manifest.json')
    if manifest.get('schema') != 'READY_MA3_FULL200_PORTABLE_BUNDLE_V1' or manifest.get('publication_full200_actual_gate_passed') is not True or manifest.get('trusted_archive_index_sha256') != INDEX_SHA:
        raise ValueError('No publication from prepared/partial/mock manifest flags')
    verify_relative_pins(root, manifest['public_file_sha256'])
    archive_index = root / 'archives/full200-archive-index.json'
    if sha(archive_index) != INDEX_SHA:
        raise ValueError('Pinned WHOLE1044/eight-part index required')
    read_actual_complete_audit(root / 'evidence/root-fresh-audit')
    actual_supervision_gate(root / 'evidence/root-fresh-boundary')
    return manifest
