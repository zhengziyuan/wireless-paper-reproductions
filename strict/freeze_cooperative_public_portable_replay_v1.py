"""Append distinct actual portable replay evidence, never rewrite old flags."""
import hashlib
import json
from pathlib import Path
import shutil

STRICT=Path(__file__).resolve().parent
ROOT=STRICT.parent.parent
PUBLIC=STRICT/'validation/cooperative-recording-v4-python-two-fullcases-v1'
INPUTS=STRICT/'validation/cooperative-configured-v3-inputs-v1'
WORK=ROOT/'work/cooperative-rgd-audit/recording-v4-actual-fullcases-20261004-v1'
DEST=PUBLIC/'portable-replay-actual-v1'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not DEST.exists()
    original_manifest=sha(PUBLIC/'manifest.json')
    assert original_manifest=='a1512e10e47ac0d8d75d754a429f6a94145b5c41b8286e3ccfb5ce328e26f25c'
    records=[]
    for name in ('M30','N48'):
        actual=WORK/f'{name}-portable-public-replay-actual-v1.json'
        item=json.loads(actual.read_text(encoding='utf-8-sig'))
        assert item['all_independent_implemented_numerical_checks_pass'] and all(item['checks'].values())
        assert item['auditor_source_sha256']==sha(PUBLIC/'audit_recorded_fullcase.py')
        assert item['actual_array_bank_sha256']==sha(PUBLIC/f'{name}-recorded-state.npz')
        assert item['actual_recording_receipt_sha256']==sha(PUBLIC/f'{name}-recorded-state.json')
        assert item['actual_result_sha256']==sha(PUBLIC/f'{name}-actual-python.json')
        assert item['actual_configuration_sha256']==sha(INPUTS/f'{name}-configuration.json')
        assert item['actual_original_moment_draw_audit']['all_original_draws_bitwise_replayed']
        assert item['actual_original_moment_draw_audit']['original_rng_after_bitwise_pass']
        assert item['actual_original_moment_draw_audit']['actual_draw_count']==1000
        assert not item['full_reproduction_pass'] and not item['native_recording_layer_fullcase_independent_certified']
        records.append((name,actual))
    DEST.mkdir()
    for name,actual in records:shutil.copyfile(actual,DEST/f'{name}-actual-public-portable-replay.json')
    readme='''# Additional ACTUAL public-directory portable replay

After the original immutable evidence manifest was frozen, the portable
auditor was actually executed serially against BOTH published NPZ/metadata
banks and published unchanged configuration attachments. Both passed all
final matrix, original physical, fixed-context scalar gradient, accepted-QT,
actual caller-return and full1000 bitwise RNG/draw/moment checks. No optimizer
was run and no new heavy fullcase was substituted. The original manifest's
then-false direct-portable-reexecution flag remains unchanged; this later
supplement supplies the actual additional evidence with separate hashes.

This does not certify native recording-v4, formal183, optimized-performance
1000 MC, MP80 gradients/duals, publisher conformance or author's historical
unreported geometry/curves. Those flags remain false.
'''
    (DEST/'README.md').write_text(readme,encoding='utf-8')
    manifest={'scope':'later_actual_public_directory_Python_savedstate_replay_NOT_rewritten_original_manifest',
        'original_immutable_manifest_sha256':original_manifest,'portable_entry_sha256':sha(PUBLIC/'audit_recorded_fullcase.py'),
        'both_actual_portable_replays_pass':True,'original_manifest_bytes_unchanged':sha(PUBLIC/'manifest.json')==original_manifest,
        'freezer_source_sha256':sha(Path(__file__)),'full_reproduction_pass':False,
        'public_files':[{ 'filename':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(DEST.iterdir())]}
    (DEST/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'both_actual_public_portable_replays_pass':True,'original_manifest_unchanged':True,
        'new_supplement_manifest_sha256':sha(DEST/'manifest.json'),'full_reproduction_pass':False}))


if __name__=='__main__':main()
