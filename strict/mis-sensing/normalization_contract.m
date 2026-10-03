function contract = normalization_contract(settings, powerDbm)
% Explicit SI reference and matched-noise contract; no implicit PRI count.
if nargin<2,powerDbm=settings.power_dbm;end
required={'reference_echo_db','reference_echo_unit','reference_echo_noise_domain','effective_reference_gain_factor'};
for k=1:numel(required),assert(isfield(settings,required{k}),['Explicit sensing normalization field required: ',required{k}]);end
unit=string(settings.reference_echo_unit);domain=string(settings.reference_echo_noise_domain);
assert(any(unit==["inverse_watt","inverse_milliwatt"]),'Invalid reference_echo_unit');
assert(any(domain==["raw_per_PRI","processed"]),'Invalid reference_echo_noise_domain');
gain=settings.effective_reference_gain_factor;
assert(isscalar(gain)&&isfinite(gain)&&gain>0,'Effective reference gain must be finite and positive');
assert(domain~="processed"||gain==1,'Processed reference already includes gain; double counting rejected');
referenceDb=settings.reference_echo_db;
assert(isscalar(referenceDb)&&isfinite(referenceDb)&&isscalar(powerDbm)&&isfinite(powerDbm),'Reference level and power must be finite scalars');
siDb=referenceDb+30*double(unit=="inverse_milliwatt");
ratio=10^(siDb/10);powerWatt=10^((powerDbm-30)/10);
assert(isfinite(ratio)&&ratio>0&&isfinite(powerWatt)&&powerWatt>0,'SI ratio and power must remain finite and positive');
effectiveRatio=ratio*gain;effectivePower=powerWatt*gain;
assert(isfinite(effectiveRatio)&&effectiveRatio>0&&isfinite(effectivePower)&&effectivePower>0,'Effective products must remain finite and positive');
noiseOverPower=1/effectivePower;assert(isfinite(noiseOverPower)&&noiseOverPower>0,'Effective noise must remain finite and positive');
if isfield(settings,'normalization_status'),status=settings.normalization_status;else,status='explicit_contract_not_source_parameter_certification';end
contract=struct('physical_power_dbm',powerDbm,'physical_power_watt',powerWatt,...
    'input_reference_echo_db',referenceDb,'input_reference_echo_unit',char(unit),...
    'reference_echo_db_per_watt',siDb,'reference_echo_ratio_per_watt',ratio,...
    'reference_echo_noise_domain',char(domain),'effective_reference_gain_factor',gain,...
    'effective_reference_ratio_per_watt',effectiveRatio,'echo_beta_squared',ratio,...
    'noise_over_power',noiseOverPower,'normalization_status',status,...
    'physical_processing_origin_verified',false);
end
