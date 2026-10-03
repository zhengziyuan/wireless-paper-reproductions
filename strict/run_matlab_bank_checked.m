function receipt=run_matlab_bank_checked(paper,bankFolder,outputFolder)
% Execute independent full MATLAB banks with durable BEFORE/AFTER identities.
% This wrapper does not change the frozen paper numerical engines. A Python
% renderer independently checks every original stop and every MATLAB record.
assert(any(strcmp(paper,{'rotatable-isac','two-timescale-ma'})));
base=fileparts(mfilename('fullpath'));package=fullfile(base,paper);addpath(package);
configPath=fullfile(bankFolder,'run_config.json');manifestPath=fullfile(bankFolder,'manifest.json');
manifest=jsondecode(fileread(manifestPath));assert(manifest.realizations_per_case==100);
if strcmp(paper,'two-timescale-ma'),assert(manifest.nlos_per_geometry==1000);end
assert(manifest.input_bank_complete&&manifest.expected_jobs==manifest.case_count*100);
if ~isfolder(outputFolder),mkdir(outputFolder);end
clear strict_ma_implementation_fingerprint strict_isac_implementation_fingerprint
before=source_identity(base,package,paper);
implementationBefore=engine_fingerprint(paper);
binding=struct('paper_id',paper,'source_identity',before,'matlab_version',version, ...
    'runtime_implementation_fingerprint',implementationBefore, ...
    'manifest_sha256',file_hash(manifestPath),'configuration_sha256',file_hash(configPath), ...
    'plan_sha256',file_hash(fullfile(bankFolder,'plan.json')),'expected_jobs',manifest.expected_jobs);
startPath=fullfile(outputFolder,'execution-start-identity.json');
if isfile(startPath)
    previous=jsondecode(fileread(startPath));
    % jsondecode can convert cell-of-struct arrays into struct arrays.
    assert(strcmp(jsonencode(previous),jsonencode(binding)), ...
        'Frozen MATLAB execution binding changed; use a fresh result directory');
else
    assert(isempty(dir(fullfile(outputFolder,'case-*-mc-*-matlab.json'))), ...
        'Existing unbound MATLAB results cannot acquire a post-hoc execution-time certificate');
    write_json(startPath,binding);
end
% Preserve every old failed/interrupted attempt before the engine can retry.
old=dir(fullfile(outputFolder,'case-*-mc-*-matlab.json'));
for index=1:numel(old)
    path=fullfile(old(index).folder,old(index).name);archive=fullfile(outputFolder,'retained-attempts');
    if ~isfolder(archive),mkdir(archive);end
    [~,stem]=fileparts(path);target=fullfile(archive,[stem,'-',file_hash(path),'.json']);
    if ~isfile(target),copyfile(path,target);end
end
if strcmp(paper,'rotatable-isac')
    run_full_isac_figure(fullfile(bankFolder,'jobs'),outputFolder,configPath);
    implementation=strict_isac_implementation_fingerprint();
else
    run_full_ma_figure(fullfile(bankFolder,'jobs'),outputFolder,configPath);
    implementation=strict_ma_implementation_fingerprint();
end
% Force a new dependency/runtime digest, not the engine's persistent cache.
clear strict_ma_implementation_fingerprint strict_isac_implementation_fingerprint
implementationAfter=engine_fingerprint(paper);
after=source_identity(base,package,paper);items=cell(numel(manifest.files),1);valid=true;
for index=1:numel(manifest.files)
    entry=manifest.files(index);[~,stem]=fileparts(entry.filename);
    jobPath=fullfile(bankFolder,'jobs',entry.filename);resultName=[stem,'-matlab.json'];resultPath=fullfile(outputFolder,resultName);
    expected=input_fingerprint(configPath,jobPath);sameInput=strcmp(expected,entry.input_fingerprint);
    exists=isfile(resultPath);sameImplementation=false;boundResult=false;resultSHA='';
    if exists
        resultSHA=file_hash(resultPath);raw=jsondecode(fileread(resultPath));
        sameImplementation=isfield(raw,'implementation_fingerprint')&&strcmp(raw.implementation_fingerprint,implementation);
        boundResult=isfield(raw,'input_fingerprint')&&strcmp(raw.input_fingerprint,expected);
    end
    valid=valid&&sameInput&&exists&&sameImplementation&&boundResult;
    items{index}=struct('input_filename',entry.filename,'input_fingerprint',expected, ...
        'result_filename',resultName,'result_sha256',resultSHA,'input_identity_pass',sameInput, ...
        'result_exists',exists,'result_input_identity_pass',boundResult,'implementation_identity_pass',sameImplementation);
end
receipt=struct('paper_id',paper,'engine','matlab', ...
    'scope','actual_full_bank_execution_time_source_identity_NOT_convergence_or_reference_certificate', ...
    'binding',binding,'implementation_fingerprint',implementation,'sources_before',before,'sources_after',after, ...
    'runtime_implementation_fingerprint_after',implementationAfter, ...
    'runtime_dependency_identity_unchanged',strcmp(implementationBefore,implementationAfter)&&strcmp(implementation,implementationBefore), ...
    'source_unchanged_during_run',isequal(before,after),'expected_jobs',manifest.expected_jobs, ...
    'all_result_identities_pass',valid,'records',{items},'full_reproduction_pass',false, ...
    'original_curve_closeness_verified',false);
write_json(fullfile(outputFolder,'execution-identity.json'),receipt);
assert(receipt.source_unchanged_during_run,'MATLAB sources changed during actual full execution');
assert(receipt.runtime_dependency_identity_unchanged,'MATLAB engine/runtime dependency digest changed during actual full execution');
end

function value=engine_fingerprint(paper)
if strcmp(paper,'rotatable-isac'),value=strict_isac_implementation_fingerprint();
else,value=strict_ma_implementation_fingerprint();end
end

function records=source_identity(base,package,paper)
if strcmp(paper,'rotatable-isac')
    names={'run_strict_rotatable_isac.m','run_full_isac_figure.m','strict_isac_implementation_fingerprint.m'};
else
    names={'run_strict_two_timescale_ma.m','run_full_ma_figure.m','strict_ma_implementation_fingerprint.m','ma_exact_coordinate.m'};
end
records=cell(numel(names)+1,1);
for k=1:numel(names),records{k}=struct('relative_path',[paper,'/',names{k}],'sha256',file_hash(fullfile(package,names{k})));end
records{end}=struct('relative_path','run_matlab_bank_checked.m','sha256',file_hash(fullfile(base,'run_matlab_bank_checked.m')));
end

function value=input_fingerprint(configPath,jobPath)
digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(uint8('strict-v1'));digest.update(uint8(0));
digest.update(read_binary(configPath));digest.update(uint8(0));digest.update(read_binary(jobPath));value=digest_value(digest);
end

function value=file_hash(path)
digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(read_binary(path));value=digest_value(digest);
end

function bytes=read_binary(path)
fid=fopen(path,'rb');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');
end

function value=digest_value(digest)
raw=typecast(digest.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end

function write_json(path,value)
fid=fopen(path,'w','n','UTF-8');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(value));
end
