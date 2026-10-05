"""Reproducible scalar-array MIS demonstration, not measured/full-wave data.

Run: python compute/generate.py  (requires only numpy >= 1.24).
All lengths in the numerical model are normalized by wavelength. Coordinates
are row-major (y then x), propagation is toward +z, and the receiver direction
is (sin(az)*cos(el), sin(el), cos(az)*cos(el)).

The optimizer uses exact discrete position scheduling at every evaluation and
analytic phase gradients for a log-sum-exp worst-target surrogate, with a
limited-memory BFGS/Armijo phase step. This follows the paper's design objective
and static-phase architecture but is NOT a replication of its RCG solver.
"""
from __future__ import annotations
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import time
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261005


class MISModel:
    def __init__(self):
        self.n1, self.n2 = 16, 12
        self.M, self.N = self.n1**2, self.n2**2
        self.frequency_ghz, self.pitch_mm = 12.2, 6.0
        self.wavelength_mm = 299792458.0 / (self.frequency_ghz * 1e9) * 1000
        self.pitch = self.pitch_mm / self.wavelength_mm
        self.positions = [dict(index=j*5+i, x=i-2, y=j-2,
                               dxMm=(i-2)*self.pitch_mm,
                               dyMm=(j-2)*self.pitch_mm)
                          for j in range(5) for i in range(5)]
        self.targets = []
        for el in [-20, 0, 20]:
            for az in [-30, 0, 30]:
                a, e = np.deg2rad([az, el])
                self.targets.append(dict(az=az, el=el, ux=float(np.sin(a)*np.cos(e)),
                                         uy=float(np.sin(e))))
        self.xy1 = self.coordinates(self.n1)
        self.xy2 = self.coordinates(self.n2)
        self.map = np.array([
            [(r+2+p['y'])*self.n1+c+2+p['x']
             for r in range(self.n2) for c in range(self.n2)]
            for p in self.positions], dtype=int)
        uv = np.array([[t['ux'], t['uy']] for t in self.targets])
        self.steer = np.exp(-2j*np.pi*(uv @ self.xy1.T))
        self.c = float(np.sin(np.deg2rad(35)) / (2*self.pitch))
        self.snell = np.r_[np.pi*self.c*np.sum(self.xy1**2, axis=1),
                            -np.pi*self.c*np.sum(self.xy2**2, axis=1)]

    def coordinates(self, n):
        return np.array([((c-(n-1)/2)*self.pitch, (r-(n-1)/2)*self.pitch)
                         for r in range(n) for c in range(n)], dtype=float)

    def evaluate(self, phases):
        # Padding is the complex coefficient +1: uncovered phase is zero.
        # Every MS1 cell contributes, including its uncovered region.
        composite = np.broadcast_to(phases[:self.M], (25,self.M)).copy()
        composite[np.arange(25)[:,None], self.map] += phases[self.M:]
        aperture = np.exp(1j*composite)
        field = self.steer @ aperture.T / self.M
        gain = np.abs(field)**2
        schedule = np.argmax(gain,axis=1)
        selected = gain[np.arange(9),schedule]
        return gain, schedule, selected, aperture, field

    def loss_gradient(self, phases, mu):
        gain, schedule, selected, aperture, field = self.evaluate(phases)
        min_gain = float(np.min(selected))
        exp_terms = np.exp(-(selected-min_gain)/mu)
        weights = exp_terms / exp_terms.sum()
        # -softmin, offset by log(K) solely to make displayed surrogate scale
        # close to actual min; this offset does not change gradients.
        loss = -min_gain + mu*(np.log(exp_terms.sum())-np.log(len(selected)))
        z = self.steer * aperture[schedule]
        d_gain = -2*np.imag(np.conj(field[np.arange(9),schedule,None])*z)/self.M
        weighted = -weights[:,None]*d_gain
        g1 = weighted.sum(axis=0)
        g2 = weighted[np.arange(9)[:,None],self.map[schedule]].sum(axis=0)
        return float(loss), np.r_[g1,g2], min_gain, schedule

    def export_method(self, phases, label):
        gain,schedule,selected,_,_ = self.evaluate(phases)
        wrapped = np.mod(phases, 2*np.pi)
        return dict(label=label, phi1=wrapped[:self.M].tolist(),
                    phi2=wrapped[self.M:].tolist(), gainMatrix=gain.tolist(),
                    schedule=schedule.tolist(), targetPower=selected.tolist(),
                    score=float(selected.min()), scoreDb=float(10*np.log10(selected.min())),
                    meanPower=float(selected.mean()))


