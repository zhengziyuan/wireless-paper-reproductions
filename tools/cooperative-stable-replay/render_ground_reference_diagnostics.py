"""Show all original ground-factor points beside both reconstructed returns.

Original nonzero vertical minima are preserved. The reconstructed panel has
its own explicit nonnegative scale so no computed ordinate is clipped to the
author's range. No source ordinate is used by an optimizer or fitted model.
"""
import argparse
from pathlib import Path

import numpy as np

from audit_native_case import sha
from build_power_curve_views import NAMES, read, require, write
from compare_power_references import COLORS, LABELS


def run(directory):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    target = directory/'source-comparison'
    require(not target.exists(), 'Preserve prior rendered diagnostics')
    index = read(directory/'final-state-index.json')
    require(index['case_scope']=='ground' and index['expected_case_ordinals']==list(range(66,111)),
            'All three exact15-point source cohorts required')
    report = read(directory/'independent-all720-final-states-MP80-MP100.json')
    require(report['all_final_states_physics_and_precision_pass'] and report['actual_final_states_per_precision']==720,
            'All720 actual final states must pass independent final physics first')
    views = {language:read(directory/(language+'-curve-view.json')) for language in ('python','matlab')}
    require(all(len(v['results'])==45 for v in views.values()),'All45 slots per language required')
    target.mkdir()
    plt.rcParams.update({'font.family':'serif','font.size':9,'axes.labelsize':9,'axes.titlesize':9,
                         'xtick.labelsize':8,'ytick.labelsize':8,'svg.fonttype':'none'})
    markers = ('^','>','v','o','x','+','s','d')
    rows = []
    for figure,kappa,ymin,ymax in ((8,0,1,4),(9,10,2,6.5),(10,20,2.5,7.5)):
        source_path = directory/f'reference-comparison/original-figure-{figure}-vector-reference.json'
        source = read(source_path)
        calibration = source['axis_calibration']
        require(calibration['x_range']==[-12,30] and calibration['y_range']==[ymin,ymax],
                'Original source axes, including nonzero minimum, must stay unchanged')
        original = {c['label']:c for c in source['curves']}
        require(set(original)==set(LABELS)==set(NAMES),'Every original source legend required')
        fig,axes = plt.subplots(1,2,figsize=(10,4.8))
        numeric = {}
        for label,color,marker in zip(LABELS,COLORS,markers):
            ref = original[label]
            require(len(ref['x'])==len(ref['y'])==15,'Every original vector point required')
            axes[0].plot(ref['x'],ref['y'],color=color,marker=marker,markersize=3.5,linewidth=1.2)
            numeric[label] = {}
            for language,style in (('matlab','-'),('python','--')):
                points = [p for p in views[language]['results'] if p['sweep']==f'ground_kL{kappa}']
                require([p['value'] for p in points]==list(range(-12,31,3)),'Missing or reordered original slot')
                values = [float(np.min(p['schemes'][label]['evaluation']['sinr'])) for p in points]
                require(np.isfinite(values).all() and min(values)>0,'All positive actual returns required')
                axes[1].plot([p['value'] for p in points],values,color=color,linestyle=style,linewidth=1.2,
                    marker=marker if language=='matlab' else None,markersize=3)
                numeric[label][language] = values
        axes[0].set_ylim(ymin,ymax)
        axes[1].set_ylim(bottom=0)
        axes[0].set_title('Author thesis EPS; publisher equivalence unverified')
        axes[1].set_title('Reconstructed inputs; source agreement unverified')
        for ax in axes:
            ax.set_xlim(-12,30)
            ax.set_xticks(list(range(-12,31,6)))
            ax.set_xlabel(r'RIS-to-LU Rician factor $\kappa_R$ (dB)')
            ax.set_ylabel('Minimum SINR (linear)')
            ax.grid(True,color='0.87',linewidth=.6)
            ax.tick_params(direction='in',top=True,right=True)
        handles = [Line2D([0],[0],color=color,marker=marker,markersize=3,linewidth=1.2,label=name)
                   for name,color,marker in zip(LABELS,COLORS,markers)]
        handles += [Line2D([0],[0],color='black',linestyle=style,linewidth=1.2,label=language)
                    for language,style in (('MATLAB','-'),('Python','--'))]
        fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.015),ncol=5,
                   frameon=True,facecolor='white',framealpha=1,fontsize=8)
        fig.suptitle(r'Ground-factor sweep, $\kappa_L='+str(kappa)+r'\,\mathrm{dB}$',fontsize=10)
        fig.subplots_adjust(left=.07,right=.985,bottom=.25,top=.85,wspace=.28)
        stem = target/f'ground-factor-source-vs-reconstructed-{figure}'
        fig.savefig(stem.with_suffix('.png'),dpi=180)
        fig.savefig(stem.with_suffix('.svg'))
        plt.close(fig)
        row = dict(figure=figure,kappa_leo_db=kappa,source_vector_sha256=sha(source_path),
            original_x_range=[-12,30],original_y_range=[ymin,ymax],nonzero_source_y_minimum_retained=True,
            source_points=120,reconstructed_points=240,all_reconstructed_ordinates_retained=True,
            reconstructed_curves=numeric,reconstructed_axis_uses_separate_nonnegative_scale=True,
            source_numbers_used_by_solver_or_fitted_parameters=False,original_curve_or_full_paper_pass=False,
            PNG_sha256=sha(stem.with_suffix('.png')),SVG_sha256=sha(stem.with_suffix('.svg')))
        write(stem.with_suffix('.json'),row)
        rows.append(row)
    write(target/'render-receipt.json',dict(scope='Three complete original ground-factor source panels and both real reconstructed curves',
        figures=rows,renderer_sha256=sha(Path(__file__)),all360_source_and720_reconstructed_ordinates_present=True,
        visual_inspection_completed_by_renderer=False,optimizer_or_RNG_calls=0,original_reference_or_full_paper_pass=False))
    print(dict(figures=[8,9,10],source_points=360,reconstructed_points=720,original_agreement_certified=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory',type=Path,required=True)
    run(p.parse_args().directory)
