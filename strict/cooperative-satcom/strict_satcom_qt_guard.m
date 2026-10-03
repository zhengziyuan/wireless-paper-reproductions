function [candidate,info]=strict_satcom_qt_guard(kind,varargin)
% Identical original QT inputs/auxiliaries/constraints under CVX precision retries.
assert(any(strcmp(kind,{'mr','ap'})),'Unknown original QT guard');previous=cvx_precision;restore=onCleanup(@()cvx_precision(previous));controls={'high','best'};attempts={};last='';
for k=1:numel(controls)
    cvx_precision(controls{k});
    try
        [value,out]=strict_satcom_core([kind,'_qt_update'],varargin{:});d=out.solver_diagnostics;before=min(out.before.sinr);after=min(out.after.sinr);
        accepted=isfinite(after)&&after>=before-1e-5&&isfinite(d.constraint_max_relative_violation)&&d.constraint_max_relative_violation<=1e-5 ...
            &&isfinite(out.qt_bound_max_violation)&&out.qt_bound_max_violation<=1e-5;
        attempts{end+1}=struct('numerical_precision',controls{k},'solver_status',out.solver_status, ...
            'primal_relative_violation',d.constraint_max_relative_violation,'qt_bound_violation',out.qt_bound_max_violation, ...
            'before_minimum_sinr',before,'after_minimum_sinr',after,'accepted',accepted); %#ok<AGROW>
        if accepted,candidate=value;info=out;info.solver_diagnostics.same_original_QT_numerical_attempts=attempts;return;end
        last='Original physical/primal/QT/monotonicity gates rejected the numeric solution';
    catch err,last=err.message;attempts{end+1}=struct('numerical_precision',controls{k},'error',last,'accepted',false);end %#ok<AGROW>
end
error('Same-input same-QT precision controls exhausted; no model or gate relaxed: %s',last);
end
