"""Saved ISAC NoRIS rate, sensing, and total rotation-gradient diagnostic.

No optimization, source code import, random channel sampling or trajectory generation.
The channel is re-evaluated from saved path parameters at perturbations.
"""
from argparse import ArgumentParser
from pathlib import Path
import json, decimal
import numpy as np
D=decimal.Decimal
decimal.getcontext().prec=50
a=ArgumentParser();a.add_argument('--input-dir',type=Path,required=True);a.add_argument('--output',type=Path,required=True);args=a.parse_args()
scene=json.loads((args.input_dir/'scene.json').read_text(encoding='utf-8'))
with np.load(args.input_dir/'operands.npz',allow_pickle=False) as z:
    if set(z.files)!={'w','r','fc','jac_comm_rotation','fs','jac_sens_rotation','pd','p'}:raise ValueError('unexpected array inventory')
    w=z['w'].copy();angles=z['r'].copy();field=z['fc'].copy();jac=z['jac_comm_rotation'].copy();fs=z['fs'].copy();js=z['jac_sens_rotation'].copy();pd=z['pd'].copy();saved_p=z['p'].copy()
if (w.shape,angles.shape,field.shape,jac.shape)!=((4,6),(6,),(4,2),(4,2,3)):raise ValueError('unexpected shapes')
if (fs.shape,js.shape,pd.shape,saved_p.shape)!=((4,66),(4,66,3),(66,),(66,)):raise ValueError('unexpected sensing shapes')
if not all(np.all(np.isfinite(v)) for v in (w,angles,field,jac,fs,js,pd,saved_p)):raise ValueError('nonfinite input')
if scene['directivity_exponent']!=2 or scene['case_metadata']['realization']!=4:raise ValueError('unexpected saved case')

def decimal_float(x):return D.from_float(float(x))
def sc(x):
    ss=x; cc=D(1); st=x; ct=D(1); j=1
    while True:
        st=-st*x*x/D((2*j)*(2*j+1)); ct=-ct*x*x/D((2*j-1)*(2*j))
        nss=ss+st; ncc=cc+ct
        if nss==ss and ncc==cc:return ss,cc
        ss=nss;cc=ncc;j+=1
        if j>200:raise ArithmeticError('trig convergence')
def dot(x,y):return sum((a*b for a,b in zip(x,y)),D(0))
def mul(a,b):return (a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0])
def conj(a):return (a[0],-a[1])
def add(a,b):return (a[0]+b[0],a[1]+b[1])
def norm2(a):return a[0]*a[0]+a[1]*a[1]

ww=[[(decimal_float(x.real),decimal_float(x.imag)) for x in row] for row in w]
coords=[[decimal_float(x) for x in row] for row in scene['bs_coordinates']]
center=[decimal_float(x) for x in scene['bs_center']]
directions=[[[decimal_float(x) for x in d] for d in user] for user in scene['bu_directions']]
gains=[[(decimal_float(a),decimal_float(b)) for a,b in zip(ar,ai)] for ar,ai in zip(scene['bu_gain_re'],scene['bu_gain_im'])]
noise=[decimal_float(x) for x in scene['noise']]
wave=decimal_float(2*np.pi/scene['wavelength']); gain=decimal_float(scene['maximum_gain']).sqrt()

def rate(angle):
    sx,cx=sc(angle[0]);sy,cy=sc(angle[1]);sz,cz=sc(angle[2])
    q=[[cy*cz,-cy*sz,sy],[cx*sz+sx*sy*cz,cx*cz-sx*sy*sz,-sx*cy],[sx*sz-cx*sy*cz,sx*cz+cx*sy*sz,cx*cy]]
    fc=[[(D(0),D(0)) for _ in range(2)] for _ in range(4)];cosines=[]
    for u in range(2):
        for j,d in enumerate(directions[u]):
            cosine=dot([q[k][2] for k in range(3)],d); cosines.append(cosine)
            if cosine<=0:continue
            for k in range(4):
                xyz=[dot(q[i],coords[k])+center[i] for i in range(3)]
                sn,cs=sc(wave*dot(xyz,d));amplitude=gain*cosine
                fc[k][u]=add(fc[k][u],mul(gains[u][j],(amplitude*cs,amplitude*sn)))
    vals=[]
    for u in range(2):
        y=[sum_complex([mul(conj(fc[k][u]),ww[k][j]) for k in range(4)]) for j in range(6)]
        signal=norm2(y[u]);interference=noise[u]+sum((norm2(y[j]) for j in range(6) if j!=u),D(0))
        vals.append((D(1)+signal/interference).ln()/D(2).ln())
    return sum(vals,D(0)),cosines,fc
def sum_complex(items):
    return (sum((z[0] for z in items),D(0)),sum((z[1] for z in items),D(0)))

