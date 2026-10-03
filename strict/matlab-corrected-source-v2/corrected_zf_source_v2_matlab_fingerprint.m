function [value,identity]=corrected_zf_source_v2_matlab_fingerprint(configPath)
% Fresh NEW trajectory/adapter identity; original v3 integral is not rewritten.
base=fileparts(mfilename('fullpath'));package=fullfile(fileparts(base),'two-timescale-ma');
if nargin<1,configPath=fullfile(package,'configs','full-ao10000-fig03-18-v2.json');end
[sourceFingerprint,sourceIdentity]=strict_ma_full_v2_implementation_fingerprint(configPath);
d=java.security.MessageDigest.getInstance('SHA-256');d.update(uint8('corrected-source-MATLAB-full-v2-original-segmented-integral'));d.update(uint8(0));d.update(uint8(sourceFingerprint));d.update(uint8(0));
names={'run_corrected_ma_figure_matlab_source_v2.m','evaluate_correlated_zf_matlab_source_v2.m','validate_corrected_zf_source_matlab_full_v2.m','validate_corrected_zf_position_matlab_source_v2.m','corrected_zf_source_v2_matlab_fingerprint.m'};
original={'correlated_zf_inverse_moment.m','correlated_zf_jensen_bound.m','corrected_zf_position_matlab.m','corrected_zf_context_matlab.m'};
sources=struct('name',{},'repository_relative_path',{},'sha256',{});
for group=1:2
    if group==1,current=names;folder=base;relative='strict/matlab-corrected-source-v2/';else,current=original;folder=package;relative='strict/two-timescale-ma/';end
    for i=1:numel(current)
        path=fullfile(folder,current{i});assert(isfile(path),'Missing explicit versioned evaluator dependency.');
        [~,functionName]=fileparts(current{i});assert(strcmpi(which(functionName),path),'Versioned numeric helper is shadowed by a different MATLAB path.');
        fid=fopen(path,'rb');assert(fid>=0);bytes=fread(fid,Inf,'*uint8');fclose(fid);d.update(uint8([relative current{i}]));d.update(uint8(0));d.update(bytes);d.update(uint8(0));
        h=java.security.MessageDigest.getInstance('SHA-256');h.update(bytes);raw=typecast(h.digest(),'uint8');fileHash=lower(reshape(dec2hex(raw,2).',1,[]));
        sources(end+1)=struct('name',current{i},'repository_relative_path',[relative current{i}],'sha256',fileHash); %#ok<AGROW>
    end
end
d.update(uint8(version));raw=typecast(d.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
identity=struct('version','corrected-source-MATLAB-full-v2','original_integrator_context_position_sources_unchanged',true,'new_trajectory_implementation_fingerprint',sourceFingerprint,...
    'trajectory_runtime_identity',sourceIdentity,'sources',{sources},'implementation_fingerprint',value,'fresh_before_after_not_persistent_cache',true);
end
