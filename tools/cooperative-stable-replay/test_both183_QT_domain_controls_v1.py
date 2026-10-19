"""Exercise strict primal domains and the unchanged1e-5 physical tolerance."""
import argparse
import copy
import json
from pathlib import Path

import numpy as np
import audit_both183_QT_domains_v1 as checker


def run(output):
    checker.require(not output.exists(),'Preserve domain-control evidence')
    rows=[]
    def rejected(label,call):
        try:value=call()
        except ValueError as error:rows.append(dict(control=label,rejected=True,reason=str(error)));return
        checker.require(not value,'Invalid primal/physical domain accepted: '+label)
        rows.append(dict(control=label,rejected=True,reason='The original domain/constraint gate is false'))
    shape=(3,2)
    rejected('missing_MR_primal_coordinate',lambda:checker.domain(np.ones(5),shape,True)['passed_strict_domain'])
    rejected('complex_MR_primal',lambda:checker.domain(np.ones(shape,dtype=complex)+1j,shape,True)['passed_strict_domain'])
    rejected('nonfinite_MR_primal',lambda:checker.domain(np.full(shape,np.inf),shape,True)['passed_strict_domain'])
    rejected('nan_AP_primal',lambda:checker.domain(np.full((3,16,2),np.nan+1j), (3,16,2),False)['passed_strict_domain'])
    rejected('AP_vector_replaced_by_one_norm',lambda:checker.domain(np.ones(1),(3,16,2),False)['passed_strict_domain'])
    rejected('negative_MR_within_constraint_tolerance',lambda:checker.domain(np.full(shape,-1e-10),shape,True)['passed_strict_domain'])
    fields=dict(satellite_power=dict(reference=['1']),gt_interference=dict(reference=['1']),denominator=dict(reference=['1']))
    def constraint(change):
        values=copy.deepcopy(fields);change(values)
        return checker.feasibility(values,np.ones(1),np.ones(1))['passed_original1e_minus5_constraints']
    rejected('before_satellite_power_over_original_tolerance',lambda:constraint(lambda f:f['satellite_power'].update(reference=['1.00002'])))
    rejected('before_ground_interference_over_original_tolerance',lambda:constraint(lambda f:f['gt_interference'].update(reference=['1.00002'])))
    rejected('zero_received_signal_denominator',lambda:constraint(lambda f:f['denominator'].update(reference=['0'])))
    rejected('negative_received_signal_denominator',lambda:constraint(lambda f:f['denominator'].update(reference=['-1'])))
    rejected('nonfinite_MP100_physical_field',lambda:constraint(lambda f:f['satellite_power'].update(reference=['NaN'])))
    rejected('missing_original_physical_bound',lambda:checker.feasibility(fields,np.ones(2),np.ones(1))['passed_original1e_minus5_constraints'])
    checker.require(checker.domain(np.zeros(shape),shape,True)['passed_strict_domain'],'Zero MR positive control failed')
    checker.require(checker.domain(np.ones((3,16,2))+1j,(3,16,2),False)['passed_strict_domain'], 'Finite complex AP positive control failed')
    checker.require(constraint(lambda f:f['satellite_power'].update(reference=['1.000005'])),'Original1e-5 positive control failed')
    checker.require(len(rows)==12,'A mandatory invalid-domain control is missing')
    result=dict(actual_negative_controls=12,all_expected_invalid_primal_or_physical_domains_rejected=True,
        zero_MR_finite_complex_AP_and_original_tolerance_positive_controls_pass=True,
        checker_sha256=checker.sha(Path(checker.__file__)),control_source_sha256=checker.sha(Path(__file__)),
        synthetic_controls_only=True,original_optimizer_or_production_RNG_calls=0,controls=rows)
    checker.save(output,result)
    print(json.dumps({k:v for k,v in result.items() if k!='controls'}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    run(p.parse_args().output)
