"""Full-draw evidence at one unchanged original Algorithm2 position.

Both channel models use the exact inverse-moment Jensen integral; iid Eq39
is additionally retained as the ORIGINAL design approximation, not silently
replaced in the position optimizer. No finite-MC lower-bound guarantee.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import numpy as np
from core import instantaneous,los,spatial_covariance,zf_statistics
from correlated_zf import correlated_jensen_bound


def evaluator_fingerprint():
    digest=hashlib.sha256(b"corrected-ZF-full-position-v3-segmented-integral\0")
    for name in ["corrected_zf_position.py","correlated_zf.py","evaluate_correlated_zf.py"]:
        digest.update(name.encode()+b"\0"+Path(__file__).with_name(name).read_bytes()+b"\0")
    return digest.hexdigest()


def position_evidence_complete(record,positions,m):
    """Reject truncated/nonfinite cached evidence, not just a success flag."""
    try:
        if (record.get("nlos_samples")!=1000 or record.get("trajectory_position_reoptimized") is not False
            or not np.array_equal(np.asarray(record["positions"]),np.asarray(positions))):return False
        for model in ["iid","correlated"]:
            r=record["models"][model];a=r["actual_full1000_MC"];b=r["exact_original_model_Jensen"]
            samples=np.asarray(a["sample_sum_rates"],dtype=float)
            if samples.shape!=(1000,) or not np.all(np.isfinite(samples)) or not np.isclose(samples.mean(),a["mean_sum_rate"],rtol=1e-12,atol=1e-12):return False
            for key in ["powers","off_diagonal_amplitude"]:
                values=np.asarray(a[key]);
                if values.shape!=(1000,) or not np.all(np.isfinite(values)):return False
            for source,key in [(r,"direct_MC_inverse_diagonal_samples"),(b,"conditional_inverse_moment_samples"),(b,"conditional_quadrature_error_samples")]:
                values=np.asarray(source[key],dtype=float)
                if values.shape!=(1000,m) or not np.all(np.isfinite(values)) or np.any(values<0):return False
                if key!="conditional_quadrature_error_samples" and np.any(values<=0):return False
            if not (r["all1000_times_M_Schur_identities_pass"] and r["all1000_ZF_beamformer_rate_identities_pass"]
                    and b["outer_expectation_samples"]==1000 and np.isfinite(b["sum_rate"])):return False
        return True
    except (ValueError,TypeError,KeyError):return False


def evaluate_model(t,c,nlos,correlated):
    t=np.asarray(t,dtype=float);z=np.asarray(nlos,dtype=complex);n,m=t.shape[0],len(c["beta"])
    if z.shape!=(1000,n,m) or c.get("nlos_realizations_per_geometry")!=1000:
        raise ValueError("All configured1000 unchanged NLoS draws required")
    covariance=spatial_covariance(t,c) if correlated else np.eye(n)
    eigenvalues,eigenvectors=np.linalg.eigh(covariance)
    if eigenvalues.min()<=0:raise ValueError("Original covariance must be positive; no ridge or clipping")
    root=(eigenvectors*np.sqrt(eigenvalues))@eigenvectors.conj().T
    kap=np.asarray(c["rician"]);mean=los(t,c)*np.sqrt(kap/(kap+1))
    X=mean+np.einsum("ab,sbc->sac",root,z)/np.sqrt(kap+1)
    gram=X.conj().transpose(0,2,1)@X
    inverse=np.linalg.solve(gram,np.broadcast_to(np.eye(m),gram.shape))
    diagonal=np.real(np.diagonal(inverse,axis1=1,axis2=2))
    if not np.all(np.isfinite(diagonal)) or np.any(diagonal<=0):raise ValueError("Finite positive original inverse-Gram diagonal required")
    schur=np.empty_like(diagonal)
    for user in range(m):
        other=np.delete(X,user,axis=2);Q,_=np.linalg.qr(other,mode="complete")
        projection=np.einsum("sni,sn->si",Q[:,:,m-1:].conj(),X[:,:,user])
        schur[:,user]=1/np.sum(abs(projection)**2,axis=1)
    schur_error=abs(schur-diagonal)
    if not np.allclose(schur,diagonal,rtol=1e-8,atol=1e-10):raise RuntimeError("Full1000xM Schur identities failed")
    actual=instantaneous(t,c,z,"ZF",correlated)
    samples=np.asarray(actual["sample_sum_rates"])
    a=c["power"]*np.asarray(c["beta"])/(m*np.asarray(c["noise"]))
    identity_rates=np.log2(1+a/diagonal).sum(axis=1)
    identity_error=float(np.max(abs(identity_rates-samples)))
    if not np.allclose(identity_rates,samples,rtol=1e-9,atol=1e-9):raise RuntimeError("Original ZF beamformer/inverse-Gram rate identity failed")
    bound=correlated_jensen_bound(t,c,z,correlated)
    moment=np.asarray(bound["mean_inverse_normalized_Gram_diagonal"])
    derivative=a/(np.log(2)*moment*(moment+a))
    quad_error=float(np.sum(derivative*np.asarray(bound["mean_quadrature_error_estimate_per_user"])))
    # First-order delta standard error of the SUM, retaining cross-user covariance.
    conditional=np.asarray(bound["conditional_inverse_moment_samples"])
    delta_se=float(np.std(conditional@derivative,ddof=1)/np.sqrt(1000))
    result={"channel_model":"Eq68_spatially_correlated" if correlated else "Eq1_4_iid",
        "actual_full1000_MC":actual,"MC_standard_error_within_geometry":float(samples.std(ddof=1)/np.sqrt(1000)),
        "exact_original_model_Jensen":bound,"MC_minus_population_Jensen_plugin":float(samples.mean()-bound["sum_rate"]),
        "population_Jensen_rate_quadrature_error_estimate_first_order":quad_error,
        "population_Jensen_rate_outer_MC_standard_error_delta_method":delta_se,
        "direct_MC_inverse_diagonal_samples":diagonal.tolist(),
        "direct_MC_inverse_diagonal_mean":diagonal.mean(axis=0).tolist(),
        "direct_MC_inverse_diagonal_standard_error":(diagonal.std(axis=0,ddof=1)/np.sqrt(1000)).tolist(),
        "maximum_Schur_identity_absolute_error":float(schur_error.max()),
        "maximum_ZF_beamformer_inverse_Gram_rate_identity_error":identity_error,
        "minimum_original_covariance_eigenvalue":float(eigenvalues.min()),
        "all1000_times_M_Schur_identities_pass":True,
        "all1000_ZF_beamformer_rate_identities_pass":True,
        "quadrature_error_is_reported_estimate_not_interval_certificate":True,
        "rate_error_delta_method_is_not_a_confidence_interval":True,
        "finite_ensemble_bound_guaranteed":False}
    return result


def evaluate_position(t,c,nlos):
    t=np.asarray(t,dtype=float);n=len(t)
    if t.shape!=(n,2) or n<=len(c["beta"]) or not np.all(np.isfinite(t)):
        raise ValueError("Original finite N>M antenna geometry required")
    distances=np.linalg.norm(t[:,None,:]-t[None,:,:],axis=2)+np.eye(n)*1e9
    tol=c["verification_tolerance"]
    if distances.min()<c["minimum_distance"]-tol or np.any(t<np.asarray(c["region_lower"])-tol) or np.any(t>np.asarray(c["region_upper"])+tol):
        raise ValueError("Unchanged accepted original Algorithm2 position must be feasible")
    return {"positions":t.tolist(),"nlos_samples":1000,"models":{
        "iid":evaluate_model(t,c,nlos,False),"correlated":evaluate_model(t,c,nlos,True)},
        "original_iid_Algorithm2_statistical_design_objective":float(zf_statistics(t,c)[0]),
        "iid_design_objective_is_source_noncentral_Wishart_approximation_not_exact_inverse_moment":True,
        "trajectory_position_reoptimized":False,"original_covariance_or_power_model_changed":False,
        "printed_Eq74_75_recovered":False,"original_curve_closeness_verified":False}
