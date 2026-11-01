"""Re-render ten scientific figures solely from the two bundled public JSONs.
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
    for n,(scope,sweep,ids) in FIGS.items():
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
        if scope=='power':note='Saved bank uses terrestrial factor 10 dB; final prose describes both factors 20/0 dB.'
        elif scope=='interference':note='Printed W versus implemented I/N is unresolved; no rescaling or fitted ordinates.'
        else:note='Historical EPS/final-publisher equivalence and reference agreement remain unverified.'
        fig.text(.5,.907,note,ha='center',fontsize=8.4,color='#713b24')
        handles=[Line2D([0],[0],color=co,marker=ma,markersize=3,linewidth=1.1,label=na)
                 for na,co,ma in zip(NAMES,COLORS,MARKERS)]
        handles += [Line2D([0],[0],color='black',linestyle=st,label=la) for la,st in [('Python','-'),('MATLAB','--')]]
        fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.51,.04),ncol=5,fontsize=8,frameon=True)
        stem=figs/f'Fig{n:02d}-corrected-Algorithm3-saved-dual-and-unfitted-author-reference'
        save_figure(fig,stem);rendered.append(dict(figure=n,PNG=str(stem.with_suffix('.png')),SVG=str(stem.with_suffix('.svg'))))

    ref=refs[11];sources={x['label']:x for x in ref['curves']}
    families=['M_AP','M_MR_TTS_TS','S_AP_offset1.25','S_MR_TTS_TS_offset1.25','S_AP_offset2.5','S_MR_TTS_TS_offset2.5']
    colors={f:tuple(next(v['rgb'] for k,v in sources.items() if family(k)==f)) for f in families}
    selected=selections11();need({x[0] for x in selected}==set(sources),'All12 genuine figure11 curves')
    fig,axes=plt.subplots(2,2,figsize=(12.2,8.5))
    fig.subplots_adjust(left=.075,right=.985,top=.855,bottom=.225,wspace=.23,hspace=.38)
    for label,sweep,scheme in selected:
        ids=[x['ordinal'] for x in data['cases'] if x['sweep']==sweep]
        need(len(ids)==12,'All12 original multi/single source samples')
        xs=[byid[i]['value'] for i in ids];row=0 if '_kL20' in label else 1
        source=sources[label];color=colors[family(label)]
        axes[row,0].plot(source['x'],source['y'],color=color,marker='o',markersize=2.5,linewidth=1.15)
        for j,(sx,sy) in enumerate(zip(source['x'],source['y'])):
            reference_rows.append(dict(figure=11,label=label,sample=j,x=sx,y=sy,source='historical_author_EPS_vectors'))
        for language,style,marker in [('python','-','o'),('matlab','--','x')]:
            ys=[byid[i][language]['schemes'][scheme]['min_sinr'] for i in ids]
            axes[row,1].plot(xs,ys,color=color,linestyle=style,marker=marker,markersize=3,linewidth=1.15)
            gaps=np.asarray(ys)-np.asarray(source['y'])
            comparisons.append(dict(figure=11,language=language,label=label,matched_points=12,
                                    maximum_absolute_linear_SINR_gap=float(np.max(abs(gaps))),
                                    RMS_linear_SINR_gap=float(np.sqrt(np.mean(gaps*gaps))),
                                    reference_agreement_tolerance_prespecified=False,reference_PASS=False))
            for j,i in enumerate(ids):
                plotrows.append(dict(figure=11,language=language,label=label,ordinal=i,x=xs[j],minimum_SINR_linear=ys[j],historical_author_EPS_y=source['y'][j]))
    maximum=max(ax.get_ylim()[1] for ax in axes[:,1])
    for row,beta in enumerate((20,0)):
        for column in (0,1):
            basic_axes(axes[row,column],[.01,.12]);axes[row,column].set_xticks([.01,.03,.05,.07,.09,.11,.12])
        axes[row,0].set_ylim(0,14);axes[row,1].set_ylim(0,maximum)
        axes[row,0].set_xlabel('Interference threshold (W, printed in source)')
        axes[row,1].set_xlabel('Supplied normalized interference limit, I/N')
        axes[row,0].set_title(f'Historical author EPS; satellite factor {beta} dB')
        axes[row,1].set_title(f'Corrected saved results; satellite factor {beta} dB')
    names=['Multi: AP-AO','Multi: MR-TTS-TS','Single 1.25°: AP-AO','Single 1.25°: MR-TTS-TS','Single 2.5°: AP-AO','Single 2.5°: MR-TTS-TS']
    handles=[Line2D([0],[0],color=colors[f],linewidth=1.4,label=na) for f,na in zip(families,names)]
    handles += [Line2D([0],[0],color='black',linestyle=st,marker=ma,markersize=3,label=la) for la,st,ma in [('Python','-','o'),('MATLAB','--','x')]]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.53,.055),ncol=3,fontsize=8.8,frameon=True)
    fig.suptitle('Figure 11 candidate | corrected Algorithm 3 and saved AP-AO',fontsize=13,y=.973)
    fig.text(.5,.915,'Historical EPS vectors versus actual saved dual-language curves; no fitted parameters.',ha='center',fontsize=9)
    fig.text(.5,.884,'Printed W and supplied normalized I/N remain unresolved; reference matching is conditional.',ha='center',fontsize=8.8,color='#713b24')
    stem=figs/'Fig11-corrected-Algorithm3-saved-dual-and-unfitted-author-reference';save_figure(fig,stem)
    rendered.append(dict(figure=11,PNG=str(stem.with_suffix('.png')),SVG=str(stem.with_suffix('.svg'))))
    need(len(plotrows)==2064 and len(reference_rows)==1032,'Every computed and historical plotted point retained')
    csv_write(OUT/'Fig2_11_all2064_dual_plotted_ordinates_and_unfitted_reference.csv',plotrows)
    csv_write(OUT/'Fig2_11_all1032_historical_author_EPS_ordinates.csv',reference_rows)
    fresh(OUT/'Fig2_11_unfitted_reference_gaps_no_agreement_PASS.json',dict(curves=comparisons,reference_ordinates_used_by_optimizer=False,
          source='historical author EPS vector reference, final publisher vector equivalence not newly certified',
          source_W_vs_I_over_N_conflict_figures=[4,5,11],power_kappa_R_source_vs_bank_conflict_figures=[2,3],original_reference_or_paper_PASS=False))
    return rendered

def main():
    global OUT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True,help='A new directory for figures and numerical tables')
    args=parser.parse_args()
    OUT=args.output_dir.resolve()
    OUT.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parent
    data=json.loads((root/'all183_dual_corrected_performance_six_reused_two_TS_replaced.json').read_text(encoding='utf-8'))
    refs={int(k):v for k,v in json.loads((root/'historical_author_EPS_vector_references_Fig2_11.json').read_text(encoding='utf-8')).items()}
    need(len(data['cases'])==183,'Complete saved183 performance aggregate')
    render(data,refs)
    print('Rendered ten figures,2064 computed ordinates,1032 historical author EPS ordinates; no scientific computation rerun.')

if __name__=='__main__': main()
