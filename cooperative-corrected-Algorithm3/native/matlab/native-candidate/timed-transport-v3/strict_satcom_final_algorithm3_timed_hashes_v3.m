function hashes=strict_satcom_final_algorithm3_timed_hashes_v3(configPath)
% Delegate original complete science/CVX/runtime bindings, then close new transport.
hashes=strict_satcom_v3_hashes(configPath);
base=fileparts(mfilename('fullpath'));parent=fileparts(base);
paths={fullfile(parent,'strict_satcom_algorithms_final_algorithm3_v2.m'),fullfile(parent,'timed-transport-v2','strict_satcom_algorithms_final_algorithm3_v2_timed_v2.m'),fullfile(base,'run_strict_cooperative_final_algorithm3_timed_v3.m'),fullfile(base,'strict_satcom_final_algorithm3_timed_hashes_v3.m'),fullfile(base,'strict_satcom_complex_json_transport_v1.m'),fullfile(base,'strict_satcom_complex_json_transport_selftest_v1.m')};
keys={'final_Algorithm3_V2_source','actual_timed_algorithm_entry','actual_timed_runner_entry','actual_timed_hash_entry','actual_complex_JSON_transport','actual_complex_JSON_selftest'};
for k=1:numel(paths),hashes.(keys{k})=struct('path',paths{k},'sha256',sha256(paths{k}));end
end
function value=sha256(path)
fid=fopen(path,'rb');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(bytes);raw=typecast(digest.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end
