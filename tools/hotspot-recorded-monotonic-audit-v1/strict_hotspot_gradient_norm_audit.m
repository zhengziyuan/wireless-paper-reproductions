function out = strict_hotspot_gradient_norm_audit(norm_value,tolerance)
% Independent recorded-gradient check. No optimizer changes.
assert(isnumeric(norm_value)&&isreal(norm_value)&&isscalar(norm_value)&&isfinite(norm_value),'finite real norm required');
assert(isnumeric(tolerance)&&isreal(tolerance)&&isscalar(tolerance)&&isfinite(tolerance)&&tolerance>0,'positive finite tolerance required');
out=struct('production_gradient_stop_recomputed',norm_value<=tolerance, ...
    'norm_nonnegative',norm_value>=0,'independent_recorded_gradient_gate',norm_value>=0&&norm_value<=tolerance, ...
    'mathematical_convergence_proved',false,'source_provenance_authenticated',false,'full_paper_pass',false);
end
