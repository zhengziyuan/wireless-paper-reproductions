"""Prepared all200 Fig3 display route, gated by a fresh unchanged-math portable audit."""
from pathlib import Path
import argparse
import json
import full_archive_v1 as archive
import safe_archive_v1 as codec


def render(tree, index_path, trusted_sha, audit, out):
    tree, audit, out = Path(tree), Path(audit), Path(out)
    if out.exists(): raise FileExistsError('Fresh figure output required')
    index = archive.pinned_index(index_path, trusted_sha)
    archive.verify_tree(tree, index)
    summary_path = audit/'actual-full200-dual-summary.json'
    summary = json.loads(summary_path.read_bytes())
    binding = json.loads((audit/'portable-audit-completion-byte-binding.json').read_bytes())
    start = json.loads((audit/'portable-audit-start-identity.json').read_bytes())
    if (summary.get('attempted_cases') != 200 or summary.get('passed_cases') != 200
            or summary.get('failed_cases') != 0 or summary.get('full200_independent_numeric_pass') is not True
            or binding.get('all1044_original_evidence_bytes_unchanged') is not True
            or binding.get('portable_source_bytes_unchanged') is not True
            or start.get('trusted_whole_archive_index_sha256') != trusted_sha):
        raise ValueError('All200 independently re-audited cases required, not archived/partial/survivor-only flags')
    expected = {stem+'-independent-dual.json' for stem in archive.recipe.SLOTS}
    if set(summary['all200_case_audit_sha256']) != expected:
        raise ValueError('Complete200 fresh case audit population required')
    for name, expected_sha in summary['all200_case_audit_sha256'].items():
        if codec.sha(audit/'case-audits'/name) != expected_sha:
            raise ValueError('Fresh numerical case audit changed')
    # Display-only libraries imported AFTER complete population/provenance gate.
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    def terminal_hold(values):
        arrays = [np.asarray(value, dtype=float) for value in values]
        if len(arrays) != 100 or any(a.ndim != 1 or not len(a) or not np.all(np.isfinite(a)) for a in arrays):
            raise ValueError('All100 finite original trajectories required')
        length = max(map(len, arrays))
        return np.mean([np.pad(a, (0, length-len(a)), mode='edge') for a in arrays], axis=0)
    all_data = {}
    for language in ('python', 'matlab'):
        curves = []
        for case, kappa in enumerate((6, 100)):
            objects, actual_mc = [], []
            for realization in range(100):
                stem = f'case-{case:03d}-mc-{realization:03d}'
                raw = json.loads((tree/f'snapshot/raw/{language}/{stem}-{language}.json').read_bytes())
                proof = json.loads((audit/f'case-audits/{stem}-independent-dual.json').read_bytes())
                if proof.get('passed') is not True: raise ValueError('No failed case may be omitted')
                objects.append(raw['history']['mrt']['objective'])
                actual_mc.append(proof['languages'][language]['accepted_position_physics']['mrt']['fresh_mean_rates'])
            for kind, values in (('original statistical design objective', objects), ('actual all1000 NLoS MC mean', actual_mc)):
                y = terminal_hold(values)
                curves.append({'kappa': kappa, 'quantity': kind, 'x': list(range(len(y))), 'y': y.tolist(),
                               'geometries': 100, 'draws_per_geometry': 1000})
        all_data[language] = curves
    out.mkdir(parents=True)
    document = {'figure': 3, 'source_scenario': 'N6 M5 kappa6/100 P1W A2', 'curves': all_data,
        'aggregation': 'Every100 original trajectories; terminal accepted state held unchanged for unequal stopping lengths; no fictitious updates or sample discard',
        'source_independent_audit_summary_sha256': codec.sha(summary_path), 'trusted_whole_index_sha256': trusted_sha,
        'source_original_fig3_four_series': True, 'same_nonconvex_solution_required': False,
        'geometry100_NLoS1000_declared_reconstruction_counts_not_author_reported': True,
        'original_curve_closeness_certified': False, 'global_nonconvex_AO_optimality_certified': False,
        'new_optimizer_newMC_or_physics_evaluator_called': False}
    with (out/'portable-all200-Fig3-curves.json').open('x', encoding='utf-8') as stream:
        json.dump(document, stream, indent=2, allow_nan=False); stream.write('\n')
    for language, curves in all_data.items():
        fig, ax = plt.subplots(figsize=(8.2, 5.2))
        for curve in curves:
            ax.plot(curve['x'], curve['y'], label=f"{curve['quantity']}; kappa={curve['kappa']}")
        ax.set(xlabel='Actual AO sweep index (terminal hold explicitly declared)', ylabel='Rate (bps/Hz)',
               title=f'Complete200 independently audited · {language} · historical agreement NOT certified')
        ax.grid(True, alpha=.25); ax.legend(fontsize=7); fig.tight_layout()
        fig.savefig(out/f'portable-Fig3-{language}.png', dpi=220)
        fig.savefig(out/f'portable-Fig3-{language}.svg'); plt.close(fig)
    return {'full200_Fig3_display_complete': True, 'original_figure_reproduction_certified': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extracted-tree', type=Path, required=True)
    parser.add_argument('--index', type=Path, required=True)
    parser.add_argument('--index-sha256', required=True)
    parser.add_argument('--fresh-independent-audit', type=Path, required=True)
    parser.add_argument('--fresh-output-dir', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(render(args.extracted_tree, args.index, args.index_sha256,
                            args.fresh_independent_audit, args.fresh_output_dir)))
