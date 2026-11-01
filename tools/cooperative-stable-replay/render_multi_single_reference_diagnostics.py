"""Render all12 original figure11 curves with explicit unresolved x-axis units."""
import argparse
from pathlib import Path
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

from audit_native_case import sha
from build_power_curve_views import read, require, write
from compare_multi_single_reference import selections, validate_reference


def flat(document):
    if 'panels' in document:
        require(len(document['panels']) == 1, 'One complete original figure11 panel required')
        return document['panels'][0]['curves']
    return document['curves']


def family(label):
    return re.sub(r'_kL(?:20|0)', '', label)


def draw(reference, simulations, stem, full72_final_physics_checked=False):
    """Also supports a clearly labeled Python-only layout preflight."""
    require(not any(stem.with_suffix(s).exists() for s in ('.png','.svg','.json')),
            'Preserve previous plot and numerical metadata')
    validate_reference(reference)
    languages = tuple(simulations)
    require(languages in (('python',), ('python','matlab')), 'Explicit actual language scope required')
    require(not full72_final_physics_checked or languages == ('python','matlab'),
            'Complete paired physics requires both actual languages')
    sources = {c['label']:c for c in reference['curves']}
    computed = {language:{c['label']:c for c in flat(doc)} for language,doc in simulations.items()}
    wanted = {label for label,_,_ in selections()}
    for curves in computed.values():
        require(set(curves) == wanted and all(len(c['x']) == len(c['y']) == 12 for c in curves.values()),
                'All144 original-matched computed ordinates per actual language required')
        require(all(np.isfinite(c['y']).all() and np.min(c['y']) >= 0 for c in curves.values()),
                'Every actual nonnegative computed ordinate must remain visible')
    families = ['M_AP','M_MR_TTS_TS','S_AP_offset1.25','S_MR_TTS_TS_offset1.25',
                'S_AP_offset2.5','S_MR_TTS_TS_offset2.5']
    names = ['Multi: AP-AO','Multi: MR-TTS-TS','Single 1.25°: AP-AO',
             'Single 1.25°: MR-TTS-TS','Single 2.5°: AP-AO','Single 2.5°: MR-TTS-TS']
    colors = {}
    for f in families:
        pair = [c for label,c in sources.items() if family(label) == f]
        require(len(pair) == 2 and pair[0]['rgb'] == pair[1]['rgb'], 'Original paired legend colors differ')
        colors[f] = tuple(pair[0]['rgb'])
    require(len(set(colors.values())) == 6, 'Every original scenario/scheme color must remain distinct')
    largest = max(float(np.max(c['y'])) for curves in computed.values() for c in curves.values())
    right_max = largest*1.10 if largest>0 else 1.
    plt.rcParams.update({'font.size':9.5,'axes.labelsize':10,'axes.titlesize':11,
                         'svg.fonttype':'none','axes.unicode_minus':True})
    fig, axes = plt.subplots(2,2,figsize=(12.2,8.5))
    fig.subplots_adjust(left=.075,right=.985,top=.855,bottom=.225,wspace=.23,hspace=.38)
    for row,beta in enumerate((20,0)):
        for label,source in sources.items():
            if f'_kL{beta}' not in label:
                continue
            f = family(label)
            axes[row,0].plot(source['x'],source['y'],color=colors[f],
                linestyle='-' if beta==20 else '--',marker='o',markersize=2.5,linewidth=1.15)
            for language in languages:
                curve = computed[language][label]
                axes[row,1].plot(curve['x'],curve['y'],color=colors[f],
                    linestyle='-' if language=='python' else '--',
                    marker='o' if language=='python' else 'x',
                    markersize=3 if language=='python' else 4,linewidth=1.15,
                    markeredgewidth=.75)
        for column in (0,1):
            ax = axes[row,column]
            ax.set_xlim(.01,.12)
            ax.set_xticks([.01,.03,.05,.07,.09,.11,.12])
            ax.grid(True,alpha=.22,linewidth=.6)
            ax.set_ylabel('Minimum SINR (linear)')
        axes[row,0].set_ylim(0,14)
        axes[row,1].set_ylim(0,right_max)
        axes[row,0].set_xlabel('Interference threshold (W, as printed in source)')
        axes[row,1].set_xlabel('Supplied normalized interference limit, I/N')
        axes[row,0].set_title(f'Original source: satellite Rician factor {beta} dB')
        axes[row,1].set_title(f'Reconstructed returns: satellite Rician factor {beta} dB')
    handles = [Line2D([0],[0],color=colors[f],linewidth=1.5,label=name)
               for f,name in zip(families,names)]
    handles += [Line2D([0],[0],color='black',linestyle='-' if lang=='python' else '--',
                marker='o' if lang=='python' else 'x',markersize=3,label=lang.upper()) for lang in languages]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.53,.055),ncol=3,
               fontsize=8.8,frameon=True,columnspacing=1.6,handlelength=2.2)
    subtitle = ('All72 paired source cases; independent final physics checked' if full72_final_physics_checked
                else 'Saved Python returns only; complete native comparison and full72 physics remain pending')
    fig.suptitle('Original figure11 and complete stored source-matched curves',fontsize=13,y=.973)
    fig.text(.5,.925,subtitle,ha='center',fontsize=10)
    fig.text(.5,.894,'The printed W axis and supplied normalized I/N remain unresolved; horizontal pairing is conditional.',
             ha='center',fontsize=9,color='#713b24')
    stem.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(stem.with_suffix('.png'),dpi=180)
    fig.savefig(stem.with_suffix('.svg'),metadata={'Date':None})
    plt.close(fig)
    write(stem.with_suffix('.json'),dict(
        source_figure=11,actual_languages=list(languages),source_original_y_range=[0,14],
        reconstructed_y_range=[0,right_max],source_points=144,reconstructed_points=144*len(languages),
        all12_original_curves_and_all_actual_computed_points_retained=True,
        source_interference_W_versus_normalized_I_over_N_conflict_unresolved=True,
        original_reference_comparison_is_conditional=True,
        complete72_paired_final_physics_checked=full72_final_physics_checked,
        original_reference_or_full183_or_paper_pass=False,
        source_curves=reference['curves'],reconstructed_curves=computed,
        PNG_sha256=sha(stem.with_suffix('.png')),SVG_sha256=sha(stem.with_suffix('.svg')),
        renderer_SHA256=sha(Path(__file__)),optimizer_or_RNG_calls=0))
    return stem.with_suffix('.json')


