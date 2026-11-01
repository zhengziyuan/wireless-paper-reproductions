"""Re-render Figures2 and3 from saved performance and the existing public reference JSON.
No optimizer, sampling, case-return reader, or private-runtime path is used.
The plotting function bodies and constants match the first actual saved-data render.
"""
from pathlib import Path
import argparse, csv, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

NAMES = ('AP-NoRIS','MR-S-NoRIS','MR-TTS-NoRIS','AP-AO',
         'MR-S-PA','MR-TTS-PA','MR-S-TS','MR-TTS-TS')

TS = ('MR-S-TS','MR-TTS-TS')

SIX = tuple(x for x in NAMES if x not in TS)

COLORS = ((.376,.447,.455),(.702,.702,.702),(.439,.384,.2),(.443,.114,.69),
          (.761,.071,.573),(1.,.655,.196),(.373,.741,1.),(.937,.251,.251))

MARKERS = ('^','>','v','o','x','+','s','d')

FIGS = {2:('power','power_kL20',list(range(0,11))),
        3:('power','power_kL0',list(range(11,24))),
        4:('interference','interference_kL20',list(range(24,36))),
        5:('interference','interference_kL0',list(range(36,48))),
        6:('subsurfaces','subsurfaces_kL20',list(range(48,57))),
        7:('subsurfaces','subsurfaces_kL0',list(range(57,66))),
        8:('ground','ground_kL0',list(range(66,81))),
        9:('ground','ground_kL10',list(range(81,96))),
        10:('ground','ground_kL20',list(range(96,111)))}

def need(test, message):
    if not test:
        raise ValueError(message)

def fresh(path, value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')

def csv_write(path, rows):
    need(rows, 'Nonempty numerical table')
    with path.open('x',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def selections11():
    selected=[]
    for beta in (20,0):
        for scheme in ('AP-AO','MR-TTS-TS'):
            tag='AP' if scheme=='AP-AO' else 'MR_TTS_TS'
            selected.append((f'M_{tag}_kL{beta}',f'multi_vs_single_multi_kL{beta}',scheme))
        for offset in (1.25,2.5):
            for scheme in ('AP-AO','MR-TTS-TS'):
                tag='AP' if scheme=='AP-AO' else 'MR_TTS_TS'
                selected.append((f'S_{tag}_kL{beta}_offset{offset}',f'multi_vs_single_single_{offset}_kL{beta}',scheme))
    return selected

def family(label):
    import re
    return re.sub(r'_kL(?:20|0)','',label)

def basic_axes(ax,xrange):
    ax.set_xlim(*xrange);ax.grid(True,color='0.87',linewidth=.6)
    ax.tick_params(direction='in',top=True,right=True)
    ax.set_ylabel('Minimum LU SINR (linear)')

def save_figure(fig, stem):
    for suffix in ('.png','.svg'):
        need(not stem.with_suffix(suffix).exists(),'Keep earlier plot outputs')
    fig.savefig(stem.with_suffix('.png'),dpi=180)
    fig.savefig(stem.with_suffix('.svg'),metadata={'Date':None})
    plt.close(fig)

def render(data,refs):
    byid={x['ordinal']:x for x in data['cases']}
    plt.rcParams.update({'font.family':'serif','font.size':9,'axes.labelsize':9,'axes.titlesize':10,
                         'xtick.labelsize':8,'ytick.labelsize':8,'svg.fonttype':'none'})
    figs=OUT/'figures';figs.mkdir()
    rendered=[];plotrows=[];comparisons=[];reference_rows=[]
    for n,(scope,sweep,ids) in ((n,FIGS[n]) for n in (2,3)):
        ref=refs[n];sources={x['label']:x for x in ref['curves']}
        need(set(sources)==set(NAMES),'All eight genuine author vector curves')
        need(all(byid[i]['sweep']==sweep for i in ids),'Figure/source-index sweep mapping')
        xs=[byid[i]['value'] for i in ids]
        fig,axes=plt.subplots(1,2,figsize=(11,5.15))
        fig.subplots_adjust(left=.067,right=.987,bottom=.29,top=.84,wspace=.27)
        for name,color,marker in zip(NAMES,COLORS,MARKERS):
            source=sources[name];need(len(source['y'])==len(ids),'No missing author vector ordinate')
            axes[0].plot(source['x'],source['y'],color=color,marker=marker,markersize=3.3,linewidth=1.15)
            for j,(sx,sy) in enumerate(zip(source['x'],source['y'])):
                reference_rows.append(dict(figure=n,label=name,sample=j,x=sx,y=sy,source='historical_author_EPS_vectors'))
            for language,style in (('python','-'),('matlab','--')):
                ys=[byid[i][language]['schemes'][name]['min_sinr'] for i in ids]
                axes[1].plot(xs,ys,color=color,linestyle=style,marker=marker if language=='matlab' else None,
                             markersize=3,linewidth=1.15)
                gaps=np.asarray(ys)-np.asarray(source['y'])
                comparisons.append(dict(figure=n,language=language,label=name,matched_points=len(ids),
                                        maximum_absolute_linear_SINR_gap=float(np.max(abs(gaps))),
                                        RMS_linear_SINR_gap=float(np.sqrt(np.mean(gaps*gaps))),
                                        reference_agreement_tolerance_prespecified=False,reference_PASS=False))
                for j,i in enumerate(ids):
                    plotrows.append(dict(figure=n,language=language,label=name,ordinal=i,x=xs[j],
                                         minimum_SINR_linear=ys[j],historical_author_EPS_y=source['y'][j]))
        for ax in axes:basic_axes(ax,ref['axis_calibration']['x_range'])
        axes[0].set_ylim(*ref['axis_calibration']['y_range']);axes[1].set_ylim(bottom=0)
        if scope=='power':labels=('Per-LEO transmit power $P_T$ (W)',)*2
        elif scope=='interference':labels=('Interference threshold (W, printed in source)','Supplied normalized interference limit, I/N')
        elif scope=='subsurfaces':labels=('RIS subsurface count $M$',)*2
        else:labels=(r'RIS-to-LU Rician factor $\kappa_R$ (dB)',)*2
        for ax,label in zip(axes,labels):ax.set_xlabel(label)
        axes[0].set_title('Historical author EPS vectors')
        axes[1].set_title('Corrected Algorithm 3; saved dual-language results')
        kappa=byid[ids[0]]['full_reported_scene']['kappa_leo_db']
        fig.suptitle(f'Figure {n} candidate | satellite Rician factor {kappa} dB',y=.975,fontsize=12)
        if scope=='power':note=f'Final-source both Rician factors {kappa} dB; all8 methods fresh. Configured1000 draws validate moments only.\nCurves are single-configuration optimized results; author moment sample count remains unreported.'
        elif scope=='interference':note='Printed W versus implemented I/N is unresolved; no rescaling or fitted ordinates.'
        else:note='Historical EPS/final-publisher equivalence and reference agreement remain unverified.'
        fig.text(.5,.907,note,ha='center',fontsize=8.0,color='#713b24')
        handles=[Line2D([0],[0],color=co,marker=ma,markersize=3,linewidth=1.1,label=na)
                 for na,co,ma in zip(NAMES,COLORS,MARKERS)]
        handles += [Line2D([0],[0],color='black',linestyle=st,label=la) for la,st in [('Python','-'),('MATLAB','--')]]
        fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.51,.04),ncol=5,fontsize=8,frameon=True)
        stem=figs/f'Fig{n:02d}-corrected-Algorithm3-saved-dual-and-unfitted-author-reference'
        save_figure(fig,stem);rendered.append(dict(figure=n,PNG=str(stem.with_suffix('.png')),SVG=str(stem.with_suffix('.svg'))))

    need(len(rendered)==2 and len(plotrows)==384 and len(reference_rows)==192,'All fresh24 full8 dual plotted values and unchanged reference ordinates')
    csv_write(OUT/'Fig2_Fig3_all384_fresh_dual_plotted_ordinates_and_unfitted_reference.csv',plotrows)
    csv_write(OUT/'Fig2_Fig3_all192_historical_author_EPS_ordinates.csv',reference_rows)
    fresh(OUT/'Fig2_Fig3_unfitted_reference_gaps_no_agreement_PASS.json',dict(curves=comparisons,
        reference_ordinates_used_by_optimizer=False,reference='Existing historical author EPS vector extraction, final publisher equivalence remains unverified',
        reference_pairing='Method label plus original ascending sample order; both original source x and configured x retained without fitting',
        final_source_kappa_ground_db20_and0_executed=True,
        configured1000_draws_are_channel_moment_validation_not_performance_MC_average=True,
        author_moment_sample_count_recovered=False,original_reference_or_paper_PASS=False))
    return rendered

