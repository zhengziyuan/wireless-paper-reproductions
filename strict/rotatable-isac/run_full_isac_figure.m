function summary=run_full_isac_figure(jobFolder,outputFolder,configPath)
% Full shared random inputs, independently evaluated by MATLAB paper algorithms.
if ~isfolder(outputFolder),mkdir(outputFolder);end
if nargin<3,configPath=fullfile(fileparts(jobFolder),'run_config.json');end
files=dir(fullfile(jobFolder,'case-*-mc-*.json'));
[manifest,coverage]=is_validate_bank(jobFolder,configPath,files);successful=false(size(coverage));
for index=1:numel(files)
    [~,name]=fileparts(files(index).name);output=fullfile(outputFolder,[name,'-matlab.json']);jobPath=fullfile(files(index).folder,files(index).name);expected=is_resume_fingerprint(configPath,jobPath);
    entry=manifest.files(strcmp({manifest.files.filename},files(index).name));
    if ~is_resume_complete(output,expected)
        try,result=run_strict_rotatable_isac('',jobPath,configPath);scene=jsondecode(fileread(jobPath));result.case_metadata=scene.case_metadata;
        catch exception,result=struct('paper_id','rotatable-isac','mode','full_scenario','status','failed','error',exception.message,'input_fingerprint',expected);end
        fid=fopen(output,'w');fprintf(fid,'%s\n',jsonencode(result));fclose(fid);
    end
    successful(entry.case_index+1,entry.realization+1)=is_resume_complete(output,expected);
