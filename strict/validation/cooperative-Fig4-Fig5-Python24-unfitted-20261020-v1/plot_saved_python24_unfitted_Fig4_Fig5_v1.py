"""Plot only the sealed 192 scalar rows. No scientific solver or sample reader."""
from pathlib import Path
import argparse,csv,hashlib,math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator

HERE=Path(__file__).resolve().parent
CSV=HERE/'Python24_Fig4_Fig5_192_unfitted_original_EPS_ordinates.csv'
CSV_SHA256='0ad38fe5df2df33fbebb1fa5512bf4aa8b0a48cdb34b1ca4ac792d603648facf'
METHODS=('AP-NoRIS','AP-AO','MR-S-NoRIS','MR-S-PA','MR-S-TS','MR-TTS-NoRIS','MR-TTS-PA','MR-TTS-TS')
COLORS=('#0072B2','#D55E00','#009E73','#CC79A7','#E69F00','#56B4E9','#332288','#555555')
MARKERS=('o','s','^','D','v','P','X','h')

def run(output):
    raw=CSV.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=CSV_SHA256:raise ValueError('Sealed scalar CSV changed')
    with CSV.open(encoding='utf8',newline='') as f:rows=list(csv.DictReader(f))
    if len(rows)!=192:raise ValueError('Exactly24 points x8 methods required')
    for r in rows:
        if any(r[k]!='True' for k in ('Python_saved_science_PASS','producer_same_handle_natural0_sourceclosed','result_configuration_and_science_binding_pass')):
            raise ValueError('Only the existing fully science-bound Python rows are plotted')
        for k in ('original_mapped_y_linear_SINR','python_minSINR_linear','signed_difference_from_EPS'):
            if not math.isfinite(float(r[k])):raise ValueError('No missing/nonfinite ordinates may be drawn')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.labelsize':10,'axes.titlesize':12,
        'axes.linewidth':0.8,'xtick.labelsize':9,'ytick.labelsize':9,'legend.fontsize':8,
        'pdf.fonttype':42,'ps.fonttype':42,'savefig.facecolor':'white'})
    made=[]
    for figure,kn in ((4,20),(5,0)):
        fig,(ax,dx)=plt.subplots(2,1,figsize=(8.4,7.2),sharex=True,gridspec_kw={'height_ratios':[2.6,1.]})
        fig.subplots_adjust(left=.11,right=.975,top=.84,bottom=.13,hspace=.09)
        handles=[]
        for method,color,marker in zip(METHODS,COLORS,MARKERS):
            rs=sorted((r for r in rows if int(r['figure'])==figure and r['method']==method),key=lambda r:int(r['ordinal_one_based']))
            if len(rs)!=12 or [int(r['ordinal_one_based']) for r in rs]!=list(range(1,13)):
                raise ValueError('All twelve actual ordinals of each of eight methods required')
            x=list(range(1,13));ref=[float(r['original_mapped_y_linear_SINR']) for r in rs]
            actual=[float(r['python_minSINR_linear']) for r in rs];gap=[float(r['signed_difference_from_EPS']) for r in rs]
            ax.plot(x,ref,color=color,ls='--',lw=1.,marker=marker,ms=4.5,mfc='white',mec=color,mew=.8,alpha=.90,zorder=2)
            ax.plot(x,actual,color=color,ls='-',lw=1.35,marker=marker,ms=3.,mfc=color,mec=color,mew=.6,zorder=3)
            dx.plot(x,gap,color=color,lw=1.05,marker=marker,ms=3.,mfc=color,mec=color,mew=.5)
            handles.append(Line2D([0],[0],color=color,marker=marker,lw=1.2,ms=4,label=method))
        fig.suptitle('Fig. %d: Python saved results vs historical EPS  ($\\kappa_N=%d$ dB)'%(figure,kn),x=.5,y=.988,fontsize=12)
        fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.53,.954),ncol=4,frameon=False,
            columnspacing=1.7,handlelength=2.0,handletextpad=.55)
        ax.legend(handles=[Line2D([0],[0],color='black',ls='-',marker='o',ms=3,lw=1.35,label='Python actual'),
            Line2D([0],[0],color='black',ls='--',marker='o',mfc='white',ms=4.5,lw=1.,label='Historical EPS')],
            loc='upper left',frameon=True,framealpha=.95,borderpad=.5)
        ax.set_ylabel('Minimum user SINR (linear)');ax.set_ylim(bottom=0)
        dx.set_ylabel('Python $-$ EPS\n(linear SINR)');dx.set_xlabel('Paired ordinal (1–12; W ↔ INR mapping unverified)')
        dx.axhline(0,color='.25',lw=.7,zorder=0)
        for axis in (ax,dx):
            axis.set_xlim(.75,12.25);axis.set_xticks(range(1,13));axis.grid(True,color='.88',lw=.5)
            axis.spines['top'].set_visible(False);axis.spines['right'].set_visible(False)
            axis.tick_params(direction='out',length=3,width=.7)
        ax.yaxis.set_major_locator(MaxNLocator(6));dx.yaxis.set_major_locator(MaxNLocator(5))
        dx.ticklabel_format(axis='y',style='plain',useOffset=False)
        fig.text(.11,.037,'Reference gate: not passed. Fixed ordinal pairing; no fitting or unit conversion.',fontsize=8.2,color='.25')
        stem='Fig%d_Python12_all8_unfitted_original_EPS_diagnostic'%figure
        for suffix in ('.png','.pdf'):
            target=output/(stem+suffix)
            if target.exists():raise FileExistsError('Preserve each existing plot output')
            if suffix=='.png':fig.savefig(target,dpi=240)
            else:fig.savefig(target,metadata={'Title':'Saved Python Fig%d unfitted EPS diagnostic'%figure,'Author':'','CreationDate':None,'ModDate':None})
            made.append(str(target))
        plt.close(fig)
    if hashlib.sha256(CSV.read_bytes()).hexdigest()!=CSV_SHA256:raise ValueError('Input CSV changed during plotting')
    print('\n'.join(made))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,default=HERE);a=p.parse_args();run(a.output_dir)
