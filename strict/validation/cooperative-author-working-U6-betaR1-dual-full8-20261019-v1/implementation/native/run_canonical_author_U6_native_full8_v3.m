function result=run_canonical_author_U6_native_full8_v3(configPath,outputPath,sweepId,canonicalMATPath)
% Explicit full author-model run. No automatic count/cap/dimension reduction.
% External CVX required. Full defaults can be expensive; root coordinates runs.
entryWall=tic; entryCPU=cputime;
assert(nargin==4&&isfile(canonicalMATPath),'Explicit canonical saved input required');
canonicalBindingBefore=canonical_binding(configPath,canonicalMATPath);
strict_satcom_power24_mc_capture_v1('configure',outputPath);
passiveMCGuard=onCleanup(@()strict_satcom_power24_mc_capture_v1('abort_if_open')); %#ok<NASGU>
timedV2Root=fileparts(which('strict_satcom_algorithms_final_algorithm3_v2_timed_v2'));addpath(timedV2Root,'-begin');
complexTransportSelftest=strict_satcom_complex_json_transport_selftest_v1();
pipelineClocks=struct('clock_APIs','MATLAB_tic_toc_and_cputime','CPU_scope','MATLAB_cputime_process_CPU_not_external_descendants','matlab_version',version,'matlab_release',version('-release'),'computer',computer,'prefdir',prefdir,'tempdir',tempdir,'actual_CVX_solver',cvx_solver,'scheme_scope','complete_disjoint_numeric_components_with_disclosed_internal_capture_overhead','setup_MC_export_outside_scheme_clocks',true);
assert(nargin>=3&&strcmp(sweepId,'base'),'Prospectivev3 one fullcase preflight only; no formal183/grid run before nativefull/source approval');
config=canonical_config_for_MAT(configPath); sweeps=num2cell(config.sweeps); comparison=config.multi_vs_single;
if comparison.enabled
    if isfield(comparison,'interference_values_linear'), axisName='interference_to_noise_ratio';grid=comparison.interference_values_linear;
    else, axisName='interference_to_noise_db';grid=comparison.interference_values_db; end
    for kappa=comparison.kappa_leo_db(:).'
        sweeps{end+1}=struct('id',sprintf('multi_vs_single_multi_kL%g',kappa),'parameter',axisName, ...
            'values',grid,'kappa_leo_db',kappa,'satellite_mode','multi'); %#ok<AGROW>
        for offset=comparison.offsets_deg(:).'
            sweeps{end+1}=struct('id',sprintf('multi_vs_single_single_%g_kL%g',offset,kappa),'parameter',axisName, ...
                'values',grid,'kappa_leo_db',kappa,'satellite_mode','single','offset_deg',offset); %#ok<AGROW>
        end
    end
end
if nargin>=3 && strcmp(sweepId,'base')
    sweeps={struct('id','base','parameter','power_w','values',config.reported.power_w,'kappa_leo_db',config.reported.kappa_leo_db)};
elseif nargin>=3
    ids=cellfun(@(x)x.id,sweeps,'UniformOutput',false); sweeps=sweeps(strcmp(ids,sweepId)); assert(~isempty(sweeps),'Unknown sweep');
