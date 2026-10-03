"""One FULL original-sized failed-power scenario, exact same-QT guard audit."""
import argparse
import hashlib
import json
import time
from pathlib import Path
from scenario import make_scenario
import algorithms
from spectral_rmo import rmo_ascent
from qt_numerical_guard import install
from receipts import save


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();base=Path(__file__).parent
    names=('diagnose_full_qt_guard.py','qt_numerical_guard.py','spectral_rmo.py','algorithms.py','models.py','increments.py','core.py','scenario.py','spectral_config.json')
    hashes={n:hashlib.sha256((base/n).read_bytes()).hexdigest() for n in names}
    c=json.loads((base/'spectral_config.json').read_text());c['reported']['power_w']=2.8284271247461903;data,pl,il=make_scenario(c)
    algorithms.rmo_ascent=rmo_ascent;install();clock=time.perf_counter()
    try:
        schemes=algorithms.run_all_schemes(data,c['tuned_not_reported'],pl,il)
        allpass=all(s['status']['algorithm_success'] for s in schemes.values());result={'schemes':schemes,'all_original_algorithm_gates_pass':allpass,'status':'executed'}
    except Exception as error:result={'all_original_algorithm_gates_pass':False,'status':'failed','error':str(error),'failure_receipt':getattr(error,'receipt',None)}
    result.update(scope='complete_full_dimension_failed_power_case_same_QT_numerical_guard_diagnosis_NOT_full_figures',
                  configuration=c,elapsed_seconds=time.perf_counter()-clock,executed_source_hashes=hashes,
                  source_unchanged_during_run=hashes=={n:hashlib.sha256((base/n).read_bytes()).hexdigest() for n in names},full_reproduction_pass=False)
    save(a.output,result);print(json.dumps({k:v for k,v in result.items() if k not in ('schemes','configuration','executed_source_hashes')}),flush=True)
    if not result['all_original_algorithm_gates_pass']:raise SystemExit(1)
