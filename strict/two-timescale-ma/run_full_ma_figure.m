function summary=run_full_ma_figure(jobFolder,outputFolder,configPath)
% Consume complete Python-exported random inputs, using independent MATLAB math.
if nargin<3,configPath=fullfile(fileparts(jobFolder),'run_config.json');end
if ~isfolder(outputFolder),mkdir(outputFolder);end
files=dir(fullfile(jobFolder,'case-*-mc-*.json'));
config=jsondecode(fileread(configPath));
[manifest,coverage]=ma_validate_bank(jobFolder,configPath,files,config);successful=false(size(coverage));implementedSuccessful=false(size(coverage));originalAvailable=true;
for index=1:numel(files)
    [~,name]=fileparts(files(index).name);out=fullfile(outputFolder,[name,'-matlab.json']);jobPath=fullfile(files(index).folder,files(index).name);job=jsondecode(fileread(jobPath));expected=ma_resume_fingerprint(configPath,jobPath);
    entry=manifest.files(strcmp({manifest.files.filename},files(index).name));
    if ~ma_resume_implemented_complete(out,expected,job,config)
        try,run_strict_two_timescale_ma(out,jobPath,configPath);
        catch exception
            result=struct('paper_id','two-timescale-ma','mode','full_scenario','status','failed','error',exception.message,'job',files(index).name,'input_fingerprint',expected);
            fid=fopen(out,'w');fprintf(fid,'%s\n',jsonencode(result));fclose(fid);
        end
    end
    implementedSuccessful(entry.case_index+1,entry.realization+1)=ma_resume_implemented_complete(out,expected,job,config);
    originalJobAvailable=~(isfield(job,'correlated')&&job.correlated)||(isfield(job,'figure')&&ismember(job.figure,[13,15]));originalAvailable=originalAvailable&&originalJobAvailable;
    successful(entry.case_index+1,entry.realization+1)=implementedSuccessful(entry.case_index+1,entry.realization+1)&&originalJobAvailable;
end
originalComplete=all(coverage(:))&&all(successful(:));originalStatus='not_run_or_incomplete';blockers={};
if ~originalAvailable,originalStatus='blocked_by_source_formulation';blockers={'Correlated-ZF Eq72/74/75 have unresolved dimensions and row-correlated Wishart assumptions. No replacement formula is used.'};
elseif originalComplete,originalStatus='complete';end
summary=struct('paper_id','two-timescale-ma','input_bank_complete',all(coverage(:)),'expected_jobs',manifest.expected_jobs,...
    'successful_jobs',sum(successful(:)),'per_case_all_success',all(successful,2)',...
    'implemented_scope_successful_jobs',sum(implementedSuccessful(:)),'per_case_implemented_scope_success',all(implementedSuccessful,2)',...
    'overall_implemented_scope_success',all(coverage(:))&&all(implementedSuccessful(:)),'overall_full_success',originalComplete,...
    'original_figure_complete',originalComplete,'original_curve_closeness_verified',false,'original_figure_status',originalStatus,'original_figure_blockers',{blockers},'executed',true);
fid=fopen(fullfile(outputFolder,'full_summary.json'),'w');fprintf(fid,'%s\n',jsonencode(summary));fclose(fid);
end

function [manifest,coverage]=ma_validate_bank(jobFolder,configPath,files,config)
path=fullfile(fileparts(jobFolder),'manifest.json');if ~isfile(path),error('Complete shared-input manifest required.');end
manifest=jsondecode(fileread(path));plan=jsondecode(fileread(fullfile(fileparts(jobFolder),'plan.json')));R=config.geometry_realizations;
if ~manifest.input_bank_complete||manifest.realizations_per_case~=R||manifest.nlos_per_geometry~=config.nlos_realizations_per_geometry||manifest.case_count~=numel(plan.cases)||manifest.expected_jobs~=manifest.case_count*R||numel(files)~=manifest.expected_jobs||numel(manifest.files)~=manifest.expected_jobs,error('Full per-case geometry coverage is incomplete.');end
if ~strcmp(ma_config_digest(configPath),manifest.config_sha256),error('Full configuration does not match input-bank manifest.');end
coverage=false(manifest.case_count,R);
for index=1:numel(manifest.files)
    entry=manifest.files(index);a=entry.case_index+1;b=entry.realization+1;
    if a<1||a>manifest.case_count||b<1||b>R||coverage(a,b),error('Duplicate or out-of-range case/realization.');end
    expectedName=sprintf('case-%03d-mc-%03d.json',a-1,b-1);path=fullfile(jobFolder,entry.filename);
    if ~strcmp(entry.filename,expectedName)||~isfile(path)||~strcmp(ma_resume_fingerprint(configPath,path),entry.input_fingerprint),error('Shared input missing or fingerprint mismatch.');end
    job=jsondecode(fileread(path));if job.realization~=b-1||size(job.nlos_re,1)~=config.nlos_realizations_per_geometry||size(job.nlos_im,1)~=config.nlos_realizations_per_geometry,error('Full input count/realization mismatch.');end
    coverage(a,b)=true;
