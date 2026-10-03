function hashes=strict_hotspot_runtime_hashes(configPath,regime)
% Hash only actual runtime sources and immutable settings; no private paths.
base=fileparts(mfilename('fullpath'));
common={'strict_hotspot_core.m','strict_hotspot_scenario.m','strict_hotspot_termination.m','strict_hotspot_runtime_hashes.m'};
if strcmp(regime,'statistical-controlled')
    files=[common,{'strict_hotspot_statistical.m','strict_hotspot_rgd_controls.m','run_strict_hotspot_statistical_controlled.m'}];
elseif strcmp(regime,'instantaneous')
    files=[common,{'strict_instantaneous_sdr_guard.m','strict_instantaneous_ao_guarded.m','run_strict_hotspot_satcom.m'}];
else,error('Unknown actual runtime source contract');end
hashes=struct();
for k=1:numel(files),hashes.(matlab.lang.makeValidName(files{k}))=struct('filename',files{k},'sha256',sha256(fullfile(base,files{k})));end
[~,name,extension]=fileparts(configPath);hashes.immutable_configuration=struct('filename',[name,extension],'sha256',sha256(configPath));
end

function value=sha256(path)
fid=fopen(path,'rb');assert(fid>=0,'Runtime source is missing');cleanup=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');
digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(bytes);raw=typecast(digest.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end
