function out = strict_hotspot_recorded_history_audit(history,tolerance,complete,numerical_abs_tolerance)
% Independent recorded-history check. Does not change optimizer stop behavior.
if nargin < 4,numerical_abs_tolerance=1e-6;end
assert(islogical(complete)&&isscalar(complete),'complete must be scalar logical');
assert(isnumeric(history)&&isreal(history)&&(isvector(history)||isempty(history))&&all(isfinite(history(:))),'finite real history required');
assert(isnumeric(tolerance)&&isreal(tolerance)&&isscalar(tolerance)&&isfinite(tolerance)&&tolerance>0,'invalid tolerance');
assert(isnumeric(numerical_abs_tolerance)&&isreal(numerical_abs_tolerance)&&isscalar(numerical_abs_tolerance)&&isfinite(numerical_abs_tolerance)&&numerical_abs_tolerance>=0,'invalid numerical tolerance');
h=double(history(:).'); d=diff(h); assert(all(isfinite(d)),'nonfinite computed difference');
signed=[];old=[];if ~isempty(d),signed=d(end)/max(abs(h(end-1)),1e-12);assert(isfinite(signed),'nonfinite signed residual');old=signed<tolerance;end
neg=d(d<0); nondecrease=[];gate=[];
if ~isempty(neg),nondecrease=false;elseif complete&&~isempty(d),nondecrease=true;end
if ~isempty(neg),gate=false;elseif complete&&~isempty(d),gate=old;end
out=struct('history_complete_asserted',complete,'record_count',numel(h), ...
    'differences',d,'signed_relative_increment',signed,'production_signed_stop_recomputed',old, ...
    'negative_increment_count',numel(neg),'negative_within_numerical_abs_tolerance_count',sum(neg>=-numerical_abs_tolerance), ...
    'numerical_abs_tolerance',double(numerical_abs_tolerance),'recorded_nondecrease',nondecrease, ...
    'independent_recorded_stop_and_nondecrease_gate',gate,'source_provenance_authenticated',false, ...
    'mathematical_convergence_proved',false,'full_paper_pass',false);
end
