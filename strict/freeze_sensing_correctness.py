"""Verify actual dual-language outputs and freeze a compact PUBLIC evidence set.

This neither runs optimizers nor certifies original 6000-start paper figures.
Large full-grid outputs remain local; their hashes and small solved states are
retained. All numerical checks precede copies into the public evidence folder.
"""
from __future__ import annotations
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
from compare_components import compare as compare_components

STRICT=Path(__file__).resolve().parent
PACKAGE=STRICT/"mis-sensing"
REFERENCE=STRICT/"figure-reference/mis-sensing-fig15.json"
EXPECTED_AUTHOR_SHA="b0ac3782b11cdb7d2b0d1dfe581bfcfbe17c72c52f64aef3e55cd0bfce25592a"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    with Path(path).open(encoding="utf-8-sig") as stream:
        return json.load(stream)


def require(condition,message):
    if not condition:raise ValueError(message)


def relative(path):
    return Path(path).resolve().relative_to(STRICT).as_posix()


def privacy_check(value):
    """Reject absolute host paths before publishing copied/derived receipts."""
    if isinstance(value,dict):
        for key,item in value.items():privacy_check(key);privacy_check(item)
    elif isinstance(value,list):
        for item in value:privacy_check(item)
    elif isinstance(value,str):
        require(not re.search(r"(?:^|[\s(])(?:[A-Za-z]:[\\/]|/Users/|/home/)",value),
                "Receipt contains a private absolute host path")
    elif isinstance(value,float):
        require(math.isfinite(value),"Public receipt contains nonfinite scientific value")


def recorded_source_hashes(receipt):
    source=receipt.get("source_hashes")
    require(source is not None,"Candidate receipt has no execution source hashes")
    if isinstance(source,dict):return source
    require(isinstance(source,list),"Unsupported candidate source manifest")
    result={}
    for row in source:
        require(set(row)>={"filename","sha256"},"Incomplete MATLAB execution source entry")
        require(row["filename"] not in result,"Duplicate execution source filename")
        result[row["filename"]]=row["sha256"]
    return result


def check_candidate_source(receipt,language):
    require(receipt.get("runtime_source_unchanged") is True,language+" execution sources changed")
    hashes=recorded_source_hashes(receipt)
    required={"settings_reference_candidate.json","mis-sensing-fig15.json"}
    if language=="python":required|={"engine.py","run.py","normalization.py","reference_candidate_fingerprint.py"}
    else:required|={"mis_sensing_strict_engine.m","normalization_contract.m","run_reference_candidate.m"}
    require(required<=set(hashes),language+" missing executed-module/settings/reference hash")
    for name,digest in hashes.items():
        require(Path(name).name==name and len(name)>0,"Execution manifest contains a path instead of a basename")
        path=REFERENCE if name==REFERENCE.name else PACKAGE/name
        require(path.is_file(),"Executed source no longer exists: "+name)
        require(sha(path).lower()==str(digest).lower(),language+" stale source: "+name)
    require(receipt.get("settings")==read(PACKAGE/"settings_reference_candidate.json"),language+" settings payload differs from executed candidate")
    return hashes


def check_stable(receipt,language):
    require(receipt.get("number_of_checks")==11,language+" must include all 11 stable-increment cases")
    require(receipt.get("all_checks_pass") is True,language+" stable-increment overall failure")
    checks=receipt.get("checks",[])
    require(len(checks)==11 and all(c.get("increment_identity_pass") is True for c in checks),language+" failed/missing increment identity")
    require(receipt.get("line_search_acceptance_slack_added") is False,language+" added acceptance slack")
    require(receipt.get("optimizer_stop_threshold_changed") is False,language+" changed optimizer thresholds")


