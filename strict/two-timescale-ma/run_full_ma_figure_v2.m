function summary=run_full_ma_figure_v2(jobFolder,outputFolder,configPath)
% Independent versioned MATLAB full-bank entry. No original file is edited.
% All configured 100 geometries x 1000 NLoS and all five schemes are retained.
if nargin<3,configPath=fullfile(fileparts(jobFolder),'run_config.json');end
if ~isfolder(outputFolder),mkdir(outputFolder);end
files=dir(fullfile(jobFolder,'case-*-mc-*.json'));config=jsondecode(fileread(configPath));
assert(config.geometry_realizations==100&&config.nlos_realizations_per_geometry==1000,'This full-bank entry requires complete 100 x 1000 configured ensembles.');
[manifest,coverage]=validate_bank(jobFolder,configPath,files,config);
[initialFingerprint,initialIdentity]=strict_ma_full_v2_implementation_fingerprint(configPath);
successful=false(size(coverage));attempted=false(size(coverage));numericCompleted=false(size(coverage));sourceAvailable=true;
write_json(fullfile(outputFolder,'execution-start-identity.json'),struct('implementation_fingerprint',initialFingerprint,'source_identity',initialIdentity,'config_sha256',file_sha(configPath),'input_manifest_sha256',file_sha(fullfile(fileparts(jobFolder),'manifest.json')),'existing_old_bank_results_reused',false));
for index=1:numel(files)
    assert(strcmp(strict_ma_full_v2_implementation_fingerprint(configPath),initialFingerprint),'Sources changed since this bank started; do not mix versions.');
    [~,name]=fileparts(files(index).name);out=fullfile(outputFolder,[name,'-matlab.json']);jobPath=fullfile(files(index).folder,files(index).name);job=jsondecode(fileread(jobPath));expected=input_fingerprint(configPath,jobPath);
    entry=manifest.files(strcmp({manifest.files.filename},files(index).name));a=entry.case_index+1;b=entry.realization+1;
    if ~implemented_complete(out,expected,initialFingerprint,job,config)
        % Keep every earlier raw failure/stale version rather than overwriting it.
        if isfile(out)
            archive=fullfile(outputFolder,'retained-attempts');if ~isfolder(archive),mkdir(archive);end
            [~,nonce]=fileparts(tempname(archive));copyfile(out,fullfile(archive,[name,'-',nonce,'.json']));
        end
        try
            run_strict_two_timescale_ma_full_v2(out,jobPath,configPath);
        catch exception
            failure=struct('paper_id','two-timescale-ma','mode','full_scenario','status','failed','error',exception.message,'error_identifier',exception.identifier,...
                'stack',{exception.stack},'failure_class','exception_during_full_scenario','numerical_case_completed',false,'job',files(index).name,'input_fingerprint',expected,...
                'implementation_fingerprint',initialFingerprint,'matlab_source_version','MATLAB-full-v2-history-storage');
            write_json(out,failure);
        end
    end
    attempted(a,b)=true;successful(a,b)=implemented_complete(out,expected,initialFingerprint,job,config);
    if isfile(out)
        raw=jsondecode(fileread(out));numericCompleted(a,b)=isfield(raw,'metrics')&&isfield(raw,'history');
    end
    sourceAvailable=sourceAvailable&&(~(isfield(job,'correlated')&&job.correlated)||ismember(job.figure,[13,15]));
    write_json(fullfile(outputFolder,'execution-progress.json'),struct('expected_jobs',manifest.expected_jobs,'attempted',sum(attempted(:)),...
        'complete_numeric_raw_cases',sum(numericCompleted(:)),'passed_all_numeric_gates',sum(successful(:)),'failed_or_gate_incomplete',sum(attempted(:))-sum(successful(:)),...
        'all_jobs_attempted',all(attempted(:)),'all_numeric_gates_passed',all(successful(:)),'raw_file_count_is_not_numerical_case_count',true,...
        'current_job',name,'implementation_fingerprint',initialFingerprint,'input_bank_complete',all(coverage(:))));
