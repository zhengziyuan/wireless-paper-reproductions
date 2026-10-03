"""Actual full six-scheme AO parity, excluding code identity/runtime only."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from execute_bank import atomic_json
from isac_metadata import complete


def compare(old_path,new_path,snapshot,output):
    spec=importlib.util.spec_from_file_location("preserved_isac_meta",snapshot/"numeric-source"/"isac_metadata.py")
    oldmeta=importlib.util.module_from_spec(spec);spec.loader.exec_module(oldmeta)
    old=json.loads(old_path.read_text());new=json.loads(new_path.read_text())
    if old["input_fingerprint"]!=new["input_fingerprint"]:raise ValueError("Exact same full scenario fingerprint required")
    if not oldmeta.complete(old,old["input_fingerprint"]) or not complete(new,new["input_fingerprint"]):raise ValueError("Both original and new FULL original six-scheme receipts must actually pass")
    checks={key:old[key]==new[key] for key in ["metrics","checks","history"]}
    result={"paper_id":"rotatable-isac","scope":"actual_full_six_scheme_AO_original_vs_fixed_channel_version_one_scenario_not_full100_channel_figures",
        "same_input_fingerprint":old["input_fingerprint"],"old_implementation_fingerprint":old["implementation_fingerprint"],"new_implementation_fingerprint":new["implementation_fingerprint"],
        "old_source_result_sha256":hashlib.sha256(old_path.read_bytes()).hexdigest(),"new_source_result_sha256":hashlib.sha256(new_path.read_bytes()).hexdigest(),
        "all_actual_metrics_states_checks_and_full_AO_histories_bitwise_equal":all(checks.values()),"checks":checks,
        "old_elapsed_seconds":old["elapsed_seconds"],"new_elapsed_seconds":new["elapsed_seconds"],"measured_full_scenario_speedup":old["elapsed_seconds"]/new["elapsed_seconds"],
        "all100_channels_or_all500_jobs_completed":False,"historical_original_figure_closeness_verified":False}
    output.parent.mkdir(parents=True,exist_ok=True);atomic_json(output,result);print(json.dumps(result))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--old",type=Path,required=True);p.add_argument("--new",type=Path,required=True);p.add_argument("--snapshot",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args();compare(a.old,a.new,a.snapshot,a.output)
