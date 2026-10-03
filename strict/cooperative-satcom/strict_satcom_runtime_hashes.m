function hashes=strict_satcom_runtime_hashes(configPath)
% Actual executed MATLAB package/config SHA256 without machine-private paths.
base=fileparts(mfilename('fullpath'));files={'strict_satcom_core.m','strict_satcom_models.m','strict_satcom_scenario.m', ...
    'strict_satcom_algorithms.m','strict_satcom_increments.m','strict_satcom_runtime_hashes.m','run_strict_cooperative_satcom.m'};hashes=struct();
for k=1:numel(files),hashes.(matlab.lang.makeValidName(files{k}))=struct('filename',files{k},'sha256',sha256(fullfile(base,files{k})));end
[~,name,extension]=fileparts(configPath);hashes.immutable_configuration=struct('filename',[name,extension],'sha256',sha256(configPath));
end
function value=sha256(path)
fid=fopen(path,'rb');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(bytes);raw=typecast(digest.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end
