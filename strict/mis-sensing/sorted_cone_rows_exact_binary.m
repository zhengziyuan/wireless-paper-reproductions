function [out, info] = sorted_cone_rows_exact_binary(X, y)
% WORK: same Euclidean simplex tangent cone, finite sorted scalar root.
% No pruning, support tolerance, changed metric, or direction formula.
% Only roundoff-uncertain comparisons escalate to exact stored-binary sums.
out = zeros(size(y)); info = cell(size(y,1),1);
for row = 1:size(y,1)
    values = y(row,:); mandatory = X(row,:) > 0;
    free = find(mandatory);
    if isempty(free) || any(~isfinite(values))
        error('sensing:invalidConeInput','Finite raw direction and positive simplex coordinate required');
    end
    if all(values == values(free(1)))
        info{row} = struct('method','exact_constant_row','mandatory_count',numel(free),'optional_active_count',0);
        continue
    end
    centered = values - values(free(1));
    optional = find(~mandatory);
    [~, order] = sort(centered(optional),'descend'); optional = optional(order);
    chosen = free; count = 0;
    threshold = compensated_sum(centered(chosen)) / numel(chosen);
    for index = optional
        if centered(index) <= threshold, break; end
        chosen(end+1) = index; count = count+1;
        threshold = compensated_sum(centered(chosen)) / numel(chosen);
    end
    previousOK = count==0 || centered(optional(count)) > threshold;
    nextOK = count==numel(optional) || threshold >= centered(optional(count+1));
    roundoffGuard = 16*eps*max(max(abs(centered)),realmin);
    uncertain = any(abs(centered(optional)-threshold) <= roundoffGuard);
    if ~previousOK || ~nextOK || uncertain
        [out(row,:), exactInfo] = exact_binary_row(values, mandatory, optional);
        exactInfo.roundoff_guard_only_not_support_or_stopping_tolerance = roundoffGuard;
        info{row} = exactInfo;
    else
        result = max(centered-threshold,0);
        result(mandatory) = centered(mandatory)-threshold;
        out(row,:) = result;
        info{row} = struct('method','finite_sorted_centered_compensated_sum', ...
            'mandatory_count',numel(free),'optional_active_count',count, ...
            'roundoff_guard_only_not_support_or_stopping_tolerance',roundoffGuard);
    end
end
end

function value = compensated_sum(values)
% Neumaier summation. Uncertain support comparisons never rely on this alone.
total = 0; compensation = 0;
for x = values
    trial = total + x;
    if abs(total) >= abs(x)
        compensation = compensation + ((total-trial)+x);
    else
        compensation = compensation + ((x-trial)+total);
    end
    total = trial;
end
value = total + compensation;
end

function [out, info] = exact_binary_row(values, mandatory, optional)
% BigDecimal(double), NOT valueOf(double), represents the actual IEEE binary
% double exactly. Sums/multiplication/comparisons below have NO MathContext.
% Membership uses n*y_i versus the exact sum, avoiding rounded division.
if ~usejava('jvm')
    error('sensing:exactConeRequiresJVM','Exact binary uncertain-row fallback requires the bundled MATLAB JVM');
end
raw = cell(1,numel(values));
for index = 1:numel(values)
    raw{index} = javaObject('java.math.BigDecimal',double(values(index)));
end
total = javaObject('java.math.BigDecimal',int32(0));
free = find(mandatory);
for index = free, total = total.add(raw{index}); end
rounding = javaMethod('valueOf','java.math.RoundingMode','HALF_EVEN');
context = javaObject('java.math.MathContext',int32(128),rounding);
for count = 0:numel(optional)
    if count>0, total = total.add(raw{optional(count)}); end
    denominator = javaObject('java.math.BigDecimal',int32(numel(free)+count));
    previousOK = count==0;
    if count>0
        previousScaled = raw{optional(count)}.multiply(denominator);
        previousOK = previousScaled.compareTo(total)>0;
    end
    nextOK = count==numel(optional);
    if count<numel(optional)
        nextScaled = raw{optional(count+1)}.multiply(denominator);
        nextOK = total.compareTo(nextScaled)>=0;
    end
    if previousOK && nextOK
        out = zeros(size(values));
        for index = 1:numel(values)
            scaled = raw{index}.multiply(denominator);
            numerator = scaled.subtract(total);
            if mandatory(index) || numerator.signum()>0
                divided = numerator.divide(denominator,context);
                out(index) = divided.doubleValue();
            end
        end
        threshold = total.divide(denominator,context);
        info = struct('method','exact_binary_BigDecimal_row_only', ...
            'mandatory_count',numel(free),'optional_active_count',count, ...
            'threshold_decimal_128',char(threshold.toString()), ...
            'membership_comparison_exact_without_division',true, ...
            'BigDecimal_constructor_exact_binary_not_valueOf',true);
        return
    end
end
error('sensing:exactConeRoot','Exact finite cone root could not be bracketed');
end