end
if ~all(coverage(:)),error('Full geometry coverage is incomplete.');end
end

function value=ma_config_digest(path)
fid=fopen(path,'rb');bytes=fread(fid,Inf,'*uint8');fclose(fid);digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(bytes);raw=typecast(digest.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end

function complete=ma_resume_implemented_complete(path,expected,job,config)
% Reuse implemented MC subset, but never promote it to original-figure closure.
complete=false;if ~isfile(path),return;end
try
    result=jsondecode(fileread(path));if ~isfield(result,'input_fingerprint')||~strcmp(result.input_fingerprint,expected)||~isfield(result,'checks'),return;end
    if ~isfield(result,'implementation_fingerprint')||~strcmp(result.implementation_fingerprint,strict_ma_implementation_fingerprint()),return;end
    flags={'mrt_converged','zf_converged','mrt_nominal_design_spacing_feasible','zf_nominal_design_spacing_feasible','mrt_nominal_design_box_feasible','zf_nominal_design_box_feasible'};
    for i=1:numel(flags),if ~isfield(result.checks,flags{i})||~result.checks.(flags{i}),return;end,end
    names={'MA_MRT','MA_ZF','FPA_MRT','FPA_ZF','FPA_OPT'};
    for i=1:numel(names)
        item=result.metrics.schemes.(names{i});if numel(item.sample_sum_rates)~=config.nlos_realizations_per_geometry||~all(isfinite(item.sample_sum_rates)),return;end
        if isfield(item,'nonconverged_samples')&&item.nonconverged_samples~=0,return;end
    end
    if isfield(job,'correlated')&&job.correlated
        ext=result.metrics.correlated_extension;if numel(ext.MA_MRT_MC.sample_sum_rates)~=config.nlos_realizations_per_geometry||numel(ext.MA_ZF_MC.sample_sum_rates)~=config.nlos_realizations_per_geometry,return;end
        if ~all(isfinite(ext.MA_MRT_MC.sample_sum_rates))||~all(isfinite(ext.MA_ZF_MC.sample_sum_rates)),return;end
    end
    mode='';if isfield(job,'figure')&&ismember(job.figure,[3,13,15]),mode='mrt';elseif isfield(job,'figure')&&ismember(job.figure,[4,14,16]),mode='zf';end
    if ~isempty(mode)
        hist=result.history.(mode);count=numel(hist.objective);
        if count<2||~isfield(hist,'instantaneous_MC_mean')||numel(hist.instantaneous_MC_mean)~=count||~all(isfinite(hist.instantaneous_MC_mean)),return;end
        if isfield(job,'correlated')&&job.correlated
            ext=result.metrics.correlated_extension;names={'ZF_correlated_MC_history'};if strcmp(mode,'mrt'),names={'MRT_correlated_MC_history','MRT_Eq69_history'};end
            for i=1:numel(names),if ~isfield(ext,names{i})||numel(ext.(names{i}))~=count||~all(isfinite(ext.(names{i}))),return;end,end
        end
    end
    if isfield(job,'brute_force_D')
        if ~result.metrics.brute_force.MRT.search.complete||~result.metrics.brute_force.ZF.search.complete,return;end
    end
    complete=true;
catch,complete=false;end
end

function value=ma_resume_fingerprint(configPath,jobPath)
digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(uint8('strict-v1'));digest.update(uint8(0));
fid=fopen(configPath,'rb');bytes=fread(fid,Inf,'*uint8');fclose(fid);digest.update(bytes);digest.update(uint8(0));
fid=fopen(jobPath,'rb');bytes=fread(fid,Inf,'*uint8');fclose(fid);digest.update(bytes);raw=typecast(digest.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end
