"""Prospective WORK recording-only hooks around the frozen v3 Python engine.

No solver/model/gradient/RNG is called a second time. Original function return
objects and original call order are retained. Not installed or certified.
"""
import copy
import functools
import hashlib
import inspect
import json
from pathlib import Path

import numpy as np


def snapshot(value):
    if isinstance(value,np.ndarray):return value.copy()
    if isinstance(value,dict):return {k:snapshot(v) for k,v in value.items()}
    if isinstance(value,tuple):return tuple(snapshot(v) for v in value)
    if isinstance(value,list):return [snapshot(v) for v in value]
    if callable(value):return {'callable_name_only':getattr(value,'__qualname__',type(value).__name__)}
    return copy.deepcopy(value)


class RecordingV4:
    """Install after the original v3 controls; restore every hook on exit."""
    BOUNDARIES=('ap_no_ris','ap_ao','mr_power','mr_two_stage','ap_qt_update','mr_qt_update')

    def __init__(self,algorithms,runner=None):
        self.algorithms=algorithms;self.runner=runner;self.originals={};self.cases=[];self.current=None

    def __enter__(self):
        for name in self.BOUNDARIES:
            original=getattr(self.algorithms,name);self.originals[name]=original
            setattr(self.algorithms,name,self.boundary(name,original))
        original=self.algorithms.rmo_ascent;self.originals['rmo_ascent']=original
        self.algorithms.rmo_ascent=self.phase(original)
        original=self.algorithms.run_all_schemes;self.originals['run_all_schemes']=original
        self.algorithms.run_all_schemes=self.case(original)
        if self.runner is not None:
            self.originals['runner.run_all_schemes']=self.runner.run_all_schemes
            self.originals['runner.sample_effective']=self.runner.sample_effective
            self.runner.run_all_schemes=self.algorithms.run_all_schemes
            self.runner.sample_effective=self.sampler(self.runner.sample_effective)
        return self

    def __exit__(self,*exception):
        for name,original in self.originals.items():
            if name.startswith('runner.'):
                setattr(self.runner,name.split('.',1)[1],original)
            else:setattr(self.algorithms,name,original)

    def case(self,original):
        @functools.wraps(original)
        def call(*args,**kwargs):
            record={'data':snapshot(args[0]),'settings':snapshot(args[1]),
                'power_limits':snapshot(args[2]),'interference_limits':snapshot(args[3]),
                'boundary_calls':[],'phase_stages':[],'effective_channel_draws':[]}
            self.cases.append(record);self.current=record
            try:
                result=original(*args,**kwargs)
                record['original_numeric_result']=snapshot(result)
                record['scheme_final_states']=self.final_states(record['boundary_calls'])
                record['complete_original_return']=True
                return result
            except Exception as error:
                record['complete_original_return']=False
                record['actual_exception_type']=type(error).__name__
                record['actual_exception_message']=str(error)
                raise
        return call

    @staticmethod
    def final_states(calls):
        """Read already returned states; do not reconstruct/re-run any model."""
        complete=[c for c in calls if 'original_return' in c]
        saved=[]
        for c in complete:
            if c['function']=='ap_no_ris':
                saved.append({'scheme':'AP-NoRIS','phi':snapshot(c['original_inputs'][1]),
                    'AP_W':snapshot(c['original_return'][0]),'noRIS':True,'tts':False})
            elif c['function']=='ap_ao':
                saved.append({'scheme':'AP-AO','phi':snapshot(c['original_return'][0]),
                    'AP_W':snapshot(c['original_return'][1]),'noRIS':False,'tts':False})
        powers=[c for c in complete if c['function']=='mr_power']
        phases=[c for c in complete if c['function']=='mr_two_stage']
        # This declared mapping belongs to the frozen original eight-chain
        # call schedule. Partial/failed schedules are retained, never guessed.
        if len(powers)==6 and len(phases)==2 and len(saved)==2:
            for group,prefix in enumerate(('MR-S','MR-TTS')):
                for offset,label in enumerate(('NoRIS','PA','TS')):
                    phase=saved[0]['phi'] if label=='NoRIS' else saved[1]['phi']
                    if label=='TS':phase=phases[group]['original_return'][0]
                    saved.append({'scheme':prefix+'-'+label,'phi':snapshot(phase),
                        'MR_p':snapshot(powers[3*group+offset]['original_return'][0]),
                        'noRIS':label=='NoRIS','tts':bool(group),
                        'phase_fixed_power':snapshot(phases[group]['original_inputs'][2]) if label=='TS' else None})
        return saved

    def boundary(self,name,original):
        @functools.wraps(original)
        def call(*args,**kwargs):
            record={'function':name,'original_inputs':snapshot(args),'original_keyword_inputs':snapshot(kwargs)}
            self.current['boundary_calls'].append(record)
            try:
                result=original(*args,**kwargs)
                record['original_return']=snapshot(result)
                record['original_inputs_after']=snapshot(args)
                record['original_keyword_inputs_after']=snapshot(kwargs)
                return result
            except Exception as error:
                record['actual_exception_type']=type(error).__name__;record['actual_exception_message']=str(error)
                raise
        return call

    def phase(self,original):
        signature=inspect.signature(original)
        @functools.wraps(original)
        def call(*args,**kwargs):
            bound=signature.bind(*args,**kwargs);bound.apply_defaults()
            fg=bound.arguments['value_gradient'];last={}
            def same_fg(phi):
                result=fg(phi)
                last.update(phi=snapshot(phi),original_value=snapshot(result[0]),original_gradient=snapshot(result[1]))
                return result
            bound.arguments['value_gradient']=same_fg
            try:
                result=original(*bound.args,**bound.kwargs)
            except Exception as error:
                self.current['phase_stages'].append({'complete_original_return':False,
                    'actual_exception_type':type(error).__name__,'actual_exception_message':str(error),
                    'original_last_fg_call':snapshot(last),'original_phase_status':snapshot(bound.arguments.get('status')),
                    'no_extra_gradient_evaluation':True})
                raise
            closure={name:snapshot(cell.cell_contents) for name,cell in zip(
                getattr(fg,'__code__',None).co_freevars if hasattr(fg,'__code__') else (),
                fg.__closure__ or ())} if hasattr(fg,'__closure__') else {}
            record={'original_final_phi':snapshot(result[0]),'original_history':snapshot(result[1]),
                'complete_original_return':True,
                'original_final_fg_call':snapshot(last),'same_final_phi_as_existing_FG_call':
                bool(np.array_equal(result[0],last['phi'])),'original_FG_closure_context':closure,
                'original_phase_status':snapshot(bound.arguments.get('status')),
                'no_extra_gradient_evaluation':True}
            self.current['phase_stages'].append(record)
            return result
        return call

    def sampler(self,original):
        @functools.wraps(original)
        def call(data,phi,rng):
            if not self.current['effective_channel_draws']:
                self.current['actual_MC_rng_state_before']=snapshot(rng.bit_generator.state)
                self.current['actual_MC_phi']=snapshot(phi)
            result=original(data,phi,rng)
            self.current['effective_channel_draws'].append(snapshot(result))
            self.current['actual_MC_rng_state_after']=snapshot(rng.bit_generator.state)
            return result
        return call

    def save(self,prefix):
        """Generated actual data only. Array values remain dtype/shape exact."""
        prefix=Path(prefix);npz_path=Path(str(prefix)+'.npz');json_path=Path(str(prefix)+'.json')
        assert not npz_path.exists() and not json_path.exists()
        arrays={}
        def encode(value):
            if isinstance(value,np.ndarray):
                key='array_'+str(len(arrays));arrays[key]=value
                return {'recorded_array':key,'shape':list(value.shape),'dtype':value.dtype.str}
            if isinstance(value,np.generic):return encode(value.item())
            if isinstance(value,complex):
                return {'recorded_complex_scalar':{'real':encode(value.real),'imag':encode(value.imag)}}
            if isinstance(value,float) and not np.isfinite(value):
                return {'recorded_nonfinite_scalar':str(value)}
            if isinstance(value,dict):return {k:encode(v) for k,v in value.items()}
            if isinstance(value,(tuple,list)):return [encode(v) for v in value]
            return value
        payload=encode(self.cases)
        prefix.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(npz_path,**arrays)
        digest=hashlib.sha256(npz_path.read_bytes()).hexdigest()
        receipt={'scope':'prospective_WORK_recording_only_existing_v3_calls_NOT_new_science_or_certified_bank',
            'cases':payload,'actual_saved_array_bank_sha256':digest,
            'recorder_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'no_extra_original_model_gradient_solver_or_random_draw_call':True,
            'native_Python_recording_adapter_actual_preflight_pass':False,'full_reproduction_pass':False}
        json_path.write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        return receipt
