"""Fast immutable packet and raw/actual receipt binding, not a fresh solver run."""
import hashlib
import json
from pathlib import Path


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    folder=Path(__file__).resolve().parent
    manifest=json.loads((folder/"freeze-manifest.json").read_text(encoding="utf-8"))
    for rel,expected in manifest["published_files_sha256"].items():
        path=Path(rel);assert not path.is_absolute() and ".." not in path.parts
        assert sha(folder/path)==expected,rel
    counts=0
    for scheme,binding in manifest["actual_raw_bindings"].items():
        raw=folder/"records"/scheme
        record=json.loads((raw/"start-000001-record.json").read_text(encoding="utf-8"))
        assert sha(raw/"start-000001-full.mat")==record["full_payload_sha256"]==binding["native_full_mat_sha256"]
        assert sha(raw/"start-000001-initial.json")==record["initial_file_sha256"]
        actual=folder/("actual-native-recording-v2-"+scheme+"1-source-bound-endpoints-v2.json")
        assert sha(actual)==binding["source_bound_actual_audit_sha256"]
        receipt=json.loads(actual.read_text(encoding="utf-8"))
        assert receipt["all_required_one_start_gates_pass"] and receipt["actual_endpoints_checked"]==17
        assert receipt["actual_source_input_raw_sha256"]["full_mat"]==record["full_payload_sha256"]
        assert receipt["source_origin_binding_v2"]["actual_pre_result_native_source_freeze_SHA256"]==manifest["actual_source_freeze_sha256"]
        counts+=receipt["actual_endpoints_checked"]
    old=json.loads((folder/"retained-old-four-start-preflight-metadata-shape-failure-v1.json").read_text(encoding="utf-8"))
    assert not old["all_four_recording_reference_and_saved_payload_exact"]
    assert old["all_four_original_solver_gates"] and old["source_before_after_unchanged"]
    for item in old["cases"]:
        assert [k for k,v in item["checks"].items() if not v]==["saved_model_geometry_exact"]
    assert counts==34 and not manifest["full12000_native_completion_claimed"]
    print(json.dumps({"frozen_packet_hashes_and_raw_receipt_bindings_pass":True,"recorded_starts":2,"actual_mu_endpoints":counts,"fresh_physical_or_solver_run_claimed":False,"old_false_receipt_preserved":True}))


if __name__=="__main__":main()
