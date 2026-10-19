function result=assemble_native_A088_saved_two_TS_reuse_v1(jobPath)
% Pure saved-data transport: no scientific provider, optimizer or RNG calls.
job=jsondecode(fileread(jobPath));assert(job.ordinal==88,'Exact original088 only');
assert(strcmp(job.disposition,'reuse-existing-corrected-native-A-exact-inputs'),'Exact A reuse admission');
reuse=job.existing_corrected_A_reuse;
assert(strcmp(sha256(job.old_states.path),job.old_states.sha256)&&strcmp(sha256(job.old_container.path),job.old_container.sha256),'Old native source binding');
assert(strcmp(sha256(reuse.corrected_A_recording.path),reuse.corrected_A_recording.sha256),'Actual corrected A recording binding');
assert(strcmp(sha256(reuse.corrected_A_raw_full_result.path),reuse.corrected_A_raw_full_result.sha256),'Actual corrected A raw complex result');
assert(strcmp(sha256(reuse.corrected_A_ownstate_mathematics_proof.path),reuse.corrected_A_ownstate_mathematics_proof.sha256),'Actual A independent mathematics binding');
assert(~isfile(fullfile(job.output_directory,'case-matlab-corrected-two-TS-recorded.json')),'Exclusive new reuse result');
oldMAT=load(job.old_states.path,'recording');aMAT=load(reuse.corrected_A_recording.path,'recording');rawA=load(reuse.corrected_A_raw_full_result.path,'result');
old=jsondecode(fileread(job.old_container.path));aResult=rawA.result;
assert(exact_value(oldMAT.recording.input,aMAT.recording.input),'All actual data/configuration/settings/limits exact including numeric bits');
oldStates=as_cells(oldMAT.recording.final_states);aStates=as_cells(aMAT.recording.final_states);
for k=[3,6],assert(exact_value(oldStates{k}.p,aStates{k}.p)&&exact_value(oldStates{k}.phi,aStates{k}.phi),'Both own native NoRIS p0 and phase exact');end
oldPoint=one(old.results);aPoint=one(aResult.results);oldSchemes=oldPoint.schemes;aSchemes=aPoint.schemes;
if iscell(oldSchemes),oldSchemes=[oldSchemes{:}];end
if iscell(aSchemes),aSchemes=[aSchemes{:}];end
assert(numel(oldSchemes)==8&&numel(aSchemes)==8,'Complete original/common eight scheme order');
allQT=as_cells(aMAT.recording.QT_candidates);allPhases=as_cells(aMAT.recording.phase_endpoints);
offsets=zeros(1,9);
for k=1:8
    records=as_cells(aSchemes(k).status.solver_diagnostics);returned=0;
    for r=1:numel(records)
        attempts=as_cells(records{r}.solver_diagnostics.same_original_QT_numerical_attempts);
        returned=returned+sum(cellfun(@(x)isfield(x,'solver_status'),attempts));
    end
    offsets(k+1)=offsets(k)+returned;
end
assert(offsets(end)==numel(allQT),'All actual A QT observations partitioned, including returned precision attempts');
recording=struct('schema',1,'input',oldMAT.recording.input,'final_states',{oldStates},'phase_endpoints',{{}},'QT_candidates',{{}});
preambleIndices=zeros(1,2);newCounts=zeros(2,2);
for t=1:2
    tts=t==2;k=5;if tts,k=8;end
    oldSchemes(k)=aSchemes(k);recording.final_states{k}=aStates{k};
    qt=allQT((offsets(k)+1):offsets(k+1));phases={};
    for n=1:numel(allPhases)
        p=allPhases{n};if ~p.vector_objective&&p.context.tts==tts,phases{end+1}=p;end %#ok<AGROW>
    end
    assert(~isempty(phases)&&~isempty(qt),'All actual saved A affected observations');
    preamble=aSchemes(k).status.final_algorithm3_preamble;
    attempts=as_cells(preamble.P7_info.solver_diagnostics.same_original_QT_numerical_attempts);
    returned=sum(cellfun(@(x)isfield(x,'solver_status'),attempts));assert(returned>0);
    accepted=qt{returned};assert(exact_value(accepted.input{1},preamble.input_p_INIT)&&exact_value(accepted.candidate,preamble.updated_p_INIT),'Actual saved preamble operands');
    preambleIndices(t)=numel(recording.QT_candidates)+returned-1;
    recording.phase_endpoints=[recording.phase_endpoints,phases];recording.QT_candidates=[recording.QT_candidates,qt];
    newCounts(t,:)=[numel(phases),numel(qt)];
