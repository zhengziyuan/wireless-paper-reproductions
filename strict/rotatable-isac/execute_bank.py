"""Durable complete-bank execution; no channel/scheme/budget reduction.

Prepare inputs with figures.py --prepare first. Every required job is retained,
including failed/nonconverged outcomes. A bounded worker count controls CPU,
not the experiment population. Each worker runs the unchanged full scenario
entrypoint in a separate process with one BLAS thread.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import time

from isac_metadata import bank_complete, implementation_fingerprint, reusable


def atomic_json(path, value):
    path=Path(path); temporary=path.with_suffix(path.suffix+".tmp")
    encoded=json.dumps(value,indent=2,allow_nan=False)+"\n"
    for attempt in range(8):
        try:
            temporary.write_text(encoded,encoding="utf-8");temporary.replace(path);return
        except OSError as error:
            if error.errno!=13 and getattr(error,"winerror",None) not in [5,32,33]:raise
            if attempt==7:raise RuntimeError("Transient I/O receipt write exhausted retries; this is not a numerical failure") from error
            time.sleep(min(.1*2**attempt,2.))


def execute(bank, workers,previous_runner_sha256=None):
    config_path=bank/"run_config.json";config_bytes=config_path.read_bytes()
    manifest=json.loads((bank/"manifest.json").read_text())
    if manifest.get("realizations_per_case")!=100 or not bank_complete(bank/"jobs",manifest,config_bytes):
        raise ValueError("Complete original 100-channel input bank and immutable configuration required")
    implementation=implementation_fingerprint()
    records=[];began=time.perf_counter();runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    def job(entry):
        output=bank/(Path(entry["filename"]).stem+"-python.json")
        if reusable(output,entry["input_fingerprint"]):
            return dict(entry,status="reused_converged",result=output.name)
        env=dict(os.environ,OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1",MKL_NUM_THREADS="1")
        process=subprocess.run([sys.executable,str(Path(__file__).with_name("run.py")),
            "--config",str(config_path),"--scenario",str(bank/"jobs"/entry["filename"]),
            "--output",str(output)],capture_output=True,text=True,env=env)
        valid=reusable(output,entry["input_fingerprint"])
        if not output.exists():
            atomic_json(output,{"paper_id":"rotatable-isac","mode":"full_scenario","status":"failed",
                "input_fingerprint":entry["input_fingerprint"],"implementation_fingerprint":implementation,
                "process_exit_code":process.returncode,"error":process.stderr[-4000:]})
        return dict(entry,status="converged_complete" if valid else "executed_failed_or_unconverged",
                    result=output.name,process_exit_code=process.returncode)
    def receipt():
        success=sum(r["status"] in ["reused_converged","converged_complete"] for r in records)
        return {"paper_id":"rotatable-isac","scope":"original_full_channel_bank_execution",
            "case_count":manifest["case_count"],"channels_per_case":100,"scheme_count":6,
            "expected_jobs":manifest["expected_jobs"],"finished_jobs":len(records),"successful_jobs":success,
            "failed_or_unconverged_jobs":len(records)-success,"workers":workers,"blas_threads_per_worker":1,
            "implementation_fingerprint":implementation,"input_bank_complete":True,
            "runner_source_sha256":runner_sha256,"io_only_predecessor_runner_source_sha256":previous_runner_sha256,
            "runner_io_retry_policy":"8 bounded retries for Windows sharing/access transient errors; no numerical parameter mutation",
            "elapsed_seconds":time.perf_counter()-began,"records":records,
            "full_bank_execution_complete":len(records)==manifest["expected_jobs"],
            "overall_full_success":success==manifest["expected_jobs"],
            "original_figure_reproduction_certified":False}
    atomic_json(bank/"execution-progress.json",receipt())
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures=[pool.submit(job,entry) for entry in manifest["files"]]
        for future in as_completed(futures):
            records.append(future.result())
            atomic_json(bank/"execution-progress.json",receipt())
            print(json.dumps({"finished_jobs":len(records),"expected_jobs":manifest["expected_jobs"],
                "latest":records[-1]["result"],"status":records[-1]["status"]}),flush=True)
    final=receipt();atomic_json(bank/"execution-summary.json",final)
    return final


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--bank",type=Path,required=True)
    parser.add_argument("--workers",type=int,default=1)
    parser.add_argument("--previous-runner-sha256",default=None,help="Explicit hash of a prior I/O-only runner for recovery provenance")
    args=parser.parse_args()
    if not 1<=args.workers<=4:raise ValueError("Resource-bounded workers must be1 through4")
    if args.previous_runner_sha256 and (len(args.previous_runner_sha256)!=64 or any(c not in "0123456789abcdef" for c in args.previous_runner_sha256.lower())):raise ValueError("Prior runner SHA256 must be64 hex characters")
    print(json.dumps(execute(args.bank,args.workers,args.previous_runner_sha256)),flush=True)
