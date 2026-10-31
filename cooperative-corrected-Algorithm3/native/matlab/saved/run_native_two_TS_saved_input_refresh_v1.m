function result=run_native_two_TS_saved_input_refresh_v1(jobPath,mode)
% New transport only. Every numerical kernel remains frozen in the dispatcher.
assert(nargin==2&&any(strcmp(mode,{'execute','io-only'})),'Explicit execution or IO-only mode required');
job=jsondecode(fileread(jobPath));root=fileparts(mfilename('fullpath'));
assert(strcmp(job.schema,'native-original183-saved-input-two-TS-job-v1'),'Unexpected job schema');
assert(job.ordinal>=0&&job.ordinal<183&&job.ordinal==fix(job.ordinal),'Original ordinal required');
assert(strcmp(sha256(job.old_container.path),job.old_container.sha256),'Old native container identity');
assert(strcmp(sha256(job.old_states.path),job.old_states.sha256),'Old native recording identity');
assert(strcmp(sha256(job.original_configuration.path),job.original_configuration.sha256),'Original configuration identity');
before=check_pins(job.source_pins);
assert(~isfile(fullfile(job.output_directory,'execution-start.json')),'Preserve prior attempt');
assert(isfolder(job.output_directory),'Prepare isolated output/preferences first');
assert(startsWith(normal(prefdir),[normal(job.output_directory),'/']),'Process-local E preference directory required');
assert(startsWith(normal(tempdir),[normal(job.output_directory),'/']),'Process-local E temporary directory required');
saved=load(job.old_states.path,'recording');oldRecording=saved.recording;
old=jsondecode(fileread(job.old_container.path));oldPoint=one(old.results);
names={'AP-NoRIS','AP-AO','MR-S-NoRIS','MR-S-PA','MR-S-TS','MR-TTS-NoRIS','MR-TTS-PA','MR-TTS-TS'};
oldFinal=as_cells(oldRecording.final_states);schemes=oldPoint.schemes;
if iscell(schemes),schemes=[schemes{:}];end
assert(numel(oldFinal)==8&&numel(schemes)==8,'All eight old results/states required');
for k=1:8,assert(strcmp(oldFinal{k}.scheme,names{k})&&strcmp(schemes(k).scheme,names{k}),'Original complete order');end
input=oldRecording.input;settings=input.configuration.tuned_not_reported;
assert(isequaln(old.configuration.reported,job.expected_reported_scene),'Exact source-index scenario slot');
assert(isequaln(input.configuration.reported,old.configuration.reported),'Recording/result scenario identity');
assert(settings.qt_max_iterations==200&&settings.ao_max_iterations==200&&settings.rmo_max_iterations==100000,'Keep QT/AO/RMO budgets');
assert(settings.relative_tolerance==1e-4&&settings.gradient_tolerance==1e-6,'Keep original stops');
assert(settings.smoothing_initial==1&&settings.smoothing_final==0.001&&settings.smoothing_max_repeats==50,'Keep complete smoothing');
assert(settings.monte_carlo_realizations==1000&&oldPoint.monte_carlo.count==1000,'Explicit complete old MC reuse');
J=input.configuration.reported.J;U=input.configuration.reported.U;N=input.configuration.reported.N;M=input.configuration.reported.M;
assert(isequal(size(input.data.d_mean),[J,U,N])&&isequal(size(input.data.r_mean),[U,M]),'Actual native dimensions');
assert(numel(fieldnames(input.data))==11,'All eleven actual input arrays');
phi=oldFinal{3}.phi;pS=oldFinal{3}.p;pT=oldFinal{6}.p;
assert(exact_numeric(phi,oldFinal{6}.phi)&&isequal(size(phi),[U,M]),'Exact original common NoRIS initial phase');
assert(isequal(size(pS),[J,U])&&isequal(size(pT),[J,U]),'Exact native NoRIS power dimensions');
assert(all(isfinite(phi(:)))&&all(isfinite(pS(:)))&&all(isfinite(pT(:))),'Finite saved initialization');
assert(all(pS(:)>=0)&&all(pT(:)>=0),'Native nonnegative saved powers');
initialization=struct('old_input_copied_without_scenario_generation',true,'both_native_NoRIS_powers_read_directly',true,...
    'source_index_scenario_exact',true,'initial_phase_shape',size(phi),'initial_phase_class',class(phi),...
    'P_S_shape',size(pS),'P_TTS_shape',size(pT),'configured_original_moments',1000,...
    'new_scenario_calls',0,'new_sampler_or_RNG_calls',0,'new_unaffected_optimizer_calls',0);
if strcmp(mode,'io-only')
    result=struct('scope','NON_SCIENTIFIC_SAVED_INPUT_IO_ONLY','initialization',initialization,...
        'actual_TS_optimizer_calls',0,'scientific_PASS',false,'job_SHA256',sha256(jobPath));
    save(fullfile(job.output_directory,'non-scientific-saved-input-IO-snapshot.mat'),'input','phi','pS','pT','result','-v7');
    codecReceipt=strict_satcom_complex_json_transport_selftest_v1();result.codec_selftest=codecReceipt;
    export_result(result,fullfile(job.output_directory,'NON_SCIENTIFIC_INPUT_IO_ONLY.json'));
    assert(isequal(before,check_pins(job.source_pins)),'Read-only IO source pins');return;
