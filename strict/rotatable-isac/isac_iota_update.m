function result = isac_iota_update(p, desired, previous_iota, mode, epsilon, epsilon_source)
%ISAC_IOTA_UPDATE Prepared standalone fixed-state component; no optimizer.
% The source label is supplied by the caller and is not independently verified.
% Outputs and comparisons use double arithmetic and can hide changes due to
% rounding. This file is not connected to the production MATLAB implementation.
% If p=0 and desired has positive energy, the NMSE is 1 for any positive iota;
% this helper conservatively refuses that degenerate update, not because its
% finite NMSE minimizers do not exist.

if nargin < 5, epsilon = []; end
if nargin < 6, epsilon_source = []; end
result = struct('schema','isac-iota-fixed-state-helper-v1', ...
    'mode',mode,'status','failed','source_provenance_verified',false, ...
    'full_scientific_acceptance',false, ...
    'numeric_precision','binary64; comparison can hide changes below rounding precision');
try
    mode = text_value(mode,'unknown_mode');
    if ~(strcmp(mode,'exact') || strcmp(mode,'safeguarded'))
        fail('unknown_mode');
    end
    result.mode = mode;
    if strcmp(mode,'exact') && (~isempty(epsilon) || ~isempty(epsilon_source))
        fail('exact_disallows_epsilon');
    end
    if strcmp(mode,'safeguarded')
        epsilon = positive(epsilon,'epsilon');
        epsilon_source = text_value(epsilon_source,'epsilon_source_required');
        if isempty(strtrim(epsilon_source)) || numel(epsilon_source)>512
            fail('epsilon_source_required');
        end
        result.epsilon=epsilon; result.epsilon_source=epsilon_source;
    end
    previous_iota=positive(previous_iota,'previous_iota');
    p=vector_value(p,'pattern'); desired=vector_value(desired,'desired');
    if numel(p) ~= numel(desired), fail('length_mismatch'); end
    c=finite_sum(products(p,p,'pattern_square'),'pattern_energy');
    d=finite_sum(products(p,desired,'overlap_product'),'overlap');
    e=finite_sum(products(desired,desired,'desired_square'),'desired_energy');
    if c<=0, fail('zero_pattern_energy'); end
    if e<=0, fail('zero_desired_energy'); end
    if strcmp(mode,'exact') && d<=0, fail('exact_zero_overlap_no_finite_minimizer'); end
    if strcmp(mode,'exact')
        denominator=d;
    else
        denominator=d+epsilon;
        result.epsilon_addition_rounded_away=(denominator==d);
    end
    if ~isfinite(denominator) || denominator<=0
        fail('update_denominator_overflow_or_nonpositive');
    end
    new_iota=positive(checked_divide(c,denominator,'iota'),'new_iota');
    before=calc_nmse(p,desired,previous_iota,e);
    after=calc_nmse(p,desired,new_iota,e);
    if after>before
        change='increased';
    elseif after<before
        change='decreased';
    else
        change='equal';
    end
    result.status='ok'; result.pattern_energy=c; result.overlap=d;
    result.desired_energy=e; result.previous_iota=previous_iota;
    result.new_iota=new_iota; result.nmse_before=before; result.nmse_after=after;
    result.observed_change=change;
    result.interpretation='fixed saved state only; no AO monotonicity or convergence claim';
catch err
    % Do not disguise an implementation error as a validated arithmetic failure.
    if ~strcmp(err.identifier,'isac_iota_update:InvalidArithmetic'), rethrow(err); end
    result.reason=err.message;
end
end

function fail(reason)
error('isac_iota_update:InvalidArithmetic','%s',reason);
end

function value=text_value(value,reason)
if isstring(value) && isscalar(value), value=char(value); end
if ~ischar(value) || (~isrow(value) && ~isempty(value)), fail(reason); end
end

function value=positive(value,field)
if ~isnumeric(value) || islogical(value) || ~isreal(value) || ~isscalar(value)
    fail([field '_not_real']);
end
value=double(value);
if ~isfinite(value) || value<=0, fail([field '_not_finite_positive']); end
end

function value=vector_value(value,field)
if ~isnumeric(value) || islogical(value) || ~isreal(value) || ~isvector(value) || isempty(value) || numel(value)>4096
    fail([field '_invalid_length']);
end
value=double(value(:));
if any(~isfinite(value)) || any(value<0), fail([field '_negative_or_nonfinite']); end
end

function value=products(a,b,field)
value=a.*b;
if any(~isfinite(value)), fail([field '_overflow']); end
if any(a~=0 & b~=0 & value==0), fail([field '_underflow']); end
end

function value=finite_sum(terms,field)
value=sum(terms);
if ~isfinite(value), fail([field '_overflow']); end
end

function value=checked_divide(a,b,field)
if ~isfinite(b) || b<=0, fail([field '_invalid_denominator']); end
value=a./b;
if any(~isfinite(value)), fail([field '_overflow']); end
if any(a~=0 & value==0), fail([field '_underflow']); end
end

function value=calc_nmse(p,desired,iota,energy)
residual=checked_divide(p,iota,'p_over_iota')-desired;
if any(~isfinite(residual)), fail('residual_overflow'); end
value=checked_divide(finite_sum(products(residual,residual,'residual_square'),'residual_sum'),energy,'nmse');
end
