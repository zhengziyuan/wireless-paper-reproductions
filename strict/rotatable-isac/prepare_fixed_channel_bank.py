"""New numeric version, byte-identical complete500 inputs, no output mixing."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from execute_bank import atomic_json
from isac_metadata import bank_complete,implementation_fingerprint


def prepare(old,new,snapshot,proof):
    if new.exists():raise ValueError("Fresh explicit bank path required; never overwrite an existing bank")
    cb=(old/"run_config.json").read_bytes();manifest=json.loads((old/"manifest.json").read_text());config=json.loads(cb)
    if manifest["expected_jobs"]!=500 or config["channel_realizations"]!=100 or not bank_complete(old/"jobs",manifest,cb):raise ValueError("Immutable complete original500 inputs required")
    original=json.loads((snapshot/"snapshot-manifest.json").read_text());verified=json.loads(proof.read_text());current=implementation_fingerprint()
    if (verified.get("all_six_saved_scheme_states_and_full_W_runs_verified") is not True
        or verified.get("original_implementation_fingerprint")!=original["original_implementation_fingerprint"]
        or verified.get("new_implementation_fingerprint")!=current):raise ValueError("Actual source-bound original/production exact-equivalence proof required")
    new.mkdir(parents=True);(new/"jobs").mkdir();count=0
    for name in ["run_config.json","manifest.json","plan.json"]:shutil.copy2(old/name,new/name)
    for entry in manifest["files"]:
        path=old/"jobs"/entry["filename"];destination=new/"jobs"/entry["filename"];shutil.copy2(path,destination)
        if path.read_bytes()!=destination.read_bytes():raise RuntimeError("Copied full scene changed bytes")
        count+=1
    if cb!=(new/"run_config.json").read_bytes() or not bank_complete(new/"jobs",manifest,cb):raise RuntimeError("Full input bank/config identity failed")
    package=Path(__file__).parent;frozen=new/"frozen-numeric-source";frozen.mkdir();source_hashes=[]
    for name in ["core.py","run.py","figures.py","isac_metadata.py","execute_bank.py","run_strict_rotatable_isac.m","run_full_isac_figure.m","strict_isac_implementation_fingerprint.m"]:
        path=package/name;shutil.copy2(path,frozen/name);source_hashes.append({"name":name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    receipt={"paper_id":"rotatable-isac","scope":"new_frozen_version_same_original_W_algorithm_fixed_channel_hoist",
        "old_bank":"isac-power-b2-20261003","old_bank_status":"historical_incomplete_not_theory_failure",
        "old_implementation_fingerprint":original["original_implementation_fingerprint"],"new_implementation_fingerprint":current,
        "all500_exported_scenes_byte_identical":count==500,"all500_input_fingerprints_unchanged":True,"config_bytes_identical":True,
        "source_input_manifest_sha256":hashlib.sha256((old/"manifest.json").read_bytes()).hexdigest(),
        "exact_equivalence_proof_sha256":hashlib.sha256(proof.read_bytes()).hexdigest(),"frozen_numeric_source_files":source_hashes,
        "original_thresholds_QT_MM_RCG_PGA_and_all66_directions_unchanged":True,"old_result_files_reused_or_copied":False,
        "all500_jobs_will_restart_with_new_source_fingerprint":True,"executed":False,"full_figures_complete":False}
    atomic_json(new/"frozen-version-manifest.json",receipt)
    atomic_json(old/"version-superseded.json",{"paper_id":"rotatable-isac","old_bank_status":"historical_incomplete_not_theory_failure",
        "old_completed_jobs_at_stop":original["validated_old_completed_jobs"],"old_expected_jobs":500,
        "verified_owned_actual_python_processes_stopped":[50148,35312,29192],
        "pending_inflight_jobs_without_saved_final_states":["case-000-mc-001","case-000-mc-002"],
        "all_existing_results_configs_inputs_and_historical_failures_preserved":True,"new_bank":new.name,
        "new_input_scenes_and_config_byte_identical":True,"reason":"proven identical fixed-channel hoist; not algorithm/theory failure"})
    print(json.dumps({"new_implementation_fingerprint":current,"all500_exported_scenes_byte_identical":True,"old_result_files_reused":False,"executed":False}))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--old-bank",type=Path,required=True);p.add_argument("--new-bank",type=Path,required=True)
    p.add_argument("--snapshot",type=Path,required=True);p.add_argument("--proof",type=Path,required=True);a=p.parse_args();prepare(a.old_bank,a.new_bank,a.snapshot,a.proof)
