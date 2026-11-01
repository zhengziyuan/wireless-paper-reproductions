"""Future finite saved-JSON assembly, gated on actual native cohort closure.

No process launch/poll loop, optimizer, MP, MAT/RAW read, MC or channel draw.
"""
from pathlib import Path
import argparse,csv,hashlib,importlib.util,json,math,struct,sys
HERE=Path(__file__).resolve().parent;B=HERE.parent;R=B.parent
OLD=B/'Fig4-Fig5-current-closed-unfitted-reference-v1/collect_closed_U6_Fig4_Fig5_unfitted_reference_v1.py'
sp=importlib.util.spec_from_file_location('existing_closed_scalar_functions',OLD);old=importlib.util.module_from_spec(sp);sp.loader.exec_module(old)
sys.path.insert(0,str(old.HELPER.parent));from root_shared_controller_snapshot_v1 import read_snapshot
METHODS=old.METHODS
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
    if not v:raise ValueError(m)
def put(p,v):
    with Path(p).open('x',encoding='utf-8',newline='\n')as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def snapshot(path):
    s=read_snapshot(path);return s['parsed_JSON'],dict(path=str(path),SHA256=s['SHA256'],bytes=len(s['raw_bytes']))
def stats(rows,key):
    ds=[r[key]for r in rows]
    return dict(count=len(ds),maximum_absolute=max(map(abs,ds)),RMS=math.sqrt(math.fsum(x*x for x in ds)/len(ds)),mean_signed=math.fsum(ds)/len(ds))
def csv_write(p,rows,columns):
    with p.open('x',encoding='utf8',newline='')as f:
        w=csv.DictWriter(f,fieldnames=columns);w.writeheader()
        for row in rows:w.writerow({k:row.get(k)for k in columns})
    with p.open(encoding='utf8',newline='')as f:
        saved=list(csv.DictReader(f));need(len(saved)==len(rows),'CSV row count')
        for a,b in zip(saved,rows):
            for k in columns:
                if type(b.get(k))is float:need(struct.pack('>d',float(a[k]))==struct.pack('>d',b[k]),'CSV float64 roundtrip '+k)
def closed0(path,reader,expected=None):
    j,ident=reader.json(path,expected);life=old.closure_status(j)
    need(life['status']=='closed'and life['actual_child_exit_code']==life['effective_host_exit_code']==0 and not life['original_host_errors'],'Actual same-held/birth/natural0/source interval: '+str(path))
    return j,ident