def execute(data_path,reference_path,output):
    import hashlib
    global OUT
    data_path=Path(data_path);reference_path=Path(reference_path);OUT=Path(output).resolve()
    raw=data_path.read_bytes();data=json.loads(raw)
    need(data.get('all48_case_lanes_four_actual_saved_gate_closures_admitted') is True,'Do not render an unclosed/partial curve as complete')
    need([row['ordinal'] for row in data['cases']]==list(range(24)),'Exactly the new24, no old183 read')
    source=reference_path.read_bytes()
    need(hashlib.sha256(source).hexdigest()=='30aaef7c01dd07567208c1b3f977202cb874b94543dcbdc2e259fce504a45237','Reuse exact existing reference, do not reextract EPS')
    refs={int(key):value for key,value in json.loads(source).items()}
    OUT.mkdir(parents=True,exist_ok=False)
    rendered=render(data,refs)
    report=dict(rendered=rendered,actual_figures=2,actual_computed_ordinates=384,actual_historical_reference_ordinates=192,
        data_SHA256=hashlib.sha256(raw).hexdigest(),reference_SHA256=hashlib.sha256(source).hexdigest(),
        old183_aggregate_or_case_reads=0,new_optimizer_MC_RNG_or_MP_calls=0,
        reference_fitting_or_original_reference_PASS=False,
        visual_layout_review_pending_after_first_true_render=True)
    fresh(OUT/'ACTUAL_FIG2_FIG3_RENDER_FROM_NEW24_ONLY_SCOPE_V1.json',report)
    return report

def main():
    parser=argparse.ArgumentParser(description='Only final-source corrected Fig2/3 from a completed new24 aggregate')
    parser.add_argument('--data',type=Path,required=True);parser.add_argument('--reference',type=Path,required=True);parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();execute(args.data,args.reference,args.output_dir)

if __name__=='__main__':main()
