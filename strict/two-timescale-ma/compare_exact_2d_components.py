"""Pair actual physical points/objectives/certificates, not bookkeeping counts."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from coordinate_exact import polygon
from core import mrt_statistics,zf_statistics,zf_surrogate
from run import scenario


def compare(py,mat):
    folder=Path(__file__).parent;config=json.loads((folder/"full_config.json").read_text());fixture=json.loads((folder/"fixture.json").read_text())
    c,_=scenario(config,6,5,fixture["rician_linear"],geometry=fixture);t=np.asarray(fixture["positions"]);modes={};bookkeeping={}
    for mode in ["mrt","zf"]:
        points={name:np.asarray(result["metrics"][mode+"_one_coordinate"]) for name,result in [("Python",py),("MATLAB",mat)]}
        np.testing.assert_allclose(points["Python"],points["MATLAB"],rtol=1e-9,atol=1e-10)
        rechecks={}
        for name,result in [("Python",py),("MATLAB",mat)]:
            point=points[name];np.testing.assert_array_equal(point[1:],t[1:]);delta=point[0]-t[0]
            A,b,vertices,tolerance=polygon(t,c,0)
            if mode=="mrt":
                before,g,q,_=mrt_statistics(t,c,0);after=mrt_statistics(point,c)[0]
                surrogate=before+g[0]@delta-q/2*(delta@delta);gradient=g[0]-q*delta
            else:
                before,_,_,eta=zf_statistics(t,c);after=zf_statistics(point,c)[0];s=zf_surrogate(t,c,0)
                minor=s["chi"]+s["f0"]+s["gradient"]@delta-s["curvature"]/2*(delta@delta)
                surrogate=np.log2(1+eta*minor).sum()
                r=s["ratio"]+1/eta+s["gradient"]@delta-s["curvature"]/2*(delta@delta)
                gradient=np.sum((s["gradient"]-s["curvature"][:,None]*delta)/r[:,None],axis=0)/np.log(2)
            gap=max(0.,float(np.max((vertices-delta)@gradient)));primal=max(0.,float(np.max(A@delta-b)))
            history=result["history"][mode];certificate=history["certificate"]
            for key,value in [("before",before),("after",after),("surrogate",surrogate),("lower_bound_gap",after-surrogate)]:
                np.testing.assert_allclose(history[key],value,rtol=1e-9,atol=1e-10)
            if not np.isfinite(gap+primal) or gap>certificate["global_objective_gap_tolerance"] or primal>tolerance:
                raise ValueError("Independent physical-coordinate global/primal certificate failed")
            np.testing.assert_allclose(certificate["global_objective_gap_upper_bound"],gap,rtol=1e-8,atol=1e-10)
            np.testing.assert_allclose(certificate["maximum_normalized_constraint_violation"],primal,rtol=1e-8,atol=1e-12)
            rechecks[name]={"before":float(before),"after":float(after),"source_surrogate":float(surrogate),
                "gap_recomputed_from_original_minorant_gradient_and_all_polygon_vertices":gap,
                "maximum_primal_violation":primal,"source_gap_tolerance":certificate["global_objective_gap_tolerance"],
                "all_other_antennas_unchanged":True,"independent_source_certificate_passed":True}
        modes[mode]={"maximum_full_array_position_difference":float(np.max(abs(points["Python"]-points["MATLAB"]))),"independent_checks":rechecks}
        bookkeeping[mode]={"Python_finite_candidate_count":py["history"][mode]["certificate"]["finite_feasible_candidates"],
            "MATLAB_finite_candidate_count":mat["history"][mode]["certificate"]["finite_feasible_candidates"],
            "Python_solver_iterations":py["history"][mode]["solver_iterations"],
            "MATLAB_solver_iterations":mat["history"][mode]["solver_iterations"]}
    return {"paper_id":"two-timescale-ma","scope":"actual_full_N6_M5_two_original_coordinate_subproblems_physical_pairing",
        "physical_point_objective_and_certificate_parity_passed":True,"relative_tolerance":1e-9,"absolute_tolerance":1e-10,
        "modes":modes,"nonphysical_bookkeeping_retained_not_required_equal":bookkeeping,
        "all_fields_or_bitwise_parity_claimed":False,"state_field_available":False,"full100_geometry_figure_complete":False,
        "original_curve_closeness_verified":False}


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--python-result",type=Path,required=True);p.add_argument("--matlab-result",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True);args=p.parse_args();py=args.python_result.read_bytes();mat=args.matlab_result.read_bytes()
    result=compare(json.loads(py),json.loads(mat));result["Python_result_sha256"]=hashlib.sha256(py).hexdigest();result["MATLAB_result_sha256"]=hashlib.sha256(mat).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"physical_point_objective_and_certificate_parity_passed":True,"modes":result["modes"]}))