def run(plan_path,output):
    plan=json.loads(plan_path.read_bytes());need(plan['prepared_only_no_collection_executed']is True,'Exact prepared assembly plan')
    for p,digest in plan['source_pins'].items():need(sha(p)==digest,'Frozen scalar assembly dependency '+p)
    need(not output.exists(),'Fresh output only; no overwrite or automatic continuation')
    reader=old.Reader()
    producer,pid=snapshot(Path(plan['producer_progress']));science,sid=snapshot(Path(plan['science_progress']))
    # Progress counts alone are never sufficient. Both original owners and
    # each original child/auditor journal are required below.
    need(producer['status']=='completed_all23_natural_children'and producer['all23_producer_host0']is True and not producer['failed_points'],'Native producer actual completed cohort metadata required')
    need(science['status']=='completed'and science['all23_three_stage_scientific_PASS']is True and not science['failed']and not science['pending']and science['active']is None,'Native all23 saved-stage actual closure required')
    _,producer_owner_id=closed0(Path(plan['producer_owner_journal']),reader)
    _,science_owner_id=closed0(Path(plan['science_owner_journal']),reader)
    producers={x['point_id']:x for x in producer['closed_points']};scientific={x['point_id']:x for x in science['completed']}
    need(len(producers)==len(scientific)==23 and set(producers)==set(scientific),'Exactly23 distinct matching closed native inputs')
    refs,refid=reader.json(old.REFERENCE,old.REFERENCE_SHA256);construction,construction_id=reader.json(old.CONSTRUCTION)
    all_specs={x['point_id']:x for x in construction['points']};need(len(construction['points'])==len(all_specs)==24 and 'kN20-INR001' not in producers and set(all_specs)==set(producers)|{'kN20-INR001'},'Exactly23 new generated native points plus the fixed separately verified reused first point');specs={k:v for k,v in all_specs.items()if k!='kN20-INR001'}
    user,user_id=reader.json(old.U6_CONFIRMATION)
    py,pyid=reader.json(Path(plan['published_Python24_report']),plan['published_Python24_report_SHA256'])
    need(py['lane']=='python'and py['all24_points_all8_actual_methods_present']and py['every_actual_result_configuration_producer_and_science_binding_pass'],'Reuse actual published Python24 only')
    pyrows={(x['point_id'],x['method']):x for x in py['rows']};pypoints={x['point_id']:x for x in py['points']}
    need(len(pyrows)==192 and len(pypoints)==24,'Exactly192 existing Python values')
    first,first_id=reader.json(old.FIRST,old.FIRST_SHA256)
    firstclose,firstclose_id=reader.json(old.FIRST_NATIVE,'186ecdb900c38aba721c63d73d2a50aad5bc5df2ef75dd73d7fd10678b5939ea')
    need(firstclose['scoped_saved_scientific_PASS']and firstclose['original_native_producer_natural_exit']==0 and firstclose['all_source_and_input_intervals_closed'],'Exact first native four-stage closure reused')
    stage_info=firstclose['stage_receipts']['ownstate'];firststage,firststageid=reader.json(stage_info['path'],stage_info['SHA256'])
    need(firststage['actual_stage_pass']and firststage['source_interval_pass']and firststage['source_before']==firststage['source_after']and firststage['actual_error']is None,'First actual ownstate source interval')
    first_projection_paths=[p for p in firststage['source_before']if p.endswith('native-U6-original-config-text-metadata-only-projection.json')]
    need(len(first_projection_paths)==1,'Exact first full-JSON metadata projection route')
    projected,firstprojectid=reader.json(first_projection_paths[0],firststage['source_before'][first_projection_paths[0]])
    firstcfg=projected['configuration'];firstvalues=old.result_view(projected,firstcfg,'python')
    need(firststage['configuration_metadata_binding']['original_JSON_SHA256']==first['original_full_JSON_SHA256'],'First science full configuration binding')
    for row in first['rows']:
        need(all(old.same_float(a,b)for a,b in zip(firstvalues[row['scheme']]['all6_SINR_linear'],row['native_all6_SINR_linear'])),'First actual native six values equal exact previously closed comparison')
    points=[];rows=[]
    for kn in (20,0):
        for index in range(1,13):
            point='kN%d-INR%03d'%(kn,index)
            if point=='kN20-INR001':
                cfg=firstcfg;values=firstvalues
                binding=dict(point_id=point,reused_previously_closed_first=True,science_summary=firstclose_id,recorded_result=firstprojectid,original_result=first['native_result'],configuration_SHA256=first['original_full_JSON_SHA256'],native_saved_science_PASS=True,producer_same_handle_natural0_sourceclosed=True,result_configuration_and_science_binding_pass=True,first_four_stage_closure_reused=True,first_performance_values_IEEE_bound_to_original_closed_comparison=True)
            else:
                pr=producers[point];sr=scientific[point];spec=specs[point]
                need(pr['actual_child_exit_code']==pr['effective_host_exit_code']==0 and pr['natural_wait_completed']and pr['same_original_handle_birth_exit']and pr['source_interval_pass']and pr['all11_actual_input_binding_pass'],'Actual native point producer binding '+point)
                need(sr['scientific_pass']and sr['actual_reader_effective_exit']==0,'Actual saved-stage result '+point)
                summ,summid=reader.json(sr['closure'],sr['closure_SHA256'])
                need(summ['point_id']==point and summ['three_saved_scientific_stages_pass']and summ['source_interval_pass']and summ['source_before']==summ['source_after'],'Exact scientific closure/source interval '+point)
                need(summ['original_producer_exit_code']==summ['original_effective_host_exit_code']==0 and not summ['original_host_errors'],'Science preserves original producer exit '+point)
                need(summ['nonconfiguration_numeric_bits_preserved']and summ['actual_recording_counts']['final_states']==8 and summ['existing_MC1000_gate_reused_without_replay'],'Original full8 and bound same-lane MC evidence '+point)
                need(set(summ['stages'])=={'ownstate','stops','initial'}and all(x['passed']and x['error']is None and all(v is True for v in x['required_flags'].values())for x in summ['stages'].values()),'All three existing scientific stages '+point)
                _,auditor_id=closed0(Path(sr['actual_reader_owned_journal']),reader,sr['actual_reader_owned_journal_SHA256'])
                journal,journal_id=closed0(Path(pr['journal']),reader)
                cfg,cfgid=reader.json(spec['full_original_configuration'],spec['full_configuration_SHA256'])
                need(journal['source_before'].get(cfgid['path'])==cfgid['SHA256'] and summ['source_before'].get(cfgid['path'])==cfgid['SHA256'],'Producer/auditor same full configuration '+point)
                resultpath=Path(pr['output'])/'actual-native-complete-timed-result.json'
                result,rid=reader.json(resultpath,summ['source_before'][str(resultpath)])
                need(summ['source_before'].get(journal_id['path'])==journal_id['SHA256'],'Scientific closure binds exact original terminal '+point)
                values=old.result_view(result,cfg,'native')
                binding=dict(point_id=point,reused_previously_closed_first=False,science_summary=summid,recorded_result=rid,original_result=rid,configuration_SHA256=cfgid['SHA256'],actual_configuration=cfgid,producer_journal=journal_id,auditor_journal=auditor_id,moment_mode=pr['moment_mode'],native_saved_science_PASS=True,producer_same_handle_natural0_sourceclosed=True,result_configuration_and_science_binding_pass=True,three_newpoint_stages_reused_without_MP=True,actual_saved_counts=summ['actual_recording_counts'],same_lane_existing_MC1000_evidence_reused_without_new_audit=True)
            rep=cfg['reported'];need(tuple(rep[k]for k in ('J','U','N','M','K'))==(3,6,16,25,1)and rep['kappa_leo_db']==kn and rep['kappa_ground_db']==10 and rep['kappa_geo_db']==30 and rep['power_w']==50 and old.same_float(rep['interference_to_noise_ratio'],index/100.),'Exact author-confirmed24-point scope')
            need(binding['configuration_SHA256']==pypoints[point]['configuration_SHA256'],'Same actual full configuration as the published Python point')
            binding.update(kappaN_dB=kn,ordinal_one_based=index,normalized_INR=index/100.,scientific_configuration=dict(reported=rep,tuned_not_reported=cfg['tuned_not_reported']));points.append(binding)
            for method in METHODS:
                ref=old.reference_row(refs[str(4 if kn==20 else 5)],method,index);value=values[method]['minSINR_linear'];y=ref['original_mapped_y_linear_SINR'];delta=value-y;prior=pyrows[point,method];pv=prior['python_minSINR_linear']
                need(old.same_float(prior['original_mapped_y_linear_SINR'],y)and prior['configuration_SHA256']==binding['configuration_SHA256'],'Exact same historical ordinate/configuration; no reference substitution')
                rows.append(dict(point_id=point,kappaN_dB=kn,kappaR_dB=10,ordinal_one_based=index,**ref,original_vector_x=ref['original_vector_plot_coordinate'][0],original_vector_y=ref['original_vector_plot_coordinate'][1],native_minSINR_linear=value,all6_native_SINR_linear=values[method]['all6_SINR_linear'],python_minSINR_linear=pv,native_minus_python=value-pv,absolute_native_python_gap=abs(value-pv),signed_difference_from_EPS=delta,absolute_difference_from_EPS=abs(delta),signed_relative_difference_from_EPS=delta/y if y else None,absolute_difference_in_full_EPS_ordinate_steps=abs(delta)/ref['EPS_full_y_ordinate_rounding_step'],within_one_full_EPS_ordinate_step=abs(delta)<=ref['EPS_full_y_ordinate_rounding_step'],native_saved_science_PASS=True,Python_previously_published_science_PASS=prior['Python_saved_science_PASS'],producer_same_handle_natural0_sourceclosed=True,result_configuration_and_science_binding_pass=True,configuration_SHA256=binding['configuration_SHA256'],original_result_SHA256=binding['original_result']['SHA256'],science_summary_SHA256=binding['science_summary']['SHA256'],optimized_equality_gate_applied=False,same_state_physical_fields_tested=False))
    need(len(points)==24 and len(rows)==192 and len({(x['point_id'],x['method'])for x in rows})==192,'All24 x8 unique actual ordinates')
    _,pid_after=snapshot(Path(plan['producer_progress']));_,sid_after=snapshot(Path(plan['science_progress']))
    need(pid_after==pid and sid_after==sid,'Closed small ledgers unchanged during saved readback')
    summaries={}
    for fig in (4,5):
        rr=[x for x in rows if x['figure']==fig]
        summaries[str(fig)]=dict(native_unfitted_EPS=stats(rr,'signed_difference_from_EPS'),native_minus_saved_Python=stats(rr,'native_minus_python'),within_full_EPS_step=sum(x['within_one_full_EPS_ordinate_step']for x in rr),outside_full_EPS_step=sum(not x['within_one_full_EPS_ordinate_step']for x in rr),full_EPS_ordinate_step=refs[str(fig)]['maximum_ordinate_rounding_resolution'],maximum_absolute_relative_EPS_gap=max(abs(x['signed_relative_difference_from_EPS'])for x in rr if x['signed_relative_difference_from_EPS']is not None),minimum_absolute_gap_in_full_EPS_steps=min(x['absolute_difference_in_full_EPS_ordinate_steps']for x in rr),maximum_absolute_gap_in_full_EPS_steps=max(x['absolute_difference_in_full_EPS_ordinate_steps']for x in rr),methods={m:dict(EPS=stats([x for x in rr if x['method']==m],'signed_difference_from_EPS'),dual=stats([x for x in rr if x['method']==m],'native_minus_python'))for m in METHODS})
    report=dict(schema='actual-native24-complete-192-unfitted-EPS-and-existing-Python192-saved-scalar-comparison-v1',lane='native',all24_points_all8_actual_methods_present=True,actual_point_count=24,actual_method_ordinates=192,producer_progress=pid,science_progress=sid,producer_owner=producer_owner_id,science_owner=science_owner_id,reference=refid,construction=construction_id,user_confirmation=user_id,existing_published_Python24=pyid,points=points,rows=rows,summaries=summaries,completed_small_ledgers_unchanged=True,all23_existing_three_stage_summaries_and_original_first_four_stage_closure_reused=True,every_actual_result_configuration_producer_and_science_binding_pass=True,interpretation=dict(author_confirmed_U6_J3_N16_M25_K1_P50_kR10_kG30=True,all24x8_are_saved_optimized_scenarios_not1000_performance_repetitions=True,MC1000_are_independent_channel_moment_populations_with_same_lane_family_reuse=True,no_fitting_interpolation_rescaling_or_hidden_unit_conversion=True,historical_W_versus_normalized_INR_mapping_unresolved=True,ordinal_pairing_not_unit_recovery=True,EPS_step_is_coordinate_quantization_not_CI=True,optimized_language_difference_not_same_state_physical_residual_or_solution_equality=True,author_cached_W_random_initial_phi_and_optimized_performance_population_not_recovered=True),original_reference_PASS=False,optimized_dual_equality_PASS=False,full_paper_PASS=False,fresh_optimizer_MC_RNG_MP_or_input_generation_calls=0,consumed_only_closed_JSON_inputs=reader.consumed)
    output.mkdir(parents=True,exist_ok=False);name='ACTUAL_NATIVE24_FIG4_FIG5_UNFITTED_REFERENCE_REUSED_SCIENCE_AND_SAVED_PYTHON192_V1.json';put(output/name,report)
    columns=['figure','point_id','method','kappaN_dB','kappaR_dB','ordinal_one_based','nominal_paired_INR','original_vector_x','original_vector_y','original_mapped_x','original_mapped_y_linear_SINR','native_minSINR_linear','python_minSINR_linear','native_minus_python','absolute_native_python_gap','signed_difference_from_EPS','absolute_difference_from_EPS','signed_relative_difference_from_EPS','absolute_difference_in_full_EPS_ordinate_steps','EPS_full_x_coordinate_rounding_step','EPS_full_y_ordinate_rounding_step','within_one_full_EPS_ordinate_step','native_saved_science_PASS','Python_previously_published_science_PASS','producer_same_handle_natural0_sourceclosed','result_configuration_and_science_binding_pass','configuration_SHA256','original_result_SHA256','science_summary_SHA256']
    csv_write(output/'Native24_Fig4_Fig5_192_unfitted_EPS_and_saved_Python_ordinates.csv',rows,columns)
    public=output/'public';public.mkdir();projpath=Path(plan['metadata_projection_helper']);sp=importlib.util.spec_from_file_location('existing_metadata_projection_only',projpath);proj=importlib.util.module_from_spec(sp);sp.loader.exec_module(proj)
    aliases={x:'source-'+hashlib.sha256(x.encode()).hexdigest()[:12]+'/'+x.replace('\\','/').split('/')[-1]for x in proj.paths_in(report)};public_report=proj.project(report,aliases);proj.numeric_identity(report,public_report);put(public/name,public_report)
    (public/'Native24_Fig4_Fig5_192_unfitted_EPS_and_saved_Python_ordinates.csv').write_bytes((output/'Native24_Fig4_Fig5_192_unfitted_EPS_and_saved_Python_ordinates.csv').read_bytes())
    selected={str(f):refs[str(f)]for f in (4,5)};selected_public=proj.project(selected,aliases);proj.numeric_identity(selected,selected_public);put(public/'original_EPS_Fig4_Fig5_vector_coordinates_and_calibration.json',selected_public)
    (public/'README.md').write_text('''# Complete native U6 Fig4/5: saved-only unfitted EPS and Python comparison

This packet contains24 actual native configurations and192 point-method rows (12 paired ordinals per figure, eight methods per point), with all six saved user SINRs. It reuses23 actual source-bound producer/three-stage closures and the independently closed original first point. Both original cohort owners and every per-point producer/auditor must have actual same-held natural0 terminals/source closure before assembly. Progress counts never substitute for those checks. No physics, MP, optimizer, MC or input generation was rerun.

The existing published Python192 values are joined by exact point/method and full configuration digests. Independently optimized scalar gaps are not same-state field residuals or an equality gate. Raw historical EPS ordinates and vector coordinates are retained unchanged, without fitting/interpolation/rescaling. Pairing uses ordinal1..12; the historical W versus reconstructed normalized-INR mapping remains unresolved. EPS steps describe coordinate quantization, not confidence intervals. Original-reference, optimized-dual-equality and full-paper gates remain false.

The user-confirmed scene uses U6/J3/N16/M25/K1, P50W, ground kappa10dB and GEO kappa30dB. The two axes use LEO kappa20/0dB. The actual1000 channel draws or explicit same-lane/family audited reuse validate moments;24x8 saved optimized methods are not1000 optimized performance repetitions. The author cached W/random phase and historical optimized averaging population have not been recovered. Metadata path projection preserves numeric values and CSV float64 bits. This scalar evidence does not replace the underlying closed science receipts.
'''.replace('contains24','contains 24').replace('and192','and 192').replace('reuses23','reuses 23').replace('Python192','Python 192').replace('ordinal1','ordinal 1').replace('actual1000','actual 1000').replace(';24x8','; 24x8').replace('not1000','not 1000'),encoding='utf8')
    manifest={'files':[dict(path=p.name,bytes=p.stat().st_size,SHA256=sha(p))for p in sorted(public.iterdir())if p.is_file()]};put(public/'MANIFEST.json',manifest)
    put(output/'FINAL_NATIVE24_SAVED_SCALAR_PUBLIC_DRAFT_PLAN_V1.json',dict(public_directory=str(public),repository_relative_directory=plan['publication_target'],files=[dict(path=p.name,bytes=p.stat().st_size,SHA256=sha(p))for p in sorted(public.iterdir())if p.is_file()],source_bindings_complete=True,all192_CSV_float64_fields_checked=True,new_scientific_calls=0,original_reference_PASS=False,Git_actions=0))
    print(json.dumps(dict(output=str(output),points=24,rows=192,reference_PASS=False,new_scientific_calls=0,summaries=summaries),indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--finish',action='store_true',required=True);p.add_argument('--plan',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();run(a.plan,a.output_dir)