end
summary=struct('paper_id','rotatable-isac','input_bank_complete',all(coverage(:)),'expected_jobs',manifest.expected_jobs,...
    'successful_jobs',sum(successful(:)),'per_case_all_success',all(successful,2)','overall_full_success',all(coverage(:))&&all(successful(:)),'executed',true);
fid=fopen(fullfile(outputFolder,'full_summary.json'),'w');fprintf(fid,'%s\n',jsonencode(summary));fclose(fid);
end

function [manifest,coverage]=is_validate_bank(jobFolder,configPath,files)
path=fullfile(fileparts(jobFolder),'manifest.json');if ~isfile(path),error('Complete shared-input manifest required; existing files alone do not establish a full run.');end
manifest=jsondecode(fileread(path));plan=jsondecode(fileread(fullfile(fileparts(jobFolder),'plan.json')));
if ~manifest.input_bank_complete||manifest.realizations_per_case~=100||manifest.case_count~=numel(plan.cases)||manifest.expected_jobs~=manifest.case_count*100||numel(files)~=manifest.expected_jobs||numel(manifest.files)~=manifest.expected_jobs,error('Full 100-channel per-case coverage is incomplete.');end
if ~strcmp(is_config_digest(configPath),manifest.config_sha256),error('Full configuration does not match input-bank manifest.');end
coverage=false(manifest.case_count,100);
for index=1:numel(manifest.files)
    entry=manifest.files(index);a=entry.case_index+1;b=entry.realization+1;
    if a<1||a>manifest.case_count||b<1||b>100||coverage(a,b),error('Duplicate or out-of-range case/realization in manifest.');end
    expectedName=sprintf('case-%03d-mc-%03d.json',a-1,b-1);path=fullfile(jobFolder,entry.filename);
    if ~strcmp(entry.filename,expectedName)||~isfile(path)||~strcmp(is_resume_fingerprint(configPath,path),entry.input_fingerprint),error('Shared input missing or fingerprint mismatch.');end
    scene=jsondecode(fileread(path));if scene.case_metadata.realization~=b-1,error('Input realization metadata mismatch.');end
    coverage(a,b)=true;
end
if ~all(coverage(:)),error('Full channel coverage is incomplete.');end
end

function value=is_config_digest(path)
fid=fopen(path,'rb');bytes=fread(fid,Inf,'*uint8');fclose(fid);digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(bytes);raw=typecast(digest.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end

function complete=is_resume_complete(path,expected)
complete=false;if ~isfile(path),return;end
try
    result=jsondecode(fileread(path));if ~isfield(result,'input_fingerprint')||~strcmp(result.input_fingerprint,expected)||~isfield(result,'checks')||numel(result.checks)~=6,return;end
    if ~isfield(result,'implementation_fingerprint')||~strcmp(result.implementation_fingerprint,strict_isac_implementation_fingerprint()),return;end
    for s=1:6
        if iscell(result.checks),item=result.checks{s};else,item=result.checks(s);end
        if ~isfield(item,'status')||~strcmp(item.status,'executed')||~item.converged||~isfield(item,'inner_all_converged')||~item.inner_all_converged||~isfield(item,'full_converged')||~item.full_converged||~item.power_feasible||~item.rotation_feasible||item.unit_modulus_error>1e-10,return;end
        if iscell(result.history),history=result.history{s};else,history=result.history(s);end
        if ~isfield(history,'inner_all_converged')||~history.inner_all_converged||~isfield(history,'full_converged')||~history.full_converged||~isfield(history,'blocks')||isempty(history.blocks),return;end
        for index=1:numel(history.blocks)
            if iscell(history.blocks),block=history.blocks{index};else,block=history.blocks(index);end
            if ~is_inner_complete(block.W,'W')||~is_inner_complete(block.RIS,'RIS')||~is_inner_complete(block.rotation,'rotation'),return;end
        end
        if iscell(result.metrics),metric=result.metrics{s};else,metric=result.metrics(s);end
        if ~all(isfinite([metric.utility,metric.rate,metric.nmse])),return;end
    end
    complete=true;
catch,complete=false;end
end

function complete=is_inner_complete(item,kind)
complete=false;
if ~isfield(item,'converged')||~item.converged||~isfield(item,'capped_unconverged')||item.capped_unconverged||~isfield(item,'termination_reason'),return;end
reason=item.termination_reason;
if strcmp(kind,'RIS')&&isfield(item,'applicable')&&~item.applicable
    complete=strcmp(reason,'not_applicable_no_RIS')&&item.iterations==0;return;
end
if ~isfield(item,'iterations')||~isfield(item,'iteration_budget')||item.iterations<=0||item.iterations>item.iteration_budget,return;end
switch kind
    case 'W'
        if strcmp(reason,'relative_objective_tolerance'),complete=is_measured_stop(item,'relative_objective_improvement','relative_tolerance',true);
        elseif strcmp(reason,'relative_step_tolerance'),complete=is_measured_stop(item,'relative_step','relative_tolerance',true);end
    case 'RIS'
        complete=strcmp(reason,'gradient_tolerance')&&is_measured_stop(item,'last_checked_normalized_gradient_norm','gradient_tolerance',false);
    case 'rotation'
        if strcmp(reason,'projected_gradient_tolerance'),complete=is_measured_stop(item,'last_checked_projected_gradient_norm','gradient_tolerance',false);
        elseif strcmp(reason,'relative_step_tolerance'),complete=is_measured_stop(item,'relative_step','relative_tolerance',false);end
end
end

function complete=is_measured_stop(item,field,tolerance,strict)
complete=false;if ~isfield(item,field)||~isfield(item,tolerance),return;end
value=item.(field);tol=item.(tolerance);if ~isscalar(value)||~isscalar(tol)||~isfinite(value)||~isfinite(tol),return;end
if strict,complete=value<tol;else,complete=value<=tol;end
end

function value=is_resume_fingerprint(configPath,jobPath)
digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(uint8('strict-v1'));digest.update(uint8(0));
fid=fopen(configPath,'rb');bytes=fread(fid,Inf,'*uint8');fclose(fid);digest.update(bytes);digest.update(uint8(0));
fid=fopen(jobPath,'rb');bytes=fread(fid,Inf,'*uint8');fclose(fid);digest.update(bytes);raw=typecast(digest.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end
