"""Source-bound receipts and durable checkpoints; never recycle stale results."""
import hashlib
import json
from pathlib import Path
import numpy as np


def numerical_json(value):
    if isinstance(value,np.ndarray):return value.tolist()
    if isinstance(value,np.generic):return value.item()
    raise TypeError(type(value).__name__)


def source_hashes(paths):
    root=Path(__file__).parent
    return {p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}


def unchanged(hashes):
    return source_hashes(hashes)==hashes


def save_receipt(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.partial')
    temporary.write_text(json.dumps(value,indent=2,allow_nan=False,default=numerical_json)+'\n',encoding='utf-8')
    temporary.replace(path)


def checkpoint_contract(config,hashes):
    contract={'configuration':config,'executed_source_hashes':hashes}
    contract['sha256']=hashlib.sha256(json.dumps(contract,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return contract


def load_checkpoint(path,contract):
    if not Path(path).exists():return None
    receipt=json.loads(Path(path).read_text(encoding='utf-8'))
    if receipt.get('contract')!=contract:
        raise RuntimeError('Checkpoint source/configuration mismatch; use a new output directory. No stale simulation is reused.')
    return receipt