def optimize(model, max_per_stage=100):
    rng = np.random.default_rng(SEED)
    starts = [model.snell.copy(), model.snell+rng.normal(0,.6,model.M+model.N),
              rng.uniform(-np.pi,np.pi,model.M+model.N)]
    mus = [.06,.025,.012,.006,.003,.0015,.0007]
    best = model.snell.copy()
    incumbent = model.evaluate(best)[2].min()
    history = [dict(iteration=0,score=float(incumbent),start="snell_incumbent",mu=None)]
    total_iter = 0
    runs = []
    for start_id,x0 in enumerate(starts):
        x = x0.copy()
        stage_reports = []
        for mu in mus:
            memories=[]
            f,g,score,schedule=model.loss_gradient(x,mu)
            accepted=0
            for it in range(max_per_stage):
                q=g.copy()
                alphas=[]
                for s,y,rho in reversed(memories):
                    alpha=rho*np.dot(s,q)
                    q-=alpha*y
                    alphas.append(alpha)
                scale=np.dot(memories[-1][0],memories[-1][1])/np.dot(memories[-1][1],memories[-1][1]) if memories else 40.0
                d=q*max(.01,min(1e4,scale))
                for (s,y,rho),alpha in zip(memories,reversed(alphas)):
                    d+=s*(alpha-rho*np.dot(y,d))
                d=-d
                slope=float(np.dot(g,d))
                if slope>=0 or not np.isfinite(slope):
                    d=-40*g
                    slope=float(np.dot(g,d))
                    memories=[]
                if np.linalg.norm(g)<1e-7:
                    break
                step=1.0
                # Armijo safeguards phase updates. Exact scheduling is recomputed
                # at every trial, so selection is jointly updated with the masks.
                for backtrack in range(24):
                    xn=x+step*d
                    fn,gn,scoren,schedulen=model.loss_gradient(xn,mu)
                    if fn <= f+1e-4*step*slope:
                        break
                    step*=.5
                else:
                    break
                s=xn-x
                y=gn-g
                sy=float(np.dot(s,y))
                if sy>1e-10:
                    memories.append((s,y,1/sy))
                    memories=memories[-9:]
                x,f,g,score,schedule=xn,fn,gn,scoren,schedulen
                total_iter+=1
                accepted+=1
                if score>incumbent:
                    incumbent=score
                    best=x.copy()
                history.append(dict(iteration=total_iter,score=float(incumbent),
                                    currentScore=float(score),start=start_id,mu=mu))
            stage_reports.append(dict(mu=mu,iterations=accepted,score=float(score),
                                      gradientNorm=float(np.linalg.norm(g))))
            print(json.dumps(dict(start=start_id,mu=mu,iterations=accepted,
                                  currentScore=float(score),bestScore=float(incumbent))),flush=True)
        runs.append(dict(start=start_id,stages=stage_reports))
    return best,history,runs


