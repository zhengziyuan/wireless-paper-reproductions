function result = run_mis_communications(outputPath)
%RUN_MIS_COMMUNICATIONS Independent reduced LoS MIS max-min SNR implementation.
% Base MATLAB only. Exact per-user position selection; circle Armijo ascent.
root = fileparts(mfilename('fullpath'));
if nargin < 1
    outputPath = fullfile(root,'results-matlab.json');
end
f = jsondecode(fileread(fullfile(root,'fixture.json')));
model = initialize_model(f);
initial_min = min(selected_model(model,model.initial));
[baseline,~] = phase_ascent(model,model.initial,f.static_iterations,f.smoothing_mu,true,false);
static_min = min(selected_model(model,baseline));
best = baseline; best_min = static_min; history = struct([]);
starts = {baseline,model.initial};
for s = 1:numel(starts)
    [candidate,trajectory] = phase_ascent(model,starts{s},f.iterations,f.smoothing_mu,false,false);
    minimum = min(selected_model(model,candidate));
    if minimum >= best_min
        best = candidate; history = trajectory; best_min = minimum;
    end
end
rates = evaluate_model(model,best);
[selected,~,schedule] = selected_model(model,best);
value = softmin_model(model,best,f.smoothing_mu,false);
checks = model_diagnostics(model,best);
checks.gradient_pass = checks.rate_gradient_relative_error < 1e-6;
checks.constraint_pass = checks.unit_modulus_error < 1e-12 && checks.one_hot_row_sum_error == 0;
checks.static_incumbent_retained = best_min+1e-12 >= static_min;
checks.softmin_lower_bound_error = max(0,value-best_min);
checks.softmin_upper_bound_error = max(0,best_min-value-f.smoothing_mu*log(model.K));
if isempty(history)
    checks.accepted_objective_monotonicity_error = 0;
else
    differences = diff([history.softmin]);
    checks.accepted_objective_monotonicity_error = max([0,-differences]);
end
metrics = struct('initial_worst_snr',initial_min,'optimized_static_worst_snr',static_min, ...
    'optimized_mis_worst_snr',best_min,'mis_gain_over_static',best_min-static_min, ...
    'selected_user_snr',selected.','snr_by_user_and_position',rates, ...
    'selected_position_index_one_based',schedule.','ms1_phase_radians',best(1:model.M).', ...
    'ms2_phase_radians',best(model.M+1:end).','softmin_value',value, ...
    'smoothing_gap_bound',f.smoothing_mu*log(model.K));
result = struct('paper_id',f.paper_id,'metrics',metrics,'checks',checks,'history',history);
save_json(result,outputPath);
fprintf('MIS communications: %.12g\n',best_min);
end

function model = initialize_model(f)
model.f = f;
mr = f.ms1_shape(1); mc = f.ms1_shape(2);
nr = f.ms2_shape(1); nc = f.ms2_shape(2);
model.M = mr * mc; model.N = nr * nc;
model.K = size(f.cascaded_spatial_frequencies, 1); model.P = model.M + model.N;
model.U = (mr - nr + 1) * (mc - nc + 1);
model.mapping = zeros(model.U, model.N);
u = 0;
for r = 0:mr-nr
    for c = 0:mc-nc
        u = u + 1; n = 0;
        for i = 0:nr-1
            for j = 0:nc-1
                n = n + 1;
                model.mapping(u,n) = (r+i)*mc+c+j+1;
            end
        end
    end
end
coordinates = zeros(model.M,2); m = 0;
for r = 0:mr-1
    for c = 0:mc-1
        m = m+1; coordinates(m,:) = [r,c];
    end
