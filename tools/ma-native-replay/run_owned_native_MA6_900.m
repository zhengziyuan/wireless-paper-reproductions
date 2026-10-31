function receipt=run_owned_native_MA6_900(preparedPath,expectedPreparedSHA,freshOutputFolder)
% Current user full-six-paper goal: one missing-language original full900 bank.
% One unchanged original entry call; no numerical function transformation.
here=fileparts(mfilename('fullpath'));assert(strcmp(which(mfilename),fullfile(here,[mfilename,'.m'])),'Recorder entry shadowed.');
assert(strcmp(file_sha(preparedPath),expectedPreparedSHA),'External prepared-recorder SHA mismatch.');
p=jsondecode(fileread(preparedPath));assert(strcmp(p.scope,'CURRENT_GOAL_owned_native_MA6_full900_record_only_v1'),'Exact recorder preparation required.');
assert(strcmp(file_sha(p.selected_input_binding_path),p.selected_input_binding_sha256),'Exact selected original900 input binding changed.');
assert(p.whole_population_count==900&&numel(p.original_inputs)==900,'All900 original inputs required.');
folder=canonical(freshOutputFolder);allowed=canonical(p.allowed_output_parent);
assert(~isfolder(folder)&&~isfile(folder)&&strcmpi(canonical(fileparts(folder)),allowed),'Strict NEW declared data-folder child required.');
originalPath=path;cleanup=onCleanup(@()path(originalPath)); %#ok<NASGU>
sourceFolder=fileparts(p.selected_original_sources(1).path);addpath(sourceFolder,'-begin');
mkdir(folder);
r=struct('scope','ACTUAL_owned_native_MA6_full900_record_only_v1','prepared_native_sha256',expectedPreparedSHA,...
    'prepared_sha256',p.selected_input_binding_sha256,'fresh_output_created_without_reuse',true,...
    'numerical_sources_modified_by_wrapper',false,'scientific_entry_call_count',0,...
    'all900_actual_saved_schema_and_declared_gate_observations_passed',false,'independent_physical_or_FPA_step_KKT_verified',false,...
    'original_author_curve_closeness_verified',false,'original_hidden_local_stop_quantity_recovered',false,...
    'complete_runtime_binary_dependency_provenance',false,'exception',[],'evidence_exceptions',{{}});
% BEGIN V2 ACTUAL OUTPUT ROOT LINK
r.actual_native_PID=feature('getpid');r.actual_native_output_root=folder;r.native_output_observation_scope='owned_postcall_observation_not_optimizer_worker_finish_hashes';
% END V2 ACTUAL OUTPUT ROOT LINK
try
    r.own_recording_sources_before=file_list_identity(p.own_sources);
    [r.selected_source_before,r.selected_which_paths_before]=selected_identity(p.selected_original_sources);
    r.original_bank_metadata_before=file_list_identity(p.original_bank_metadata);
    r.input_before=file_list_identity(p.original_inputs);
    r.own_runtime_before=runtime_identity();
    write_receipt(fullfile(folder,'owned-native-before.json'),r);
    % ORIGINAL SCIENTIFIC ENTRY; EXACTLY ONE INVOCATION, SAME THREE ARGUMENTS.
    r.scientific_entry_call_count=1;
    r.original_returned_summary=run_full_ma_figure_v2(p.original_job_folder,folder,p.original_config_path);
catch exception
    r.exception=exception_record(exception);
