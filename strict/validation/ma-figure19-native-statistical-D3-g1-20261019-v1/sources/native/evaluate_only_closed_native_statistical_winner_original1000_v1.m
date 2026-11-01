function receipt=evaluate_only_closed_native_statistical_winner_original1000_v1(admissionPath)
% One native saved winner, one original1000 return. No search/AO/FPA/RNG.
a=jsondecode(fileread(admissionPath));
assert(a.root_admitted_unique_saved_native_winner_original1000&&a.user_selected_statistical_target,'MAFinal:Admission','Explicit actual native winner evaluation admission required.');
assert(strcmp(ma_native_grid_io_v1('sha_file',a.prepared_plan_path),a.prepared_plan_SHA256),'MAFinal:Plan','Reviewed final1000 plan differs.');
before=pin_identity(a.source_pins);
for i=1:numel(a.source_pins)
    p=a.source_pins(i);[~,name,extension]=fileparts(p.path);
    if strcmp(extension,'.m'),assert(strcmpi(strrep(which(name),'\','/'),strrep(p.path,'\','/')),'MAFinal:Provider','Loaded evaluation provider differs.');end
end
for i=1:numel(a.closed_search_files),p=a.closed_search_files(i);assert(strcmp(ma_native_grid_io_v1('sha_file',p.path),p.SHA256),'MAFinal:ClosedSearch','Closed native search bytes differ.');end
assert(strcmp(ma_native_grid_io_v1('sha_file',a.search_terminal_path),a.search_terminal_SHA256),'MAFinal:Terminal','Actual original-handle native terminal changed.');
terminal=jsondecode(fileread(a.search_terminal_path));
assert(terminal.natural_wait_completed&&terminal.initial_child_birth_observed&&terminal.exact_original_handle_birth_and_exit_match&&terminal.all_watched_source_and_job_bytes_unchanged&&terminal.actual_child_terminal_exit_code==0&&terminal.effective_host_exit_code==0,'MAFinal:Terminal','Complete source-closed natural0 native search required.');
assert(terminal.actual_child_terminal_observation.exact_original_Popen_handle_used&&terminal.actual_child_terminal_observation.actual_OS_exit_code==0&&terminal.child.PID==terminal.actual_child_terminal_observation.PID&&terminal.child.creation_FILETIME==terminal.actual_child_terminal_observation.creation_FILETIME,'MAFinal:Terminal','Same original handle/birth/exit required.');
assert(isequal(terminal.command,a.actual_search_command),'MAFinal:Terminal','Actual native search command differs from admission.');
state=ma_native_grid_io_v1('load',fullfile(a.search_directory,'bounded-frontier.mat'));
searchBinding=ma_native_grid_io_v1('load',fullfile(a.search_directory,'binding.mat'));
ma_native_grid_io_v1('assert_same',state.binding,searchBinding,'Search binding and final frontier differ');
assert(state.complete&&isempty(state.stack)&&strcmp(state.status,'complete_exact_native_statistical_search')&&~isempty(state.best)&&isempty(state.host_failure),'MAFinal:Incomplete','Only a complete error-free actual native statistical frontier can be evaluated.');
primitive=ma_native_grid_io_v1('load',fullfile(a.search_directory,'native-frozen-primitive-inputs-once.mat'));
assert(strcmp(ma_native_grid_io_v1('sha_value',primitive),state.binding.model_primitive_SHA256),'MAFinal:Basis','Actual native primitive bits differ from search target.');
assert(strcmp(state.binding.mode,a.mode)&&strcmp(primitive.mode,a.mode)&&any(strcmp(a.mode,{'MRT','ZF'})),'MAFinal:Mode','Only the same native single-mode winner.');
caller=state.binding.caller_binding;
assert(strcmp(caller.job_SHA256,a.job_SHA256)&&strcmp(caller.configuration_SHA256,a.configuration_SHA256),'MAFinal:Input','Native winner job/config identity differs.');
pin_identity(caller.source_pins); % Exact frozen search provider closure, no source execution.
assert(strcmp(ma_native_grid_io_v1('sha_file',a.job_path),a.job_SHA256)&&strcmp(ma_native_grid_io_v1('sha_file',a.configuration_path),a.configuration_SHA256),'MAFinal:Input','Original saved geometry/population/config changed.');
job=jsondecode(fileread(a.job_path));config=jsondecode(fileread(a.configuration_path));
assert(job.figure==a.figure&&job.point==a.D&&job.brute_force_D==a.D&&job.realization==a.realization&&job.N==primitive.N&&job.N==state.binding.N&&job.M==state.binding.M,'MAFinal:Slot','Native winner slot/dimensions differ.');
assert(config.nlos_realizations_per_geometry==1000&&numel(job.nlos_re)==1000*job.N*job.M&&isequal(size(job.nlos_re),[1000,job.N,job.M])&&isequal(size(job.nlos_im),size(job.nlos_re)),'MAFinal:Population','Exactly the original1000 saved NLoS arrays required.');
context=ma_theory_native_original_bridge_v1('context',config,job);c=context.c;
names={'beta','rician','noise','power','directions','wavelength','minimum_distance','region_lower','region_upper'};
physical=struct;for i=1:numel(names),name=names{i};ma_native_grid_io_v1('assert_same',c.(name),primitive.(name),['Native physical field differs: ',name]);physical.(name)=c.(name);end
indices=state.winner_indices;
assert(isequal(size(indices),[1,job.N])&&all(isfinite(indices))&&all(indices==fix(indices))&&all(diff(indices)>0)&&all(indices>=1)&&all(indices<=size(primitive.grid,1)),'MAFinal:Winner','Canonical actual native winner indices required.');
for i=1:numel(indices),for j=i+1:numel(indices),assert(primitive.actual_exact_squared_spacing_compatibility(indices(i),indices(j)),'MAFinal:Spacing','Saved native winner violates exact search spacing.');end,end
positions=primitive.grid(indices,:);
binding=struct('role','one complete native statistical winner original1000 final performance',...
    'source_pins',{a.source_pins},'search_terminal_SHA256',a.search_terminal_SHA256,'closed_search_files',{a.closed_search_files},...
    'job_SHA256',a.job_SHA256,'configuration_SHA256',a.configuration_SHA256,'native_model_primitive_SHA256',state.binding.model_primitive_SHA256,...
    'mode',a.mode,'figure',job.figure,'D',a.D,'realization',job.realization,'winner_indices',indices,...
    'winner_positions_SHA256',ma_native_grid_io_v1('sha_value',positions),'native_physical_fields_SHA256',ma_native_grid_io_v1('sha_value',physical),...
    'original_input_fingerprint',caller.original_shared_bank_input_fingerprint,'population_count',1000,...
    'MATLAB_version',version,'BLAS',version('-blas'));
ma_native_grid_io_v1('bind',a.output_directory,binding);
closed=fullfile(a.output_directory,'closed-original1000-return.mat');
if isfile(closed)
    receipt=ma_native_grid_io_v1('load',closed);ma_native_grid_io_v1('assert_same',receipt.binding,binding,'Closed original1000 return identity differs');
    assert(strcmp(ma_native_grid_io_v1('sha_file',receipt.full_saved_input_and_return_path),receipt.full_saved_input_and_return_SHA256),'MAFinal:ChangedReturn','Existing closed performance evidence changed.');return;
end
lock=fullfile(a.output_directory,'active-original1000-evaluation.lock');f=javaObject('java.io.File',lock);
assert(f.createNewFile(),'MAFinal:ActiveOrUncertain','Existing active/uncertain evaluation requires actual owner terminal review; no automatic repeat.');
started=tic;
try
    actual=ma_theory_native_original_bridge_v1('final1000',config,job,positions,a.mode);
    elapsed=toc(started);
    assert(numel(actual.sample_sum_rates)==1000&&numel(actual.powers)==1000&&numel(actual.off_diagonal_amplitude)==1000,'MAFinal:Return','Original complete1000 return required.');
    allFinite=all(isfinite(actual.sample_sum_rates))&&all(isfinite(actual.powers))&&all(isfinite(actual.off_diagonal_amplitude));
    payload=struct('binding',binding,'positions',positions,'physical',physical,'original_statistical_exact_product',state.best,...
        'original_saved_nlos_re',job.nlos_re,'original_saved_nlos_im',job.nlos_im,...
        'actual_original_instantaneous_return',actual,'full_configuration_JSON_bytes',read_bytes(a.configuration_path));
    resultPath=fullfile(a.output_directory,'saved-native-winner-input-and-all1000-performance.mat');
    ma_native_grid_io_v1('mat',resultPath,payload);after=pin_identity(a.source_pins);
    assert(ma_native_grid_io_v1('same',before,after),'MAFinal:Source','Evaluation source changed; return retained without acceptance.');
    assert(strcmp(ma_native_grid_io_v1('sha_file',a.job_path),a.job_SHA256)&&strcmp(ma_native_grid_io_v1('sha_file',a.configuration_path),a.configuration_SHA256),'MAFinal:InputInterval','Original population/config changed; return retained without acceptance.');
    for i=1:numel(a.closed_search_files),p=a.closed_search_files(i);assert(strcmp(ma_native_grid_io_v1('sha_file',p.path),p.SHA256),'MAFinal:InputInterval','Closed native search input changed during evaluation.');end
    receipt=struct('binding',binding,'actual_original_sample_count',1000,'all_actual_return_fields_finite',allFinite,...
        'actual_original_mean_sum_rate',actual.mean_sum_rate,'actual_original_sample_sum_rates',actual.sample_sum_rates,...
        'actual_original_powers',actual.powers,'actual_original_off_diagonal_amplitude',actual.off_diagonal_amplitude,...
        'full_saved_input_and_return_path',resultPath,'full_saved_input_and_return_SHA256',ma_native_grid_io_v1('sha_file',resultPath),...
        'source_before',{before},'source_after',{after},'source_interval_closed',true,'saved_input_interval_closed',true,'elapsed_original1000_seconds',elapsed,...
        'new_search_AO_FPA_optimizer_or_RNG_calls',0,'original_saved_NLoS_samples_evaluated',1000,...
        'independent_physics_or_statistical_winner_or_dual_PASS',false,'historical_reference_PASS',false,'paper_PASS',false);
    ma_native_grid_io_v1('mat',closed,receipt);ma_native_grid_io_v1('json',fullfile(a.output_directory,'ACTUAL_ONE_NATIVE_STATISTICAL_WINNER_ORIGINAL1000_FINAL_RETURN_V1.json'),receipt);delete(lock);
catch err
    retained=struct('binding',binding,'failure',ma_native_grid_io_v1('failure',err),'partial_outputs_retained',true,'automatic_retry_allowed',false,...
        'independent_physics_or_statistical_winner_or_dual_PASS',false);
    ma_native_grid_io_v1('mat',fullfile(a.output_directory,'retained-original1000-evaluation-error.mat'),retained);rethrow(err);
end
end

function values=pin_identity(pins)
values=pins;for i=1:numel(pins),values(i).SHA256=ma_native_grid_io_v1('sha_file',pins(i).path);assert(strcmp(values(i).SHA256,pins(i).SHA256),'MAFinal:Source','Pinned source differs: %s',pins(i).path);end
end

function bytes=read_bytes(path)
fid=fopen(path,'rb');assert(fid>=0,'MAFinal:IO','Cannot read saved configuration bytes.');clean=onCleanup(@()fclose(fid));bytes=fread(fid,inf,'*uint8'); %#ok<NASGU>
end
