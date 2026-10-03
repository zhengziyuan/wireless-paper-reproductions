function value=corrected_zf_matlab_fingerprint()
% Separate identity: none of these adapters mutates frozen original MA engine.
base=fileparts(mfilename('fullpath'));d=java.security.MessageDigest.getInstance('SHA-256');d.update(uint8('corrected-ZF-full-position-v3-segmented-integral'));d.update(uint8(0));
names={'correlated_zf_inverse_moment.m','correlated_zf_jensen_bound.m','corrected_zf_position_matlab.m','corrected_zf_context_matlab.m',...
    'validate_corrected_zf_source_matlab.m','evaluate_correlated_zf_matlab.m','corrected_zf_matlab_fingerprint.m','run_corrected_ma_figure_matlab.m'};
for name=names
    d.update(uint8(name{1}));d.update(uint8(0));fid=fopen(fullfile(base,name{1}),'rb');assert(fid>=0);bytes=fread(fid,Inf,'*uint8');fclose(fid);d.update(bytes);d.update(uint8(0));
end
d.update(uint8(version));raw=typecast(d.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end
