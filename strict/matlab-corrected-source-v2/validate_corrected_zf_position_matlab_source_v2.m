function result=validate_corrected_zf_position_matlab_source_v2(outputPath,jobPath,configPath)
% Initial full1000 position evidence, not source optimization or full300 figure.
before=corrected_zf_source_v2_matlab_fingerprint(configPath);
job=jsondecode(fileread(jobPath));config=jsondecode(fileread(configPath));[c,nlos,t]=corrected_zf_context_matlab(job,config);
result=corrected_zf_position_matlab(t,c,nlos);assert(strcmp(before,corrected_zf_source_v2_matlab_fingerprint(configPath)),'Original evaluator dependencies changed');
result.paper_id='two-timescale-ma';result.figure=job.figure;result.mode='actual_original_integral_full1000_position_evidence_not_full300_or_trajectory';
result.corrected_adapter_version='corrected-source-MATLAB-full-v2';result.evaluator_source_sha256=before;
result.input_job_sha256=file_sha(jobPath);result.input_config_sha256=file_sha(configPath);
result.original_integrator_context_position_sources_unchanged=true;result.complete_position_evidence_passed=true;result.all_figure_geometries_or_trajectories_verified=false;
folder=fileparts(outputPath);if ~isempty(folder)&&~isfolder(folder),mkdir(folder);end
fid=fopen(outputPath,'w','n','UTF-8');assert(fid>=0);cleaner=onCleanup(@()fclose(fid));fprintf(fid,'%s',jsonencode(result,'PrettyPrint',true));
end
function value=file_sha(path)
fid=fopen(path,'rb');assert(fid>=0);bytes=fread(fid,Inf,'*uint8');fclose(fid);d=java.security.MessageDigest.getInstance('SHA-256');d.update(bytes);raw=typecast(d.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end
