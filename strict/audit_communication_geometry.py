"""Verify the Fig7 structural contradiction; original EPS is comparison-only.

The entire explicit exporter coordinate transform and axes are checked. No
phase/spacing/angle is fitted to the EPS. The original literal model is tested
independently; a two-element analytic optimum explains the axis correction.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'mis-communications'))
from engine import Model

def audit(source,output):
    text=source.read_text(encoding='latin-1')
    if 'Apache XML Graphics' not in text:raise ValueError('Unsupported exporter')
    reference=[]
    for block in re.findall(r'GS\s+(.*?)\s+GR',text.split('%%EndProlog',1)[-1],re.S):
        points=re.findall(r'^([-+0-9.]+) ([-+0-9.]+) ([ML])$',block,re.M)
        if len(points)<300:continue
        transforms=re.findall(r'\[([^\]]+)\] CT',block)
        if transforms!=['0.75 0 0 0.75 0 -0.25']:
            raise ValueError('Reference axes and all polylines must share the checked coordinate frame')
        path=np.asarray([[float(x),float(y)] for x,y,_ in points])
        if path.shape!=(360,2) or not np.all(np.diff(path[:,0])>0):raise ValueError('Unexpected path structure')
        if not np.all((54-.002<=path[:,0])&(path[:,0]<=478+.002)&(96-.002<=path[:,1])&(path[:,1]<=422+.002)):
            raise ValueError('Out-of-axis vector coordinates')
        reference.append({'label':['MIS pattern1','MIS pattern2','SMS'][len(reference)],
            'x':((path[:,0]-54)*180/424-90).tolist(),'y':((422-path[:,1])*.04/326).tolist()})
    if len(reference)!=3:raise ValueError('Need both MIS paths and SMS')
    # Axes are explicitly evidenced by original ticks and the 10^-2 multiplier.
    for token in ['(-80) t','(80) t','(0.5) t','(4) t','(10) t','(-2) t']:
        if token not in text:raise ValueError('Axis tick or power multiplier missing')
    az=np.linspace(-90,90,360);el=np.full(360,45.)
    cfg=dict(ms1=[2,1],ms2=[1,1],azimuth_deg=az.tolist(),elevation_deg=el.tolist(),
        number_of_targets=360,reference_snr=.01,spacing_over_wavelength=.5,incidence_direction_cosines=[0,0])
    literal=Model(cfg)
    rng=np.random.default_rng(91007)
    states=[{'phi':np.exp(1j*rng.uniform(-np.pi,np.pi,2)),
             'theta':np.exp(1j*rng.uniform(-np.pi,np.pi,1))} for _ in range(12)]
    literal_asymmetry=max(np.max(np.abs(literal.metric(z,'communications')-literal.metric(z,'communications')[::-1])) for z in states)
    # With r=0 and c=0,1, the exponent is beta*sin(az). Fixed target phase
    # centres are midpoints of the paired +/-20 and +/-60 directions.
    corrected=Model(dict(cfg,ms1=[1,2]))
    targetphase=np.pi*np.sin(np.deg2rad(45))*(np.sin(np.deg2rad(20))+np.sin(np.deg2rad(60)))/2
    z={'phi':np.ones(2,dtype=complex),'theta':np.asarray([np.exp(1j*targetphase)])}
    patterns=corrected.metric(z,'communications')
    sms=Model(dict(cfg,ms1=[1,2],ms2=[0,0])).metric({'phi':np.ones(2,dtype=complex),'theta':np.empty(0,dtype=complex)},'communications')[:,0]
    userphases=np.pi*np.sin(np.deg2rad(45))*np.sin(np.deg2rad([-60,-20,20,60]))
    # A beam phase is the pair midpoint; |1+exp(i*delta)|^2
    # is 4*cos(delta/2)^2, giving the extra factor of two here.
    optimum=.04*np.cos((userphases[-1]-userphases[-2])/4)**2
    result={'paper_id':'mis-communications','source_correction_id':'COMM-GEOMETRY-FIG7',
        'scope':'source_structural_and_analytic_audit_NOT_full_6000_start_reproduction',
        'reference_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'reference_axes':{'rectangle':[54,96,478,422],'x_range':[-90,90],'y_range':[0,.04],
                          'explicit_common_transform':[.75,0,0,.75,0,-.25],
                          'tick_and_multiplier_checks_passed':True},
        'original_literal_ms1':[2,1],'corrected_figure_ms1':[1,2],
        'literal_even_symmetry_error_12_independent_phase_states':float(literal_asymmetry),
        'original_MIS_path_asymmetries':[float(np.max(np.abs(np.asarray(curve['y'])-np.asarray(curve['y'])[::-1]))) for curve in reference[:2]],
        'axis_conflict_proved':literal_asymmetry<1e-14 and all(np.max(np.abs(np.asarray(c['y'])-np.asarray(c['y'])[::-1]))>.03 for c in reference[:2]),
        'unfitted_analytic_optimum_minimum_SNR':float(optimum),
        'comparison_grid_note':'Analytic grid has 360 uniform samples; original EPS x has decimal coordinate rounding. All points compared in export order; no fitted parameters.',
        'unfitted_analytic_MIS_max_absolute_errors':[float(np.max(np.abs(patterns[:,i]-np.asarray(reference[i]['y'])))) for i in range(2)],
        'unfitted_analytic_SMS_max_absolute_error':float(np.max(np.abs(sms-np.asarray(reference[2]['y'])))),
        'original_figure_reproduction_certified':False}
    assert result['axis_conflict_proved']
    assert max(result['unfitted_analytic_MIS_max_absolute_errors'])<5e-7
    assert result['unfitted_analytic_SMS_max_absolute_error']<5e-7
    output.mkdir(parents=True,exist_ok=True)
    (output/'geometry-audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    (output/'original-fig7-reference.json').write_text(json.dumps({'paper_id':'mis-communications','figure':7,
        'data_kind':'original_plot_vector_reference_NOT_simulation','source_sha256':result['reference_source_sha256'],
        'curves':reference,'axis_calibration':result['reference_axes']},indent=2)+'\n',encoding='utf-8')
    fig,ax=plt.subplots(figsize=(7.7,4.9),constrained_layout=True)
    for index,curve in enumerate(reference):
        actual=patterns[:,index] if index<2 else sms
        line=ax.plot(az,actual,label=f'Analytic {curve["label"]}')[0]
        ax.plot(curve['x'],curve['y'],'--',color=line.get_color(),alpha=.65,label=f'Original EPS {curve["label"]}')
    ax.set(xlabel='Azimuth (degrees)',ylabel='SNR (linear)',xlim=(-90,90),ylim=(0,.042),
           title='Fig7 axis erratum: unfitted analytic evidence, not a full optimizer bank')
    ax.grid(alpha=.25);ax.legend(fontsize=8)
    fig.savefig(output/'geometry-audit.png',dpi=180);fig.savefig(output/'geometry-audit.svg');plt.close(fig)
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source-eps',type=Path,required=True);parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(audit(args.source_eps,args.output_dir),indent=2))