end
% Attempt every evidence capture separately even after an original failure.
try,r.own_recording_sources_after=file_list_identity(p.own_sources);catch exception,r.evidence_exceptions{end+1}=struct('stage','own_recording_sources_after','exception',exception_record(exception));end
try,[r.selected_source_after,r.selected_which_paths_after]=selected_identity(p.selected_original_sources);catch exception,r.evidence_exceptions{end+1}=struct('stage','selected_source_after','exception',exception_record(exception));end
try,r.original_bank_metadata_after=file_list_identity(p.original_bank_metadata);catch exception,r.evidence_exceptions{end+1}=struct('stage','original_metadata_after','exception',exception_record(exception));end
try,r.input_after=file_list_identity(p.original_inputs);catch exception,r.evidence_exceptions{end+1}=struct('stage','all900_input_after','exception',exception_record(exception));end
try,r.own_runtime_after=runtime_identity();catch exception,r.evidence_exceptions{end+1}=struct('stage','own_runtime_after','exception',exception_record(exception));end
% BEGIN V2 ACTUAL SUMMARY START OUTPUT LINK
try,r.actual_native_full_summary_sha256=file_sha(fullfile(folder,'full_summary.json'));catch exception,r.evidence_exceptions{end+1}=struct('stage','actual_full_summary_output_hash','exception',exception_record(exception));end
try,r.actual_native_start_identity_sha256=file_sha(fullfile(folder,'execution-start-identity.json'));catch exception,r.evidence_exceptions{end+1}=struct('stage','actual_start_identity_output_hash','exception',exception_record(exception));end
% END V2 ACTUAL SUMMARY START OUTPUT LINK
observations=struct([]);
for index=1:900
    item=p.original_inputs(index);[~,stem]=fileparts(item.filename);rawPath=fullfile(folder,[stem,'-matlab.json']);
    record=struct('filename',item.filename,'case_index',item.case_index,'realization',item.realization,...
        'input_fingerprint',item.input_fingerprint,'raw_path',rawPath,'raw_exists',isfile(rawPath),...
        'saved_schema_and_declared_gates_passed',false,'independent_physical_or_KKT_verified',false,'exception',[]);
    try
        assert(isfile(rawPath),'Expected original raw missing.');record.raw_sha256=file_sha(rawPath);raw=jsondecode(fileread(rawPath));
        record.saved_metadata_status='original_raw';if isfield(raw,'status'),record.saved_metadata_status=raw.status;end
        record.recorded_original_failure=[];if isfield(raw,'error'),record.recorded_original_failure=struct('message',raw.error);if isfield(raw,'stack'),record.recorded_original_failure.stack=raw.stack;end;end
        record.saved_schema=observe_raw(raw,item,p);record.saved_schema_and_declared_gates_passed=record.saved_schema.all_recorded_data_gates_passed;
    catch exception
        record.exception=exception_record(exception);
    end
    % Uniform fields keep every missing/malformed/capped slot, not survivors.
    if ~isfield(record,'raw_sha256'),record.raw_sha256='';end
    if ~isfield(record,'saved_metadata_status'),record.saved_metadata_status='missing_or_unreadable';end
    if ~isfield(record,'recorded_original_failure'),record.recorded_original_failure=[];end
    if ~isfield(record,'saved_schema'),record.saved_schema=struct();end
    if isempty(observations),observations=record;else,observations(end+1)=record;end %#ok<AGROW>
end
r.raw_observations=observations;r.actual_expected_jobs=900;r.actual_raw_slots_observed=numel(observations);
r.actual_saved_schema_gate_count=sum([observations.saved_schema_and_declared_gates_passed]);
r.all900_actual_saved_schema_and_declared_gate_observations_passed=numel(observations)==900&&all([observations.saved_schema_and_declared_gates_passed]);
% Preserve the actual partial/failure state before the final source gates.
write_receipt(fullfile(folder,'owned-native-partial-observation.json'),r);
r.source_and_input_interval_unchanged=isfield(r,'selected_source_before')&&isfield(r,'selected_source_after')&&isequal(r.selected_source_before,r.selected_source_after)...
    &&isfield(r,'input_before')&&isfield(r,'input_after')&&isequal(r.input_before,r.input_after)&&isfield(r,'original_bank_metadata_before')&&isfield(r,'original_bank_metadata_after')&&isequal(r.original_bank_metadata_before,r.original_bank_metadata_after)...
    &&isfield(r,'own_recording_sources_before')&&isfield(r,'own_recording_sources_after')&&isequal(r.own_recording_sources_before,r.own_recording_sources_after);
