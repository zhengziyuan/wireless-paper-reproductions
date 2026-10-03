"""Exact fresh native runtime subset, explicitly not the entire42 origin snapshot."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def reconstruct(repo,output):
    here=Path(__file__).resolve().parent;contract=json.loads((here/"runtime-subset-contract.json").read_text(encoding="utf-8"))
    repo=Path(repo).resolve();output=Path(output).resolve()
    assert not output.exists(),"Fresh directory required; no source/result overwrite."
    sources=[]
    for row in contract["selected_files"]:
        rel=Path(row["runtime_relative_path"]);origin=Path(row["repository_source_relative_path"])
        assert not rel.is_absolute() and ".." not in rel.parts and not origin.is_absolute() and ".." not in origin.parts
        source=repo/origin;assert sha(source)==row["sha256"],str(origin);sources.append((row,source))
    output.mkdir(parents=True)
    for row,source in sources:
        target=output/row["runtime_relative_path"];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
        assert sha(target)==sha(source)==row["sha256"]
    metadata={"scope":"runtime_only_selected17_native_source_subset_not_full42_origin",
        "files_sha256":{row["runtime_relative_path"]:row["sha256"] for row in contract["selected_files"]},
        "origin_full42_manifest_sha256":contract["origin_full42_manifest_sha256"],
        "runtime_contract_sha256":sha(here/"runtime-subset-contract.json"),"all42_source_identity_claimed":False,
        "native_runtime_reexecution_claimed":False,"historical_outputs_or_author_files_included":False}
    (output/"recording-source-freeze.json").write_text(json.dumps(metadata,indent=2)+"\n",encoding="utf-8")
    identity={"scope":"actual_fresh_byte_reconstruction_of_numeric_runtime_subset_not_optimizer_execution",
        "selected_files":contract["selected_files"],"files_checked":len(sources),"all_selected_SHA_match":True,
        "generated_subset_metadata_sha256":sha(output/"recording-source-freeze.json"),
        "full42_origin_snapshot_claimed":False,"builder_sha256":sha(Path(__file__))}
    (output/"runtime-subset-reconstruction.json").write_text(json.dumps(identity,indent=2)+"\n",encoding="utf-8")
    return identity


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--repo",type=Path,required=True);parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();result=reconstruct(args.repo,args.output)
    print(json.dumps({k:v for k,v in result.items() if k!="selected_files"}))


if __name__=="__main__":main()
