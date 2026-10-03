"""Early ESA-weighted signal model versus later scalar-isotropic covariance.

No optimizer or reference ordinate is used. A scalar mean variance is used
only as the proven closest isotropic matrix, not as a substituted model.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
from scenario_geometry import sample_scenario
from run_support import source_hashes,unchanged,save_receipt

if __name__=='__main__':
    base=Path(__file__).parent;config=json.loads((base/'statistical_geometry_config.json').read_text());config['reported'].update(U=6,K=10,kappa_ground_db=20,kappa_satellite_db=0)
    hashes=source_hashes(['scenario_geometry.py','audit_covariance_contract.py','statistical_geometry_config.json'])
    f=sample_scenario(config,np.random.default_rng(config['tuned_not_reported']['seed']));x=f['mean_inputs'];rng=np.random.default_rng(2026100499);records=[];count=20000
    for kind in ('direct','nhu'):
        variance=x[kind+'_variance'];means=x[kind+'_mean'];J,N=variance.shape
        draws=(rng.standard_normal((count,J,N))+1j*rng.standard_normal((count,J,N)))/np.sqrt(2)
        observed=np.mean(abs(draws*np.sqrt(variance)[None,:,:])**2,axis=0)
        for j in range(J):
            v=variance[j];closest_scalar=float(np.mean(v));error=float(np.linalg.norm(v-closest_scalar)/np.linalg.norm(v));mc_error=float(np.max(abs(observed[j]-v)/v))
            records.append({'type':kind,'user_index':j,'original_ESA_weighted_variance_by_feed':v.tolist(),
                'D_squared_by_feed':(abs(means[j])**2+v).tolist(),
                'closest_isotropic_scalar_variance':closest_scalar,
                'closest_isotropic_relative_Frobenius_error':error,'isotropic_representation_exact':bool(error<1e-12),
                'independent_MC_draws':count,'physical_covariance_MC_max_relative_error':mc_error,
                'physical_covariance_MC_pass':bool(mc_error<6/np.sqrt(count)),
                'closest_scalar_is_diagnostic_only_NOT_author_mu_or_production_substitution':True})
    result={'scope':'source_model_covariance_contract_audit_NOT_optimized_performance_or_reproduction',
            'derivation':'h_n=D_n*(sqrt(beta/(1+beta))*a_n+sqrt(1/(1+beta))*e_n), e_nIIDCN(0,1) => Cov=diag(D_n^2)/(1+beta). Later scalar muI equals it only if allD_n^2 identical.',
            'closest_isotropic_proof':'argmin_c ||diag(v)-cI||_F^2 hasc=mean(v); anyotherauthor scalar hasatleastsameerror.',
            'cases':records,'all_physical_covariance_MC_pass':all(r['physical_covariance_MC_pass'] for r in records),
            'literal_early_signal_and_later_scalar_covariance_simultaneously_exact':all(r['isotropic_representation_exact'] for r in records),
            'no_reference_ordinates_or_optimizer_used':True,'executed_source_hashes':hashes,
            'source_unchanged_during_run':unchanged(hashes),'publisher_version_equivalence_verified':False,'full_reproduction_pass':False}
    save_receipt(base/'outputs'/'source-covariance-contract-audit.json',result)
    print(json.dumps({'all_physical_covariance_MC_pass':result['all_physical_covariance_MC_pass'],
        'closest_isotropic_relative_error_min':min(r['closest_isotropic_relative_Frobenius_error'] for r in records),
        'closest_isotropic_relative_error_max':max(r['closest_isotropic_relative_Frobenius_error'] for r in records),
        'literal_early_and_later_both_exact':result['literal_early_signal_and_later_scalar_covariance_simultaneously_exact'],
        'source_unchanged_during_run':result['source_unchanged_during_run']}),flush=True)
