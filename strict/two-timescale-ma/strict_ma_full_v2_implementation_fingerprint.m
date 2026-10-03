function [value,identity]=strict_ma_full_v2_implementation_fingerprint(configPath)
% Fresh source/runtime identity, NEVER the original persistent cached identity.
base=fileparts(mfilename('fullpath'));if nargin<1,configPath=fullfile(base,'configs','full-ao10000-fig03-18-v2.json');end
config=jsondecode(fileread(configPath));
names={'run_strict_two_timescale_ma_full_v2.m','run_full_ma_figure_v2.m','strict_ma_full_v2_implementation_fingerprint.m','ma_exact_coordinate.m'};
digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(uint8('MATLAB-full-v2-history-storage'));digest.update(uint8(0));
sources=struct('name',{},'path',{},'sha256',{});
for index=1:numel(names)
    path=fullfile(base,names{index});assert(isfile(path),'Missing versioned source dependency.');
    if strcmp(names{index},'ma_exact_coordinate.m')
        resolved=which('ma_exact_coordinate');assert(strcmpi(resolved,path),'Exact-coordinate helper is shadowed by a different MATLAB path.');
    end
    bytes=read_bytes(path);digest.update(uint8(names{index}));digest.update(uint8(0));digest.update(bytes);digest.update(uint8(0));
    sources(end+1)=struct('name',names{index},'path',path,'sha256',bytes_sha(bytes)); %#ok<AGROW>
end
backend=config.matlab_convex_solver;digest.update(uint8(backend));digest.update(uint8(0));
runtimeDependencies=struct('name',{},'path',{},'sha256',{});
% Incidental unused CVX installations do not change the exact-2D backend.
% When explicitly selecting CVX, retain the actual loaded external functions.
if ~strcmp(backend,'certified_exact_2d')
    for name={'cvx_version','cvx_begin','vec','sqlp'}
        path=which(name{1});if isempty(path)||~isfile(path),continue;end
        bytes=read_bytes(path);digest.update(uint8(name{1}));digest.update(uint8(0));digest.update(uint8(path));digest.update(uint8(0));digest.update(bytes);digest.update(uint8(0));
        runtimeDependencies(end+1)=struct('name',name{1},'path',path,'sha256',bytes_sha(bytes)); %#ok<AGROW>
    end
end
matlabVersion=version;blasVersion=version('-blas');lapackVersion=version('-lapack');
digest.update(uint8(matlabVersion));digest.update(uint8(0));digest.update(uint8(blasVersion));digest.update(uint8(0));digest.update(uint8(lapackVersion));
raw=typecast(digest.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
identity=struct('version','MATLAB-full-v2-history-storage','backend',backend,'matlab_version',matlabVersion,...
    'blas_version',blasVersion,'lapack_version',lapackVersion,'sources',{sources},'selected_runtime_dependencies',{runtimeDependencies},...
    'fresh_before_after_not_persistent_cache',true,'same_runtime_as_old_bank_claimed',false,'runtime_binary_hashes_complete',false,'implementation_fingerprint',value);
end

function bytes=read_bytes(path)
fid=fopen(path,'rb');assert(fid>=0,'Source dependency could not be read.');cleanup=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8'); %#ok<NASGU>
end
function value=bytes_sha(bytes)
digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(bytes);raw=typecast(digest.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end