def gradient_validation(model):
    rng=np.random.default_rng(SEED+1)
    phases=model.snell+rng.normal(0,.25,model.M+model.N)
    mu=.03
    _,analytic,_,_=model.loss_gradient(phases,mu)
    ids=rng.choice(len(phases),size=40,replace=False)
    epsilon=1e-5
    errors=[]
    relative=[]
    for i in ids:
        p=phases.copy(); p[i]+=epsilon
        m=phases.copy(); m[i]-=epsilon
        numerical=(model.loss_gradient(p,mu)[0]-model.loss_gradient(m,mu)[0])/(2*epsilon)
        errors.append(abs(numerical-analytic[i]))
        relative.append(abs(numerical-analytic[i])/max(1e-7,abs(numerical),abs(analytic[i])))
    return dict(count=len(ids),epsilon=epsilon,maxAbsoluteError=float(max(errors)),
                maxRelativeError=float(max(relative)),passed=bool(max(errors)<1e-8))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--iterations',type=int,default=100)
    args=parser.parse_args()
    started=time.perf_counter()
    model=MISModel()
    grad_check=gradient_validation(model)
    if not grad_check['passed']:
        raise RuntimeError(grad_check)
    best,history,runs=optimize(model,args.iterations)
    source=ROOT.parent/'论文素材库'/'Movable_Intelligent_Surface__MIS__for_Wireless_Communications__Architecture__Modeling__Algorithm__and_Prototyping__R2_ (2)'/'bare_jrnl.tex'
    source_hash=hashlib.sha256(source.read_bytes()).hexdigest() if source.exists() else None
    data=dict(schemaVersion=1,config=dict(n1=model.n1,n2=model.n2,
          pitchMm=model.pitch_mm,frequencyGHz=model.frequency_ghz,
          wavelengthMm=model.wavelength_mm,layerGapMm=1,referenceSnrDb=26,
          illumination='uniform_normal_plane_wave',padding='uncovered_complex_multiplier_1',
          snellC=model.c,snellEdgeAngleDeg=35,arrayNormalization=model.M,
          coordinateOrder='row-major: index = row*n + column; x = column, y = row',
          coordinates1Lambda=model.xy1.tolist(),coordinates2Lambda=model.xy2.tolist()),
          targets=model.targets,positions=model.positions,
          snell=model.export_method(model.snell,'Generalized Snell quadratic illustration'),
          optimized=model.export_method(best,'Joint static phases and exact discrete position scheduling'),
          history=history,provenance=dict(seed=SEED,
          generatedOn='2026-10-05',pythonVersion=platform.python_version(),numpyVersion=np.__version__,
          sourceTitle='Movable Intelligent Surface (MIS) for Wireless Communications: Architecture, Modeling, Algorithm, and Prototyping',
          sourceFile='https://arxiv.org/abs/2412.19071',sourceRelativePath=None,sourceSha256=source_hash,
          model='scalar far-field array with ideal, lossless, static phase-only transmissive cells; close-stack elementwise phase multiplication',
          objective='max_{static phi1,phi2} min_k max_u |F(k,u)|^2',
          algorithm='multi-start phase L-BFGS with Armijo line search; exact discrete argmax scheduling at each evaluation; log-sum-exp worst-target continuation',
          algorithmLimit='Demonstration implementation inspired by the paper objective, not a replication of its RCG/manifold algorithm; no global optimality guarantee.',
          snellLimit='Derived conjugate quadratic phase illustration under normal plane-wave incidence, not the fabricated prototype phase masks or its spherical-feed compensation.',
          dataStatus='computed simulation; no live hardware, measured S-parameters, measured constellation, or full-wave calibration',
          snellFormula='q1(r)=+pi*c*|r/lambda|^2; q2(r)=-pi*c*|r/lambda|^2; overlapping composite gradient/(2*pi)=c*delta/lambda',
          maxIterationsPerStage=args.iterations,runs=runs,elapsedSeconds=time.perf_counter()-started),
          validation=dict(gradient=grad_check))
    path=ROOT/'data.js'
    path.write_text('window.MIS_DATA = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
    print(json.dumps(dict(output=str(path),snellScore=data['snell']['score'],
                          optimizedScore=data['optimized']['score'],gainDb=data['optimized']['scoreDb']-data['snell']['scoreDb'],
                          elapsedSeconds=data['provenance']['elapsedSeconds']),ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