def run(directory):
    math = read(directory/'independent-all1152-final-states-MP80-MP100.json')
    require(math['all_final_states_physics_and_precision_pass'] and
            math['actual_final_states_per_precision']==1152 and math['scalar_field_coordinates_per_precision']==7680,
            'Wait for every complete actual original paired physical state')
    reference_path = directory/'reference-comparison/original-figure-11-vector-reference.json'
    paths = [reference_path, directory/'independent-all1152-final-states-MP80-MP100.json', Path(__file__)]
    simulations = {}
    for language,i in (('python',2),('matlab',3)):
        view_path = directory/(language+'-curve-view.json')
        require(math['source_input_sha256'][f'{i}:{view_path.name}']==sha(view_path),
                'Complete math receipt does not bind this actual language view')
        view = read(view_path)
        figure = directory/language/'cooperative-satcom-figure-11.json'
        document = read(figure)
        curves = {c['label']:c for c in flat(document)}
        for label,sweep,scheme in selections():
            selected = [p for p in view['results'] if p['sweep']==sweep]
            require(len(selected)==12 and curves[label]['x']==[p['value'] for p in selected] and
                    curves[label]['y']==[float(np.min(p['schemes'][scheme]['evaluation']['sinr'])) for p in selected],
                    'A plotted ordinate differs from the complete physical return')
        simulations[language] = document
        paths.extend((view_path,figure))
    before = {str(p):sha(p) for p in paths}
    result = draw(read(reference_path),simulations,directory/'source-comparison/multi-single-source-vs-reconstructed',True)
    require(before=={str(p):sha(p) for p in paths},'A bound scientific input or renderer changed')
    print(dict(output=str(result),source_points=144,computed_points=288,source_units_unresolved=True),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory',type=Path,required=True)
    run(p.parse_args().directory)