end
path=fullfile(job.output_directory,'actual-two-TS-recording.mat');assert(~isfile(path));save(path,'recording','-v7');
point=oldPoint;point.schemes=oldSchemes;
checks=struct('constraint_pass',true,'convergence_pass',true,'solver_primal_pass',true,'qt_bound_pass',true);
for k=1:8
    e=oldSchemes(k).evaluation;s=oldSchemes(k).status;
    checks.constraint_pass=checks.constraint_pass&&all(e.satellite_power(:)-recording.input.power_limit(:)<1e-5)&&all(e.gt_interference(:)-recording.input.interference_limit(:)<1e-5);
    checks.convergence_pass=checks.convergence_pass&&s.converged;if isfield(s,'phase_source_converged'),checks.convergence_pass=checks.convergence_pass&&s.phase_source_converged;end
    checks.solver_primal_pass=checks.solver_primal_pass&&s.numerical.solver_primal_pass;checks.qt_bound_pass=checks.qt_bound_pass&&s.numerical.qt_bound_pass;
end
fields=fieldnames(checks);for k=1:numel(fields),point.(fields{k})=checks.(fields{k});end
point.valid_figure_point=all(structfun(@logical,checks));point.status='exact_saved_native_A088_two_TS_and_six_original_chains_reused';
result=struct('paper_id','cooperative-satcom','language','matlab','configuration',old.configuration,...
    'scope','All eight states are saved-data reuse: six original native088 and two corrected nativeA with exact actual inputs and initialization',...
    'results',point,'checks',checks,'overall_implemented_scope_success',point.valid_figure_point,...
    'source_unchanged_during_run',true,'state_recording',struct('filename','actual-two-TS-recording.mat','sha256',sha256(path),...
      'final_scheme_states',8,'phase_endpoints',numel(recording.phase_endpoints),'QT_candidates',numel(recording.QT_candidates)),...
    'exact_reuse_provenance',struct('original_result_container',job.old_container,'original_state_recording',job.old_states,...
      'unaffected_schemes',{{'AP-NoRIS','AP-AO','MR-S-NoRIS','MR-S-PA','MR-TTS-NoRIS','MR-TTS-PA'}},...
      'configured1000_moment_result_copied_without_new_draws',true,'original_own_state_QT_report',job.old_physics_reference,...
      'original_phase_reference',job.old_phase_reference,'original_MC1000_proof',job.old_MC1000_proof,...
      'corrected_TS_source',reuse,'all11data_limits_controls_both_NoRIS_p0_and_phi_exact',true),...
    'actual_new_Algorithm3_preamble_QT_indices',preambleIndices,'saved_corrected_A_phase_QT_counts_by_TS',newCounts,...
    'actual_new_TS_optimizer_calls',0,'actual_new_MC_draws',0,'original_corrected_A_host_exit_code',1,...
    'original_corrected_A_host_terminal0_claimed',false,'source_corrected_chain_independent_exact_transport_readback_pending',true,...
    'full183_or_reference_or_paper_PASS',false);
out=fullfile(job.output_directory,'case-matlab-corrected-two-TS-recorded.json');assert(~isfile(out)&&~isfile([out,'.full-result-before-JSON.mat']));
save([out,'.full-result-before-JSON.mat'],'result','-v7');copy=strict_satcom_complex_json_transport_v1('encode',result);
fid=fopen(out,'w');assert(fid>=0);clean=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(copy));
end
function out=exact_value(a,b)
out=false;if ~strcmp(class(a),class(b))||~isequal(size(a),size(b)),return;end
if isnumeric(a),out=isequal(typecast(real(a(:)),'uint8'),typecast(real(b(:)),'uint8'))&&isequal(typecast(imag(a(:)),'uint8'),typecast(imag(b(:)),'uint8'));
elseif isstruct(a)
    if ~isequal(sort(fieldnames(a)),sort(fieldnames(b))),return;end
    fields=fieldnames(a);out=true;for n=1:numel(a),for k=1:numel(fields),out=out&&exact_value(a(n).(fields{k}),b(n).(fields{k}));end,end
elseif iscell(a),out=true;for n=1:numel(a),out=out&&exact_value(a{n},b{n});end
else,out=isequaln(a,b);end
end
function out=as_cells(value)
if iscell(value),out=reshape(value,1,[]);else,out=num2cell(value);end
end
function out=one(value)
if iscell(value),assert(numel(value)==1);out=value{1};else,assert(numel(value)==1);out=value;end
end
function value=sha256(path)
fid=fopen(path,'rb');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(bytes);raw=typecast(digest.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end