end
sourceHashes=strict_satcom_final_algorithm3_timed_hashes_v3(configPath);started=tic; records={};
for sidx=1:numel(sweeps)
    sweep=sweeps{sidx};
    for value=sweep.values(:).'
        scene=config; scene.reported.(sweep.parameter)=value; scene.reported.kappa_leo_db=sweep.kappa_leo_db;
        if isfield(sweep,'satellite_mode') && strcmp(sweep.satellite_mode,'single')
            scene.reported.J=1; scene.reported.N=comparison.single_N; scene.reported.power_w=comparison.single_power_w;
            scene.tuned_not_reported.satellite_latitudes_deg=sweep.offset_deg; scene.tuned_not_reported.upa_shape=comparison.single_upa_shape;
        end
        setupWall=tic; setupCPU=cputime;
        [data,pl,il]=load_canonical_author_U6_data_v1(canonicalMATPath,scene);
        strict_satcom_capture('begin',struct('configuration',scene,'data',data,'power_limit',pl,'interference_limit',il));
        setupClock=struct('wall_seconds',toc(setupWall),'process_CPU_seconds',cputime-setupCPU,'scope','canonical_saved_input_format_load_and_capture_begin');
        algorithmWall=tic; algorithmCPU=cputime;
        try,[schemes,measuredClocks]=strict_satcom_algorithms_final_algorithm3_v2_timed_v2(data,scene.tuned_not_reported,pl,il);
            algorithmClock=struct('wall_seconds',toc(algorithmWall),'process_CPU_seconds',cputime-algorithmCPU,'scope','all_eight_chains_and_outer_assembly_evaluation_capture','complete',true);
        catch exception
            algorithmClock=struct('wall_seconds',toc(algorithmWall),'process_CPU_seconds',cputime-algorithmCPU,'scope','actual_partial_eight_chain_pipeline_until_exception','complete',false,'partial_scheme_clocks_unavailable_on_exception',true);
            stateExportWall=tic; stateExportCPU=cputime;
            stateRecording=strict_satcom_capture('save',[outputPath '.states.mat']);
            stateExportClock=struct('wall_seconds',toc(stateExportWall),'process_CPU_seconds',cputime-stateExportCPU,'scope','state_export_and_original_export_hash');
            records{end+1}=struct('sweep',sweep.id,'parameter',sweep.parameter,'value',value,'status','failed','error',exception.message, ...
                'constraint_pass',false,'convergence_pass',false,'solver_primal_pass',false,'qt_bound_pass',false,'valid_figure_point',false); %#ok<AGROW>
            records{end}.measured_setup_clock=setupClock;records{end}.measured_algorithm_pipeline_clock=algorithmClock;
            continue;
        end
        violations=0;
        for e=1:numel(schemes)
            violations=max([violations;schemes(e).evaluation.satellite_power-pl;schemes(e).evaluation.gt_interference-il]);
        end
        momentWall=tic; momentCPU=cputime;
        mc=moment_mc(data,scene.tuned_not_reported.monte_carlo_realizations,scene.tuned_not_reported.seed);
        momentClock=struct('wall_seconds',toc(momentWall),'process_CPU_seconds',cputime-momentCPU,'count',scene.tuned_not_reported.monte_carlo_realizations,'scope','independent_channel_moment_validation_not_optimized_performance_MC');
        convergence=true;primal=true;bound=true;
        for e=1:numel(schemes)
            status=schemes(e).status;convergence=convergence&&status.converged;if isfield(status,'phase_source_converged'),convergence=convergence&&status.phase_source_converged;end
            primal=primal&&status.numerical.solver_primal_pass;bound=bound&&status.numerical.qt_bound_pass;
        end
        physical=violations<scene.tuned_not_reported.solver_objective_tolerance;valid=physical&&convergence&&primal&&bound;reason='executed_but_capped_or_numerically_unvalidated';if valid,reason='converged_and_validated';end
        records{end+1}=struct('sweep',sweep.id,'parameter',sweep.parameter,'value',value,'schemes',schemes, ...
            'monte_carlo',mc,'constraint_pass',physical,'convergence_pass',convergence,'solver_primal_pass',primal,'qt_bound_pass',bound,'valid_figure_point',valid,'status',reason); %#ok<AGROW>
        records{end}.measured_setup_clock=setupClock;records{end}.measured_algorithm_pipeline_clock=algorithmClock;records{end}.measured_algorithm_clocks=measuredClocks;records{end}.measured_moment_validation_clock=momentClock;
        fprintf('Completed author-model %s value=%g in %.1fs\n',sweep.id,value,toc(started));
    end
end
if ~exist('stateRecording','var'),stateExportWall=tic;stateExportCPU=cputime;stateRecording=strict_satcom_capture('save',[outputPath '.states.mat']);stateExportClock=struct('wall_seconds',toc(stateExportWall),'process_CPU_seconds',cputime-stateExportCPU,'scope','state_export_and_original_export_hash');end
checks=struct('constraint_pass',all(cellfun(@(x)x.constraint_pass,records)),'convergence_pass',all(cellfun(@(x)x.convergence_pass,records)), ...
    'solver_primal_pass',all(cellfun(@(x)x.solver_primal_pass,records)),'qt_bound_pass',all(cellfun(@(x)x.qt_bound_pass,records)));
