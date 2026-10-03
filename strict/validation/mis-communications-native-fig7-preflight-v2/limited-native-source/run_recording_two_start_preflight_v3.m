function receipt=run_recording_two_start_preflight_v3(outputFolder)
% Two fixed full-budget starts; only recording changes versus byte-copy science.
base=fileparts(mfilename('fullpath'));science=fullfile(base,'scientific-source');
assert(~isfolder(outputFolder),'Fresh preflight evidence folder required.');mkdir(outputFolder);
plan=jsondecode(fileread(fullfile(base,'two-start-shape-preflight-plan-v3.json')));
before=verify_source_files(science,plan);
addpath(science,'-begin');
assert(strcmp(which('mis_communications_strict_engine_recording_v2'),fullfile(science,'mis_communications_strict_engine_recording_v2.m')));
assert(strcmp(which('mis_communications_native_reference_v2'),fullfile(science,'mis_communications_native_reference_v2.m')));
write_fresh(fullfile(outputFolder,'before-source-runtime-identity.json'),struct('source_files',{before},'matlab_version',version,'computer',computer));
settings=fullfile(science,'settings.json');schemes={'MIS','SMS'};items=cell(1,2);itemIndex=0;
fields={'scope','scheme','start','original_number_of_starts','original_rcg_budget','initial_state',...
    'random_state_after_initialize','seed_offset','actual_steering_matrix','actual_indices_one_based','actual_model_dimensions','configuration','settings','final_state','history','metrics','solver_status'};
for schemeIndex=1:2
    for start=1
        itemIndex=itemIndex+1;scheme=schemes{schemeIndex};stem=sprintf('%s-start-%06d',scheme,start);
        name=sprintf('recording-preflight:fig7:%s:%d',scheme,start);
        recordFolder=fullfile(outputFolder,[stem,'-records']);
        recordedPath=fullfile(outputFolder,[stem,'-recorded.json']);referencePath=fullfile(outputFolder,[stem,'-reference.json']);
        recorded=run_mis_communications_recording_v2(recordedPath,name,settings,recordFolder);
        reference=mis_communications_native_reference_v2(referencePath,name,settings);
        checks=struct();for j=1:numel(fields),f=fields{j};checks.(f)=exact_bitwise_equal(recorded.(f),reference.(f));end
        status=recorded.native_all_start_recording_status;expected=zeros(1,2);expected(schemeIndex)=1;
        checks.actual_one_record_present=isequal(status.completed_start_records,expected)&&isempty(status.auxiliary_recording_failures);
        checks.not_a_full12000_claim=~status.all_full12000_start_payloads_saved&&~status.all_full_recording_gates_passed;
        matrixPath=fullfile(recordFolder,scheme,sprintf('start-%06d-full.mat',start));
        loaded=load(matrixPath,'payload');payload=loaded.payload;
        checks.saved_actual_steering_matrix_bitwise=exact_bitwise_equal(payload.initial.actual_steering_matrix,reference.actual_steering_matrix);
        checks.saved_actual_indices_bitwise=exact_bitwise_equal(payload.initial.actual_indices_one_based,reference.actual_indices_one_based);
        checks.saved_actual_dimensions_bitwise=exact_bitwise_equal(payload.initial.actual_model_dimensions,reference.actual_model_dimensions);
        checks.saved_initial_state_bitwise=exact_bitwise_equal(payload.initial.state,reference.initial_state);
        checks.saved_final_state_bitwise=exact_bitwise_equal(payload.final_state,reference.final_state);
        checks.saved_history_bitwise=exact_bitwise_equal(payload.full_history,reference.history);
        checks.saved_metrics_bitwise=exact_bitwise_equal(payload.metrics,reference.metrics);
        checks.saved_stop_bitwise=exact_bitwise_equal(payload.solver_status,reference.solver_status);
        checks.every_actual_mu_endpoint_present=numel(payload.continuation_stages)==numel(reference.history);
        stageChecks=true;for j=1:numel(reference.history)
            actual=payload.continuation_stages{j};old=reference.history{j};
            stageChecks=stageChecks&&actual.stage_index==j-1&&actual.mu==old.mu&&...
                exact_bitwise_equal(actual.inner,old.inner)&&exact_bitwise_equal(actual.stop,old.stop);
        end
        checks.every_saved_stage_history_stop_matches_original=stageChecks;
        checks.last_actual_mu_endpoint_is_final_state=exact_bitwise_equal(payload.continuation_stages{end}.state,reference.final_state);
        checks.saved_model_geometry_exact=numel(payload.initial.model.ms1)==2&&isequal(payload.initial.model.ms1(:),[1;2])&&payload.initial.model.number_of_targets==4;
        item=struct();item.scheme=scheme;item.start=start;item.checks=checks;
        item.exact_recording_reference_and_saved_payload_pass=all(cellfun(@(f)checks.(f),fieldnames(checks)));
        item.source_solver_stop=reference.solver_status;item.actual_mu_endpoint_count=numel(payload.continuation_stages);
        item.recorded_output_sha256=file_sha(recordedPath);item.reference_output_sha256=file_sha(referencePath);
        item.full_payload_sha256=file_sha(matrixPath);item.recording_completion_sha256=file_sha(fullfile(recordFolder,'recording-completion.json'));
        item.full12000_run=false;item.independent_physical_KKT_certification=false;
        items{itemIndex}=item;write_fresh(fullfile(outputFolder,[stem,'-paired-preflight.json']),item);
    end
