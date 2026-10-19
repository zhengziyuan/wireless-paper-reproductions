"""Cold full six-scheme original scenario with isolated stable arithmetic only."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
from equivalent_runtime import binding,load_core


def run(config,scenario,output):
    if output.exists():raise FileExistsError('Preserve prior full result')
    before=binding();before['tools/isac-line-search-replay/run_equivalent.py']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    core=load_core();package=Path(__file__).resolve().parents[2]/'strict/rotatable-isac'
    sys.path.insert(0,str(package));spec=importlib.util.spec_from_file_location('original_isac_run_adapter',package/'run.py')
    runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    runner.optimize=core.optimize;runner.evaluate=core.evaluate
    c=json.loads(scenario.read_bytes());started=time.perf_counter()
    # No fixture, scenario, iteration limit or initialization is changed.
    result=runner.run_scenario(c)
    after=binding();after['tools/isac-line-search-replay/run_equivalent.py']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    assert before==after
    result.update(scope='Full original cold six-scheme case; equivalent stable self-excluded interference arithmetic',
        original_strict_files_unchanged=True,executed_source_binding=before,
        implementation_fingerprint=hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),
        input_config_sha256=hashlib.sha256(config.read_bytes()).hexdigest(),input_scenario_sha256=hashlib.sha256(scenario.read_bytes()).hexdigest(),
        original_controls={key:c[key] for key in ('W_solver','RCG_solver','PGA_solver','AO_solver')},
        elapsed_seconds=time.perf_counter()-started,independent_physics_dual_language_original_reference_or_full_paper_pass=False)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(checks=result['checks'],elapsed_seconds=result['elapsed_seconds'])),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True);p.add_argument('--scenario',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.config,a.scenario,a.output)
