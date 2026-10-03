"""Read-only SciPy v7 payload schema/hash audit, not independent physics or KKT.

Retains MATLAB cell/array dimensions. No production numerical kernel imports.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.io import loadmat


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scalar(value):
    a=np.asarray(value)
    assert a.size==1
    return a.reshape(-1)[0].item()


def node(array):
    a=np.asarray(array,dtype=object)
    assert a.size==1
    return a.reshape(-1)[0]


def exact_bytes(value):
    if hasattr(value,"_fieldnames"):
        return ("struct",tuple((f,exact_bytes(getattr(value,f))) for f in value._fieldnames))
    if isinstance(value,np.ndarray):
        if value.dtype==object:
            return ("cell",value.shape,tuple(exact_bytes(v) for v in value.flat))
        return ("array",value.shape,value.dtype.str,value.tobytes(order="C"))
    raise TypeError(type(value))


def check_record(path):
    record=json.loads(path.read_text(encoding="utf-8"))
    matrix=path.parent/record["full_payload_file"]
    initial_path=path.parent/record["initial_file"]
    assert sha(matrix)==record["full_payload_sha256"]
    assert sha(initial_path)==record["initial_file_sha256"]
    source_before=sha(matrix)
    parsed=loadmat(matrix,squeeze_me=False,struct_as_record=False)
    payload=node(parsed["payload"])
    initial=node(payload.initial);dims=node(initial.actual_model_dimensions)
    actual_dims={f:int(scalar(getattr(dims,f))) for f in ("M","N","U","K","targets")}
    scheme=record["scheme"]
    assert actual_dims==dict(zip(("M","N","U","K","targets"),(2,1,2,4,4) if scheme=="MIS" else (2,0,1,4,4)))
    coefficients=node(initial.actual_steering_matrix)
    assert coefficients.real.shape==coefficients.imag.shape==(4,2)
    indices=initial.actual_indices_one_based
    assert indices.shape==((2,1) if scheme=="MIS" else (1,0))
    if scheme=="MIS":assert np.array_equal(indices,np.array([[1.],[2.]]))
    stages=payload.continuation_stages;history=payload.full_history
    count=record["actual_continuation_endpoint_count"]
    assert stages.shape==history.shape==(1,count)
    expected_mu=float(scalar(initial.continuation_initial_mu))
    stage_state_hashes=[]
    for j in range(count):
        stage=node(stages[0,j]);original=node(history[0,j])
        assert int(scalar(stage.stage_index))==j
        assert scalar(stage.mu)==scalar(original.mu)==expected_mu==record["mu_values"][j]
        assert exact_bytes(stage.inner)==exact_bytes(original.inner)
        assert exact_bytes(stage.stop)==exact_bytes(original.stop)
        state=node(stage.state)
        phi=node(state.phi);theta=node(state.theta)
        assert phi.real.shape==phi.imag.shape==(2,1)
        assert theta.real.shape==theta.imag.shape==((1,1) if scheme=="MIS" else (0,1))
        assert state.X.shape==(4,actual_dims["U"])
        # This digest documents each actual stored state; equality is not forced
        # to be unequal across stages because a legitimate stage may not move.
        stage_state_hashes.append(hashlib.sha256(repr(exact_bytes(stage.state)).encode()).hexdigest())
        expected_mu*=.5
    settings=node(initial.settings)
    assert expected_mu<float(scalar(settings.terminal_mu))
    assert exact_bytes(node(stages[0,-1]).state)==exact_bytes(payload.final_state)
    assert source_before==sha(matrix)
    return {"scheme":scheme,"start":record["start"],"actual_mu_count":count,"v7_schema_hash_and_history_consistency_pass":True,
            "native_dimensions":actual_dims,"steering_real_binary_sha256":hashlib.sha256(coefficients.real.tobytes()).hexdigest(),
            "steering_imag_binary_sha256":hashlib.sha256(coefficients.imag.tobytes()).hexdigest(),
            "stage_state_hashes":stage_state_hashes,"original_record_source_solver_pass":record["final_solver_status"]["convergence_verified"],
            "independent_physical_KKT_certification":False,"full_payload_sha256":source_before}


def main():
    parser=argparse.ArgumentParser();parser.add_argument("folder",type=Path);parser.add_argument("--output",type=Path);args=parser.parse_args()
    paths=sorted(args.folder.rglob("start-*-record.json"));assert paths
    result={"scope":"read_only_native_v7_recorded_schema_not_physical_or_full12000_certificate",
            "record_count":len(paths),"cases":[check_record(p) for p in paths],"script_sha256":sha(Path(__file__))}
    if args.output:
        assert not args.output.exists(),"Preserve any previous inspection."
        args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,separators=(",",":")))


if __name__=="__main__":main()
