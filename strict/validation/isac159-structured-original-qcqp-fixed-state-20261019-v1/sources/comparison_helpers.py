"""Exact unchanged numeric comparison helpers from the actual closed audit."""
import numpy as np
import mpmath as mp

def ex(v):
    if isinstance(v,dict):return mp.mpc(mp.mpf(v['real']),mp.mpf(v['imag']))
    if isinstance(v,str):return mp.mpf(v)
    if np.iscomplexobj(v):return mp.mpc(mp.mpf(float(np.real(v))),mp.mpf(float(np.imag(v))))
    return mp.mpf(float(v))

def matrix(a):return mp.matrix([[ex(x) for x in row] for row in a])

def txt(x):return mp.nstr(x,110)

def fro(a):return mp.sqrt(mp.fsum(abs(x)**2 for x in a))

def power(a):return mp.fsum(abs(x)**2 for x in a)

def objective(w,q,p):return 2*mp.re(mp.fsum(mp.conj(p[i,j])*w[i,j] for i in range(w.rows) for j in range(w.cols)))-mp.re(mp.fsum(mp.conj(w[i,j])*(q*w)[i,j] for i in range(w.rows) for j in range(w.cols)))

def physical(w,fc,fs,scene,iota):
    y=fc.conjugate().transpose()*w;z=fs.conjugate().transpose()*w;k=fc.cols
    signal=[abs(y[u,u])**2 for u in range(k)]
    interference=[ex(scene['noise'][u])+mp.fsum(abs(y[u,j])**2 for j in range(w.cols) if j!=u) for u in range(k)]
    rate=mp.fsum(mp.log1p(s/i) for s,i in zip(signal,interference))/mp.log(2)
    pattern=[mp.fsum(abs(z[l,j])**2 for j in range(w.cols)) for l in range(fs.cols)]
    pd=[ex(x) for x in scene['desired_pattern']];den=iota*iota*mp.fsum(v*v for v in pd)
    nmse=mp.fsum((p-iota*d)**2 for p,d in zip(pattern,pd))/den
    return dict(utility=rate-ex(scene['rho'])*nmse,rate=rate,nmse=nmse,power=power(w))
