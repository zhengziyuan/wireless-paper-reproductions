"""Receipt-only validation; this module never changes an optimization update."""
import numpy as np


def relative_stop(history, cap, tolerance):
    residual=None if len(history)<2 else float((history[-1]-history[-2])/max(abs(history[-2]),1e-12))
    converged=residual is not None and np.isfinite(residual) and np.isfinite(tolerance) and 0<tolerance and residual<tolerance
    return {'converged':bool(converged),'termination':'relative_improvement' if converged else 'configured_iteration_cap',
            'iterations':len(history)-1,'iteration_cap':cap,'stop_rule':'signed_relative_objective_increase',
            'threshold':tolerance,'final_residual':residual}


def gradient_stop(norm, iterations, cap, tolerance):
    converged=np.isfinite(norm) and np.isfinite(tolerance) and 0<tolerance and norm<tolerance
    return {'converged':bool(converged),'termination':'gradient_tolerance' if converged else 'configured_iteration_cap',
            'iterations':iterations,'iteration_cap':cap,'stop_rule':'Riemannian_gradient_norm',
            'threshold':tolerance,'final_residual':float(norm)}


def numerical_gate(records, settings):
    primal=settings.get('solver_primal_relative_tolerance',1e-5); bound=settings.get('qt_bound_tolerance',1e-5)
    records=[r if isinstance(r,dict) else {} for r in records]
    errors=[r.get('solver_diagnostics',{}).get('constraint_max_relative_violation') for r in records]
    bounds=[r.get('qt_bound_max_violation') for r in records]
    finite=lambda values:bool(values) and all(isinstance(v,(float,int,np.number)) and np.isfinite(v) and v>=0 for v in values)
    return {'solver_primal_pass':bool(finite(errors) and np.isfinite(primal) and primal>0 and all(v<=primal for v in errors)),
            'qt_bound_pass':bool(finite(bounds) and np.isfinite(bound) and bound>0 and all(v<=bound for v in bounds)),
            'solver_primal_relative_tolerance':primal,'qt_bound_tolerance':bound,
            'maximum_primal_relative_violation':max(errors) if finite(errors) else None,
            'maximum_qt_bound_violation':max(bounds) if finite(bounds) else None}


def stop_valid(stop):
    if not isinstance(stop,dict):return False
    value=stop.get('final_residual');threshold=stop.get('threshold')
    return bool(stop.get('converged') is True and isinstance(value,(float,int,np.number)) and np.isfinite(value)
                and isinstance(threshold,(float,int,np.number)) and np.isfinite(threshold) and threshold>0
                and value<threshold and stop.get('stop_rule') in ('signed_relative_objective_increase','Riemannian_gradient_norm'))


def scheme_status(stops, records, settings):
    numerical=numerical_gate(records,settings)
    converged=bool(stops) and all(stop_valid(s) for s in stops)
    return {'converged':bool(converged),'termination':'all_original_stop_rules_reached' if converged else 'one_or_more_configured_caps',
            'blocks':stops,'numerical':numerical,'solver_diagnostics':records,
            'algorithm_success':bool(converged and numerical['solver_primal_pass'] and numerical['qt_bound_pass'])}