end
assert(strcmp(job.disposition,'new-two-TS-required'),'A088 exact reuse is a separate non-optimizer transport');
assert(strcmp(which('strict_satcom_algorithms_only_saved_TS_v1'),fullfile(root,'strict_satcom_algorithms_only_saved_TS_v1.m')),'Exact isolated dispatch');
runtimeHashes=strict_satcom_v3_hashes(job.original_configuration.path);
start=struct('scope','Exactly two corrected complete TS chains; six saved chains and configured1000 moments explicit reuse',...
    'ordinal',job.ordinal,'source_before',{before},'actual_runtime_scientific_hashes',runtimeHashes,'job_SHA256',sha256(jobPath),...
    'old_container',job.old_container,'old_recording',job.old_states,'initialization',initialization,...
    'unaffected_schemes',{{names{[1,2,3,4,6,7]}}},'new_optimizer_calls_allowed_only',{{'MR-S-TS','MR-TTS-TS'}},...
    'original_controls',settings,'prefdir',prefdir,'tempdir',tempdir,'full183_or_reference_or_paper_PASS',false);
write_json_copy(start,fullfile(job.output_directory,'execution-start.json'));
newTapes=cell(1,2);newSchemes=cell(1,2);completed={};failure=[];started=tic;
for t=1:2
    tts=t==2;prefix='MR-S';p0=pS;index=5;if tts,prefix='MR-TTS';p0=pT;index=8;end
    strict_satcom_capture('begin',input);
    statePath=fullfile(job.output_directory,['actual-new-',prefix,'-TS-only-recording.mat']);
    try
        [newScheme,dispatchMetadata]=strict_satcom_algorithms_only_saved_TS_v1('one-saved-TS',input.data,settings,input.power_limit,input.interference_limit,phi,p0,tts);
        captureInfo=strict_satcom_capture('save',statePath);loaded=load(statePath,'recording');newTapes{t}=loaded.recording;
        assert(captureInfo.final_scheme_states==1&&strcmp(newTapes{t}.final_states{1}.scheme,names{index}),'Exactly one new final TS');
        assert(dispatchMetadata.actual_completed_TS_entries==1,'One full corrected TS entry');
        newSchemes{t}=newScheme;schemes(index)=newScheme;oldFinal{index}=newTapes{t}.final_states{1};completed{end+1}=names{index}; %#ok<AGROW>
    catch exception
        failure=exception;
        partial=fullfile(job.output_directory,['partial-new-',prefix,'-TS-only-recording.mat']);
        if ~isfile(statePath),strict_satcom_capture('save',partial);end
        break;
    end
end
if ~isempty(failure)
    result=struct('scope','FAILED_OR_PARTIAL_CORRECTED_TWO_TS_ATTEMPT','ordinal',job.ordinal,...
        'completed_new_TS',{completed},'error_identifier',failure.identifier,'error',failure.message,...
        'original_results_retained_under_source_paths',true,'source_before',{before},'source_after',{check_pins(job.source_pins)},...
        'new_MC_draws',0,'scientific_PASS',false,'full183_or_reference_or_paper_PASS',false);
    export_result(result,fullfile(job.output_directory,'partial-failed-two-TS-result.json'));rethrow(failure);
end
assert(numel(completed)==2,'Both complete original-budget TS functions must return');
recording=struct('schema',1,'input',input,'final_states',{oldFinal},'phase_endpoints',{{}},'QT_candidates',{{}});
preambleIndices=zeros(1,2);newCounts=zeros(2,2);
for t=1:2
    tape=newTapes{t};phases=as_cells(tape.phase_endpoints);qt=as_cells(tape.QT_candidates);
    assert(~isempty(phases)&&~isempty(qt),'All actual new endpoint/QT observations required');
    for k=1:numel(phases),assert(~phases{k}.vector_objective,'No AP phase optimization');end
    attempts=as_cells(newSchemes{t}.status.final_algorithm3_preamble.P7_info.solver_diagnostics.same_original_QT_numerical_attempts);
    returned=sum(cellfun(@(x)isfield(x,'solver_status'),attempts));assert(returned>0&&returned<=numel(qt),'Actual returned preamble attempts');
    pre=qt{returned};preamble=newSchemes{t}.status.final_algorithm3_preamble;
    assert(strcmp(pre.kind,'mr_qt_update')&&exact_numeric(pre.input{1},preamble.input_p_INIT)&&exact_numeric(pre.candidate,preamble.updated_p_INIT),'Accepted actual preP7 recording binding');
    preambleIndices(t)=numel(recording.QT_candidates)+returned-1;
    recording.phase_endpoints=[recording.phase_endpoints,phases];recording.QT_candidates=[recording.QT_candidates,qt];
    newCounts(t,:)=[numel(phases),numel(qt)];
