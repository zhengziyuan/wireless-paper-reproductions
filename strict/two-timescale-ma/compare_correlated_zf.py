"""Full1000-draw cross-language comparison; no figure-completion inflation."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def compare(python_result,matlab_result):
    for r in [python_result,matlab_result]:
        if r["outer_ensemble_count"]!=1000 or r["N"]!=6 or r["M"]!=5 or not all(r["checks"].values()):
            raise ValueError("Actual full original1000-draw N6/M5 identity receipts required")
        if r["printed_Eq74_closed_form_recovered"] or r["original_figure_reproduction_certified"]:
            raise ValueError("Standalone bound identity must not claim original figure recovery")
    pairs={"positions":(python_result["positions"],matlab_result["positions"]),
        "conditional_inverse_moments_all5000":(python_result["conditional_exact_Jensen_evaluator"]["conditional_inverse_moment_samples"],matlab_result["conditional_exact_Jensen_evaluator"]["conditional_inverse_moment_samples"]),
        "actual_correlated_rates_all1000":(python_result["actual_correlated_ZF"]["sample_sum_rates"],matlab_result["actual_correlated_ZF"]["sample_sum_rates"]),
        "direct_MC_inverse_diagonal_mean":(python_result["direct_MC_inverse_diagonal_mean"],matlab_result["direct_MC_inverse_diagonal_mean"]),
        "Jensen_per_user_rates":(python_result["conditional_exact_Jensen_evaluator"]["per_user_rates"],matlab_result["conditional_exact_Jensen_evaluator"]["per_user_rates"])}
    errors={};conditional_fixed_tolerance_passed=True
    combined_quadrature_error=(python_result["conditional_exact_Jensen_evaluator"]["maximum_quadrature_error"]
        +matlab_result["conditional_exact_Jensen_evaluator"]["maximum_quadrature_error"])
    for name,(a,b) in pairs.items():
        a=np.asarray(a);b=np.asarray(b)
        if a.shape!=b.shape or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
            raise ValueError(f"Full finite paired arrays required: {name}")
        maximum_difference=float(np.max(abs(a-b)))
        if name=="conditional_inverse_moments_all5000":
            conditional_fixed_tolerance_passed=bool(np.all(abs(a-b)<=1e-10+1e-9*abs(b)))
            if maximum_difference>combined_quadrature_error:raise ValueError("Conditional moments exceed combined reported adaptive-quadrature error estimates")
        else:np.testing.assert_allclose(a,b,rtol=1e-9,atol=1e-10)
        errors[name]={"shape":list(a.shape),"maximum_absolute_difference":maximum_difference}
    return {"paper_id":"two-timescale-ma","scope":"actual_same_full1000_draw_original_correlated_model_cross_language_identity",
        "all_passed":True,"N":6,"M":5,"draw_count":1000,"Schur_identities_per_language":5000,
        "parity_relative_tolerance":1e-9,"parity_absolute_tolerance":1e-10,"array_errors":errors,
        "all5000_conditional_moments_fixed_tolerance_passed":conditional_fixed_tolerance_passed,
        "all5000_conditional_moments_within_combined_reported_quadrature_error_estimates":True,
        "combined_reported_adaptive_quadrature_error_estimate":combined_quadrature_error,
        "quadrature_estimates_are_not_interval_arithmetic_proof":True,
        "Python_corrected_Jensen_estimate":python_result["conditional_exact_Jensen_evaluator"]["sum_rate"],
        "MATLAB_corrected_Jensen_estimate":matlab_result["conditional_exact_Jensen_evaluator"]["sum_rate"],
        "Python_actual_correlated_ZF_mean":python_result["actual_correlated_ZF"]["mean_sum_rate"],
        "MATLAB_actual_correlated_ZF_mean":matlab_result["actual_correlated_ZF"]["mean_sum_rate"],
        "source_row_covariance_unchanged":True,"covariance_or_Wishart_approximation_substituted":False,
        "printed_Eq74_closed_form_recovered":False,"full100_geometry_figure_complete":False,
        "original_curve_closeness_verified":False}


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--python-result",type=Path,required=True);p.add_argument("--matlab-result",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True);args=p.parse_args()
    py=args.python_result.read_bytes();mat=args.matlab_result.read_bytes();result=compare(json.loads(py),json.loads(mat))
    result["Python_result_sha256"]=hashlib.sha256(py).hexdigest();result["MATLAB_result_sha256"]=hashlib.sha256(mat).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"all_passed":result["all_passed"],"array_errors":result["array_errors"]}))
