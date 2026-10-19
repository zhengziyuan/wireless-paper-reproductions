"""Run the genuine original full12000 native Fig8 control with complete recording."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def literal(p):return "'"+str(p).replace('\\','/').replace("'","''")+"'"


def run(matlab,output):
    if output.exists():raise FileExistsError('Preserve old numerical results and use a fresh campaign folder')
    source=Path(__file__).resolve().parent/'native';binding=json.loads(source.parent.joinpath('source-binding.json').read_bytes())['native_source_files']
    before={name:sha(source/name) for name in binding}
    if before!=binding:raise ValueError('Original complete native source binding differs')
    settings=json.loads((source/'settings-cap100000.json').read_bytes())
    assert settings['number_of_starts']==6000 and settings['rcg_max_iterations']==100000 and settings['rcg_gradient_tolerance']==1e-6
    output.mkdir(parents=True);settings['recording']=dict(mode='full12000',record_folder=str(output/'records').replace('\\','/'))
    path=output/'actual-settings.json';path.write_text(json.dumps(settings,indent=2)+'\n',encoding='utf-8')
    expression='restoredefaultpath;addpath('+literal(source)+');mis_communications_fig8_full_recording_v1('+literal(output/'full-result-matlab.json')+",'record-Fig8-full12000',"+literal(path)+');'
    cmd=[str(matlab),*(['-wait'] if os.name=='nt' else []),'-batch',expression]
    start=time.perf_counter();receipt=dict(scope='Actual full6000MIS plus6000SMS, matched disclosed100000-cap Python control',
        started_utc=datetime.now(timezone.utc).isoformat(),source_files=before,actual_settings_sha256=sha(path),argv=cmd,
        old_synthetic768_storage_checks_count_as_optimizer_starts=False,unreported_cap100000_disclosed=True)
    (output/'campaign-start.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    flags={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
    with (output/'native.log').open('wb') as log:
        result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,**flags)
    after={name:sha(source/name) for name in binding}
    receipt.update(exit_code=result.returncode,elapsed_seconds=time.perf_counter()-start,sources_unchanged=before==after,
        independent_physics_or_full12000_success_or_original_reference_pass=False)
    (output/'execution-ended.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    if result.returncode or before!=after:raise SystemExit(result.returncode or 1)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--matlab',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();run(a.matlab.resolve(strict=True),a.output_dir.resolve())
