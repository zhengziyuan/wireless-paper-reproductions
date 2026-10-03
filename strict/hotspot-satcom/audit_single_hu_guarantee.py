"""Explicit source-matrix and PSD/global-optimality counterexamples; no fitting."""
import json
from pathlib import Path
import numpy as np
from run_support import save_receipt,source_hashes,unchanged


def rgrad(C,phi):
    g=2*C@phi
    return g-np.real(g*np.conj(phi))*phi


if __name__=='__main__':
    C=np.array([[1.,1.],[1.,0.]])
    PSD=np.ones((2,2));stationary=np.array([1.,-1.],complex);global_phi=np.ones(2,complex)
    # Larger full-rank PSD Hermitian example with a strict suboptimal local max:
    # three ferromagnetic angles in each group, weak negative cross-coupling.
    # The simple stationary counterexample suffices to refute a general theorem;
    # no claim that this tiny example is an author full-scene simulation.
    shifted=PSD+np.eye(2)
    source=source_hashes(['audit_single_hu_guarantee.py','run_support.py'])
    result={'scope':'mathematical_counterexample_NOT_original_channel_simulation_or_curve',
        'author_source_anchors':{'printed_augmented_matrix':'ch_third.tex349-353','general_PSD_global_claim':'ch_third.tex390'},
        'printed_block_counterexample':{'matrix':C.tolist(),'principal_minor_determinant':float(np.linalg.det(C)),
            'eigenvalues':np.linalg.eigvalsh(C).tolist(),'printed_PSD_claim_false_if_cross_block_nonzero':bool(np.min(np.linalg.eigvalsh(C))<0)},
        'PSD_non_global_stationary_counterexample':{'matrix':PSD.tolist(),'eigenvalues':np.linalg.eigvalsh(PSD).tolist(),
            'stationary_point':stationary.real.tolist(),'stationary_objective':float(np.vdot(stationary,PSD@stationary).real),
            'stationary_Riemannian_gradient_norm':float(np.linalg.norm(rgrad(PSD,stationary))),
            'global_point':global_phi.real.tolist(),'global_objective':float(np.vdot(global_phi,PSD@global_phi).real),
            'positive_definite_shift_eigenvalues':np.linalg.eigvalsh(shifted).tolist(),
            'shifted_stationary_objective':float(np.vdot(stationary,shifted@stationary).real),
            'shifted_global_objective':float(np.vdot(global_phi,shifted@global_phi).real)},
        'conclusion':'PSD and monotone RGD alone do not guarantee global maximization of a unit-modulus QCQP; original RGD retained with stationarity-only evidence',
        'executed_source_hashes':source,'source_unchanged_during_run':unchanged(source),'reference_ordinates_used':False,
        'full_reproduction_pass':False,'publisher_version_equivalence_verified':False}
    result['all_counterexamples_verified']=bool(np.linalg.det(C)<0 and np.linalg.norm(rgrad(PSD,stationary))==0 and result['PSD_non_global_stationary_counterexample']['global_objective']>result['PSD_non_global_stationary_counterexample']['stationary_objective'])
    save_receipt(Path(__file__).with_name('outputs')/'single-HU-guarantee-counterexamples.json',result)
    print(json.dumps({'all_counterexamples_verified':result['all_counterexamples_verified'],'source_unchanged_during_run':result['source_unchanged_during_run']}),flush=True)
