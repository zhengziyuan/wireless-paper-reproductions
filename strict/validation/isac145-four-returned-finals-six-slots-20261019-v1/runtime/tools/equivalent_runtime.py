"""Isolated original ISAC algorithms with equivalent stable arithmetic.

The live strict source is read without edits. Its algorithms are executed in
a private module. Only evaluate() and the QT auxiliary's self-excluded power
sum are replaced; loops, initialization, PR mode, BB choice and budgets are
identical. This variant has its own source binding and never relabels old runs.
"""
import hashlib
from pathlib import Path
import types
import numpy as np
from stable_metrics import evaluate as stable_evaluate

OLD_AUX = 'signal=abs(y[np.arange(k),np.arange(k)])**2;mu=signal/(total-signal);eta=y[np.arange(k),np.arange(k)]/total'
NEW_AUX = 'signal=abs(y[np.arange(k),np.arange(k)])**2;interference=np.array([c["noise"][u]+sum(abs(y[u,s])**2 for s in range(w.shape[1]) if s!=u) for u in range(k)]);total=signal+interference;mu=signal/interference;eta=y[np.arange(k),np.arange(k)]/total'


def load_core():
    source=Path(__file__).resolve().parents[2]/'strict/rotatable-isac/core.py'
    text=source.read_text(encoding='utf-8')
    if text.count(OLD_AUX)!=1:raise ValueError('Original QT auxiliary changed; review before adapting')
    model=types.ModuleType('isac_equivalent_stable_arithmetic')
    model.__file__=str(source)
    exec(compile(text.replace(OLD_AUX,NEW_AUX),str(source)+'::equivalent-stable-arithmetic','exec'),model.__dict__)
    model.evaluate_subtractive_control=model.evaluate
    def evaluate(w,theta,r,c,iota=None,gradients=False,_fixed_channel_bundle=None,_fixed_rotation_base=None):
        bundle=model.channels(theta,r,c,_fixed_rotation_base) if _fixed_channel_bundle is None else _fixed_channel_bundle
        if iota is None:
            field=bundle[0];k=len(c['noise']);z=field[:,k:].conj().T@w
            pattern=np.sum(abs(z)**2,axis=1);desired=np.asarray(c['desired_pattern']);overlap=float(desired@pattern)
            if overlap<=c['iota_denominator_epsilon']:raise ValueError('Exact iota* is undefined at this zero-overlap pattern; no fabricated sensing score is returned.')
            iota=float(pattern@pattern/overlap)
        return stable_evaluate(w,*bundle,c,iota,gradients)
    model.evaluate=evaluate
    return model


def binding():
    repo=Path(__file__).resolve().parents[2]
    paths=[repo/'strict/rotatable-isac'/name for name in ('core.py','run.py','isac_metadata.py')]
    paths += [Path(__file__),Path(__file__).with_name('stable_metrics.py')]
    return {str(p.relative_to(repo)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
