function receipt=run_cooperative_v4_native_checked_work(configPath,outputPath,bindingOutputPath)
% WORK recording-only actual native wrapper; no scientific algorithm changes.
statePath=[outputPath,'.states.mat'];
assert(~exist(outputPath,'file')&&~exist(bindingOutputPath,'file')&&~exist(statePath,'file'),'Fresh actual outputs required');
config=jsondecode(fileread(configPath));assert(config.tuned_not_reported.monte_carlo_realizations==1000);
assert(config.tuned_not_reported.gradient_tolerance==1e-6);
expectedNames={'AP-NoRIS','AP-AO','MR-S-NoRIS','MR-S-PA','MR-S-TS','MR-TTS-NoRIS','MR-TTS-PA','MR-TTS-TS'};
scientificBefore=strict_satcom_v3_hashes(configPath);
selectedRunner=which('run_strict_cooperative_v4_recording_work');assert(~isempty(selectedRunner));
recordingSources={selectedRunner,which('strict_satcom_algorithms_v4_recording_work'),which('strict_satcom_recording_v4_work')};
expectedRecording={'49fada43f6db98188944c6bff4b47076761080442a1f2fbca60c7ea06ef500f7','7219d3fb9e92dc46d70ab6026ca2c6698f7a55dde7ebafe757534b417496cd7f','dd3776b251cc935f5e04a2ddaE94b4ad783954d18770e8e376a9c1070b4db9ab'};
for i=1:numel(recordingSources),assert(strcmpi(hash_file(recordingSources{i}),expectedRecording{i}),'Frozen recording source changed');end
global cvx___
shim=cvx___.solvers.list(cvx___.solvers.selected);callback=functions(shim.solve);
backendRoot=fileparts(shim.fullpath);files=dir(fullfile(backendRoot,'**','*.m'));
binaries=dir(fullfile(backendRoot,'**','*.mexw64'));
runtimePaths={[mfilename('fullpath'),'.m'],configPath,shim.fullpath,callback.file};
runtimePaths=[runtimePaths,recordingSources];
for i=1:numel(files),runtimePaths{end+1}=fullfile(files(i).folder,files(i).name);end %#ok<AGROW>
for i=1:numel(binaries),runtimePaths{end+1}=fullfile(binaries(i).folder,binaries(i).name);end %#ok<AGROW>
before=hashes(runtimePaths);began=tic;
result=run_strict_cooperative_v4_recording_work(configPath,outputPath,'base');
after=hashes(runtimePaths);scientificAfter=strict_satcom_v3_hashes(configPath);
sourcePass=isequal(before,after)&&isequal(scientificBefore,scientificAfter)&&result.source_unchanged_during_run;
assert(sourcePass&&result.recording_only_protocol.adapter_source_binding.adapter_source_unchanged_during_run,'Native source/runtime/configuration interval changed');
assert(numel(result.results)==1,'Exactly one full original scene required');
entry=result.results{1};chainNames={};
if isfield(entry,'schemes'),chainNames={entry.schemes.scheme};end
namesPass=isequal(chainNames,expectedNames);
assert(result.configuration.reported.M==config.reported.M&&exist(statePath,'file')==2);
stateBinding=result.recording_only_protocol.state_file_sha256;
assert(numel(stateBinding)==1&&strcmp(hash_file(statePath),stateBinding(1).sha256),'Actual native state SHA binding mismatch');
receipt=struct('scope','WORK_actual_recording_only_native_full_original_scene_eight_chains_NOT183_or_historical_figures', ...
    'full_scene_parameters',config.reported,'monte_carlo_moment_draw_count',1000, ...
    'actual_scheme_names',{chainNames},'all_eight_original_scheme_names_pass',namesPass, ...
    'actual_all_original_implementation_gates_pass',result.overall_implemented_scope_success&&namesPass, ...
    'source_and_selected_backend_interval_pass',sourcePass, ...
    'actual_selected_backend_name',shim.name,'actual_selected_backend_version',shim.version, ...
    'actual_backend_callback_Mfile_sha256',hash_file(callback.file), ...
    'selected_backend_MAT_and_MEX_inventory_before',{before},'selected_backend_MAT_and_MEX_inventory_after',{after}, ...
    'scientific_source_and_configuration_before',scientificBefore,'scientific_source_and_configuration_after',scientificAfter, ...
    'recording_sources_expected_sha256',{expectedRecording}, ...
    'actual_full_result_sha256',hash_file(outputPath),'actual_recorded_states_sha256',hash_file(statePath), ...
    'actual_seconds',toc(began),'recording_only_no_scientific_return_change',true, ...
    'independent_saved_final_matrix_gradient_QT_and_draw_audit_complete',false, ...
    'complete_all_runtime_binary_inventory_verified',false,'full_reproduction_pass',false);
fid=fopen(bindingOutputPath,'w');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(receipt));
fprintf('Actual native recording fullscene eight chains pass=%d source interval=%d\n',receipt.actual_all_original_implementation_gates_pass,sourcePass);
end
function out=hashes(paths)
out=cell(size(paths));for i=1:numel(paths)
    [~,name,extension]=fileparts(paths{i});out{i}=struct('filename',[name,extension],'sha256',hash_file(paths{i}));
end
end
function digestValue=hash_file(path)
fid=fopen(path,'rb');assert(fid>=0,'Cannot hash exact resolved source: %s',path);bytes=fread(fid,inf,'*uint8');fclose(fid);
digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(bytes);
digestValue=lower(reshape(dec2hex(typecast(digest.digest(),'uint8'),2).',1,[]));
end
