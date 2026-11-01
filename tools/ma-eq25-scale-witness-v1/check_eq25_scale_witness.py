"""Recheck MA paper Eq. (24)-(29) on one saved input; no optimizer or RNG."""
import argparse
import json
import math
from pathlib import Path
import numpy as np


def evaluate(data):
    if data['schema'] != 'MA_FIG5_CASE7_GEOM0_EQ29_SAVED_INPUT_V1':
        raise ValueError('Unexpected saved input schema')
    n,m=data['N'],data['M']; pos=np.asarray(data['mrt_positions'],dtype=float)
    dirs=np.asarray(data['directions'],dtype=float); beta=np.asarray(data['beta'],dtype=float)
    kappa=np.asarray(data['rician'],dtype=float); wavelength=float(data['wavelength'])
    if pos.shape!=(n,2) or dirs.shape!=(m,2) or beta.shape!=(m,) or kappa.shape!=(m,):
        raise ValueError('Input shapes differ')
    if not all(np.isfinite(x).all() for x in (pos,dirs,beta,kappa)) or not math.isfinite(wavelength) or wavelength<=0 or np.any(beta<=0) or np.any(kappa<0):
        raise ValueError('Invalid model input')
    wave=2*math.pi/wavelength; scale=8*math.pi**2/wavelength**2; rows=[]
    for antenna in range(n):
        for user in range(m):
            psi=np.zeros((2,2)); hessian=np.zeros((2,2))
            for other in range(m):
                if other==user: continue
                diff=dirs[user]-dirs[other]; phase=wave*(pos@diff)
                tau=sum(np.exp(1j*phase[i]) for i in range(n) if i!=antenna)
                c1=beta[other]*kappa[user]*kappa[other]/((kappa[user]+1)*(kappa[other]+1))
                weighted=c1*abs(tau); outer=np.outer(diff,diff)
                psi+=weighted*np.abs(outer)
                hessian-=scale*weighted*math.cos(float(phase[antenna])-float(np.angle(tau)))*outer
            norm2=float(np.linalg.norm(hessian,2)); bound2=float(np.linalg.norm(psi,2))
            normf=float(np.linalg.norm(hessian,'fro')); boundf=float(np.linalg.norm(psi,'fro'))
            if bound2<=0 or boundf<=0: raise ValueError('Degenerate witness matrix')
            rows.append({'antenna_one_based':antenna+1,'user_one_based':user+1,
                         'hessian':hessian.tolist(),'psi':psi.tolist(),
                         'hessian_norm_2':norm2,'psi_norm_2':bound2,
                         'hessian_norm_fro':normf,'psi_norm_fro':boundf,
                         'unscaled_2_ratio':norm2/bound2,'unscaled_fro_ratio':normf/boundf,
                         'scaled_2_ratio':norm2/(scale*bound2),'scaled_fro_ratio':normf/(scale*boundf)})
    # A separate finite difference of the printed Eq.(22) gradient checks one
    # Hessian reconstruction. This is a numerical sanity check, not an interval
    # certificate or an optimizer execution.
    chosen=max(rows,key=lambda row:row['unscaled_2_ratio'])
    ant=chosen['antenna_one_based']-1; user=chosen['user_one_based']-1
    def gradient(location):
        out=np.zeros(2)
        for other in range(m):
            if other==user: continue
            diff=dirs[user]-dirs[other]; phase=wave*(pos@diff)
            tau=sum(np.exp(1j*phase[i]) for i in range(n) if i!=ant)
            c1=beta[other]*kappa[user]*kappa[other]/((kappa[user]+1)*(kappa[other]+1))
            out-=2*wave*c1*abs(tau)*math.sin(wave*float(location@diff)-float(np.angle(tau)))*diff
        return out
    step=1e-5
    fd=np.column_stack([(gradient(pos[ant]+step*np.eye(2)[axis])-gradient(pos[ant]-step*np.eye(2)[axis]))/(2*step)
                        for axis in range(2)])
    actual=np.asarray(chosen['hessian'])
    fd_error=float(np.max(np.abs(fd-actual))/np.max(np.abs(actual)))
    return {'schema':'MA_EQ25_EQ27_HESSIAN_SCALE_SAVED_WITNESS_V1',
            'scope':'Saved Fig. 5 Python MRT geometry and positions; direct Eq.24 Hessian and Eq.26 matrix; binary64; no optimization or sampling.',
            'factor_8pi2_over_wavelength2':scale,'matrix_count':len(rows),
            'printed_eq27_norm_2_violation_count':sum(row['unscaled_2_ratio']>1 for row in rows),
            'printed_eq25_fro_violation_count':sum(row['unscaled_fro_ratio']>1 for row in rows),
            'scaled_norm_2_violation_count':sum(row['scaled_2_ratio']>1+1e-12 for row in rows),
            'scaled_fro_violation_count':sum(row['scaled_fro_ratio']>1+1e-12 for row in rows),
            'max_norm_2_ratio':max(row['unscaled_2_ratio'] for row in rows),
            'max_norm_fro_ratio':max(row['unscaled_fro_ratio'] for row in rows),
            'gradient_finite_difference':{'antenna_one_based':ant+1,'user_one_based':user+1,
                                          'step':step,'relative_max_error':fd_error},
            'rows':rows,
            'limits':['The binary64 matrix construction is not an interval-certified forward-error proof.',
                      'This saved example cannot establish full scenario, MATLAB or figure agreement.',
                      'A factor is needed in the displayed Eq.25/27 bounds if Psi is as defined in Eq.26; Eq.29a already supplies the factor.']}


def main():
    p=argparse.ArgumentParser();p.add_argument('saved_input',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    result=evaluate(json.loads(a.saved_input.read_text(encoding='utf8')))
    with a.output.open('x',encoding='utf8',newline='\n') as f: json.dump(result,f,indent=2,allow_nan=False);f.write('\n')

if __name__=='__main__':main()