result=struct('paper_id','cooperative-satcom','source_version',config.source_version, ...
    'final_publisher_conformance',config.final_publisher_conformance, ...
    'scope','author_model_all_eight_algorithm_chains_full_dimensions_tuned_sweeps', ...
    'elapsed_seconds',toc(started),'results',{records},'checks',checks, ...
    'overall_implemented_scope_success',~isempty(records)&&all(cellfun(@(x)x.valid_figure_point,records)), ...
    'all_configured_sweeps_requested',nargin<3,'figure_validation_policy','Failed/capped/numerically-unvalidated points are retained and invalidate their selected sweep.', ...
    'numerical_version','prospective_v3_only_exact_constant_factored_MR_QT_added_to_same_v2_increments', ...
    'old_bank_not_upgraded',true,'new_formal183_bank_executed',false,'full_reproduction_pass',false,'remaining',{{'Publisher-version conformance','Original unreported values and figure grids','Published-figure agreement'}}, ...
    'configuration',config,'state_recording',stateRecording,'executed_source_hashes',sourceHashes,'source_unchanged_during_run',isequal(sourceHashes,strict_satcom_final_algorithm3_timed_hashes_v3(configPath)));
result.canonical_saved_input_before=canonicalBindingBefore;result.canonical_saved_input_after=canonical_binding(configPath,canonicalMATPath);
result.canonical_saved_input_interval_unchanged=isequal(result.canonical_saved_input_before,result.canonical_saved_input_after);
result.physical_variant='user_source_literal_U6_native_saved_input_enabled_cold_corrected_full8';result.old_physical_scenario_factory_executed=false;result.author_original_random_channel_prefix_reexecuted=false;
result.source_literal_U6_variant_only=true;result.final_U2_Fig2_Fig3_original_reference_or_paper_PASS=false;
assert(result.canonical_saved_input_interval_unchanged,'Canonical saved input/new IO sources changed');
pipelineClocks.entry_before_JSON_export=struct('wall_seconds',toc(entryWall),'process_CPU_seconds',cputime-entryCPU);pipelineClocks.state_export=stateExportClock;pipelineClocks.configured_moment_draws=config.tuned_not_reported.monte_carlo_realizations;
result.measured_pipeline_clocks=pipelineClocks;result.complex_JSON_transport_selftest_receipt=complexTransportSelftest;result.timing_source='new_complete_component_native_final_Algorithm3_V2_transport';result.author_historical_timing_recovered=false;result.scientific_pass_implied_by_clocks=false;
assert(result.source_unchanged_during_run,'Actual cooperative runtime sources changed; no mixed-source certification');
folder=fileparts(outputPath); if ~isempty(folder) && ~exist(folder,'dir'), mkdir(folder); end
% Preserve the complete unmodified scientific result before any result JSON encoding.
fullResultPath=[outputPath '.full-result-before-JSON.mat'];assert(~isfile(fullResultPath),'Preserve prior full result MAT');
fullResultMATWall=tic;fullResultMATCPU=cputime;
save(fullResultPath,'result','-v7');
fullResultMATClock=struct('wall_seconds',toc(fullResultMATWall),'process_CPU_seconds',cputime-fullResultMATCPU,'path',fullResultPath,'scope','save_full_unmodified_result_v7_before_any_result_JSON_encode');
complexTransportWall=tic;complexTransportCPU=cputime;
transportResult=strict_satcom_complex_json_transport_v1('encode',result);
complexTransportClock=struct('wall_seconds',toc(complexTransportWall),'process_CPU_seconds',cputime-complexTransportCPU,'scope','encode_only_complex_numeric_to_reversible_tagged_copy','original_result_unchanged',true);
jsonExportWall=tic;jsonExportCPU=cputime;
fid=fopen(outputPath,'w'); assert(fid>=0); clean=onCleanup(@()fclose(fid)); fprintf(fid,'%s\n',jsonencode(transportResult));clear clean;
clockReceipt=struct('JSON_export',struct('wall_seconds',toc(jsonExportWall),'process_CPU_seconds',cputime-jsonExportCPU,'scope','original_result_JSON_encode_write_close'),'entry_through_JSON_export',struct('wall_seconds',toc(entryWall),'process_CPU_seconds',cputime-entryCPU),'clock_receipt_own_write_excluded',true,'scientific_or_original_timing_pass',false);
clockReceipt.full_result_before_JSON_MAT_export=fullResultMATClock;clockReceipt.complex_transport_encode=complexTransportClock;clockReceipt.returned_result_remains_unmodified_complex_MATLAB_result=true;
clockPath=[outputPath '.measured-clock-receipt.json'];assert(~isfile(clockPath),'Preserve previous measured clock receipt');fid=fopen(clockPath,'w');assert(fid>=0);clean=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(clockReceipt));
end

