function [phi,info]=strict_instantaneous_sdr_guard(direct,R,phi0,W,a,noise,normals)
% Re-solve the identical SDP with identical original Gaussian draws if needed.
previous=cvx_precision;restore=onCleanup(@()cvx_precision(previous));controls={'high','best'};attempts={};last='';
for k=1:numel(controls)
    cvx_precision(controls{k});
    try
        [candidate,out]=strict_hotspot_core('phase_sdr_update',direct,R,phi0,W,a,noise,normals);
        d=out.solver_diagnostics;accepted=isfinite(d.sdr_bound_max_violation)&&d.sdr_bound_max_violation<=1e-5 ...
            &&isfinite(d.constraint_max_relative_violation)&&d.constraint_max_relative_violation<=1e-5 ...
            &&out.unit_modulus_error<=1e-5&&out.diagonal_error<=1e-5&&out.smallest_sdp_eigenvalue>=-1e-5;
        attempts{end+1}=struct('numerical_precision',controls{k},'all_candidates',out.randomization_count, ...
            'rounded_surrogate',out.rounded_surrogate,'sdr_upper_bound',out.sdr_upper_bound, ...
            'bound_excess',d.sdr_bound_max_violation,'primal_relative_violation',d.constraint_max_relative_violation,'accepted',accepted); %#ok<AGROW>
        if accepted
            phi=candidate;info=out;info.solver_diagnostics.post_rounding_same_problem_attempts=attempts;
            info.solver_diagnostics.all_original_draws_upper_bound_guard='same_input_same_original_draws_same_SDP_numerical_precision_only';return;
        end
        last='Actual original Gaussian candidates exceed the unchanged SDP upper-bound/primal gate';
    catch err,last=err.message;attempts{end+1}=struct('numerical_precision',controls{k},'error',last,'accepted',false);end %#ok<AGROW>
end
error('Same-input same-SDP precision controls exhausted; no candidates dropped: %s',last);
end
