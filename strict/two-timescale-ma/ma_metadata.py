import hashlib,json,math
from functools import lru_cache
from importlib.metadata import version
from pathlib import Path
import platform


@lru_cache(maxsize=1)
def implementation_fingerprint():
    digest=hashlib.sha256(b"strict-engine-v1\0")
    for name in ["core.py","run.py","figures.py","ma_metadata.py","brute_force.py","coordinate_exact.py"]:
        digest.update(name.encode()+b"\0"+Path(__file__).with_name(name).read_bytes()+b"\0")
    runtime={"python":platform.python_version()}
    for name in ["numpy","scipy","cvxpy","clarabel"]:runtime[name]=version(name)
    digest.update(json.dumps(runtime,sort_keys=True).encode())
    return digest.hexdigest()


def fingerprint(config_bytes,job_bytes):
    return hashlib.sha256(b"strict-v1\0"+config_bytes+b"\0"+job_bytes).hexdigest()


def _saved_nonnegative_mean_valid(metric, count):
    """Check saved mean/sample consistency; not scientific acceptance."""
    rates=metric.get('sample_sum_rates'); mean=metric.get('mean_sum_rate')
    if (type(count) is not int or count<=0 or not isinstance(rates,list) or len(rates)!=count
        or type(mean) not in (int,float) or not math.isfinite(mean) or mean<0
        or not all(type(x) in (int,float) and math.isfinite(x) and x>=0 for x in rates)):
        return False
    try: observed=math.fsum(rates)/count
    except OverflowError:return False
    if not math.isfinite(observed):return False
    nu=(count+4)*(2**-53)
    if nu>=1:return False
    return abs(observed-mean)<=(2*nu/(1-nu))*max(observed,mean)


def _implemented_complete(result,expected_fingerprint,job,config,expected_implementation):
    """Check a numerical receipt against an explicitly selected source version."""
    if result.get("input_fingerprint")!=expected_fingerprint or result.get("status")=="failed":return False
    if result.get("implementation_fingerprint")!=expected_implementation:return False
    checks=result.get("checks",{})
    required=["mrt_converged","zf_converged","mrt_nominal_design_spacing_feasible","zf_nominal_design_spacing_feasible","mrt_nominal_design_box_feasible","zf_nominal_design_box_feasible"]
    if not all(checks.get(k) is True for k in required):return False
    if config["convex_solver"]["name"]=="certified_exact_2d":
        for mode in ["mrt","zf"]:
            updates=result.get("history",{}).get(mode,{}).get("coordinate_updates",[])
            if not updates:return False
            for update in updates:
                cert=update.get("certificate",{})
                if (update.get("original_subproblem_unchanged") is not True
                    or cert.get("certified_without_conic_solver_status") is not True):return False
                for value_key,tolerance_key in [("global_objective_gap_upper_bound","global_objective_gap_tolerance"),
                    ("maximum_normalized_constraint_violation","normalized_constraint_tolerance")]:
                    value=cert.get(value_key);tolerance=cert.get(tolerance_key)
                    if not isinstance(value,(int,float)) or not isinstance(tolerance,(int,float)) or not math.isfinite(value+tolerance) or value<0 or value>tolerance:return False
    schemes=result.get("metrics",{}).get("schemes",{})
    for name in ["MA-MRT","MA-ZF","FPA-MRT","FPA-ZF","FPA-OPT"]:
        s=schemes.get(name,{})
        if not _saved_nonnegative_mean_valid(s,config["nlos_realizations_per_geometry"]):return False
        # FPA solves an optimization for each sample; MA convergence is
        # established above by its own long-timescale AO flags instead.
        if name.startswith("FPA-") and (type(s.get("nonconverged_samples")) is not int or s["nonconverged_samples"]!=0):return False
    if job.get("correlated",False):
        extension=result.get("metrics",{}).get("correlated_extension",{})
        for name in ["MA-MRT_MC","MA-ZF_MC"]:
            if not _saved_nonnegative_mean_valid(extension.get(name,{}),config["nlos_realizations_per_geometry"]):return False
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


def implemented_complete(result,expected_fingerprint,job,config):
    """Numerical receipt against the current source; not original-figure closure."""
    return _implemented_complete(result,expected_fingerprint,job,config,implementation_fingerprint())


def original_scope_available(job):
    # Section V and Figs.13/15 describe model evaluation, not a new optimizer.
    # Alg.1's iid trajectory with valid Eq.68/69 evaluations is a supported
    # interpretation, not recovery of the author's undisclosed experiment.
    # Only ZF Figs.14/16 require the genuinely unresolved Eq.72/74/75 analysis.
    return not job.get("correlated",False) or job.get("figure") in [13,15]


def complete(result,expected_fingerprint,job,config):
    """Fail closed until independent figure-level acceptance is implemented.

    A single result cannot prove full scenarios, MATLAB agreement, original
    reference agreement and the other figure-level requirements.
    """
    return False


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
