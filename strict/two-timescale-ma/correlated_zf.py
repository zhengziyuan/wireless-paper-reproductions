"""Exact correlated-channel Jensen evaluator before the invalid Wishart step.

No changed covariance or substitute Wishart approximation. The conditional
Gaussian reciprocal quadratic moment is integrated exactly numerically; the
outer expectation uses the supplied complete channel ensemble. This is not a
claim to have recovered the author's undefined Eq74 closed-form expression.
"""
from __future__ import annotations
import numpy as np
from scipy.integrate import quad

QUADRATURE_WAYPOINTS=(.25,.5,.75,.9,.99)
QUADRATURE_WORKING_RELATIVE_TOLERANCE=1e-12


def reciprocal_gaussian_quadratic(mean,covariance,relative_tolerance=1e-9):
    """E[1/(z^H z)] for z~CN(mean,C), complex dimension at least2, C>0."""
    mean=np.asarray(mean,dtype=complex)
    covariance=np.asarray(covariance,dtype=complex)
    if covariance.shape!=(len(mean),len(mean)) or len(mean)<2:
        raise ValueError("ZF inverse expectation requires N>M and projected dimension>=2")
    if not np.all(np.isfinite(mean)) or not np.all(np.isfinite(covariance)):
        raise ValueError("Finite mean/covariance required")
    if np.max(np.abs(covariance-covariance.conj().T))>1e-11:
        raise ValueError("Projected covariance must be Hermitian, no silent replacement")
    eigenvalues,eigenvectors=np.linalg.eigh(covariance)
    if eigenvalues.min()<=0:
        raise ValueError("Strictly positive projected covariance required; no ridge added")
    amplitudes=np.abs(eigenvectors.conj().T@mean)**2
    scale=float(eigenvalues.sum()+amplitudes.sum())
    lambdas=eigenvalues/scale;mu=amplitudes/scale;rank=len(mean)
    def integrand(t):
        if t>=1:
            return float(np.exp(-np.log(lambdas).sum()-(mu/lambdas).sum())/scale) if rank==2 else 0.
        u=t/(1-t)
        denominator=1+u*lambdas
        exponent=-np.log(denominator).sum()-np.sum(u*mu/denominator)-2*np.log1p(-t)-np.log(scale)
        return float(np.exp(exponent))
    # Same Laplace integral: an unsplit adaptive rule missed narrow endpoint
    # structure in actual full-draw scenes. Fixed segments are deterministic,
    # not channel/model fitting; the existing acceptance gate below is unchanged.
    working_tolerance=min(QUADRATURE_WORKING_RELATIVE_TOLERANCE,relative_tolerance/100)
    value,error=quad(integrand,0,1,points=QUADRATURE_WAYPOINTS,
        epsabs=working_tolerance/scale,epsrel=working_tolerance,limit=500)
    if not np.isfinite(value) or value<=0 or error>relative_tolerance*max(value,1/scale)*10:
        raise RuntimeError("Conditional reciprocal-moment quadrature failed its disclosed accuracy")
    return value,error


def correlated_jensen_bound(t,c,nlos,spatial_correlation=True):
    """Eq35/37 exact expectation with Eq68 row correlation, finite outer bank."""
    from core import los,spatial_covariance
    nlos=np.asarray(nlos,dtype=complex);hbar=los(t,c);n,m=hbar.shape
    if n<=m or nlos.ndim!=3 or nlos.shape[1:]!=(n,m) or not len(nlos):
        raise ValueError("Full supplied N>M channel ensemble required")
    if "nlos_realizations_per_geometry" in c and len(nlos)!=c["nlos_realizations_per_geometry"]:
        raise ValueError("Do not shorten the configured original ensemble")
    S=spatial_covariance(t,c) if spatial_correlation else np.eye(n)
    values,vectors=np.linalg.eigh(S)
    if values.min()<=0:raise ValueError("Exact covariance is not strictly positive; no ridge/model repair allowed")
    root=(vectors*np.sqrt(values))@vectors.conj().T
    kap=np.asarray(c["rician"]);beta=np.asarray(c["beta"])
    means=hbar*np.sqrt(kap/(kap+1))
    conditional=np.empty((len(nlos),m));quadrature_error=np.zeros_like(conditional)
    for sample_index,sample in enumerate(nlos):
        normalized=means+(root@sample)/np.sqrt(kap+1)
        for user in range(m):
            others=np.delete(normalized,user,axis=1)
            Q,_=np.linalg.qr(others,mode="complete");basis=Q[:,m-1:]
            mu=basis.conj().T@means[:,user]
            C=basis.conj().T@S@basis/(kap[user]+1)
            conditional[sample_index,user],quadrature_error[sample_index,user]=reciprocal_gaussian_quadratic(mu,C)
    moment=conditional.mean(axis=0)
    per_user=np.log2(1+c["power"]*beta/(m*np.asarray(c["noise"])*moment))
    se=conditional.std(axis=0,ddof=1)/np.sqrt(len(nlos)) if len(nlos)>1 else np.full(m,np.nan)
    return {"sum_rate":float(per_user.sum()),"per_user_rates":per_user.tolist(),
        "mean_inverse_normalized_Gram_diagonal":moment.tolist(),
        "conditional_inverse_moment_samples":conditional.tolist(),
        "inverse_moment_standard_error":se.tolist(),"maximum_quadrature_error":float(quadrature_error.max()),
        "conditional_quadrature_error_samples":quadrature_error.tolist(),
        "mean_quadrature_error_estimate_per_user":quadrature_error.mean(axis=0).tolist(),
        "spatial_correlation":bool(spatial_correlation),
        "outer_expectation_samples":len(nlos),"projected_complex_dimension":n-m+1,
        "quadrature_controls":{"version":"segmented_same_Laplace_integral_v3",
            "normalized_interval":[0.,1.],"waypoints":list(QUADRATURE_WAYPOINTS),
            "working_relative_tolerance":QUADRATURE_WORKING_RELATIVE_TOLERANCE,
            "working_absolute_tolerance":"1e-12/(sum_covariance_eigenvalues_plus_mean_energy)",
            "declared_accuracy_gate_relative_tolerance":1e-9,"subinterval_limit":500,
            "reported_error_is_not_an_interval_certificate":True},
        "method":"exact_Schur_complement_conditional_Gaussian_Laplace_moment_then_full_exported_outer_ensemble",
        "source_model":("Eq68_exact_row_covariance;Eq35_37_original_Jensen_bound_before_invalid_Eq71_Wishart_step" if spatial_correlation
                        else "Eq1_4_exact_iid_covariance;Eq35_37_Jensen_inverse_moment_without_noncentral_Wishart_approximation"),
        "modified_channel_or_Wishart_approximation":False,
        "printed_Eq74_closed_form_recovered":False,"original_curve_closeness_verified":False}
