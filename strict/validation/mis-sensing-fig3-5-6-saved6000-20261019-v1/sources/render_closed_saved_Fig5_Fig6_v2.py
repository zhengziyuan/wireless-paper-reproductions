"""PREPARED display-only Figures5/6 from three closed assembly outputs.

Never opens a native bank/payload/receipt, computes a physical field, or calls
an optimizer/RNG/MP gate. Exact zeros have axis markers, not epsilon ordinates.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import sys


def load_bound(path, expected):
    if not isinstance(expected, str) or len(expected) != 64:
        raise ValueError('All three closed input SHA256 identities must be explicit')
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected:
        raise ValueError(f'Closed rendering input identity differs: {path.name}')
    return json.loads(raw), {'file': str(path.resolve()), 'SHA256': digest, 'bytes': len(raw)}


def put(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('A stored curve ordinate is nonnumeric/nonfinite')
    return float(value)


def validate(summary, curves, selected):
    if summary.get('scoped_assembly_pass') is not True or summary.get('complete6000_figure_input_assembly') is not True:
        raise ValueError('Refuse final render from an unclosed/partial figure-input assembly')
    if summary.get('valid_cases') != 6000 or summary.get('retained_counts_match_closed5280_720') is not True:
        raise ValueError('Refuse a population/subset mismatch')
    if summary.get('saved_combined_true') != 5280 or summary.get('saved_combined_false') != 720:
        raise ValueError('The720 retained false flags must not be removed or upgraded')
    if summary.get('prepared_code_before_after_equal') is not True or summary.get('missing_or_invalid_slots') != []:
        raise ValueError('Assembly source/input closure is incomplete')
    if curves.get('complete') is not True or selected.get('selection_complete_over6000') is not True or selected.get('provisional_if_population_incomplete') is not False:
        raise ValueError('Refuse a provisional selected initialization')
    n = selected['best']['original_start']
    if n != summary['fixed_selected_original_start'] or n != curves['selected_original_start']:
        raise ValueError('Figures5/6 do not bind the same fixed selected initialization')
    if summary['source_basis'] != selected['source_basis'] or summary['prepared_plan_identity'] != selected['prepared_plan_identity']:
        raise ValueError('Assembly inputs do not share their exact closed source/plan basis')
    policy = 'frozen_v5_relaxed_primal_max_final_eta_strict_gt_earliest_tie'
    if summary.get('implementation_selection_policy') != policy or selected.get('implementation_selection_policy') != policy:
        raise ValueError('Fixed frozen implementation policy mismatch')
    rows = curves['curves']
    if len(rows) != 30 or [row['outer_iteration'] for row in rows] != list(range(1, 31)):
        raise ValueError('Exactly30 original configured outer slots are required')
    if any(row['number_of_starts_accumulated'] != 6000 for row in rows):
        raise ValueError('All6000, including720 false, must contribute to every mean')
    history = selected['best']['history']
    if not 1 <= len(history) <= 30:
        raise ValueError('Actual selected history is missing')
    values = {key: [finite(row[key]) for row in rows] for key in
              ('mean_eta', 'selected_eta', 'mean_maximum_positive_q', 'selected_maximum_positive_q')}
    if any(value < 0 for key in ('mean_maximum_positive_q','selected_maximum_positive_q') for value in values[key]):
        raise ValueError('Stored maximum-positive residual is negative')
    for j, row in enumerate(rows):
        original = history[min(j, len(history) - 1)]
        if row['selected_eta'] != original['eta'] or row['selected_maximum_positive_q'] != original['maximum_positive_q']:
            raise ValueError('Selected displayed curve is not its actual/explicitly held history')
        if row['selected_point_derived_hold_last'] is not (j >= len(history)):
            raise ValueError('Selected actual-versus-derived-hold label mismatch')
    return n, len(history), values


def render(args):
    here = Path(__file__).resolve().parent
    plan_path = here / 'PREPARED_FIG5_FIG6_CLOSED_OUTPUT_ONLY_RENDER_PLAN_V2.json'
    plan_raw = plan_path.read_bytes()
    plan_digest = hashlib.sha256(plan_raw).hexdigest()
    plan = json.loads(plan_raw)
    admission = json.loads(args.admission.read_bytes())
    if admission.get('root_reviewed_saved_fig5_fig6_display_only') is not True or admission.get('prepared_plan_SHA256') != plan_digest:
        raise ValueError('Reviewed display-only plan admission missing')
    code_before = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_before != plan['renderer_SHA256']:
        raise ValueError('Prepared renderer source changed')
    expected = admission['input_SHA256']
    summary, summary_id = load_bound(args.summary, expected['summary'])
    curves, curves_id = load_bound(args.curves, expected['curves'])
    selected, selected_id = load_bound(args.selected, expected['selected'])
    n, actual_length, values = validate(summary, curves, selected)
    # Explicit E-data output, separate from the three closed read-only inputs.
    output = args.output.resolve()
    if not output.is_relative_to(args.data_root.resolve()) or output.exists():
        raise ValueError('Use a fresh output directory under explicit E data root')
    output.mkdir(parents=True)
    args._created_output_this_action = output
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    x = np.arange(1, 31)
    selected_certificate = selected['best']['saved_combined_convergence_feasibility']
    selected_label = f'Fixed selected #{n} (original combined={str(selected_certificate).lower()})'
    mean_label = 'All6000 starts (720 retained false)'
    short_history_count = len(summary['actual_short_history_lengths'])
    history_note = (
        'All6000 saved histories contain30 actual outer iterations; no derived hold was applied.'
        if short_history_count == 0 else
        f'{short_history_count} saved histories end before30; later mean contributions hold the last state (derived).'
    )
    foot = ('Frozen implementation output; author selection/norm/normalization not recovered.\n' +
            history_note + '\nReference and dual-language gates pending.')
    fig, ax = plt.subplots(figsize=(7.6, 4.9), constrained_layout=True)
    ax.plot(x[:actual_length], values['selected_eta'][:actual_length], color='C0', label=selected_label)
    if actual_length < 30:
        ax.plot(x[actual_length-1:], values['selected_eta'][actual_length-1:], color='C0', linestyle='--', label='Selected: derived hold after actual stop')
    ax.plot(x, values['mean_eta'], color='C1', label=mean_label)
    ax.set(xlabel='Outer iteration', ylabel='Eta (linear)', title='Figure5 variables from the closed saved population', xlim=(1,30))
    ax.grid(True, alpha=.25)
    ax.legend(fontsize=8)
    fig.supxlabel(foot, fontsize=7)
    for extension in ('png','pdf','svg'):
        fig.savefig(output / f'Fig5-saved-fixed-selection.{extension}', dpi=200)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.6, 4.9), constrained_layout=True)
    zero_ids = {}
    positive_present = False
    for key, color, label in (('selected_maximum_positive_q','C0',selected_label),
                              ('mean_maximum_positive_q','C1',mean_label)):
        y = np.asarray(values[key], dtype=float)
        positive = y > 0
        positive_present = positive_present or bool(np.any(positive))
        # Nonpositive samples are gaps on a logarithmic axis, never epsilon.
        shown = np.where(positive, y, np.nan)
        if key.startswith('selected'):
            ax.plot(x[:actual_length], shown[:actual_length], color=color, marker='o', markersize=3.5, label=label)
            if actual_length < 30:
                ax.plot(x[actual_length-1:], shown[actual_length-1:], color=color, linestyle='--', marker='o', markersize=3.5, label='Selected: derived hold')
        else:
            ax.plot(x, shown, color=color, marker='o', markersize=3.5, label=label)
        zeros = x[y == 0]
        zero_ids[key] = zeros.tolist()
        if len(zeros):
            ax.plot(zeros, np.zeros(len(zeros)), transform=ax.get_xaxis_transform(), linestyle='none',
                    marker='v', color=color, clip_on=False, label=f'{label}: exact zero (axis markers)')
    ax.set_yscale('log')
    if not positive_present:
        # A pure display frame, with no numeric log ordinates or fake samples.
        ax.set_ylim(1,10)
        ax.set_yticks([])
        ax.text(.5,.5,'All stored residuals are exactly zero; no positive log ordinates',
                transform=ax.transAxes, ha='center', va='center', fontsize=9)
    ax.set(xlabel='Outer iteration', ylabel='Maximum positive q residual (log display)',
           title='Figure6 variables from the same fixed selection', xlim=(0.75,30.25))
    ax.grid(True, alpha=.25)
    ax.legend(fontsize=7)
    fig.supxlabel(foot + '\nExact zeros: bottom-axis markers only; no epsilon floor or substituted residual.', fontsize=7)
    for extension in ('png','pdf','svg'):
        fig.savefig(output / f'Fig6-saved-fixed-selection.{extension}', dpi=200)
    plt.close(fig)
    identities_before = {'summary':summary_id,'curves':curves_id,'selected':selected_id}
    identities_after = {}
    for key, path in (('summary',args.summary),('curves',args.curves),('selected',args.selected)):
        _, identities_after[key] = load_bound(path, expected[key])
    code_after = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report = {'scope':'actual_display_only_from_three_closed_saved_assembly_outputs',
              'ended_UTC':dt.datetime.now(dt.timezone.utc).isoformat(),'prepared_plan_SHA256':plan_digest,
              'input_before':identities_before,'input_after':identities_after,'source_before_SHA256':code_before,
              'source_after_SHA256':code_after,'source_and_input_unchanged':code_before==code_after and identities_before==identities_after,
              'selected_original_start':n,'actual_selected_history_length':actual_length,
              'selected_saved_combined_certificate_retained':selected['best']['saved_combined_convergence_feasibility'],
              'mean_population':6000,'retained_combined_false':720,
              'short_history_contributions':len(summary['actual_short_history_lengths']),
              'Fig6_exact_zero_outer_iterations':zero_ids,'zero_display':'axis-coordinate markers; no positive epsilon substitution',
              'Fig6_positive_display':'small circular markers on all positive stored samples, including isolated/endpoints',
              'history_display_note':history_note,'original_combined_certificate_in_selected_legend':True,
              'stored_data_modified':False,'native_bank_or_receipts_or_payloads_read':False,
              'optimizer_RNG_MC_MP_or_deterministic_beam_evaluator_called':False,
              'human_visual_review_complete':False,'original_reference_gate':False,'dual_language_gate':False,
              'all6000_original_convergence_pass':False,'all_paper_figures_tables_complete':False}
    put(output/'display-provenance.json',report)
    return 0 if report['source_and_input_unchanged'] else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('summary','curves','selected','output','data-root','admission'):
        parser.add_argument('--'+key, type=Path, required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args(argv)
    if not args.execute:
        parser.error('Prepared only: explicit reviewed display action required')
    try:
        return render(args)
    except BaseException as error:
        owned = getattr(args,'_created_output_this_action',None)
        if owned is not None and not (owned/'failed-display-action.json').exists():
            try:
                put(owned/'failed-display-action.json',{'error_type':type(error).__name__,'error':str(error),'outputs_may_be_partial':True,'not_numerical_acceptance':True})
            except Exception:
                pass
        raise


if __name__ == '__main__':
    sys.exit(main())
