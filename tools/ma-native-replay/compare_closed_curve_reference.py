"""Compare all closed900 return means to the complete original Fig6 vectors.

No optimizer, RNG, model fitting or surrogate substitution is called. The
geometry standard error describes this supplied100-geometry ensemble only;
it is not an author confidence interval or a full mathematical certificate.
"""
import argparse
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics
import re
import sys

from replay_closed_evidence import replay


NAMES=('MA_ZF','MA_MRT','FPA_ZF','FPA_MRT','FPA_OPT')
DISPLAY={'MA_ZF':'MA-ZF (opt t)','MA_MRT':'MA-MRT (opt t)','FPA_ZF':'FPA-ZF (opt p)',
         'FPA_MRT':'FPA-MRT (opt p)','FPA_OPT':'FPA-OPT (opt W)'}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p,v):
    p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def validate_reference(ref,source_eps):
    assert ref['axis_calibration']['rectangle']==[38,7,425,300]
    colors=((.859,0,.42),(.859,.42,0),(.514,.749,.749),(.69,.718,.745),(.251,.463,.643))
    assert [c['label'] for c in ref['curves']]==list(NAMES)
    for curve,color in zip(ref['curves'],colors):
        assert tuple(curve['rgb'])==color and len(curve['original_all_path_coordinates'])==9
        xy=curve['original_all_path_coordinates']
        assert xy[0][0]==38 and xy[-1][0]==425
        assert curve['x']==[9+(x-38)/387*24 for x,y in xy]
        assert curve['y']==[2+(300-y)/293*36 for x,y in xy]
    if source_eps is not None:
        assert sha(source_eps)==ref['source_sha256']
        sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'strict'))
        from figure_reference import NUMBER,eps_paths
        text=source_eps.read_bytes().decode('latin-1')
        text=re.sub(rf'(?m)^({NUMBER}) GC\s*$',lambda m:' '.join([m[1]]*3)+' RC',text)
        paths=eps_paths(text,[38,7,425,300])
        assert len(paths)==5 and all(p['rgb']==c['rgb'] and p['path_coordinates']==c['original_all_path_coordinates']
            for p,c in zip(paths,ref['curves']))