function out=moment_mc(data,count,seed)
rng(seed,'twister'); [J,U,N]=size(data.d_mean); M=size(data.r_mean,2); phi=ones(U,M);
[~,~,Q,fourth,~]=strict_satcom_models('moments',data,phi); powers=zeros(J,U); fourths=zeros(J,U);
strict_satcom_power24_mc_capture_v1('begin',data,phi,count,seed,rng);
for realization=1:count
    for u=1:U
        r=data.r_mean(u,:).'+sqrt(data.r_var(u))*cn([M,1]);
        strict_satcom_power24_mc_capture_v1('r',realization,u,r);
        for j=1:J
            G=reshape(data.G_mean(j,u,:,:),N,M)+sqrt(data.G_var(j,u))*cn([N,M]);
            d=reshape(data.d_mean(j,u,:),N,1)+sqrt(data.d_var(j,u))*cn([N,1]); h=d+G*r;
            p=sum(abs(h).^2); powers(j,u)=powers(j,u)+p; fourths(j,u)=fourths(j,u)+p^2;
            strict_satcom_power24_mc_capture_v1('leaf',realization,u,j,G,d,h,p,p^2);
        end
    end
end
exact2=zeros(J,U); for j=1:J, for u=1:U, exact2(j,u)=real(trace(reshape(Q(j,u,:,:),N,N))); end, end
e2=abs(powers/count-exact2)./exact2; e4=abs(fourths/count-fourth)./fourth;
out=struct('count',count,'second_moment_max_relative_error',max(e2(:)),'fourth_moment_max_relative_error',max(e4(:)), ...
    'purpose','Independent finite-Rician channel validation, not fabricated performance data');
strict_satcom_power24_mc_capture_v1('finish',powers,fourths,exact2,fourth,out,rng);
end
function x=cn(shape)
x=(randn(shape)+1i*randn(shape))/sqrt(2);
end


function out=canonical_binding(configPath,canonicalMATPath)
root=fileparts(mfilename('fullpath'));
out=struct('canonical_MAT',file_identity(canonicalMATPath),'configuration',file_identity(configPath), ...
    'actual_new_runner',file_identity(fullfile(root,'run_canonical_author_U6_native_full8_v3.m')), ...
    'actual_saved_loader',file_identity(fullfile(root,'load_canonical_author_U6_data_v1.m')), ...
    'actual_passive_MC_capture',file_identity(which('strict_satcom_power24_mc_capture_v1')));
end
function out=file_identity(path)
fid=fopen(path,'rb');assert(fid>=0);cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
bytes=fread(fid,Inf,'*uint8');digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(bytes);raw=typecast(digest.digest(),'uint8');
out=struct('path',path,'SHA256',lower(reshape(dec2hex(raw,2).',1,[])));
end

function config=canonical_config_for_MAT(configPath)
% Scientific values remain exact JSON values. Long metadata keys are preserved
% as original JSON text, not truncated MATLAB struct names or dropped content.
shortText=fileread(configPath);raw=jsondecode(shortText);config=struct();
keep={'schema_version','paper_id','source_version','final_publisher_conformance', ...
    'reported','tuned_not_reported','sweeps','multi_vs_single'};
for k=1:numel(keep),config.(keep{k})=raw.(keep{k});end
assert(raw.physical_input_variant.requires_explicit_saved_factory&&strcmp(raw.physical_input_variant.stage,'enabled'));
config.physical_input_variant=struct('requires_explicit_saved_factory',true,'stage','enabled', ...
    'canonical_NPZ_SHA256','ce39e03acac33fa0670264ee5f49cf95f2ea6bf96334ab09fb0445978cf4df8e', ...
    'physical_generation_is_forbidden',true);
originalIdentity=file_identity(raw.original_config_JSON_path);
assert(strcmp(originalIdentity.SHA256,raw.original_config_JSON_SHA256)&&strcmp(originalIdentity.SHA256,'998a1c191e60897eef08fac565b3aeb95fc5e0024572dbb4ba3874feeb44f79d'));
config.original_config_JSON_text=fileread(raw.original_config_JSON_path);
config.original_config_JSON_SHA256=originalIdentity.SHA256;
shortIdentity=file_identity(configPath);config.native_short_config_JSON_SHA256=shortIdentity.SHA256;
config.metadata_projection_note='Only metadata is stored as exact original JSON text; every scientific config field/value is unchanged.';
assert_valid_MAT_field_names(config);
end
function assert_valid_MAT_field_names(value)
if isstruct(value)
    names=fieldnames(value);
    for q=1:numel(value)
        for k=1:numel(names)
            assert(numel(names{k})<=namelengthmax,'Unsafe metadata field length');
            assert_valid_MAT_field_names(value(q).(names{k}));
        end
    end
elseif iscell(value)
    for k=1:numel(value),assert_valid_MAT_field_names(value{k});end
end
end
