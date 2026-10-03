function result = run_mis_sensing(outputPath)
%RUN_MIS_SENSING Independent reduced exact-scheduling RALM for quartic echoes.
% Base MATLAB only; inner circle steepest-descent replaces original RCG.
root = fileparts(mfilename('fullpath'));
if nargin < 1
    outputPath = fullfile(root,'results-matlab.json');
end
f = jsondecode(fileread(fullfile(root,'fixture.json')));
model = initialize_model(f);
quadratic = quadratic_phases(model);
quadratic_min = min(selected_model(model,quadratic));
[baseline,~] = phase_ascent(model,model.initial,f.static_iterations,f.smoothing_mu,true,true);
static_min = min(selected_model(model,baseline));
best = baseline; best_min = static_min; history = struct([]); monotonicity_error = 0;
starts = {baseline,quadratic,model.initial};
for s = 1:numel(starts)
    [candidate,trajectory,error] = ralm(model,starts{s});
    minimum = min(selected_model(model,candidate));
    if minimum >= best_min
        best = candidate; history = trajectory; best_min = minimum; monotonicity_error = error;
    end
end
[rates,~,~,gain,echo] = evaluate_model(model,best);
[selected,~,schedule] = selected_model(model,best);
checks = model_diagnostics(model,best);
gradient_error = ralm_gradient_error(model);
checks.ralm_gradient_relative_error = gradient_error;
checks.gradient_pass = checks.rate_gradient_relative_error < 1e-6 && gradient_error < 1e-6;
checks.constraint_pass = checks.unit_modulus_error < 1e-12 && checks.one_hot_row_sum_error == 0;
checks.returned_epigraph_feasibility_error = max(0,max(best_min-selected));
checks.inner_accepted_objective_monotonicity_error = monotonicity_error;
checks.static_incumbent_retained = best_min+1e-12 >= static_min;
sweep = zeros(size(f.power_sweep));
for p = 1:numel(sweep)
    sweep(p) = min(selected_model(model,best,f.power_sweep(p)));
end
metrics = struct('initial_worst_sinr',min(selected_model(model,model.initial)), ...
    'quadratic_heuristic_worst_sinr',quadratic_min,'optimized_static_worst_sinr',static_min, ...
    'optimized_mis_worst_sinr',best_min,'optimized_mis_worst_sinr_db',10*log10(best_min), ...
    'mis_gain_over_static',best_min-static_min,'selected_target_sinr',selected.', ...
    'sinr_by_target_and_position',rates,'echo_power_by_target_and_position',echo, ...
    'selected_position_index_one_based',schedule.','ms1_phase_radians',best(1:model.M).', ...
    'ms2_phase_radians',best(model.M+1:end).','power_sweep',f.power_sweep(:).', ...
    'fixed_design_power_sweep_worst_sinr',sweep(:).');
result = struct('paper_id',f.paper_id,'metrics',metrics,'checks',checks,'history',history);
save_json(result,outputPath);
fprintf('MIS sensing: %.12g\n',best_min);
end

function [value,gradient,q] = augmented_lagrangian(model,angles,eta,multipliers,rho)
[selected,jac] = selected_model(model,angles);
q = eta-selected;
positive = max(0,multipliers/rho+q);
value = -eta+0.5*rho*(positive.'*positive);
gradient = [-rho*(jac.'*positive); -1+rho*sum(positive)];
end

function [best,history,monotonicity_error] = ralm(model,initial)
f = model.f; x = initial(:); eta = min(selected_model(model,x));
multipliers = zeros(model.K,1); rho = f.initial_penalty;
previous_violation = inf; best = x; best_min = eta; monotonicity_error = 0;
history = struct('outer_iteration',{},'eta',{},'minimum_sinr',{},'incumbent_minimum_sinr',{}, ...
    'inequality_violation',{},'penalty',{},'augmented_lagrangian',{},'gradient_norm',{});
for outer = 1:f.outer_iterations
    for inner = 1:f.inner_iterations
        [value,gradient] = augmented_lagrangian(model,x,eta,multipliers,rho);
        magnitude = norm(gradient); direction = -gradient/max(1,magnitude);
        step = 1;
        for backtrack = 1:32
            trial_x = x+step*direction(1:end-1);
            trial_eta = eta+step*direction(end);
            trial_value = augmented_lagrangian(model,trial_x,trial_eta,multipliers,rho);
            if trial_value <= value+1e-4*step*(gradient.'*direction)
                monotonicity_error = max(monotonicity_error,trial_value-value);
                x = trial_x; eta = trial_eta; break;
            end
            step = step*0.5;
        end
        minimum = min(selected_model(model,x));
        if minimum > best_min
            best_min = minimum; best = x;
        end
    end
    [value,gradient,q] = augmented_lagrangian(model,x,eta,multipliers,rho);
    violation = max(0,max(q));
    history(outer) = struct('outer_iteration',outer,'eta',eta,'minimum_sinr',min(selected_model(model,x)), ...
        'incumbent_minimum_sinr',best_min,'inequality_violation',violation,'penalty',rho, ...
        'augmented_lagrangian',value,'gradient_norm',norm(gradient));
    multipliers = min(1e6,max(0,multipliers+rho*q));
    if violation > 0.8*previous_violation
        rho = rho*f.penalty_growth;
    end
    previous_violation = violation;
end
monotonicity_error = max(0,monotonicity_error);
end

function error = ralm_gradient_error(model)
x = model.initial; eta = min(selected_model(model,x))+0.2;
multipliers = 0.2+0.1*(0:model.K-1).'; rho = 1.1;
[~,analytic] = augmented_lagrangian(model,x,eta,multipliers,rho);
z = [x;eta]; fd = zeros(size(z)); h = 1e-6;
for p = 1:numel(z)
    offset = zeros(size(z)); offset(p) = h;
    plus = z+offset; minus = z-offset;
    value_plus = augmented_lagrangian(model,plus(1:end-1),plus(end),multipliers,rho);
    value_minus = augmented_lagrangian(model,minus(1:end-1),minus(end),multipliers,rho);
    fd(p) = (value_plus-value_minus)/(2*h);
end
error = max(abs(fd-analytic))/max(1,max(abs(analytic)));
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