def verify_candidate(receipt,language,reference):
    source=check_candidate_source(receipt,language)
    require(receipt.get("language")==language,"Candidate language mislabeled")
    require(receipt.get("original_number_of_starts")==6000 and receipt.get("executed_starts_per_target_point")==1,"Incorrect diagnostic/full-bank distinction")
    require(receipt.get("point_count")==6 and receipt.get("target_count")==4,"Missing original power points or targets")
    require(receipt.get("full_figure_execution_complete") is False and receipt.get("original_figure_reproduction_certified") is False,"Candidate falsely labeled a complete original figure")
    require(receipt.get("all_original_parameter_values_recovered") is False,"Unverified normalization origin mislabeled recovered")
    require(receipt.get("original_reference_sha256")==reference["source_sha256"],"Original EPS reference SHA differs")
    settings=receipt["settings"]
    require((settings["number_of_starts"],settings["outer_iterations"],settings["rcg_max_iterations"])==(6000,30,4000),"Original budgets changed")
    require(settings["effective_reference_gain_factor"]==100,"Different normalization candidate")
    points=receipt.get("points",[])
    require(len(points)==6 and [p.get("power_dbm") for p in points]==[15,18,21,24,27,30],"Candidate does not cover original full power grid")
    derived={label:[] for label in ["RIS continuous","RIS 1-bit","RIS 2-bit"]}
    feasible=True;converged=True
    for point in points:
        targets=point.get("target_runs",[])
        require(len(targets)==4 and [t["target_index"] for t in targets]==[0,1,2,3],"Missing/reordered original target")
        require([t["target_azimuth_deg"] for t in targets]==[0,90,0,90],"Candidate azimuth geometry changed")
        require([t["target_elevation_deg"] for t in targets]==[30,30,70,70],"Candidate elevation geometry changed")
        require(point["normalization_contract"]["physical_power_watt"]==10**((point["power_dbm"]-30)/10),"Physical power conversion differs")
        for target in targets:
            require(len(target.get("history",[]))>0,"No actual outer trajectory")
            metric=target["metrics"];status=target["solver_status"]
            feasible=feasible and metric["maximum_constraint"]<=settings["feasibility_tolerance"]
            converged=converged and status["convergence_verified"]
        values={"RIS continuous":min(t["metrics"]["min_binary_metric"] for t in targets),
                "RIS 1-bit":min(t["quantized_sinr"]["one_bit"] for t in targets),
                "RIS 2-bit":min(t["quantized_sinr"]["two_bit"] for t in targets)}
        for label,value in values.items():
            require(math.isfinite(value) and value>0,"Invalid independently computed SINR")
            derived[label].append(10*math.log10(value))
    require(receipt.get("all_selected_targets_feasible") is feasible,"Stored feasibility flag differs from actual constraints")
    require(receipt.get("all_stopping_criteria_verified") is converged,"Stored convergence flag differs from actual stop statuses")
    curves={c["label"]:c for c in receipt.get("comparison",[])}
    originals={c["label"]:c for c in reference["curves"]}
    require(set(curves)==set(derived),"Missing/extra fingerprint baseline curve")
    for label,values in derived.items():
        c=curves[label];original=originals[label]
        require(c["power_dbm"]==original["x"] and c["original_plot_vector_reference_db"]==original["y"],"Original comparison data changed")
        failures=[]
        compare_components(values,c["independently_evaluated_simulation_db"],label,failures,1e-12,1e-12)
        require(not failures,"Comparison curve does not derive from actual target metrics: "+str(failures))
    return source,derived


def compact_candidate(receipt,source_path):
    result=copy.deepcopy(receipt)
    for point in result["points"]:
        for target in point["target_runs"]:
            target["outer_summary"]=[{key:value for key,value in outer.items() if key!="inner"}
                                      for outer in target.pop("history")]
    result["full_raw_receipt_sha256"]=sha(source_path)
    result["compaction_note"]="Only inner RCG iteration histories omitted. All point/target metrics, phase states, outer updates, residuals and actual stop flags retained. No convergence or complete-figure certification inferred."
    return result


def compact_beam(receipt,path):
    result={key:copy.deepcopy(value) for key,value in receipt.items() if key!="points"}
    point=receipt["points"][0];samples=point["beampattern_samples"]
    result["points"]=[dict(configuration=point["configuration"],result=point["result"],
                           beam_summary=dict(computed_grid=[len(samples["elevation_deg"]),len(samples["azimuth_deg"])],
                           panels=[{k:v for k,v in panel.items() if k not in ["normalized_gain","sinr"]} for panel in samples["maps"]]))]
    result["full_grid_raw_receipt_sha256"]=sha(path)
    result["compaction_note"]="Large dense angular maps omitted; finite phases, positions, target metrics and the exact full-grid-output hash retained. The separate parity receipt compares the original full grids."
    result["original_figure_reproduction_certified"]=False
    return result


