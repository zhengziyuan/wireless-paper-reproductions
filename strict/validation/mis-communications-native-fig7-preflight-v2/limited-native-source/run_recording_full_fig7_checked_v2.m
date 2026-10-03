function receipt=run_recording_full_fig7_checked_v2(bankFolder)
% Outer source/runtime binding only. All 12000 starts are cold and unchanged.
base=fileparts(mfilename('fullpath'));science=fullfile(base,'scientific-source');
planPath=fullfile(base,'full12000-predeclared-plan-v2.json');plan=jsondecode(fileread(planPath));
assert(strcmp(file_sha(mfilename('fullpath')+".m"),plan.execution_wrapper_sha256),'Wrapper drift; preserve and version a new plan.');
assert(~isfolder(bankFolder),'Fresh full-bank directory required; no preflight result reuse or resume.');
before=source_identity(science,plan);mkdir(bankFolder);addpath(science,'-begin');
runtimeBefore=runtime_identity(science);start=struct();start.scope='actual_native_Fig7_full12000_execution_start_not_completion';
start.source_identity=before;start.runtime_identity=runtimeBefore;start.predeclared_plan_sha256=file_sha(planPath);
start.full_scientific_source_manifest_sha256=file_sha(fullfile(science,'recording-source-freeze.json'));
start.fresh_bank_no_old_results_reused=true;start.preflight_outputs_not_used_as_bank_results=true;
start.expected_start_counts=[6000,6000];start.expected_actual_mu_endpoints=230400;
write_fresh(fullfile(bankFolder,'execution-wrapper-start-identity.json'),start);
outputPath=fullfile(bankFolder,'native-full-fig7-result.json');recordFolder=fullfile(bankFolder,'all-start-records');started=tic;
try
    result=run_mis_communications_recording_v2(outputPath,'fig7',fullfile(science,'settings.json'),recordFolder);
catch problem
    failure=struct('scope','actual_execution_exception_not_inferred_numerical_failure',...
        'identifier',problem.identifier,'message',problem.message,'stack',problem.stack,'elapsed_seconds',toc(started));
    failure.source_identity_after=source_identity(science,plan);failure.runtime_identity_after=runtime_identity(science);
    write_fresh(fullfile(bankFolder,'execution-wrapper-exception.json'),failure);rethrow(problem);
end
after=source_identity(science,plan);runtimeAfter=runtime_identity(science);
point=as_cells(result.points);assert(numel(point)==1,'Frozen Fig7 is exactly one source point.');entry=point{1};
schemes={entry.result,entry.SMS};names={'MIS','SMS'};schemeChecks=cell(1,2);
for j=1:2
    scheme=schemes{j};summaries=as_cells(scheme.all_start_summaries);
    item=struct();item.scheme=names{j};item.completed_original_start_count=numel(summaries);
    item.full6000_start_budget_execution_complete=numel(summaries)==6000&&scheme.full_start_budget_execution_complete;
    item.implementation_digest_matches_actual_runtime=strcmp(scheme.implementation_digest,runtimeBefore.implementation_digest);
    item.all_actual_source_summary_solver_gates=all(cellfun(@(s)s.solver_status.convergence_verified,summaries));
    item.all_actual_source_summary_feasibility_gates=all(cellfun(@(s)s.feasible&&s.binary_eta_feasible,summaries));
    item.start_labels_exact=isequal(cellfun(@(s)s.start,summaries),1:6000);
    item.all_start_recording_evidence_complete=scheme.all_start_recording_evidence_complete;
    item.selected_best_gate_is_not_an_all_start_certificate=true;item.selected_best_convergence_verified=scheme.selected_best_convergence_verified;
    item.source_gate_not_independent_physical_KKT_certificate=true;schemeChecks{j}=item;
end
status=result.native_all_start_recording_status;
receipt=struct();receipt.scope='actual_native_Fig7_full12000_runtime_and_recording_identity_not_independent_physical_certification';
receipt.source_before_after_unchanged=isequaln(before,after);receipt.runtime_before_after_unchanged=isequaln(runtimeBefore,runtimeAfter);
receipt.scheme_checks=schemeChecks;receipt.actual_completed_start_counts=status.completed_start_records;
receipt.actual_mu_endpoint_counts=status.actual_mu_endpoint_records;receipt.auxiliary_recording_failures=status.auxiliary_recording_failures;
receipt.source_full12000_budget_executed=all(cellfun(@(s)s.full6000_start_budget_execution_complete&&s.start_labels_exact,schemeChecks));
receipt.actual_all_start_implementation_digests_match=all(cellfun(@(s)s.implementation_digest_matches_actual_runtime,schemeChecks));
receipt.full12000_recording_complete=status.all_full12000_start_payloads_saved&&status.all230400_endpoint_count_matched;
receipt.actual_full12000_source_stops_and_feasibility_pass=all(cellfun(@(s)s.all_actual_source_summary_solver_gates&&s.all_actual_source_summary_feasibility_gates,schemeChecks));
receipt.all_source_runtime_and_full_recording_gates_pass=receipt.source_before_after_unchanged&&receipt.runtime_before_after_unchanged&&...
    receipt.source_full12000_budget_executed&&receipt.actual_all_start_implementation_digests_match&&...
    receipt.full12000_recording_complete&&receipt.actual_full12000_source_stops_and_feasibility_pass;