end
model.C = exp(2i*pi*(f.cascaded_spatial_frequencies * coordinates.'));
model.initial = [f.initial_ms1_phases(:); f.initial_ms2_phases(:)];
end

function [metric,jac,V,gain,echo] = evaluate_model(model,angles,power)
phi = exp(1i*angles(1:model.M));
theta = exp(1i*angles(model.M+1:end));
padding = complex(ones(model.M,model.U));
for u = 1:model.U
    padding(model.mapping(u,:),u) = theta;
end
V = phi .* padding;
amplitude = model.C * V;
derivative = complex(zeros(model.K,model.U,model.P));
for u = 1:model.U
    derivative(:,u,1:model.M) = reshape(1i*model.C.*V(:,u).',[model.K,1,model.M]);
    overlap = model.mapping(u,:);
    derivative(:,u,model.M+1:end) = reshape(1i*model.C(:,overlap).*V(overlap,u).',[model.K,1,model.N]);
end
gain = abs(amplitude).^2;
gain_jac = 2*real(conj(amplitude).*derivative);
if strcmp(model.f.mode,'communications')
    scale = model.f.reference_snr(:);
    metric = scale.*gain; jac = scale.*gain_jac; echo = zeros(size(gain));
else
    beta2 = model.f.beta_squared(:);
    echo = beta2.*gain.^2;
    echo_jac = 2*beta2.*gain.*gain_jac;
    if nargin < 3
        power = model.f.transmit_power;
    end
    noise = model.f.noise_power(:)/power;
    denominator = sum(echo,1)-echo+noise;
    denominator_jac = sum(echo_jac,1)-echo_jac;
    metric = echo./denominator;
    jac = echo_jac./denominator - (echo./denominator.^2).*denominator_jac;
end
end

function [selected,jac,schedule] = selected_model(model,angles,power)
if nargin < 3
    [metric,all_jac] = evaluate_model(model,angles);
else
    [metric,all_jac] = evaluate_model(model,angles,power);
end
[maximum,~] = max(metric,[],2);
% Smallest-index machine-roundoff ties, not a result-matching tolerance.
tie = 32*eps(1).*max(max(abs(metric),[],2),realmin);
schedule = zeros(model.K,1); selected = zeros(model.K,1);
for k = 1:model.K
    schedule(k) = find(metric(k,:) >= maximum(k)-tie(k),1,'first');
    selected(k) = metric(k,schedule(k));
end
jac = zeros(model.K,model.P);
for k = 1:model.K
    jac(k,:) = reshape(all_jac(k,schedule(k),:),[1,model.P]);
end
end

function [value,gradient] = softmin_model(model,angles,mu,log_metric)
[selected,jac] = selected_model(model,angles);
if log_metric
    jac = jac./(selected+1e-14);
    selected = log(selected+1e-14);
end
minimum = min(selected);
unnormalized = exp(-(selected-minimum)/mu);
weights = unnormalized/sum(unnormalized);
value = minimum-mu*log(sum(unnormalized));
gradient = jac.'*weights;
end

function [best,history] = phase_ascent(model,initial,iterations,mu,is_static,log_metric)
x = initial(:);
if is_static
    x(model.M+1:end) = 0;
end
best = x; best_min = min(selected_model(model,x));
history = struct('iteration',{},'softmin',{},'minimum_metric',{},'incumbent_minimum',{},'gradient_norm',{},'step',{});
for iteration = 1:iterations
    [value,gradient] = softmin_model(model,x,mu,log_metric);
    if is_static
        gradient(model.M+1:end) = 0;
    end
    magnitude = norm(gradient); direction = gradient/max(1,magnitude);
    step = 1; accepted = false;
    for backtrack = 1:32
        trial = x+step*direction;
        trial_value = softmin_model(model,trial,mu,log_metric);
        if trial_value >= value+1e-4*step*(gradient.'*direction)
            x = trial; accepted = true; break;
        end
        step = step*0.5;
    end
    minimum = min(selected_model(model,x));
    if minimum > best_min
        best_min = minimum; best = x;
    end
    recorded_step = 0;
    if accepted
        recorded_step = step;
    end
    history(iteration) = struct('iteration',iteration,'softmin',softmin_model(model,x,mu,log_metric), ...
        'minimum_metric',minimum,'incumbent_minimum',best_min,'gradient_norm',magnitude,'step',recorded_step);
end
end

function angles = quadratic_phases(model)
mr = model.f.ms1_shape(1); mc = model.f.ms1_shape(2);
nr = model.f.ms2_shape(1); nc = model.f.ms2_shape(2);
curvature = model.f.quadratic_curvature;
angles = zeros(model.P,1); m = 0;
for r = 0:mr-1
    for c = 0:mc-1
        m = m+1; angles(m) = curvature*(r*r+c*c);
    end
end
n = 0;
for r = 0:nr-1
    for c = 0:nc-1
        n = n+1; angles(model.M+n) = -curvature*(r*r+c*c);
    end
end
end

function checks = model_diagnostics(model,angles)
[metric,jac,V,gain,echo] = evaluate_model(model,angles);
h = 1e-6; fd = zeros(size(jac));
for p = 1:model.P
    offset = zeros(model.P,1); offset(p) = h;
    plus = evaluate_model(model,angles+offset);
    minus = evaluate_model(model,angles-offset);
    fd(:,:,p) = (plus-minus)/(2*h);
end
quadratic_error = 0; quartic_error = 0;
for k = 1:model.K
    G = conj(model.C(k,:)).' * model.C(k,:);
    for u = 1:model.U
        quadratic = real(V(:,u)'*G*V(:,u));
        quadratic_error = max(quadratic_error,abs(quadratic-gain(k,u)));
        if strcmp(model.f.mode,'sensing')
            reconstructed = model.f.beta_squared(k)*quadratic^2;
            quartic_error = max(quartic_error,abs(reconstructed-echo(k,u)));
        end
    end
end
[selected,~,schedule] = selected_model(model,angles);
onehot = zeros(model.K,model.U);
for k = 1:model.K
    onehot(k,schedule(k)) = 1;
end
checks = struct('finite_outputs',all(isfinite(metric(:))), ...
    'unit_modulus_error',max(abs(abs(V(:))-1)), ...
    'one_hot_row_sum_error',max(abs(sum(onehot,2)-1)), ...
    'quadratic_amplitude_identity_error',quadratic_error, ...
    'rate_gradient_relative_error',max(abs(fd(:)-jac(:)))/max(1,max(abs(jac(:)))), ...
    'selected_rate_identity_error',max(abs(selected-sum(onehot.*metric,2))), ...
    'number_of_positions_correct',model.U == (model.f.ms1_shape(1)-model.f.ms2_shape(1)+1)*(model.f.ms1_shape(2)-model.f.ms2_shape(2)+1));
if strcmp(model.f.mode,'sensing')
    checks.quartic_echo_identity_error = quartic_error;
end
end

function save_json(result,outputPath)
folder = fileparts(outputPath);
if ~isempty(folder) && ~isfolder(folder)
    mkdir(folder);
end
[fid,message] = fopen(outputPath,'w','n','UTF-8');
assert(fid >= 0, 'Unable to create output: %s',message);
cleanup = onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(result,PrettyPrint=true));
end