end
[finalFingerprint,finalIdentity]=strict_ma_full_v2_implementation_fingerprint(configPath);assert(strcmp(initialFingerprint,finalFingerprint),'Sources changed during bank execution.');
allNumeric=all(coverage(:))&&all(successful(:));blockers={};status='not_run_or_incomplete';
if ~sourceAvailable,status='printed_correlated_ZF_formula_requires_separately_labeled_corrected_source_adapter';blockers={'Printed correlated-ZF Eq72/74/75 cannot be silently used; the separately labeled exact original-model integral adapter is required.'};
elseif allNumeric,status='full_scenarios_computed_historical_match_unverified';end
summary=struct('paper_id','two-timescale-ma','matlab_source_version','MATLAB-full-v2-history-storage','implementation_fingerprint',initialFingerprint,...
    'input_bank_complete',all(coverage(:)),'expected_jobs',manifest.expected_jobs,'attempted_jobs',sum(attempted(:)),'complete_numeric_raw_cases',sum(numericCompleted(:)),...
    'successful_jobs',sum(successful(:)),'per_case_all_success',all(successful,2)','implemented_scope_successful_jobs',sum(successful(:)),...
    'overall_implemented_scope_success',allNumeric,'all_scenario_numeric_gates_passed',allNumeric,'overall_full_success',allNumeric&&sourceAvailable,...
    'original_figure_complete',false,'original_curve_closeness_verified',false,'original_figure_status',status,'original_figure_blockers',{blockers},...
    'executed',true,'fresh_source_identity_before',initialIdentity,'fresh_source_identity_after',finalIdentity,'source_identity_unchanged',true,'raw_file_count_is_not_numerical_case_count',true);
write_json(fullfile(outputFolder,'full_summary.json'),summary);
end

function [manifest,coverage]=validate_bank(jobFolder,configPath,files,config)
manifestPath=fullfile(fileparts(jobFolder),'manifest.json');assert(isfile(manifestPath),'Complete exported shared-input manifest is required.');
manifest=jsondecode(fileread(manifestPath));plan=jsondecode(fileread(fullfile(fileparts(jobFolder),'plan.json')));R=config.geometry_realizations;
assert(manifest.input_bank_complete&&manifest.realizations_per_case==R&&manifest.nlos_per_geometry==1000&&manifest.case_count==numel(plan.cases)&&manifest.expected_jobs==manifest.case_count*R&&numel(files)==manifest.expected_jobs&&numel(manifest.files)==manifest.expected_jobs,'Full bank coverage is incomplete.');
assert(strcmp(file_sha(configPath),manifest.config_sha256),'Config does not match immutable exported manifest.');coverage=false(manifest.case_count,R);
for index=1:numel(manifest.files)
    entry=manifest.files(index);a=entry.case_index+1;b=entry.realization+1;
    assert(a>=1&&a<=manifest.case_count&&b>=1&&b<=R&&~coverage(a,b),'Duplicate/out-of-range exported job.');
    expectedName=sprintf('case-%03d-mc-%03d.json',a-1,b-1);path=fullfile(jobFolder,entry.filename);
    assert(strcmp(entry.filename,expectedName)&&isfile(path)&&strcmp(input_fingerprint(configPath,path),entry.input_fingerprint),'Shared input is missing or its bytes changed.');
    job=jsondecode(fileread(path));assert(job.realization==b-1&&size(job.nlos_re,1)==1000&&size(job.nlos_im,1)==1000,'Full sample count/realization mismatch.');coverage(a,b)=true;
end
assert(all(coverage(:)),'Full geometry coverage is incomplete.');
end