r.own_runtime_interval_unchanged=isfield(r,'own_runtime_before')&&isfield(r,'own_runtime_after')&&isequal(r.own_runtime_before,r.own_runtime_after);
r.record_only_binding_evidence_complete=r.scientific_entry_call_count==1&&isempty(r.exception)&&isempty(r.evidence_exceptions)...
    &&r.source_and_input_interval_unchanged&&r.own_runtime_interval_unchanged&&r.all900_actual_saved_schema_and_declared_gate_observations_passed;
write_receipt(fullfile(folder,'owned-native-final-observation.json'),r);receipt=r;
assert(r.record_only_binding_evidence_complete,'Actual native/raw/source failure retained; no complete900 promotion.');
end

function result=observe_raw(raw,item,p)
result=struct('all_recorded_data_gates_passed',false,'histories',struct(),'families',struct());
assert(isfield(raw,'history')&&isfield(raw,'metrics')&&strcmp(raw.input_fingerprint,item.input_fingerprint),'Original raw/input identity missing.');
meta=raw.job_metadata;assert(meta.N==6&&meta.M==5&&meta.kappa==6&&meta.A==2&&meta.figure==6&&meta.realization==item.realization,'Original Figure6 metadata changed.');
assert(meta.point==9+3*item.case_index,'Original power point label changed.');
assert(raw.checks.full_N==6&&raw.checks.full_M==5&&raw.checks.nlos_samples==1000,'Original full shape changed.');
for mode={'mrt','zf'}
    name=mode{1};hist=raw.history.(name);obj=hist.objective(:);assert(numel(obj)>=2&&all(isfinite(obj)),'Complete finite original objective history required.');
    count=numel(obj);assert(isequal(size(hist.positions),[count,6,2])&&numel(hist.coordinate_updates)==6*(count-1),'Original ordered history sizes changed.');
    assert(hist.converged&&strcmp(hist.termination,'fractional_increase'),'Original configured-cap/false stop retained.');
    fraction=diff(obj)./abs(obj(1:end-1));assert(all(isfinite(fraction))&&fraction(end)<5e-5&&all(fraction(1:end-1)>=5e-5),'Original first full-sweep fractional stop gate not met.');
    assert(count-1<=p.AO_unreported_cap,'Source original configured budget exceeded.');
    maximumGapRatio=0;maximumPrimalRatio=0;
    for k=1:numel(hist.coordinate_updates)
        u=hist.coordinate_updates(k);assert(u.sweep==floor((k-1)/6)&&u.antenna==mod(k-1,6),'Original coordinate order changed.');
        c=u.certificate;vals=[c.global_objective_gap_upper_bound,c.global_objective_gap_tolerance,c.maximum_normalized_constraint_violation,c.normalized_constraint_tolerance];
        assert(u.original_subproblem_unchanged&&c.original_subproblem_unchanged&&c.certified_without_conic_solver_status&&all(isfinite(vals))&&all(vals>=0),'Recorded original certificate missing.');
        assert(vals(1)<=vals(2)&&vals(3)<=vals(4),'Recorded original certificate gate false.');
        if vals(2)>0,maximumGapRatio=max(maximumGapRatio,vals(1)/vals(2));end
        if vals(4)>0,maximumPrimalRatio=max(maximumPrimalRatio,vals(3)/vals(4));end
    end
    terminal=reshape(hist.positions(end,:,:),6,2);assert(isequal(terminal,raw.metrics.([name,'_positions']))&&isequal(terminal,raw.metrics.([name,'_realized_positions'])),'Own terminal state mismatch.');
    result.histories.(name)=struct('sweeps',count-1,'coordinate_count',numel(hist.coordinate_updates),'terminal_fraction',fraction(end),...
        'declared_global_full_sweep_first_stop_interpretation_verified_as_saved_data',true,'configured_original_AO_cap',p.AO_unreported_cap,...
        'maximum_recorded_concavity_gap_ratio',maximumGapRatio,'maximum_recorded_constraint_ratio',maximumPrimalRatio,'independent_coordinate_rederivation',false);
