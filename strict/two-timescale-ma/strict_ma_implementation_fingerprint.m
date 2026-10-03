function value=strict_ma_implementation_fingerprint()
% Paper-engine code/runtime identity; not interchangeable with input identity.
persistent cached
if ~isempty(cached),value=cached;return;end
base=fileparts(mfilename('fullpath'));names={'run_strict_two_timescale_ma.m','run_full_ma_figure.m','strict_ma_implementation_fingerprint.m'};
digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(uint8('strict-engine-v1'));digest.update(uint8(0));
for index=1:numel(names)
    digest.update(uint8(names{index}));digest.update(uint8(0));fid=fopen(fullfile(base,names{index}),'rb');bytes=fread(fid,Inf,'*uint8');fclose(fid);digest.update(bytes);digest.update(uint8(0));
end
for name={'cvx_version','cvx_begin','vec','sqlp'}
    path=which(name{1});if ~isempty(path)&&isfile(path),digest.update(uint8(name{1}));digest.update(uint8(0));fid=fopen(path,'rb');bytes=fread(fid,Inf,'*uint8');fclose(fid);digest.update(bytes);digest.update(uint8(0));end
end
digest.update(uint8(version));raw=typecast(digest.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));cached=value;
end