receipt.independent_physical_KKT_certification=false;receipt.original_figure_closeness_verified=false;
receipt.every_inner_iterate_state_saved=false;receipt.source_identity_after=after;receipt.runtime_identity_after=runtimeAfter;
receipt.result_sha256=file_sha(outputPath);receipt.recording_completion_sha256=file_sha(fullfile(recordFolder,'recording-completion.json'));
receipt.execution_start_identity_sha256=file_sha(fullfile(bankFolder,'execution-wrapper-start-identity.json'));
receipt.predeclared_plan_sha256=file_sha(planPath);receipt.elapsed_seconds=toc(started);
write_fresh(fullfile(bankFolder,'execution-wrapper-completion-identity.json'),receipt);
% A completed bank with genuine source failures must retain its false flags.
assert(receipt.source_before_after_unchanged&&receipt.runtime_before_after_unchanged&&receipt.actual_all_start_implementation_digests_match,...
    'Source/runtime identity failure retained; no scientific certification.');
end

function out=source_identity(base,plan)
entries=plan.source_files;if iscell(entries),entries=[entries{:}];end
out=cell(1,numel(entries));for j=1:numel(entries)
    entry=entries(j);path=fullfile(base,strrep(entry.relative_path,'/',filesep));actual=file_sha(path);
    assert(strcmp(actual,entry.sha256),'Frozen science/settings/figures source drift.');
    out{j}=struct('relative_path',entry.relative_path,'sha256',actual);
end
end

function out=runtime_identity(base)
out=struct();out.matlab_version=version;out.computer=computer;
out.engine_which=which('mis_communications_strict_engine_recording_v2');out.observer_which=which('comm_recording_observer_v2');
out.entry_which=which('run_mis_communications_recording_v2');out.actual_max_num_comp_threads=maxNumCompThreads;
assert(strcmp(out.engine_which,fullfile(base,'mis_communications_strict_engine_recording_v2.m')));
assert(strcmp(out.observer_which,fullfile(base,'comm_recording_observer_v2.m')));
assert(strcmp(out.entry_which,fullfile(base,'run_mis_communications_recording_v2.m')));
assert(out.actual_max_num_comp_threads==1,'Run this resource-bounded native bank with one computational thread.');
files=[dir(fullfile(base,'*.py'));dir(fullfile(base,'*.m'));dir(fullfile(base,'source_map.json'))];[~,order]=sort({files.name});files=files(order);
md=java.security.MessageDigest.getInstance('SHA-256');
for j=1:numel(files)
    fid=fopen(fullfile(base,files(j).name),'rb');assert(fid>=0);bytes=fread(fid,Inf,'*uint8');fclose(fid);
    md.update(uint8(unicode2native([files(j).name,char(0)],'UTF-8')));md.update(bytes);
end
md.update(uint8(unicode2native([char(0),version,char(0),computer],'UTF-8')));
out.implementation_digest=lower(reshape(dec2hex(typecast(md.digest(),'uint8'),2).',1,[]));
end

function cells=as_cells(value)
if iscell(value),cells=value;elseif isempty(value),cells={};else,cells=arrayfun(@(s)s,value,'UniformOutput',false);end
cells=reshape(cells,1,[]);
end

function write_fresh(path,value)
assert(~isfile(path),'Never overwrite an actual attempt receipt.');temporary=[path,'.writing'];assert(~isfile(temporary));
fid=fopen(temporary,'w','n','UTF-8');assert(fid>=0);cleaner=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(value));clear cleaner
for attempt=1:40,[ok,~]=movefile(temporary,path);if ok,return;end,pause(.1);end
error('comm_recording:outerImmutableIO','Outer immutable receipt I/O failed; this is not a solver conclusion.');
end

function value=file_sha(path)
fid=fopen(path,'rb');assert(fid>=0);cleaner=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');
d=java.security.MessageDigest.getInstance('SHA-256');d.update(bytes);
value=lower(reshape(dec2hex(typecast(d.digest(),'uint8'),2).',1,[]));
end
