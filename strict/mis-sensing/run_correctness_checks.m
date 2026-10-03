function results = run_correctness_checks(outputDirectory)
% Mathematical correctness checks, never a 6000-start paper-figure certificate.
base=fileparts(mfilename('fullpath'));addpath(base);
if nargin<1,outputDirectory=fullfile(base,'outputs','correctness-v2');end
if ~isfolder(outputDirectory),mkdir(outputDirectory);end
settings=jsondecode(fileread(fullfile(base,'settings.json')));
watt=normalization_contract(settings,30);milli=settings;milli.reference_echo_unit='inverse_milliwatt';milli.reference_echo_db=settings.reference_echo_db-30;
converted=normalization_contract(milli,30);
assert(abs(watt.effective_reference_ratio_per_watt-converted.effective_reference_ratio_per_watt)<=1e-14*watt.effective_reference_ratio_per_watt,'W/mW conversion must preserve physical ratios');
candidate=jsondecode(fileread(fullfile(base,'settings_reference_candidate.json')));raw=normalization_contract(candidate,30);
processed=candidate;processed.reference_echo_noise_domain='processed';processed.reference_echo_db=candidate.reference_echo_db+10*log10(candidate.effective_reference_gain_factor);processed.effective_reference_gain_factor=1;
post=normalization_contract(processed,30);
assert(abs(raw.effective_reference_ratio_per_watt-post.effective_reference_ratio_per_watt)<=1e-14*raw.effective_reference_ratio_per_watt,'Raw/processed normalization must agree');
assert(watt.physical_power_watt==1&&watt.echo_beta_squared==10^(settings.reference_echo_db/10));
for setting={settings,candidate},s=setting{1};assert(s.number_of_starts==6000&&s.outer_iterations==30&&s.rcg_max_iterations==4000);end
rejected=false;try,processed.effective_reference_gain_factor=100;normalization_contract(processed);catch,rejected=true;end
assert(rejected,'Processed reference must reject duplicate integration gain');
results.normalization=struct('W_mW_invariant',true,'raw_processed_invariant',true,'power_coefficient_not_squared_twice',true,'original_budgets',true,'double_counting_rejected',true);
results.component=run_mis_sensing(fullfile(outputDirectory,'mis-sensing-matlab.json'),'component-test-guard');
required={'gradient_pass','constraint_pass','ralm_update_pass','pslr_gradient_pass','number_of_positions_correct'};
for j=1:numel(required),assert(isfield(results.component.checks,required{j})&&isequal(results.component.checks.(required{j}),true),['Component check failed: ',required{j}]);end
checks=results.component.checks;
assert(checks.quadratic_identity_error<1e-12&&checks.quartic_echo_identity_error<1e-12&&checks.ordinary_transpose_amplitude_error<1e-12,'Independent echo identities failed');
linechecks=checks.production_line_search_regression;names=fieldnames(linechecks);
for j=1:numel(names),if endsWith(names{j},'_pass'),assert(isequal(linechecks.(names{j}),true),['Line-search regression failed: ',names{j}]);end,end
results.closed_form=run_mis_sensing(fullfile(outputDirectory,'closed-form-matlab.json'),'closed-form-test');
results.stable_increment=run_mis_sensing(fullfile(outputDirectory,'stable-increment-matlab.json'),'stable-increment-test');
disp('Sensing normalization, components, full-size finite closed-form identities and 11 Decimal-reference increments PASS. Not complete paper figures.');
end
