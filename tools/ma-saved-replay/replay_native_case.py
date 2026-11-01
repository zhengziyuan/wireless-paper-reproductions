"""Replay the paired actual native witness on the same original input bytes."""
import argparse
import gzip
import hashlib
from pathlib import Path

from audit_native_case import audit
from replay_case import restore
from source_reader import read,require,sha


def replay(packet,output,repo):
    require(not output.exists(),'Fresh paired native replay directory required')
    receipt,_=restore(packet,output/'restored-original-inputs')
    manifest=read(packet/'archive-manifest.json');native=read(packet/'native-witness-manifest.json')
    compressed=packet/native['file'];require(sha(compressed)==native['compressed_sha256'],'Actual native compressed RAW differs')
    raw=gzip.decompress(compressed.read_bytes());require(len(raw)==native['raw_bytes'] and hashlib.sha256(raw).hexdigest()==native['raw_sha256'],'Actual native RAW bytes differ')
    native_path=output/'actual-native-first-case.json';native_path.write_bytes(raw)
    math=output/'restored-actual-Python-math';(math/'cases').mkdir(parents=True)
    payload=b''.join((packet/p['file']).read_bytes() for p in manifest['archive']['parts'])
    require(hashlib.sha256(payload).hexdigest()==receipt['archive']['sha256'],'Exact actual baseline cache archive')
    (math/'cases'/receipt['archive']['file']).write_bytes(payload)
    receipt_path=math/'actual-Python-case-receipt.json';receipt_path.write_bytes((packet/manifest['receipt']['file']).read_bytes())
    original=output/'restored-original-inputs'
    return audit(native_path,receipt_path,math,original/'original-input.json',original/'original-run-config.json',output/'new-independent-native-math',repo)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--packet',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[2]);a=p.parse_args()
    if not replay(a.packet,a.output_dir,a.repo)['passed']:raise SystemExit(1)
