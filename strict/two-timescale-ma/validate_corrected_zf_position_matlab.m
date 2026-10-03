function result=validate_corrected_zf_position_matlab(outputPath,jobPath,configPath)
% Actual complete1000-draw initial-geometry test; NOT a full figure or trajectory.
job=jsondecode(fileread(jobPath));config=jsondecode(fileread(configPath));[c,nlos,t]=corrected_zf_context_matlab(job,config);
result=corrected_zf_position_matlab(t,c,nlos);result.mode='full1000_position_evidence_not_full_figure';result.figure=job.figure;
result.paper_id='two-timescale-ma';result.evaluator_version='v3_segmented_same_Laplace_integral';
result.evaluator_source_sha256=corrected_zf_matlab_fingerprint();
result.input_job_sha256=file_sha256(jobPath);result.input_config_sha256=file_sha256(configPath);
d=java.security.MessageDigest.getInstance('SHA-256');d.update(uint8('strict-v1'));d.update(uint8(0));
for filename={configPath,jobPath}
fid=fopen(filename{1},'rb');assert(fid>=0);raw=fread(fid,Inf,'*uint8');fclose(fid);d.update(raw);
if strcmp(filename{1},configPath),d.update(uint8(0));end
end
raw=typecast(d.digest(),'uint8');result.input_fingerprint=lower(reshape(dec2hex(raw,2).',1,[]));
result.unchanged_optimization_core_fingerprint=strict_ma_implementation_fingerprint();
result.validator_source_sha256=file_sha256([mfilename('fullpath') '.m']);
result.complete_position_evidence_passed=true;result.all_figure_geometries_or_trajectories_verified=false;
folder=fileparts(outputPath);if ~isempty(folder)&&~isfolder(folder),mkdir(folder);end
fid=fopen(outputPath,'w','n','UTF-8');assert(fid>=0);cleaner=onCleanup(@()fclose(fid));fprintf(fid,'%s',jsonencode(result,'PrettyPrint',true));
end
function value=file_sha256(path)
fid=fopen(path,'rb');assert(fid>=0);bytes=fread(fid,Inf,'*uint8');fclose(fid);
d=java.security.MessageDigest.getInstance('SHA-256');d.update(bytes);raw=typecast(d.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end
