"""Inspect stored native evidence integrity only; no mathematical evaluation."""
from pathlib import Path
import argparse,gzip,hashlib,json
def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--package',type=Path,default=Path(__file__).resolve().parent);args=a.parse_args();root=args.package.resolve()
    manifest=json.loads((root/'MANIFEST.json').read_bytes())
    for name,item in manifest['files_excluding_this_manifest'].items():
        p=(root/name).resolve();assert p.is_relative_to(root)
        b=p.read_bytes();assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['SHA256'],name
    s=json.loads((root/'evidence/actual-native36-final-MP-summary.json').read_bytes())
    typed=json.loads(gzip.decompress((root/'evidence/actual-native-MAT-typed-binding.json.gz').read_bytes()))
    print(json.dumps(dict(schema='relative-stored-native-evidence-integrity-only-v1',files_verified=len(manifest['files_excluding_this_manifest']),stored_returned_blocks=s['returned_inner_blocks'],stored_counts=s['returned_per_method'],stored_native_own_block_RCG_PGA_pass=s['native_own_block_RCG_PGA_strict_pass'],stored_final_joint_RCG_PGA_pass=s['native_final_joint_RCG_PGA_strict_pass'],native_per_coordinate_vector_verification_pending=s['native_per_coordinate_analytic_vector_verification_still_pending'],typed_arrays_in_original_receipt=len(typed['array_inventory_and_semantic_casts']),new_mathematical_MP_model_gradient_optimizer_MC_RNG_calls=0,scientific_replay_performed=False),indent=2))
if __name__=='__main__':main()
