function hashes=strict_hotspot_spectral_hashes(configPath)
% Actual independent spectral-control branch/config, no private path contents.
base=fileparts(mfilename('fullpath'));files={'strict_hotspot_core.m','strict_hotspot_scenario.m', ...
    'strict_hotspot_termination.m','strict_hotspot_statistical.m','strict_hotspot_rgd_spectral.m', ...
    'run_strict_hotspot_statistical_spectral.m','strict_hotspot_spectral_hashes.m'};hashes=struct();
for k=1:numel(files),hashes.(matlab.lang.makeValidName(files{k}))=struct('filename',files{k},'sha256',sha256(fullfile(base,files{k})));end
[~,name,extension]=fileparts(configPath);hashes.immutable_configuration=struct('filename',[name,extension],'sha256',sha256(configPath));
end
function value=sha256(path)
fid=fopen(path,'rb');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(bytes);raw=typecast(digest.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end
