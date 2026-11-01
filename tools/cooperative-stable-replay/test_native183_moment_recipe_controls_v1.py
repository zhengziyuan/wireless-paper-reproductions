"""Reject reduced, substituted and corrupted complete native moment evidence."""
import argparse
import copy
import json
from pathlib import Path
import shutil

import numpy as np
import native183_moment_recipe_v1 as recipe


def main(args):
    recipe.require(not args.work_dir.exists() and not args.output.exists(),'Preserve control epochs')
    args.work_dir.mkdir(parents=True)
    manifest,index,_=recipe.validate_recipe(args.recipe,args.native_packet)
    group=index['groups'][0]
    original_raw=recipe.validate_operands(group,args.primitive_directory,args.recipe)
    watched=[args.recipe/'recipe-manifest.json',args.recipe/'complete-native183-moment-recipe.json',
        Path(recipe.__file__),Path(__file__),args.primitive_directory/'index.json',original_raw]
    before={str(p):recipe.sha(p) for p in watched}
    copied=args.work_dir/'copied-recipe';shutil.copytree(args.recipe,copied)
    rows=[]
    def reject(name,call):
        try:call()
        except ValueError as error:rows.append(dict(control=name,rejected=True,actual_reason=str(error)));return
        raise AssertionError('Invalid complete native moment evidence was accepted: '+name)
    def semantic(name,change):
        altered=copy.deepcopy(index);change(altered)
        recipe.save(copied/'complete-native183-moment-recipe.json',altered)
        changed=copy.deepcopy(manifest)
        path=copied/'complete-native183-moment-recipe.json'
        changed['files'][path.name]=dict(bytes=path.stat().st_size,sha256=recipe.sha(path))
        recipe.save(copied/'recipe-manifest.json',changed)
        reject(name,lambda:recipe.validate_recipe(copied,args.native_packet))
    semantic('one_original_case_removed',lambda d:d['cases'].pop())
    semantic('duplicate_original_case_ordinal',lambda d:d['cases'][1].update(ordinal=0))
    semantic('one_exact_group_removed',lambda d:d['groups'].pop())
    semantic('different_exact_coefficients_relabelled_as_same_group',lambda d:d['groups'][1].update(input_signature=d['groups'][0]['input_signature']))
    semantic('configured1000_reduced_to999',lambda d:d['groups'][0].update(count=999))
    semantic('original_complex_vector_dimension_changed',lambda d:d['groups'][0]['dimensions'].update(M=24))
    semantic('full_primitive_bank_replaced_by_short_norms',lambda d:d['groups'][0].update(raw_primitive_bytes=96000))
    semantic('wrong_original_case_to_group_alias',lambda d:d['cases'][0].update(group_ordinal=1))
    recipe.save(copied/'complete-native183-moment-recipe.json',index);recipe.save(copied/'recipe-manifest.json',manifest)
    target=copied/group['original_sample_moments']
    with target.open('r+b') as stream:
        first=stream.read(1);stream.seek(0);stream.write(bytes([first[0]^1]))
    reject('changed_complete_draw_archive_bytes',lambda:recipe.validate_recipe(copied,args.native_packet))
    raw_folder=args.work_dir/'copied-full-primitive-group0';raw_folder.mkdir()
    shutil.copyfile(args.primitive_directory/'index.json',raw_folder/'index.json')
    raw_copy=raw_folder/original_raw.name;shutil.copyfile(original_raw,raw_copy)
    with raw_copy.open('r+b') as stream:
        stream.seek(1000);first=stream.read(1);stream.seek(1000);stream.write(bytes([first[0]^1]))
    reject('one_full_complex_operand_byte_changed',lambda:recipe.validate_operands(group,raw_folder,args.recipe))
    with raw_copy.open('r+b') as stream:stream.truncate(raw_copy.stat().st_size-8)
    reject('one_full_operand_binary64_value_missing',lambda:recipe.validate_operands(group,raw_folder,args.recipe))
    changed_meta=recipe.read(raw_folder/'index.json');changed_meta['seed']+=1;recipe.save(raw_folder/'index.json',changed_meta)
    reject('different_original_native_seed',lambda:recipe.validate_operands(group,raw_folder,args.recipe))
    with np.load(args.recipe/group['original_sample_moments'],allow_pickle=False) as archive:
        original={k:archive[k] for k in archive.files}
    bad=args.work_dir/'changed-sample-draws.npz'
    changed={k:a.copy() for k,a in original.items()};changed['second']=changed['second'][:-1]
    np.savez_compressed(bad,**changed)
    reject('one_original_per_draw_moment_row_missing',lambda:recipe.compare_draws(group,bad,args.recipe))
    changed={k:a.copy() for k,a in original.items()};changed['independent_fourth'][0,0,0]=np.inf
    np.savez_compressed(bad,**changed)
    reject('nonfinite_per_draw_moment',lambda:recipe.compare_draws(group,bad,args.recipe))
    changed={k:a.copy() for k,a in original.items()};changed['second'][0,0,0]=np.nextafter(changed['second'][0,0,0],np.inf)
    np.savez_compressed(bad,**changed)
    reject('one_original_native_sample_power_bit_changed',lambda:recipe.compare_draws(group,bad,args.recipe))
    recipe.validate_recipe(args.recipe,args.native_packet)
    recipe.validate_operands(group,args.primitive_directory,args.recipe)
    recipe.compare_draws(group,args.recipe/group['original_sample_moments'],args.recipe)
    after={str(p):recipe.sha(p) for p in watched}
    recipe.require(before==after and len(rows)==15,'A control source changed or a required negative control is absent')
    result=dict(actual_negative_controls=len(rows),all_expected_invalid_full_native_moment_evidence_rejected=True,
        complete183_case67_group_positive_control_pass=True,original_full_group0_primitive_positive_control_pass=True,
        complete1000_draw_archive_positive_control_pass=True,source_before=before,source_after=after,controls=rows,
        original_optimizer_calls=0,configured_performance_MC_or_original_reference_pass=False)
    recipe.save(args.output,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('source_before','source_after','controls')}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('recipe','native-packet','primitive-directory','work-dir','output'):p.add_argument('--'+name,type=Path,required=True)
    main(p.parse_args())