def write(path,value):
    privacy_check(value)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+"\n",encoding="utf-8")


def freeze(correctness,candidate,destination):
    correctness=Path(correctness).resolve();candidate=Path(candidate).resolve();destination=Path(destination).resolve()
    correctness.relative_to(PACKAGE/"outputs");candidate.relative_to(PACKAGE/"outputs")
    destination.relative_to(STRICT/"validation")
    inputs={}
    def load(path):
        value=read(path);privacy_check(value);inputs[relative(path)]=sha(path);return value
    component_paths={lang:correctness/("mis-sensing-"+lang+".json") for lang in ["python","matlab"]}
    components={lang:load(path) for lang,path in component_paths.items()}
    failures=[]
    for section in ["metrics","checks","history","state"]:
        require(all(section in result for result in components.values()),"Missing component section: "+section)
        compare_components(components["python"][section],components["matlab"][section],section,failures,1e-7,1e-6)
    require(not failures,"Actual component outputs disagree: "+str(failures))
    parity=load(correctness/"mis-sensing-parity.json")
    require(parity.get("component_parity_passed") is True,"Stored component parity is not passed")
    require(parity["output_sha256"]=={lang:sha(path) for lang,path in component_paths.items()},"Stored component parity hashes are stale")
    beam_paths={lang:correctness/("fig2-"+lang+".json") for lang in ["python","matlab"]}
    beams={lang:load(path) for lang,path in beam_paths.items()}
    beamparity=load(correctness/"fig2-dual-parity.json")
    require(beamparity.get("dual_full_grid_parity_passed") is True,"Full-grid parity not passed")
    require(beamparity["output_sha256"]=={lang:sha(path) for lang,path in beam_paths.items()},"Full-grid parity hashes stale")
    for lang,result in beams.items():
        require(result.get("full_figure_execution_complete") is True and len(result["points"])==1,"Closed-form full-grid result incomplete")
        require(len(result["points"][0]["beampattern_samples"]["maps"])==9,"Missing original nine-target map")
        require(result.get("original_figure_reproduction_certified") is False,"Full-grid consistency mislabeled original agreement")
    stable={lang:load(correctness/("stable-increment-"+lang+".json")) for lang in ["python","matlab"]}
    for lang,result in stable.items():check_stable(result,lang)
    closed=load(correctness/"closed-form-matlab.json")
    require(closed.get("all_passed") is True and all(x is True for x in closed["checks"].values()),"MATLAB finite closed-form identity failed")
    reference=load(REFERENCE)
    candidate_paths={lang:candidate/("ris-fingerprint-"+lang+".json") for lang in ["python","matlab"]}
    candidates={lang:load(path) for lang,path in candidate_paths.items()}
    candidate_hashes={};curves={}
    for lang,result in candidates.items():candidate_hashes[lang],curves[lang]=verify_candidate(result,lang,reference)
    errors={label:max(abs(a-b) for a,b in zip(curves["python"][label],curves["matlab"][label])) for label in curves["python"]}
    require(all(error<=1e-8 for error in errors.values()),"Dual computed candidate curves differ above 1e-8 dB")
    source_map=read(PACKAGE/"source_map.json")
    require(source_map["source_sha256"].lower()==EXPECTED_AUTHOR_SHA,"Author revision source SHA changed")
    sources=list(PACKAGE.glob("*.py"))+list(PACKAGE.glob("*.m"))
    sources += [PACKAGE/name for name in ["settings.json","settings_reference_candidate.json","source_map.json","tests/stable_increment_fixture.json","tests/stable_increment_cases.json"]]
    sources += [STRICT/"compare_components.py",Path(__file__).resolve()]
    source_hashes={relative(path):sha(path) for path in sorted(sources)}
    transfers={}
    for name in ["mis-sensing-python.json","mis-sensing-matlab.json","mis-sensing-parity.json","fig2-dual-parity.json","stable-increment-python.json","stable-increment-matlab.json","closed-form-matlab.json"]:
        transfers[name]=correctness/name
    for lang,subdir in [("python","fig2-plots"),("matlab","fig2-matlab-plots")]:
        folder=correctness/subdir;render=load(folder/"render_receipt.json")
        require(render["source_result_sha256"]==sha(beam_paths[lang]),"Figure render bound to stale output")
        require(render.get("simulation_samples_modified") is False and render["computed_grid"]==[91,361],"Figure rendering modified full-grid samples")
        for ext in ["png","svg"]:transfers["fig2-"+lang+"."+ext]=folder/("fig2."+ext)
        transfers["fig2-render-"+lang+".json"]=folder/"render_receipt.json"
    for ext in ["png","svg"]:transfers["ris-fingerprint-python."+ext]=candidate/("ris-fingerprint-python."+ext)
    for path in transfers.values():require(path.is_file(),"Missing actual render/receipt: "+path.name)
    destination.mkdir(parents=True,exist_ok=True)
    public_files={}
    for name,path in transfers.items():
        target=destination/name;shutil.copyfile(path,target);public_files[name]=sha(target)
        inputs[relative(path)]=sha(path)
    for lang in ["python","matlab"]:
        name="ris-fingerprint-"+lang+"-summary.json";write(destination/name,compact_candidate(candidates[lang],candidate_paths[lang]));public_files[name]=sha(destination/name)
        name="fig2-"+lang+"-summary.json";write(destination/name,compact_beam(beams[lang],beam_paths[lang]));public_files[name]=sha(destination/name)
    readme=destination/"README.md"
    require(readme.is_file(),"Public folder explanatory README is required")
    public_files[readme.name]=sha(readme)
    manifest=dict(scope="Actual dual-language correctness and inferred-reference evidence; NOT complete original paper-figure reproduction",
                  frozen_at_utc=datetime.now(timezone.utc).isoformat(),author_revision_source_sha256=EXPECTED_AUTHOR_SHA,
                  source_files_sha256=source_hashes,actual_input_output_sha256=inputs,
                  public_files_sha256=public_files,candidate_execution_source_hashes=candidate_hashes,
                  component_recomparison=dict(sections=["metrics","checks","history","state"],atol=1e-7,rtol=1e-6,passed=True),
                  full_grid_parity_hash_binding_verified=True,stable_increment_cases_per_language=11,
                  closed_form_matlab_all_checks_passed=True,candidate_curve_parity_max_absolute_errors_db=errors,
                  candidate_curve_parity_tolerance_db=1e-8,
                  candidate_actual_flags={lang:{key:result[key] for key in ["all_selected_targets_feasible","all_stopping_criteria_verified","full_figure_execution_complete","original_figure_reproduction_certified"]} for lang,result in candidates.items()},
                  compaction="Only large beam grids and inner fingerprint RCG histories omitted; full raw receipt hashes, finite phase states, all target metrics, outer updates and actual flags retained",
                  complete_6000_start_bank_executed=False,all_original_parameter_values_recovered=False,
                  full_published_figure_reproduction_passed=False,original_figure_reproduction_certified=False)
    require(source_hashes=={relative(path):sha(path) for path in sorted(sources)},"Sources changed during freezing")
    write(destination/"manifest.json",manifest)
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--correctness-directory",type=Path,default=PACKAGE/"outputs/correctness-v2")
    parser.add_argument("--candidate-directory",type=Path,default=PACKAGE/"outputs/reference-candidate-final")
    parser.add_argument("--destination",type=Path,default=STRICT/"validation/sensing-correctness-v2")
    args=parser.parse_args()
    result=freeze(args.correctness_directory,args.candidate_directory,args.destination)
    print(json.dumps({"public_evidence_directory":relative(args.destination),"public_file_count":len(result["public_files_sha256"]),"candidate_actual_flags":result["candidate_actual_flags"],"candidate_curve_parity_max_absolute_errors_db":result["candidate_curve_parity_max_absolute_errors_db"],"original_figure_reproduction_certified":False},indent=2))


if __name__=="__main__":main()
