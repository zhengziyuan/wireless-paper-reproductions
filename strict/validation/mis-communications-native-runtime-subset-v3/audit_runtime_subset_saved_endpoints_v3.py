"""Public selected-runtime source binding + immutable recorded-state Decimal audit."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
PACKET=HERE.parent/"mis-communications-native-fig7-preflight-v2"
EXPECTED_FULL_ORIGIN="1a643626b2ebde224c160dcf9191ceb99b56338fe189f43d0656437ed8cefd23"


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(runtime,record_folder,scheme,start):
    origin=PACKET/"limited-native-source/recording-source-freeze.json"
    assert sha(origin)==EXPECTED_FULL_ORIGIN
    hashes=json.loads(origin.read_text(encoding="utf-8"))["files_sha256"]
    selected={rel:digest for rel,digest in hashes.items() if ("/" not in rel and (rel.endswith((".py",".m")) or rel in ("settings.json","figures.json","source_map.json","unit_fixture.json"))) or rel.startswith("tests/")}
    assert len(selected)==17
    runtime=Path(runtime);before={rel:sha(runtime/rel) for rel in selected};assert before==selected
    metadata=json.loads((runtime/"recording-source-freeze.json").read_text(encoding="utf-8"))
    assert metadata["files_sha256"]==selected and metadata["all42_source_identity_claimed"] is False
    source=PACKET/"audit_native_Fig7_saved_endpoints_v1.py"
    assert sha(source)=="0386d7a02858ac2398040db2c68085e9c49d1ba26b8f8be25c74072601e81342"
    spec=importlib.util.spec_from_file_location("immutable_native_endpoint_v1",source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    initial=json.loads((Path(record_folder)/scheme/("start-%06d-initial.json"%start)).read_text(encoding="utf-8"))
    assert initial["settings"]==json.loads((runtime/"settings.json").read_text(encoding="utf-8"))
    result=module.audit_start(record_folder,scheme,start)
    assert {rel:sha(runtime/rel) for rel in selected}==before
    result["runtime_subset_binding_v3"]={"all17_selected_runtime_source_bytes_and_entire_settings_exact":True,
        "origin_full42_manifest_sha256":EXPECTED_FULL_ORIGIN,"selected_runtime_SHA_before_after":before,
        "complete42_source_origin_verifier_run_or_pass_claimed":False,"new_native_optimizer_reexecution_claimed":False,
        "actual_source_adapter_sha256":sha(Path(__file__))}
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--runtime-source",type=Path,required=True);parser.add_argument("--record-folder",required=True)
    parser.add_argument("--scheme",choices=("MIS","SMS"),required=True);parser.add_argument("--start",type=int,required=True);parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();assert not args.output.exists()
    try:result=audit(args.runtime_source,args.record_folder,args.scheme,args.start)
    except Exception as failure:
        result={"scope":"actual_runtime_subset_v3_saved_endpoint_failure_retained","scheme":args.scheme,"start":args.start,
            "all_required_one_start_gates_pass":False,"actual_exception_class":type(failure).__name__,"actual_exception_message":str(failure),
            "actual_source_adapter_sha256":sha(Path(__file__)),"full42_or_full12000_claimed":False}
        args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
        raise
    args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"scheme":args.scheme,"start":args.start,"own_mu_endpoints":result["actual_endpoints_checked"],
        "all_runtime_subset_and_physical_gates_pass":result["all_required_one_start_gates_pass"],"full42_or_full12000_claimed":False}))
    assert result["all_required_one_start_gates_pass"]


if __name__=="__main__":main()
