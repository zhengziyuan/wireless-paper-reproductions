"""Verify a complete native recipe and saved arrays; regenerate zero vectors."""
import argparse
import json
from pathlib import Path

import native183_moment_recipe_v1 as recipe


def verify(args):
    recipe.require(not args.output.exists(),'Preserve the metadata verification epoch')
    manifest,index,native=recipe.validate_recipe(args.recipe,args.native_packet)
    recipe.validate_native_inputs(args.native_restored,native,index)
    for group in index['groups']:
        recipe.compare_draws(group,args.recipe/group['original_sample_moments'],args.recipe)
    result=dict(scope=recipe.SCOPE,actual_original_native_input_cases_verified=183,
        actual_recipe_payloads_byte_verified=len(manifest['files']),
        actual_saved_full1000_draw_array_groups_shape_dtype_finiteness_verified=67,
        full_primitive_bytes_described_by_exact_hashes=2735488000,
        actual_full_native_primitive_banks_read=0,actual_full_native_vector_streams_regenerated=0,
        actual_fresh_independent_received_signal_or_MP80_MP100_moment_calculations=0,
        original_optimizer_RNG_or_gradient_calls=0,
        recipe_manifest_SHA256=recipe.sha(args.recipe/'recipe-manifest.json'),
        verifier_SHA256=recipe.sha(Path(__file__)),
        this_metadata_check_certifies_fresh_full_vector_physics=False,
        author_performance_MC_dual_language_curve_original_reference_or_full_paper_pass=False)
    recipe.save(args.output,result);print(json.dumps(result),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('recipe','native-packet','native-restored','output'):p.add_argument('--'+name,type=Path,required=True)
    verify(p.parse_args())