base=[decimal_float(x) for x in angles[:3]]
rate0,cos0,fc0=rate(base)
field_abs_diff=max((norm2((fc0[k][u][0]-decimal_float(field[k,u].real),fc0[k][u][1]-decimal_float(field[k,u].imag))).sqrt() for k in range(4) for u in range(2)))
y=field.conj().T@w
total=np.sum(abs(y)**2,axis=1)+np.asarray(scene['noise']);signal=abs(y[np.arange(2),np.arange(2)])**2;interference=total-signal
analytic=[]
for j in range(3):
    dy=jac[:,:,j].conj().T@w
    dtotal=2*np.real(np.sum(y.conj()*dy,axis=1));dsignal=2*np.real(y[np.arange(2),np.arange(2)].conj()*dy[np.arange(2),np.arange(2)])
    analytic.append(float(np.sum(dtotal/total-(dtotal-dsignal)/interference)/np.log(2)))
rows=[]
for h in (D('1e-6'),D('1e-8'),D('1e-10')):
    for j in range(3):
        plus=base.copy();minus=base.copy();plus[j]+=h;minus[j]-=h
        fplus,cplus,_=rate(plus);fminus,cminus,_=rate(minus)
        fd=(fplus-fminus)/(2*h);cross=any(a*b<=0 for a,b in zip(cplus,cminus))
        rows.append({'step':str(h),'axis':j,'decimal_rate_gradient':str(fd),'analytic_rate_gradient':analytic[j],'horizon_crossed':cross,'absolute_error':str(abs(fd-decimal_float(analytic[j])))})

if any(float(x)!=0 for x in scene['br_gain_re']+scene['br_gain_im']):raise ValueError('NoRIS bridge not zero')
target=[[decimal_float(x) for x in row] for row in scene['bt_directions']]
pdd=[decimal_float(x) for x in pd];id=decimal_float(scene['saved_previous_iota']);rho=decimal_float(scene['rho']);energy=dot(pdd,pdd)
if id<=0 or energy<=0:raise ValueError('invalid normalization')
def sensing(angle):
    sx,cx=sc(angle[0]);sy,cy=sc(angle[1]);sz,cz=sc(angle[2])
    q=[[cy*cz,-cy*sz,sy],[cx*sz+sx*sy*cz,cx*cz-sx*sy*sz,-sx*cy],[sx*sz-cx*sy*cz,sx*cz+cx*sy*sz,cx*cy]]
    powers=[];cosines=[]
    for d in target:
        cosine=dot([q[k][2] for k in range(3)],d);cosines.append(cosine)
        f=[]
        for k in range(4):
            if cosine<=0:f.append((D(0),D(0)));continue
            xyz=[dot(q[i],coords[k])+center[i] for i in range(3)]
            sn,cs=sc(wave*dot(xyz,d));amp=gain*cosine
            f.append((amp*cs,amp*sn))
        zz=[sum_complex([mul(conj(f[k]),ww[k][j]) for k in range(4)]) for j in range(6)]
        powers.append(sum((norm2(z) for z in zz),D(0)))
    return -rho*sum(((p/id-target_p)**2 for p,target_p in zip(powers,pdd)),D(0))/energy,cosines,powers
sv,cs,ps=sensing(base);z=fs.conj().T@w;pp=np.sum(abs(z)**2,axis=1);residual=pp-float(id)*pd
sg=[]
for j in range(3):
    dz=js[:,:,j].conj().T@w;dp=2*np.real(np.sum(z.conj()*dz,axis=1))
    sg.append(float(-2*float(rho)*np.dot(residual,dp)/(float(id)**2*float(energy))))
for row in rows:
    h=D(row['step']);j=row['axis'];plus=base.copy();minus=base.copy();plus[j]+=h;minus[j]-=h
    ss1,cp,_=sensing(plus);ss0,cm,_=sensing(minus)
    fd_s=(ss1-ss0)/(2*h);fd_t=fd_s+D(row['decimal_rate_gradient']);at=float(analytic[j]+sg[j])
    row.update(sensing_gradient_decimal=str(fd_s),analytic_sensing_gradient=sg[j],sensing_abs_error=str(abs(fd_s-decimal_float(sg[j]))),
       total_gradient_decimal=str(fd_t),analytic_total_gradient=at,total_abs_error=str(abs(fd_t-decimal_float(at))),
       sensing_endpoint_sign_change=any(a*b<=0 for a,b in zip(cp,cm)))
result={'schema':'ISAC004_SAVED_SENSING_AND_TOTAL_ROTATION_GRADIENT_V1','scope':'One saved NoRIS intermediate state; fixed W and iota; three BS rotations only. No optimizer or new channel realization; no claim of MATLAB, convergence, reference or paper pass.',
'decimal_precision':50,'saved_iota':float(id),'closest_bs_user_cosine':str(min(cos0,key=abs)),
'closest_target_cosine':str(min(cs,key=abs)),'max_decimal_saved_pattern_difference':str(max(abs(a-decimal_float(b)) for a,b in zip(ps,saved_p))),
'analytic_rate':analytic,'analytic_sensing':sg,'checks':rows}
with args.output.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2);f.write('\n')
print('Fixed-state sensing and total rotation-gradient diagnostic complete.')
