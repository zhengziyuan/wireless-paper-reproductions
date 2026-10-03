function hashes=strict_satcom_v3_hashes(configPath)
% Prospective v3 exact scientific/config/runtime binding, no old bank upgrade.
base=fileparts(mfilename('fullpath'));
files={'strict_satcom_core.m','strict_satcom_core_v3.m','strict_satcom_mr_qt_factored_v3.m', ...
    'strict_satcom_models.m','strict_satcom_scenario.m','strict_satcom_algorithms_v3.m', ...
    'strict_satcom_increments_v2.m','strict_satcom_qt_guard_v3.m','strict_satcom_v3_hashes.m', ...
    'run_strict_cooperative_v3.m'};
hashes=struct();
for k=1:numel(files)
    hashes.(matlab.lang.makeValidName(files{k}))=struct('filename',files{k},'sha256',sha256(fullfile(base,files{k})));
end
[~,name,extension]=fileparts(configPath);
hashes.immutable_configuration=struct('filename',[name,extension],'sha256',sha256(configPath));
hashes.actual_selected_CVX_solver=cvx_solver;
runtime={'cvx_begin','cvx_end','cvx_solver','cvx_precision','sqlp','sdpt3','mexMatvec','sedumi','eigK','quadadd'};
for k=1:numel(runtime)
    path=which(runtime{k});
    if ~isempty(path)&&exist(path,'file')
        [~,name,extension]=fileparts(path);
        hashes.(['runtime_',matlab.lang.makeValidName(runtime{k})])=struct('filename',[name,extension],'sha256',sha256(path));
    end
end
end

function value=sha256(path)
fid=fopen(path,'rb');assert(fid>=0);cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
bytes=fread(fid,Inf,'*uint8');digest=java.security.MessageDigest.getInstance('SHA-256');
digest.update(bytes);raw=typecast(digest.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end
