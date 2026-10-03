function result=run_native_runtime_subset_v3(runtimeDir,outputPath,recordFolder,figureName)
% External metadata wrapper only; engine/observer/controls keep their actual bytes.
assert(nargin==4);assert(maxNumCompThreads==1,'One native computational thread required.');
[ok,attributes]=fileattrib(runtimeDir);assert(ok&&attributes.directory);runtimeDir=attributes.Name;
metadata=jsondecode(fileread(fullfile(runtimeDir,'recording-source-freeze.json')));
assert(~metadata.all42_source_identity_claimed);
identity=jsondecode(fileread(fullfile(runtimeDir,'runtime-subset-reconstruction.json')));
assert(identity.all_selected_SHA_match&&identity.files_checked==17);
entries=identity.selected_files;if iscell(entries),entries=[entries{:}];end
before=cell(1,numel(entries));
for j=1:numel(entries),before{j}=file_sha(fullfile(runtimeDir,strrep(entries(j).runtime_relative_path,'/',filesep)));assert(strcmp(before{j},entries(j).sha256));end
addpath(runtimeDir,'-begin');assert(strcmp(which('run_mis_communications_recording_v2'),fullfile(runtimeDir,'run_mis_communications_recording_v2.m')));
result=run_mis_communications_recording_v2(outputPath,figureName,fullfile(runtimeDir,'settings.json'),recordFolder);
for j=1:numel(entries),assert(strcmp(before{j},file_sha(fullfile(runtimeDir,strrep(entries(j).runtime_relative_path,'/',filesep)))));end
end

function value=file_sha(path)
fid=fopen(path,'rb');assert(fid>=0);cleaner=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');
d=java.security.MessageDigest.getInstance('SHA-256');d.update(bytes);value=lower(reshape(dec2hex(typecast(d.digest(),'uint8'),2).',1,[]));
end
