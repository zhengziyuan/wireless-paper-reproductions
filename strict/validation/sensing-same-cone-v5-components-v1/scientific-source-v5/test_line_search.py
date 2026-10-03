"""Fast production line-search/checkpoint regressions, never a paper figure.
Run directly with Python + NumPy. No MATLAB or Monte Carlo launch occurs.
"""
from pathlib import Path
import json,tempfile
import numpy as np
from engine import block_backtracking,rcg,Model

OPTIONS={"line_search_policy":"original_per_block_backtracking","non_descent_policy":"documented_non_descent_restart",
         "initial_step":1.,"armijo_constant":1e-4,"backtrack_factor":.5,"max_backtracks":60,
         "max_iterations":40,"gradient_tolerance":1e-6}

def line_search_checks():
    # Circle counterexample: initial chord looks descending although its
    # infinitesimal raw slope is positive; backtracking alone cannot fix it.
    z={"phi":np.ones(1,dtype=complex),"theta":np.ones(2,dtype=complex),"X":np.ones((1,1))}
    w=np.array([1.,2.]);g={"phi":np.zeros(1,dtype=complex),"theta":1j*w,"X":np.zeros((1,1))}
    d={"phi":g["phi"],"theta":1j*np.array([10.,-1.]),"X":g["X"]}
    def curved(x):return float(np.sum(w*np.imag(x["theta"])+2*(1-np.real(x["theta"])))),{},{}
    new,_,info,reason=block_backtracking(z,g,d,curved,curved(z)[0],OPTIONS)
    raw=float(np.vdot(g["theta"],d["theta"]).real)
    actual=info["raw_projected_displacement_slopes"]["theta"]
    raw_pass=(reason is None and raw>=0 and actual<0 and "raw_non_descent" in info["block_restart_reasons"]["theta"]
              and curved(new)[0]<curved(z)[0] and np.max(np.abs(np.abs(new["theta"])-1))<1e-12)
    # Simplex counterexample: raw descent is reversed by the feasible projection.
    z={"phi":np.ones(1,dtype=complex),"theta":np.empty(0,dtype=complex),"X":np.array([[.5,.5,0.]])}
    g={"phi":np.zeros(1,dtype=complex),"theta":np.empty(0,dtype=complex),"X":np.array([[-2.,-1.,3.]])}
    d={"phi":g["phi"],"theta":g["theta"],"X":np.array([[-2.,4.,-2.]])}
    def linear(x):return float(np.sum(g["X"]*x["X"])),{},{}
    new,_,info,reason=block_backtracking(z,g,d,linear,linear(z)[0],OPTIONS)
    projected_pass=(reason is None and info["block_raw_direction_slopes"]["X"]<0
                    and info["raw_projected_displacement_slopes"]["X"]>0
                    and info["block_restart_reasons"]["X"]==["projected_non_descent"] and linear(new)[0]<linear(z)[0])
    # No MS2 and one-column schedule: only eta is active, others must be skipped.
    z={"phi":np.ones(1,dtype=complex),"theta":np.empty(0,dtype=complex),"X":np.ones((1,1)),"eta":np.asarray(0.)}
    g={"phi":np.zeros(1,dtype=complex),"theta":np.empty(0,dtype=complex),"X":np.zeros((1,1)),"eta":np.asarray(-1.)}
    d={b:-v for b,v in g.items()}
    def eta_cost(x):return .5*(float(x["eta"])-1)**2,{},{}
    new,_,info,reason=block_backtracking(z,g,d,eta_cost,eta_cost(z)[0],OPTIONS)
    empty_pass=(reason is None and float(new["eta"])==1 and all(info["inactive_projected_blocks"][b] for b in ("phi","theta","X")))
    # The row-mean gradient is nonzero at a simplex vertex, but KKT residual is zero.
    z={"phi":np.ones(1,dtype=complex),"theta":np.empty(0,dtype=complex),"X":np.array([[1.,0.]])}
    def vertex(x):
        return -float(x["X"][0,0]),{"phi":np.zeros(1,dtype=complex),"theta":np.empty(0,dtype=complex),"X":np.array([[-1.,0.]])},{}
    _,_,stop=rcg(z,vertex,OPTIONS)
    vertex_pass=(stop["reason"]=="gradient_tolerance" and stop["gradient_norm"]>.5 and stop["projected_kkt_norm"]==0.)
    checks={"circle_raw_slope_counterexample":raw,"circle_initial_actual_slope_counterexample":actual,
            "raw_non_descent_restart_pass":bool(raw_pass),"projected_non_descent_restart_pass":bool(projected_pass),
            "empty_stationary_blocks_pass":bool(empty_pass),"closed_simplex_KKT_pass":bool(vertex_pass)}
    assert all(checks[k] for k in checks if k.endswith("_pass")),checks
    return checks

def checkpoint_checks():
    import run
    here=Path(__file__).resolve().parent
    settings=json.loads((here/"settings.json").read_text())
    model=Model(json.loads((here/"unit_fixture.json").read_text())["model"])
    original_comm,original_sense=run.communication_solve,run.sensing_solve
    def forbidden(*args,**kwargs):raise AssertionError("A checkpoint-gate test must never enter a solve")
    run.communication_solve=forbidden;run.sensing_solve=forbidden
    refused=[]
    try:
        with tempfile.TemporaryDirectory(prefix="mis-checkpoint-unit-") as folder:
            path=Path(folder)/"unit.json"
            for saved in ({},{"schema_version":2,"implementation_digest":"different_source"}):
                path.write_text(json.dumps(saved),encoding="utf-8")
                try:run.optimize(model,settings,"communications" if settings["kind"]=="communications" else "sinr",checkpoint_path=path)
                except ValueError as error:refused.append("Legacy/different implementation" in str(error))
                else:raise AssertionError("Mismatched checkpoint incorrectly resumed")
    finally:run.communication_solve=original_comm;run.sensing_solve=original_sense
    assert all(refused) and len(refused)==2
    return {"legacy_checkpoint_rejection_pass":refused[0],"changed_source_checkpoint_rejection_pass":refused[1]}

if __name__=="__main__":
    print(json.dumps({"scope":"unit_regressions_not_paper_figure","checks":dict(line_search_checks(),**checkpoint_checks())},indent=2))

