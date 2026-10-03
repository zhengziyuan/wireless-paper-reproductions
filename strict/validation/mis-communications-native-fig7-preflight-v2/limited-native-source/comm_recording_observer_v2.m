function status=comm_recording_observer_v2(action,data)
% WORK evidence-only observer. Never consumes RNG or calls numerical science.
persistent context
if nargin<2,data=struct();end
action=char(action);
if strcmp(action,'configure')
    assert(~isfolder(data.record_folder),'Fresh record folder required.');
    mkdir(data.record_folder);
    context=struct();context.folder=data.record_folder;context.mode=data.mode;
    context.active=[];context.completed=zeros(1,2);context.stages=zeros(1,2);
    context.solver_passes=zeros(1,2);context.io_errors={};context.records={};
    context.source_identity=data.source_identity;context.started=tic;
    status=snapshot(context);return;
end
if isempty(context)
    status=struct('observer_configured',false,'evidence_complete',false);return;
end
try
    switch action
        case 'initial'
            assert(any(data.seed_offset==[0,500000]),'This recorder is scoped to one Fig7 point.');
            if data.seed_offset==0,index=1;scheme='MIS';else,index=2;scheme='SMS';end
            draws=data.model.number_of_targets*size(data.state.X,2)+numel(data.state.phi.real)+numel(data.state.theta.real);
            before=park_miller_jump(data.settings.initialization.seed+data.seed_offset,draws*(data.start-1));
            after=park_miller_jump(before,draws);
            assert(after==data.random_state_after,'Recorded original RNG endpoint disagrees.');
            active=struct();active.scheme=scheme;active.index=index;active.start=data.start;
            active.initial=data;active.initial.random_state_before=before;active.initial.random_draw_count=draws;
            active.initial.scheme=scheme;active.initial.continuation_initial_mu=data.settings.initial_mu_values(mod(data.start-1,numel(data.settings.initial_mu_values))+1);
            active.continuation_stages={};active.initial_io_saved=false;
            schemeFolder=fullfile(context.folder,scheme);if ~isfolder(schemeFolder),mkdir(schemeFolder);end
            active.stem=sprintf('start-%06d',data.start);
            active.initial_path=fullfile(schemeFolder,[active.stem,'-initial.json']);
            context.active=active;
            write_fresh_json(active.initial_path,active.initial);
            context.active.initial_io_saved=true;
        case 'continuation-stage'
            assert(~isempty(context.active),'Missing initial observation.');
            data.stage_index=numel(context.active.continuation_stages);
            context.active.continuation_stages{end+1}=data;
        case 'final'
            assert(~isempty(context.active),'Missing initial observation.');
            active=context.active;stageCount=numel(active.continuation_stages);
            assert(stageCount==numel(data.history),'Every actual stage endpoint required.');
            mus=zeros(1,stageCount);stops=cell(1,stageCount);
            for j=1:stageCount
                stage=active.continuation_stages{j};historical=data.history{j};
                assert(stage.stage_index==j-1&&stage.mu==historical.mu);
                assert(isequaln(stage.inner,historical.inner)&&isequaln(stage.stop,historical.stop));
                mus(j)=stage.mu;stops{j}=stage.stop;
            end
            assert(stageCount>0&&isequaln(active.continuation_stages{end}.state,data.state));
            payload=struct();payload.scope='every_original_mu_endpoint_not_all_inner_states';
            payload.initial=active.initial;payload.continuation_stages=active.continuation_stages;
            payload.final_state=data.state;payload.full_history=data.history;
            payload.metrics=data.metrics;payload.solver_status=data.solver_status;
            payload.original_numerical_solver_unchanged=true;
            matrixPath=fullfile(context.folder,active.scheme,[active.stem,'-full.mat']);
            assert(~isfile(matrixPath),'No existing start evidence may be overwritten.');
            save(matrixPath,'payload','-v7');
            rec=struct();rec.scheme=active.scheme;rec.start=active.start;
            rec.seed_offset=active.initial.seed_offset;rec.random_state_before=active.initial.random_state_before;
            rec.random_state_after=active.initial.random_state_after;rec.random_draw_count=active.initial.random_draw_count;
            rec.mu_values=mus;rec.actual_continuation_endpoint_count=stageCount;rec.continuation_stops=stops;
            rec.final_solver_status=data.solver_status;rec.final_metrics=data.metrics;
            rec.full_payload_file=[active.stem,'-full.mat'];rec.full_payload_sha256=file_sha(matrixPath);
            rec.initial_file=[active.stem,'-initial.json'];rec.initial_file_sha256=file_sha(active.initial_path);
            rec.all_actual_inner_histories_raw_PR_and_mu_endpoint_states_saved=true;
            rec.every_inner_iterate_state_saved=false;rec.independent_physical_KKT_audit_passed=false;
            recordPath=fullfile(context.folder,active.scheme,[active.stem,'-record.json']);
            write_fresh_json(recordPath,rec);
            context.completed(active.index)=context.completed(active.index)+1;
            context.stages(active.index)=context.stages(active.index)+stageCount;
            context.solver_passes(active.index)=context.solver_passes(active.index)+double(data.solver_status.convergence_verified);
            binding=struct('scheme',active.scheme,'start',active.start,'record_sha256',file_sha(recordPath),...
                'initial_sha256',rec.initial_file_sha256,'full_payload_sha256',rec.full_payload_sha256,'stages',stageCount);
            context.records{end+1}=binding;context.active=[];
            progress=snapshot(context);progress.last_completed_start=binding;
            progressPath=fullfile(context.folder,sprintf('progress-%06d.json',sum(context.completed)));
            write_fresh_json(progressPath,progress);
        case 'fatal-save'
            receipt=snapshot(context);receipt.actual_original_solver_exception=data;
            receipt.available_original_endpoint_observations=context.active;
            write_fresh_json(fullfile(context.folder,'fatal-original-solver-exception.json'),receipt);
        case 'finalize'
            receipt=snapshot(context);receipt.all_record_bindings=context.records;
            write_fresh_json(fullfile(context.folder,'recording-completion.json'),receipt);
        otherwise
            error('Unknown evidence-only observer action.');
    end