end
statesPath=fullfile(job.output_directory,'actual-two-TS-recording.mat');assert(~isfile(statesPath),'Preserve prior composite MAT');save(statesPath,'recording','-v7');
violations=[];converged=true;primal=true;bound=true;
for k=1:8
    e=schemes(k).evaluation;violations=[violations;e.satellite_power(:)-input.power_limit(:);e.gt_interference(:)-input.interference_limit(:)]; %#ok<AGROW>
    st=schemes(k).status;converged=converged&&st.converged;if isfield(st,'phase_source_converged'),converged=converged&&st.phase_source_converged;end
    primal=primal&&st.numerical.solver_primal_pass;bound=bound&&st.numerical.qt_bound_pass;
end
point=oldPoint;point.schemes=schemes;point.constraint_pass=max(violations)<settings.solver_objective_tolerance;point.convergence_pass=converged;point.solver_primal_pass=primal;point.qt_bound_pass=bound;
checks=struct('constraint_pass',point.constraint_pass,'convergence_pass',converged,'solver_primal_pass',primal,'qt_bound_pass',bound);
point.valid_figure_point=all(structfun(@logical,checks));point.status='corrected_two_TS_new_six_saved_chains_and_MC1000_reused';
stateInfo=struct('filename','actual-two-TS-recording.mat','sha256',sha256(statesPath),'final_scheme_states',8,...
    'phase_endpoints',numel(recording.phase_endpoints),'QT_candidates',numel(recording.QT_candidates));
result=struct('paper_id','cooperative-satcom','scope','Corrected two complete TS chains plus six explicit saved chains and old configured1000 moments',...
    'language','matlab','configuration',old.configuration,'results',point,'checks',checks,...
    'overall_implemented_scope_success',point.valid_figure_point,'source_unchanged_during_run',true,'state_recording',stateInfo,...
    'exact_reuse_provenance',struct('original_result_container',job.old_container.path,'original_result_SHA256',job.old_container.sha256,...
      'original_state_recording',job.old_states,'unaffected_schemes',{{names{[1,2,3,4,6,7]}}},...
      'configured1000_moment_result_copied_without_new_draws',true,'original_own_state_QT_report',job.old_physics_reference,...
      'original_phase_reference',job.old_phase_reference,'original_MC1000_proof',job.old_MC1000_proof),...
    'actual_new_Algorithm3_preamble_QT_indices',preambleIndices,'actual_new_phase_QT_counts_by_TS',newCounts,...
    'actual_completed_TS_entries',2,'actual_unaffected_optimizer_calls',0,'actual_new_MC_draws',0,...
    'source_before',{before},'source_after',{check_pins(job.source_pins)},'actual_runtime_scientific_hashes',runtimeHashes,...
    'elapsed_seconds',toc(started),'source_corrected_chain_independent_review_pending',true,'full183_or_reference_or_paper_PASS',false);
assert(isequal(result.source_before,result.source_after)&&isequal(runtimeHashes,strict_satcom_v3_hashes(job.original_configuration.path)),'Actual science and transport source interval must close');
export_result(result,fullfile(job.output_directory,'case-matlab-corrected-two-TS-recorded.json'));
assert(result.overall_implemented_scope_success,'Failed/capped/unverified actual outcomes retained');
end

function export_result(result,path)
assert(~isfile(path)&&~isfile([path,'.full-result-before-JSON.mat']),'Preserve prior outputs');
save([path,'.full-result-before-JSON.mat'],'result','-v7');
write_json_copy(result,path);
end
function write_json_copy(result,path)
assert(~isfile(path),'Exclusive new JSON only');copy=strict_satcom_complex_json_transport_v1('encode',result);
fid=fopen(path,'w');assert(fid>=0);clean=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(copy));
end
function out=check_pins(pins)
out=pins;for k=1:numel(pins),assert(strcmp(sha256(pins(k).path),pins(k).sha256),['Source changed: ',pins(k).path]);end
end
function out=as_cells(value)
if iscell(value),out=reshape(value,1,[]);else,out=num2cell(value);end
end
function out=one(value)
if iscell(value),assert(numel(value)==1);out=value{1};else,assert(numel(value)==1);out=value;end
end
function out=exact_numeric(a,b)
out=isnumeric(a)&&isnumeric(b)&&strcmp(class(a),class(b))&&isequal(size(a),size(b));
if out,out=isequal(typecast(real(a(:)),'uint8'),typecast(real(b(:)),'uint8'))&&isequal(typecast(imag(a(:)),'uint8'),typecast(imag(b(:)),'uint8'));end
end
function out=normal(path)
out=strrep(path,'\','/');while endsWith(out,'/'),out=out(1:end-1);end
end
function value=sha256(path)
fid=fopen(path,'rb');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(bytes);raw=typecast(digest.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end
