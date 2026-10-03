"""ISOLATED fixed-theta/r evaluator prototype, not enabled in frozen core.

Only channel construction is hoisted out of a W block. Both the fixed-iota
utility and ALL Euclidean gradients use exactly the original arithmetic.
The context must be rebuilt whenever theta, r, or scenario changes.
"""
import json
import numpy as np
from core import channels


class FixedChannelEvaluator:
    def __init__(self,theta,r,c):
        self.theta=np.asarray(theta).copy();self.r=np.asarray(r).copy();self.c=c
        self.configuration_snapshot=json.dumps(c,sort_keys=True,separators=(",",":"))
        self.field,self.jac,self.bridge,self.g=channels(theta,r,c)
        for a in [self.field,self.jac,self.bridge,self.g]:a.setflags(write=False)
        self.calls=0

    def check_immutable_configuration(self):
        if json.dumps(self.c,sort_keys=True,separators=(",",":"))!=self.configuration_snapshot:
            raise ValueError("Fixed W context configuration changed; construct a new context")

    def bind(self,w,theta,r,c,iota=None,gradients=False):
        if c is not self.c or not np.array_equal(theta,self.theta) or not np.array_equal(r,self.r):
            raise ValueError("Fixed channel context used outside its unchanged theta/r/scenario")
        return self.evaluate(w,iota,gradients)

    def evaluate(self,w,iota=None,gradients=False):
        self.calls+=1;c=self.c;field,jac,bridge,g=self.field,self.jac,self.bridge,self.g;k=len(c["noise"])
        fc,fs=field[:,:k],field[:,k:];y=fc.conj().T@w;z=fs.conj().T@w
        total=np.sum(abs(y)**2,axis=1)+c["noise"];signal=abs(y[np.arange(k),np.arange(k)])**2
        interference=total-signal;rate=float(np.log2(total/interference).sum());p=np.sum(abs(z)**2,axis=1)
        pd=np.asarray(c["desired_pattern"]);energy=float(pd@pd)
        if iota is None:
            overlap=float(pd@p)
            if overlap<=c["iota_denominator_epsilon"]:
                raise ValueError("Exact iota* is undefined at this zero-overlap pattern; no fabricated sensing score is returned.")
            iota=float(p@p/overlap)
        denominator=iota*iota*energy;residual=p-iota*pd;nmse=float(residual@residual/denominator)
        result={"utility":rate-c["rho"]*nmse,"rate":rate,"nmse":nmse,"iota":iota,"pattern":p,"sinr":signal/interference}
        if not gradients:return result
        coeff=np.repeat((1/total-1/interference)[:,None],w.shape[1],axis=1)
        coeff[np.arange(k),np.arange(k)]+=1/interference
        gw=2*fc@(coeff*y)/np.log(2)-4*c["rho"]*fs@(residual[:,None]*z)/denominator
        bw=bridge.conj().T@w;gt=np.zeros(len(self.theta),complex)
        for u in range(k):gt+=2*g[:,u].conj()*(bw@(coeff[u]*y[u].conj()))/np.log(2)
        for v in range(len(pd)):gt-=4*c["rho"]*residual[v]/denominator*g[:,k+v].conj()*(bw@z[v].conj())
        gr=np.zeros(6)
        for d in range(6):
            dy=jac[:,:k,d].conj().T@w;dz=jac[:,k:,d].conj().T@w
            dtotal=2*np.real(np.sum(y.conj()*dy,axis=1));dsignal=2*np.real(y[np.arange(k),np.arange(k)].conj()*dy[np.arange(k),np.arange(k)])
            drate=np.sum(dtotal/total-(dtotal-dsignal)/interference)/np.log(2)
            dp=2*np.real(np.sum(z.conj()*dz,axis=1));gr[d]=drate-2*c["rho"]*residual@dp/denominator
        return result,(gw,gt,gr)