catch problem
    % Recording failure does not change an original solver state or stop flag.
    item=struct('action',action,'identifier',problem.identifier,'message',problem.message);
    if ~isempty(context.active),item.scheme=context.active.scheme;item.start=context.active.start;end
    context.io_errors{end+1}=item;
    warning('comm_recording:auxiliaryFailure','Evidence-only observation failed: %s',problem.message);
end
status=snapshot(context);
if ~isempty(context.active),status.active_start=context.active.start;status.active_scheme=context.active.scheme;end
end

function out=snapshot(context)
out=struct();out.scope='WORK_native_original_Fig7_all_start_recording_not_independent_physical_certification';
out.mode=context.mode;out.completed_start_records=context.completed;out.actual_mu_endpoint_records=context.stages;
out.original_solver_diagnostic_passes=context.solver_passes;out.auxiliary_recording_failures=context.io_errors;
out.all_full12000_start_payloads_saved=isequal(context.completed,[6000,6000])&&isempty(context.io_errors);
out.all_full12000_source_solver_gates_passed=out.all_full12000_start_payloads_saved&&isequal(context.solver_passes,[6000,6000]);
out.all230400_endpoint_count_matched=sum(context.stages)==230400&&out.all_full12000_start_payloads_saved;
out.all_full_recording_gates_passed=out.all_full12000_source_solver_gates_passed&&out.all230400_endpoint_count_matched;
out.source_identity=context.source_identity;out.elapsed_seconds=toc(context.started);
out.independent_physical_KKT_audit_passed=false;out.original_figure_reproduction_certified=false;
end

function state=park_miller_jump(seed,count)
prime=uint64(2147483647);a=uint64(16807);p=uint64(1);n=uint64(count);
while n>0
    if bitand(n,uint64(1)),p=mod(p*a,prime);end
    a=mod(a*a,prime);n=bitshift(n,-1);
end
state=double(mod(uint64(seed)*p,prime));
end

function write_fresh_json(path,value)
assert(~isfile(path),'Immutable evidence filename already exists.');
temporary=[path,'.writing'];assert(~isfile(temporary),'Stale immutable writing file retained.');
fid=fopen(temporary,'w','n','UTF-8');assert(fid>=0);cleaner=onCleanup(@()fclose(fid));
fprintf(fid,'%s\n',jsonencode(value));clear cleaner
for attempt=1:40
    [ok,~]=movefile(temporary,path);
    if ok,return;end
    pause(.1);
end
error('comm_recording:immutableIO','Immutable evidence publication failed.');
end

function value=file_sha(path)
fid=fopen(path,'rb');assert(fid>=0);cleaner=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');
d=java.security.MessageDigest.getInstance('SHA-256');d.update(bytes);
value=lower(reshape(dec2hex(typecast(d.digest(),'uint8'),2).',1,[]));
end