def run(args):
    if args.output_dir.exists():
        raise FileExistsError('Preserve previous source comparison')
    args.output_dir.mkdir(parents=True)
    replay(args.closed_packet,args.output_dir/'actual-aggregate-packet-replay.json')
    watched={str(p):sha(p) for p in (args.closed_packet/'manifest.json',
        args.closed_packet/'all45-complete-curve-points.json',
        args.closed_packet/'all4500-paired-scheme-aggregates.csv.gz',args.reference,Path(__file__))}
    if args.source_eps is not None:
        watched[str(args.source_eps)]=sha(args.source_eps)
    ref=json.loads(args.reference.read_bytes())
    assert ref['figure']==6 and ref['original_source_points']==45
    assert ref['source_sha256']=='7adf4bfb0a5424a1d3129b809deeab1aad611603e984160d1bf0744f634ecf60'
    assert ref['source_figure_all_legend_colors_and_axes_actually_viewed']
    assert ref['axis_calibration']['x_range']==[9,33] and ref['axis_calibration']['y_range']==[2,38]
    validate_reference(ref,args.source_eps)
    original={c['label']:c for c in ref['curves']}
    assert set(original)==set(NAMES)
    points=json.loads((args.closed_packet/'all45-complete-curve-points.json').read_bytes())
    with gzip.open(args.closed_packet/'all4500-paired-scheme-aggregates.csv.gz','rt',newline='') as stream:
        rows=list(csv.DictReader(stream))
    comparisons=[]
    for name in NAMES:
        source=original[name]
        assert len(source['x'])==len(source['y'])==9
        for j,power in enumerate(range(9,34,3)):
            assert abs(source['x'][j]-power)<=.001*24/387
            point=next(p for p in points if p['scheme']==name and p['point_dBm']==power)
            selected=[r for r in rows if r['scheme']==name and float(r['point_dBm'])==power]
            assert len(selected)==100 and sorted(int(r['realization']) for r in selected)==list(range(100))
            for language in ('Python','MATLAB'):
                values=[float(r[language+'_sample_mean_recomputed']) for r in selected]
                mean=math.fsum(values)/100
                assert abs(mean-point[language+'_mean_sum_rate'])<=1e-12+1e-12*abs(mean)
                deviation=statistics.stdev(values)
                original_y=source['y'][j]
                comparisons.append(dict(scheme=name,language=language,power_dBm=power,
                    original_reference_sum_rate=original_y,complete_mean_sum_rate=mean,
                    actual_geometry_count=100,configured_NLoS_draws_per_geometry=1000,
                    sample_geometry_standard_deviation=deviation,geometry_standard_error=deviation/10,
                    signed_return_minus_source=mean-original_y,absolute_gap=abs(mean-original_y),
                    source_EPS_full_decimal_rounding_step=ref['maximum_ordinate_rounding_step'],
                    gap_exceeds_source_vector_rounding_step=abs(mean-original_y)>ref['maximum_ordinate_rounding_step']))
    summaries=[]
    for language in ('Python','MATLAB'):
        for name in NAMES:
            own=[r for r in comparisons if r['language']==language and r['scheme']==name]
            summaries.append(dict(language=language,scheme=name,original_points=9,
                maximum_absolute_gap=max(r['absolute_gap'] for r in own),
                RMS_gap=math.sqrt(math.fsum(r['signed_return_minus_source']**2 for r in own)/9),
                points_exceeding_source_vector_rounding_step=sum(r['gap_exceeds_source_vector_rounding_step'] for r in own),
                maximum_geometry_standard_error=max(r['geometry_standard_error'] for r in own)))
    orderings=[]
    for j,power in enumerate(range(9,34,3)):
        source_values={name:original[name]['y'][j] for name in NAMES}
        own={language:{r['scheme']:r['complete_mean_sum_rate'] for r in comparisons
             if r['language']==language and r['power_dBm']==power} for language in ('Python','MATLAB')}
        best=max(source_values,key=source_values.get)
        orderings.append(dict(power_dBm=power,original_reference_values=source_values,
            original_best_scheme=best,original_best_minus_MA_ZF=source_values[best]-source_values['MA_ZF'],
            original_MA_ZF_below_another_scheme_beyond_two_EPS_rounding_steps=
                source_values[best]-source_values['MA_ZF']>2*ref['maximum_ordinate_rounding_step'],
            reconstructed_best_schemes={language:max(values,key=values.get) for language,values in own.items()}))
    write(args.output_dir/'original-figure6-vector-reference.json',ref)
    with (args.output_dir/'all90-source-comparisons-and-geometry-variability.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(comparisons[0]));writer.writeheader();writer.writerows(comparisons)
    report=dict(scope='All45 complete closed900 terminal-rate curve points per language versus original author-R2 Fig6 vectors',
        original_source_points_per_language=45,source_curves=5,powers_dBm=list(range(9,34,3)),
        source_version=ref['source_version'],source_EPS_sha256=ref['source_sha256'],
        original_author_EPS_bytes_revalidated_this_run=args.source_eps is not None,
        all_original_vector_coordinates_recalibrated_without_fitting=True,
        source_input_sha256=watched,all900_return_slots_and4500_aggregate_rows_prevalidated=True,
        all45_original_points_per_language_matched_without_interpolation=True,
        geometry_variability='Sample standard deviation across100 complete geometry means; SE=SD/sqrt(100). Not a confidence interval or an author-population uncertainty statement.',
        source_random_inputs_MC_counts_and_initialization_recovered=False,
        source_fitted_gain_noise_geometry_or_index_shift_used=False,
        original_curve_agreement_tolerance_was_prespecified=False,
        maximum_absolute_gap=max(r['absolute_gap'] for r in comparisons),summaries=summaries,comparisons=comparisons,
        all_same_grid_scheme_orderings=orderings,
        supplied_R2_prose_ordering_scope=ref.get('R2_prose_ordering_scope'),
        source_figure_additional_non9dBm_MA_ZF_ranking_exceptions=[r['power_dBm'] for r in orderings
            if r['power_dBm']!=9 and r['original_MA_ZF_below_another_scheme_beyond_two_EPS_rounding_steps']],
        ranking_qualification_is_source_R2_prose_vs_its_EPS_not_an_algorithm_counterexample=True,
        full900_independent_signal_coordinate_FPA_KKT_or_original_reference_or_paper_pass=False,
        optimizer_or_RNG_calls=0)
    render(args.output_dir,original,comparisons)
    assert watched=={p:sha(Path(p)) for p in watched}
    report['source_and_inputs_unchanged']=True
    write(args.output_dir/'actual-all45-original-reference-comparison.json',report)
    print(json.dumps(dict(all_source_points_per_language=45,maximum_absolute_gap=report['maximum_absolute_gap'],
        summaries=summaries,full900_mathematical_or_original_reference_pass=False)),flush=True)
    return report


def render(output,original,rows):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({'font.family':'serif','font.size':9,'svg.fonttype':'none'})
    fig,axes=plt.subplots(1,2,figsize=(10,4.8))
    markers=('o','s','v','>','d')
    for name,marker in zip(NAMES,markers):
        color=original[name]['rgb']
        axes[0].plot(original[name]['x'],original[name]['y'],color=color,marker=marker,markersize=3.5,linewidth=1.2)
        for language,style in (('MATLAB','-'),('Python','--')):
            own=[r for r in rows if r['scheme']==name and r['language']==language]
            axes[1].plot([r['power_dBm'] for r in own],[r['complete_mean_sum_rate'] for r in own],
                color=color,linestyle=style,linewidth=1.2,marker=marker if language=='MATLAB' else None,markersize=3)
            if language=='MATLAB':
                axes[1].errorbar([r['power_dBm'] for r in own],[r['complete_mean_sum_rate'] for r in own],
                    yerr=[r['geometry_standard_error'] for r in own],fmt='none',color=color,capsize=2,linewidth=.7)
    axes[0].set_title('Original author-R2 source vectors')
    axes[1].set_title('Closed900 returns; bars show one geometry SE')
    axes[0].set_ylim(2,38)
    low=min(r['complete_mean_sum_rate']-r['geometry_standard_error'] for r in rows)
    high=max(r['complete_mean_sum_rate']+r['geometry_standard_error'] for r in rows)
    axes[1].set_ylim(min(2,low-.2),max(38,high+.2))
    for ax in axes:
        ax.set_xlim(9,33);ax.set_xticks(list(range(9,34,3)))
        ax.set_xlabel('Maximum transmit power (dBm)');ax.set_ylabel('Ergodic sum rate (bit/s/Hz)')
        ax.grid(True,color='0.88',linewidth=.6);ax.tick_params(direction='in',top=True,right=True)
    handles=[Line2D([0],[0],color=original[n]['rgb'],marker=m,markersize=3,linewidth=1.2,label=DISPLAY[n]) for n,m in zip(NAMES,markers)]
    handles.extend(Line2D([0],[0],color='black',linestyle=s,linewidth=1.2,label=n) for n,s in (('MATLAB','-'),('Python','--')))
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.015),ncol=4,fontsize=8,frameon=True,framealpha=1,facecolor='white')
    fig.suptitle('MA Fig.6: complete source/return comparison; full900 mathematical audit pending',fontsize=10)
    fig.subplots_adjust(left=.07,right=.985,bottom=.24,top=.84,wspace=.28)
    stem=output/'source-vs-complete-returns'
    fig.savefig(stem.with_suffix('.png'),dpi=180);fig.savefig(stem.with_suffix('.svg'));plt.close(fig)
    write(output/'render-receipt.json',dict(source_points=45,reconstructed_points=90,
        original_x_range=[9,33],original_y_range=[2,38],all_computed_means_and_SE_bars_retained=True,
        PNG_sha256=sha(stem.with_suffix('.png')),SVG_sha256=sha(stem.with_suffix('.svg')),
        actual_visual_inspection_completed_by_renderer=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--closed-packet',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--source-eps',type=Path,help='Optional authorized original R2 P_6_4.eps; exact bytes and all vector paths are rechecked when supplied.')
    run(p.parse_args())