function complete=implemented_complete(path,expected,fingerprint,job,config)
complete=false;if ~isfile(path),return;end
try
    result=jsondecode(fileread(path));if ~isfield(result,'input_fingerprint')||~strcmp(result.input_fingerprint,expected)||~isfield(result,'checks')||~isfield(result,'implementation_fingerprint')||~strcmp(result.implementation_fingerprint,fingerprint),return;end
    flags={'mrt_converged','zf_converged','mrt_nominal_design_spacing_feasible','zf_nominal_design_spacing_feasible','mrt_nominal_design_box_feasible','zf_nominal_design_box_feasible','mrt_realized_positions_spacing_feasible','zf_realized_positions_spacing_feasible','mrt_realized_positions_box_feasible','zf_realized_positions_box_feasible'};
    for i=1:numel(flags),if ~isfield(result.checks,flags{i})||~result.checks.(flags{i}),return;end,end
    if result.checks.full_N~=job.N||result.checks.full_M~=job.M||result.checks.nlos_samples~=1000,return;end
    for algorithm={'mrt','zf'}
        hist=result.history.(algorithm{1});obj=hist.objective;
        if numel(obj)<2||~all(isfinite(obj))||any(diff(obj)<-config.verification_tolerance)||~hist.converged||~strcmp(hist.termination,'fractional_increase')||(obj(end)-obj(end-1))/abs(obj(end-1))>=config.fractional_increase_threshold,return;end
        if size(hist.positions,1)~=numel(obj)||numel(hist.coordinate_updates)~=(numel(obj)-1)*job.N,return;end
        if strcmp(config.matlab_convex_solver,'certified_exact_2d')
            updates=hist.coordinate_updates;
            for updateIndex=1:numel(updates)
                u=updates(updateIndex);if ~u.original_subproblem_unchanged||~isfield(u,'certificate'),return;end;c=u.certificate;
                vals=[c.global_objective_gap_upper_bound,c.global_objective_gap_tolerance,c.maximum_normalized_constraint_violation,c.normalized_constraint_tolerance];
                if any(~isfinite(vals))||any(vals<0)||~c.certified_without_conic_solver_status||c.global_objective_gap_upper_bound>c.global_objective_gap_tolerance||c.maximum_normalized_constraint_violation>c.normalized_constraint_tolerance,return;end
                if u.after<u.before-config.verification_tolerance||u.lower_bound_gap<-config.verification_tolerance||abs(u.surrogate-u.before-c.minorant_increment)>config.verification_tolerance||abs(u.after-u.surrogate-u.lower_bound_gap)>config.verification_tolerance,return;end
            end
        end
    end
    names={'MA_MRT','MA_ZF','FPA_MRT','FPA_ZF','FPA_OPT'};
    for i=1:numel(names)
        item=result.metrics.schemes.(names{i});if numel(item.sample_sum_rates)~=1000||~all(isfinite(item.sample_sum_rates))||abs(mean(item.sample_sum_rates)-item.mean_sum_rate)>config.verification_tolerance,return;end
        if isfield(item,'nonconverged_samples')&&item.nonconverged_samples~=0,return;end
    end
    if isfield(job,'correlated')&&job.correlated
        ext=result.metrics.correlated_extension;for name={'MA_MRT_MC','MA_ZF_MC'},if numel(ext.(name{1}).sample_sum_rates)~=1000||~all(isfinite(ext.(name{1}).sample_sum_rates)),return;end,end
    end
    mode='';if ismember(job.figure,[3,13,15]),mode='mrt';elseif ismember(job.figure,[4,14,16]),mode='zf';end
    if ~isempty(mode)
        hist=result.history.(mode);count=numel(hist.objective);if ~isfield(hist,'instantaneous_MC_mean')||numel(hist.instantaneous_MC_mean)~=count||~all(isfinite(hist.instantaneous_MC_mean)),return;end
        if isfield(job,'correlated')&&job.correlated
            names={'ZF_correlated_MC_history'};if strcmp(mode,'mrt'),names={'MRT_correlated_MC_history','MRT_Eq69_history'};end
            for i=1:numel(names),if ~isfield(ext,names{i})||numel(ext.(names{i}))~=count||~all(isfinite(ext.(names{i}))),return;end,end
        end
    end
    if isfield(job,'brute_force_D')&&(~result.metrics.brute_force.MRT.search.complete||~result.metrics.brute_force.ZF.search.complete),return;end
    complete=true;
catch,complete=false;end
end

function value=input_fingerprint(configPath,jobPath)
digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(uint8('strict-v1'));digest.update(uint8(0));digest.update(read_bytes(configPath));digest.update(uint8(0));digest.update(read_bytes(jobPath));raw=typecast(digest.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end
function value=file_sha(path)
digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(read_bytes(path));raw=typecast(digest.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end
function bytes=read_bytes(path)
fid=fopen(path,'rb');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8'); %#ok<NASGU>
end
function write_json(path,data)
folder=fileparts(path);tmp=[tempname(folder),'.json'];fid=fopen(tmp,'w');assert(fid>=0);fprintf(fid,'%s\n',jsonencode(data));fclose(fid);
lastMessage='';
for attempt=1:8
    [ok,message]=movefile(tmp,path,'f');if ok,return;end;lastMessage=message;pause(min(.1*2^(attempt-1),2));
end
error('Versioned executor output I/O retry exhausted (temporary raw file retained at %s): %s',tmp,lastMessage);
end