end
after=verify_source_files(science,plan);
receipt=struct();receipt.scope='actual_two_fixed_original_full_budget_native_recording_reference_preflight_not_full12000';
receipt.cases=items;receipt.source_before_after_unchanged=isequaln(before,after);
receipt.all_two_recording_reference_and_saved_payload_exact=all(cellfun(@(s)s.exact_recording_reference_and_saved_payload_pass,items));
receipt.all_two_original_solver_gates=all(cellfun(@(s)s.source_solver_stop.convergence_verified,items));
receipt.stopping_threshold_or_direction_changed=false;receipt.complete_full12000_figure_executed=false;
receipt.independent_physical_KKT_certification=false;receipt.source_files=after;
receipt.matlab_version=version;receipt.computer=computer;
write_fresh(fullfile(outputFolder,'actual-two-start-recording-reference-preflight.json'),receipt);
assert(receipt.source_before_after_unchanged&&receipt.all_two_recording_reference_and_saved_payload_exact,...
    'Recording/reference or evidence mismatch retained in actual receipts.');
end

function out=verify_source_files(base,plan)
entries=plan.source_files;if iscell(entries),entries=[entries{:}];end
out=cell(1,numel(entries));
for j=1:numel(entries)
    entry=entries(j);path=fullfile(base,strrep(entry.relative_path,'/',filesep));
    actual=file_sha(path);assert(strcmp(actual,entry.sha256),'Source drift retained; do not execute.');
    out{j}=struct('relative_path',entry.relative_path,'sha256',actual);
end
end

function tf=exact_bitwise_equal(a,b)
tf=strcmp(class(a),class(b))&&isequal(size(a),size(b));if ~tf,return;end
if isnumeric(a)
    if isreal(a)~=isreal(b),tf=false;return;end
    if isempty(a),tf=true;return;end
    tf=isequal(typecast(real(a(:)),'uint8'),typecast(real(b(:)),'uint8'));
    if ~isreal(a),tf=tf&&isequal(typecast(imag(a(:)),'uint8'),typecast(imag(b(:)),'uint8'));end
elseif isstruct(a)
    names=fieldnames(a);tf=isequal(names,fieldnames(b));if ~tf,return;end
    for k=1:numel(a),for j=1:numel(names),if ~exact_bitwise_equal(a(k).(names{j}),b(k).(names{j})),tf=false;return;end,end,end
elseif iscell(a)
    for k=1:numel(a),if ~exact_bitwise_equal(a{k},b{k}),tf=false;return;end,end
else
    tf=isequaln(a,b);
end
end

function write_fresh(path,value)
assert(~isfile(path));fid=fopen(path,'w','n','UTF-8');assert(fid>=0);
cleaner=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(value));
end

function value=file_sha(path)
fid=fopen(path,'rb');assert(fid>=0);cleaner=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');
d=java.security.MessageDigest.getInstance('SHA-256');d.update(bytes);
value=lower(reshape(dec2hex(typecast(d.digest(),'uint8'),2).',1,[]));
end