end
names={'MA_MRT','MA_ZF','FPA_MRT','FPA_ZF','FPA_OPT'};assert(isequal(sort(fieldnames(raw.metrics.schemes)),sort(names(:))),'Exact five original families required.');
for k=1:5
    name=names{k};family=raw.metrics.schemes.(name);rates=family.sample_sum_rates(:);
    assert(numel(rates)==1000&&all(isfinite(rates))&&all(rates>=0)&&isfinite(family.mean_sum_rate),'All1000 saved rates required.');
    assert(abs(mean(rates)-family.mean_sum_rate)<=1e-6,'Original stored-mean arithmetic gate false.');
    counter=[];if startsWith(name,'FPA'),assert(isfield(family,'nonconverged_samples')&&family.nonconverged_samples==0,'Original FPA cap/false counter retained.');counter=family.nonconverged_samples;end
    result.families.(name)=struct('saved_sample_count',1000,'saved_mean_sum_rate',family.mean_sum_rate,'recorded_nonconverged_samples',counter,'independent_physical_recompute',false);
end
result.all_recorded_data_gates_passed=true;
end

function [sources,resolved]=selected_identity(rows)
sources=struct([]);resolved=struct();
for k=1:numel(rows)
    row=rows(k);actual=which(row.name);assert(strcmpi(canonical(actual),canonical(row.path)),'Selected original function shadowed.');
    digest=file_sha(actual);assert(strcmp(digest,row.sha256),'Original selected source changed.');
    current=struct('key',row.key,'name',row.name,'path',actual,'sha256',digest);if isempty(sources),sources=current;else,sources(end+1)=current;end %#ok<AGROW>
    resolved.(row.name)=actual;
end
end
function records=file_list_identity(rows)
records=struct([]);
for k=1:numel(rows)
    row=rows(k);digest=file_sha(row.path);assert(strcmp(digest,row.sha256),'Original input/metadata source changed.');
    key=row.path;if isfield(row,'key'),key=row.key;elseif isfield(row,'filename'),key=row.filename;end
    current=struct('key',key,'path',row.path,'sha256',digest);if isempty(records),records=current;else,records(end+1)=current;end %#ok<AGROW>
end
end
function result=runtime_identity()
executable=fullfile(matlabroot,'bin','win64','MATLAB.exe');assert(isfile(executable),'Actual native executable unavailable.');
result=struct('matlab_executable_path',executable,'matlab_executable_sha256',file_sha(executable),...
    'matlab_version',version,'blas_version',version('-blas'),'lapack_version',version('-lapack'),...
    'complete_transitive_runtime_binary_dependency_hashes',false);
end
function result=exception_record(exception)
causes=cell(size(exception.cause));for k=1:numel(exception.cause),causes{k}=exception_record(exception.cause{k});end
result=struct('identifier',exception.identifier,'message',exception.message,'stack',{exception.stack},'causes',{causes},...
    'extended_report',getReport(exception,'extended','hyperlinks','off'));
end
function text=canonical(path)
text=char(java.io.File(path).getCanonicalPath());
end
function digest=file_sha(path)
fid=fopen(path,'rb');assert(fid>=0,'Cannot read evidence file.');cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
h=java.security.MessageDigest.getInstance('SHA-256');while ~feof(fid),h.update(fread(fid,1048576,'*uint8'));end
raw=typecast(h.digest(),'uint8');digest=lower(reshape(dec2hex(raw,2).',1,[]));
end
function write_receipt(path,value)
assert(~isfile(path),'Immutable NEW record target already exists.');fid=fopen(path,'w');assert(fid>=0,'Cannot save actual observer evidence.');cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(value));
end
