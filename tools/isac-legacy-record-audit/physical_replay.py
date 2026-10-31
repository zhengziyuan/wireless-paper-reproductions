"""Reform every complete historical-state MP field and compare full coordinates."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import numpy as np
import mpmath as mp
import evidence as e
import legacy_fields as kernels


def compare_full_lanes(fresh,sealed):
    e.require(set(fresh)==set(sealed)=={'80','100'},'Both complete arbitrary-precision field lanes are required')
    counts={};maximum=mp.mpf(0)
    with mp.workdps(140):
        for digits in ('80','100'):
            a,b=fresh[digits],sealed[digits]
            e.require(set(a)==set(b)=={'full_fields','full_metrics'},'A complete field/metric lane is missing')
            e.require(set(a['full_fields'])==set(b['full_fields'])=={
                'direct','RIS_outgoing','BS_RIS_bridge','cascade','effective','received_signal','transmit_covariance',
                'BS_positions','RIS_positions','BS_frame','RIS_frame'},'One complete physical field matrix is missing')
            count=0
            for name,value in a['full_fields'].items():
                other=b['full_fields'][name]
                e.require(value['shape']==other['shape'] and len(value['shape'])==2,'A full physical matrix shape differs')
                rows,columns=value['shape']
                for component in ('real','imag'):
                    e.require(len(value[component])==len(other[component])==rows and all(
                        len(row)==columns for row in value[component]+other[component]),'A complete matrix ordinate is absent')
                    for row,prior in zip(value[component],other[component]):
                        for x,y in zip(row,prior):
                            x,y=mp.mpf(x),mp.mpf(y);e.require(mp.isfinite(x) and mp.isfinite(y),'A full field ordinate is nonfinite')
                            gap=abs(x-y);maximum=max(maximum,gap);count+=1
                            e.require(gap<=mp.mpf('1e-60'),'A complete fresh physical field differs from its sealed local reference')
            e.require(count==7940,'All7940 real/imag coordinates of the eleven full physical matrices are required')
            e.require(set(a['full_metrics'])==set(b['full_metrics'])=={'Pgrid','SINR','raw_MSE'},'A complete physical metric is absent')
            scalar_count=0
            for name,value in a['full_metrics'].items():
                prior=b['full_metrics'][name];e.require(len(value)==len(prior),'A complete saved scalar array is absent')
                for x,y in zip(value,prior):
                    x,y=mp.mpf(x),mp.mpf(y);gap=abs(x-y);maximum=max(maximum,gap);scalar_count+=1
                    e.require(mp.isfinite(x) and mp.isfinite(y) and gap<=mp.mpf('1e-60'),
                        'One complete fresh physical metric differs from its sealed local reference')
            e.require(scalar_count==69,'Every66 beampattern,2 SINR and1 raw MSE ordinate is required')
            counts[digits]=dict(full_matrix_real_imag_coordinates=count,full_scalar_metrics=scalar_count)
        a,b=fresh['80'],fresh['100']
        for name,value in a['full_fields'].items():
            prior=b['full_fields'][name]
            for component in ('real','imag'):
                for row,old in zip(value[component],prior[component]):
                    for x,y in zip(row,old):
                        gap=abs(mp.mpf(x)-mp.mpf(y));maximum=max(maximum,gap)
                        e.require(gap<=mp.mpf('1e-60'),'One complete MP80/MP100 physical field coordinate differs')
        for name,value in a['full_metrics'].items():
            for x,y in zip(value,b['full_metrics'][name]):
                gap=abs(mp.mpf(x)-mp.mpf(y));maximum=max(maximum,gap)
                e.require(gap<=mp.mpf('1e-60'),'One complete MP80/MP100 physical scalar differs')
    return dict(actual_complete_coordinate_and_metric_counts_per_precision=counts,
        maximum_fresh_sealed_or_MP80_MP100_gap=mp.nstr(maximum,60),all_complete_precision_lanes_pass=True)


def replay(root,context,output):
    root,output=Path(root),Path(output);e.require(not output.exists(),'Keep previous complete physical field epochs');output.mkdir()
    data=context['data'];lanes={};actual_saved={};internals={}
    for digits in (80,100):
        with mp.workdps(digits):
            parts,metrics=kernels.fields(data,digits);internals[digits]=(parts,metrics)
            actual_saved[str(digits)]=kernels.compare_actual_saved(data,parts,metrics)
            e.require(actual_saved[str(digits)]['saved_physical_real_imag_coordinates']==772 and
                actual_saved[str(digits)]['actual_saved_metric_values']==69,'A complete original saved field/metric is missing')
            lanes[str(digits)]=dict(full_fields={name:kernels.serial(value,digits) for name,value in parts.items()},
                full_metrics={name:[mp.nstr(x,digits) for x in value] for name,value in metrics.items()})
    with gzip.open(root/'sealed-initial-full-MP80-MP100-fields.json.gz','rt',encoding='utf-8') as handle:sealed=json.load(handle)
    comparison=compare_full_lanes(lanes,sealed)
    with gzip.open(output/'fresh-complete-initial-state-MP80-MP100-fields.json.gz','wt',encoding='utf-8') as handle:
        json.dump(lanes,handle,separators=(',',':'))
    pairs=[kernels.geometry_pair(data['u_BU'][i,0][:,0],data['u_RU'][i,0][:,0]) for i in range(2)]
    masks=[bool(a[2]<0 and b[2]<0) for a,b in zip(data['uBR'].T,data['uRB'].T)]
    geometry=dict(actual_complete_first_user_ray_pairs=pairs,actual_saved_legacy_negative_cosine_BR_support=masks,
        exact_zero_BR_proved_by_all_paths_blocked=not any(masks),
        first_BR_RB_pair_matches_actual_fixed_center_LoS=bool(np.array_equal(data['uBR'][:,0],[1,0,0]) and np.array_equal(data['uRB'][:,0],[-1,0,0])),
        qualification='Necessary first-LoS geometry under the literal final R1 declaration; not proof of the unseen published random draws.')
    e.require(geometry==e.read(root/'sealed-initial-exact-first-ray-geometry.json'),
        'A complete exact saved first-ray geometry certificate differs')
    e.write(output/'fresh-complete-saved-first-ray-exact-geometry.json',geometry)
    report=dict(actual_preserved_initial_states=1,actual_complete_numeric_variables=138,
        all_actual_saved_physical_coordinates_and_metrics=actual_saved,full_MP_fields=comparison,
        complete_exact_saved_user_first_ray_pairs=2,legacy_negative_cosine_bridge_initial_visible_paths=sum(masks),
        original_snapshot_is_initial_not_final_optimizer_return=True,
        original_per_cell_binary64_target_direction_intermediates_not_saved=True,
        independent_MP_target_recipe_uses_exact_saved_grid_angles=True,
        fresh_original_optimizer_initializer_sampler_native_MAT_export_or_source_document_calls=0,
        final_R1_model_source_generation_recipe_stationarity_original_reference_or_full_six_paper_pass=False)
    e.write(output/'summary.json',report)
    return report,dict(data=data,encoded=context['encoded'],parts=internals[100][0],metrics=internals[100][1])


def controls(context,output):
    output=Path(output);e.require(not output.exists(),'Keep every prior physical negative-control epoch');output.mkdir();result=[]
    def reject(name,call,mutation):
        try:call()
        except (ValueError,AssertionError,KeyError) as error:
            result.append(dict(control=name,rejected=True,reason=str(error),actual_fixture_change=mutation));return
        raise AssertionError('An altered complete historical physical field was accepted: '+name)
    data,parts,metrics=context['data'],context['parts'],context['metrics']
    for name in ('h_all','BB','Ccov','Pgrid','SINR'):
        bad=deepcopy(data)
        if name=='h_all':
            before=complex(bad[name][1,0][-1,0]);bad[name][1,0]=np.array(bad[name][1,0],dtype=np.complex128)
            bad[name][1,0][-1,0]+=0.001;after=complex(bad[name][1,0][-1,0])
        else:
            before=complex(bad[name].flat[-1]);dtype=np.float64 if np.isrealobj(bad[name]) else np.complex128
            bad[name]=np.array(bad[name],dtype=dtype);bad[name].flat[-1]+=0.001;after=complex(bad[name].flat[-1])
        e.require(before!=after,'The requested field control was silently truncated by the saved integer dtype')
        with mp.workdps(100):
            reject('one_complete_saved_'+name+'_coordinate_altered',lambda bad=bad:kernels.compare_actual_saved(bad,parts,metrics),
                dict(before=repr(before),after=repr(after),original_numpy_dtype=str(data[name].dtype)))
    bad=deepcopy(data);del bad['g_all']
    reject('complete_saved_user_outgoing_field_omitted',lambda:kernels.compare_actual_saved(bad,parts,metrics),dict(omitted='g_all'))
    bad=deepcopy(context['encoded']);before=bad['uRB']['real_hex'][-1];bad['uRB']['real_hex'][-1]=float(0.125).hex()
    reject('last_actual_original_RB_primitive_replaced',lambda:kernels.all_hex_equal(bad,context['encoded']),
        dict(before=before,after=bad['uRB']['real_hex'][-1]))
    e.require(len(result)==7,'All seven full-field and complete primitive controls are required')
    report=dict(actual_negative_controls=7,all_expected_complete_physical_field_and_primitive_controls_rejected=True,controls=result)
    e.write(output/'all7-complete-physical-field-and-primitive-controls.json',report)
    return report
