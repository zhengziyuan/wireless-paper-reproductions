function hashes=hotspot_element_count_runtime_hashes(configPath)
% Actual shared numerical files, outside-package count adapter and input bytes.
base=fileparts(mfilename('fullpath'));package=fullfile(base,'hotspot-satcom');
files={'strict_hotspot_core.m','strict_hotspot_geometry.m','strict_hotspot_termination.m', ...
    'strict_instantaneous_sdr_guard.m','strict_instantaneous_ao_guarded.m'};
hashes=struct();
for k=1:numel(files),hashes.(matlab.lang.makeValidName(files{k}))=struct('filename',files{k},'sha256',digest(fullfile(package,files{k})));end
files={'run_hotspot_element_count_matlab.m','strict_hotspot_element_count.m','hotspot_element_count_runtime_hashes.m'};
for k=1:numel(files),hashes.(matlab.lang.makeValidName(files{k}))=struct('filename',files{k},'sha256',digest(fullfile(base,files{k})));end
[~,name,extension]=fileparts(configPath);hashes.immutable_configuration=struct('filename',[name extension],'sha256',digest(configPath));
end

function value=digest(path)
fid=fopen(path,'rb');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');
md=java.security.MessageDigest.getInstance('SHA-256');md.update(bytes);raw=typecast(md.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end
