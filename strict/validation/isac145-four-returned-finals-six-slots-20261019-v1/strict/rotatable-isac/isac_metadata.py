import hashlib,json,math
from functools import lru_cache
from importlib.metadata import version
from pathlib import Path
import platform


@lru_cache(maxsize=1)
def implementation_fingerprint():
    digest=hashlib.sha256(b"strict-engine-v1\0")
    for name in ["core.py","run.py","figures.py","isac_metadata.py"]:
        digest.update(name.encode()+b"\0"+Path(__file__).with_name(name).read_bytes()+b"\0")
    digest.update(json.dumps({"python":platform.python_version(),"numpy":version("numpy")},sort_keys=True).encode())
    return digest.hexdigest()


def fingerprint(config_bytes,scene_bytes):
    return hashlib.sha256(b"strict-v1\0"+config_bytes+b"\0"+scene_bytes).hexdigest()


def inner_complete(item,kind):
    if item.get("converged") is not True or item.get("capped_unconverged") is not False:return False
    reason=item.get("termination_reason")
    if kind=="RIS" and item.get("applicable") is False:
        return reason=="not_applicable_no_RIS" and item.get("iterations")==0
    if not 0<item.get("iterations",0)<=item.get("iteration_budget",0):return False
    def measured(key,tolerance,strict=False):
        value=item.get(key);tol=item.get(tolerance)
        return isinstance(value,(int,float)) and isinstance(tol,(int,float)) and math.isfinite(value) and math.isfinite(tol) and (value<tol if strict else value<=tol)
    if kind=="W":
        return (reason=="relative_objective_tolerance" and measured("relative_objective_improvement","relative_tolerance",True)) or (reason=="relative_step_tolerance" and measured("relative_step","relative_tolerance",True))
    if kind=="RIS":return reason=="gradient_tolerance" and measured("last_checked_normalized_gradient_norm","gradient_tolerance")
    if kind=="rotation":
        return (reason=="projected_gradient_tolerance" and measured("last_checked_projected_gradient_norm","gradient_tolerance")) or (reason=="relative_step_tolerance" and measured("relative_step","relative_tolerance"))
    return False


def all_inner_complete(history):
    blocks=history.get("blocks",[])
    return bool(blocks) and history.get("inner_all_converged") is True and history.get("full_converged") is True and all(inner_complete(block.get(kind,{}),kind) for block in blocks for kind in ["W","RIS","rotation"])


def complete(result,expected_fingerprint):
    if result.get("input_fingerprint")!=expected_fingerprint or result.get("status")=="failed":return False
    if result.get("implementation_fingerprint")!=implementation_fingerprint():return False
    checks=result.get("checks",{});metrics=result.get("metrics",{})
    names=["Rot-BS & Rot-RIS","Rot-BS & Fix-RIS","Fix-BS & Rot-RIS","Fix-BS & Fix-RIS","Rot-BS & No-RIS","Fix-BS & No-RIS"]
    for name in names:
        s=checks.get(name,{})
        if s.get("status")!="executed" or not s.get("converged") or not s.get("inner_all_converged") or not s.get("full_converged") or not s.get("power_feasible") or not s.get("rotation_feasible"):return False
        if not all_inner_complete(result.get("history",{}).get(name,{})):return False
        metric=metrics.get(name,{})
        if s.get("unit_modulus_error",float("inf"))>1e-10 or not all(math.isfinite(metric.get(k,float("nan"))) for k in ["utility","rate","nmse"]):return False
    return True


def reusable(path,expected_fingerprint):
    if not path.exists():return False
    try:return complete(json.loads(path.read_text()),expected_fingerprint)
    except (ValueError,TypeError,KeyError):return False


def bank_complete(directory,manifest,config_bytes):
    expected={e["filename"] for e in manifest["files"]}
    if expected!={p.name for p in directory.glob("case-*-mc-*.json")}:return False
    pairs={(e["case_index"],e["realization"]) for e in manifest["files"]}
    if pairs!={(c,r) for c in range(manifest["case_count"]) for r in range(100)}:return False
    return all(fingerprint(config_bytes,(directory/e["filename"]).read_bytes())==e["input_fingerprint"] for e in manifest["files"])
