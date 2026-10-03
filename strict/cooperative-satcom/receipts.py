"""Durable actual source/configuration-bound sweep receipts, never stale reuse."""
import hashlib
import json
from pathlib import Path
import numpy as np


def source_hashes():
    root=Path(__file__).parent
    return {p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in ('core.py','models.py','increments.py','algorithms.py','termination.py','scenario.py','run.py','receipts.py','full_config.json')}


def unchanged(hashes):return source_hashes()==hashes


def numerical_json(value):
    if isinstance(value,np.ndarray):return value.tolist()
    if isinstance(value,np.generic):return value.item()
    raise TypeError(type(value).__name__)


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);partial=path.with_name(path.name+'.partial')
    partial.write_text(json.dumps(value,indent=2,allow_nan=False,default=numerical_json)+'\n',encoding='utf-8');partial.replace(path)


def contract(scene,hashes):
    c={'configuration':scene,'executed_source_hashes':hashes};c['sha256']=hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest();return c


def load(path,c):
    if not Path(path).exists():return None
    value=json.loads(Path(path).read_text(encoding='utf-8'))
    if value.get('contract')!=c:raise RuntimeError('Checkpoint source/settings mismatch; no old figure point is silently reused')
    return value['result']
