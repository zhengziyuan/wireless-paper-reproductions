import hashlib,json,math
from functools import lru_cache
from importlib.metadata import version
from pathlib import Path
import platform


@lru_cache(maxsize=1)
def implementation_fingerprint():
    digest=hashlib.sha256(b"strict-engine-v1\0")
    for name in ["core.py","run.py","figures.py","ma_metadata.py","brute_force.py"]:
        digest.update(name.encode()+b"\0"+Path(__file__).with_name(name).read_bytes()+b"\0")
    runtime={"python":platform.python_version()}
    for name in ["numpy","scipy","cvxpy","clarabel"]:runtime[name]=version(name)
    digest.update(json.dumps(runtime,sort_keys=True).encode())
    return digest.hexdigest()


def fingerprint(config_bytes,job_bytes):
    return hashlib.sha256(b"strict-v1\0"+config_bytes+b"\0"+job_bytes).hexdigest()


def implemented_complete(result,expected_fingerprint,job,config):
    """Reusable numerical receipt for implemented equations, not original-figure closure."""
    if result.get("input_fingerprint")!=expected_fingerprint or result.get("status")=="failed":return False
    if result.get("implementation_fingerprint")!=implementation_fingerprint():return False
    checks=result.get("checks",{})
    required=["mrt_converged","zf_converged","mrt_nominal_design_spacing_feasible","zf_nominal_design_spacing_feasible","mrt_nominal_design_box_feasible","zf_nominal_design_box_feasible"]
    if not all(checks.get(k) is True for k in required):return False
    schemes=result.get("metrics",{}).get("schemes",{})
    for name in ["MA-MRT","MA-ZF","FPA-MRT","FPA-ZF","FPA-OPT"]:
        s=schemes.get(name,{})
        rates=s.get("sample_sum_rates",[])
        if len(rates)!=config["nlos_realizations_per_geometry"] or s.get("nonconverged_samples",0)!=0 or not all(math.isfinite(x) for x in rates):return False
    if job.get("correlated",False):
        extension=result.get("metrics",{}).get("correlated_extension",{})
        for name in ["MA-MRT_MC","MA-ZF_MC"]:
            rates=extension.get(name,{}).get("sample_sum_rates",[])
            if len(rates)!=config["nlos_realizations_per_geometry"] or not all(math.isfinite(x) for x in rates):return False
    figure=job.get("figure")
    mode="mrt" if figure in [3,13,15] else ("zf" if figure in [4,14,16] else None)
    if mode is not None:
        history=result.get("history",{}).get(mode,{})
        count=len(history.get("objective",[]))
        actual=history.get("instantaneous_MC_mean",[])
        if count<2 or len(actual)!=count or not all(math.isfinite(x) for x in actual):return False
        if job.get("correlated",False):
            extension=result.get("metrics",{}).get("correlated_extension",{})
            names=["MRT_correlated_MC_history","MRT_Eq69_history"] if mode=="mrt" else ["ZF_correlated_MC_history"]
            for name in names:
                values=extension.get(name,[])
                if len(values)!=count or not all(math.isfinite(x) for x in values):return False
    if "brute_force_D" in job:
        brute=result.get("metrics",{}).get("brute_force",{})
        if not all(brute.get(mode,{}).get("search",{}).get("complete") is True for mode in ["MRT","ZF"]):return False
    return True


def original_scope_available(job):
    # Section V and Figs.13/15 describe model evaluation, not a new optimizer.
    # Alg.1's iid trajectory with valid Eq.68/69 evaluations is a supported
    # interpretation, not recovery of the author's undisclosed experiment.
    # Only ZF Figs.14/16 require the genuinely unresolved Eq.72/74/75 analysis.
    return not job.get("correlated",False) or job.get("figure") in [13,15]


def complete(result,expected_fingerprint,job,config):
    """Original-figure receipt; a runnable correlated MC subset is insufficient."""
    return original_scope_available(job) and implemented_complete(result,expected_fingerprint,job,config)


def reusable(path,expected_fingerprint,job,config):
    if not path.exists():return False
    try:return implemented_complete(json.loads(path.read_text()),expected_fingerprint,job,config)
    except (ValueError,TypeError,KeyError):return False


def bank_complete(directory,manifest,config_bytes):
    expected={e["filename"] for e in manifest["files"]}
    if expected!={p.name for p in directory.glob("case-*-mc-*.json")}:return False
    pairs={(e["case_index"],e["realization"]) for e in manifest["files"]}
    if pairs!={(c,r) for c in range(manifest["case_count"]) for r in range(manifest["realizations_per_case"])}:return False
    return all(fingerprint(config_bytes,(directory/e["filename"]).read_bytes())==e["input_fingerprint"] for e in manifest["files"])
