function receipt=run_mis_matlab_figure_checked(paper,figureId,settingsPath,outputPath)
% Full configured native MATLAB entry with actual BEFORE/AFTER binding.
% Numerical implementations and their durable checkpoints remain unchanged.
assert(any(strcmp(paper,{'mis-communications','mis-sensing'})));
assert(~isempty(regexp(figureId,'^fig[0-9]+$','once')),'A complete figure ID is required');
base=fileparts(mfilename('fullpath'));package=fullfile(base,paper);addpath(package);
settings=jsondecode(fileread(settingsPath));
assert(settings.number_of_starts==6000,'All configured 6000 start slots are required');
if strcmp(paper,'mis-sensing'),assert(strcmp(settings.kind,'sensing')&&settings.outer_iterations==30&&settings.rcg_max_iterations==4000);
else,assert(strcmp(settings.kind,'communications')&&settings.rcg_max_iterations>0&&fix(settings.rcg_max_iterations)==settings.rcg_max_iterations);end
if strcmp(paper,'mis-communications'),entry='run_mis_communications';
else,entry='run_mis_sensing';end
assert(strcmpi(which(entry),fullfile(package,[entry,'.m'])),'Selected numerical MATLAB entry is shadowed');
[folder,stem,~]=fileparts(outputPath);if isempty(folder),folder=pwd;end
if ~isfolder(folder),mkdir(folder);end
startPath=fullfile(folder,[stem,'-execution-start.json']);
before=source_identity(base,package,paper);configurationBefore=file_hash(settingsPath);
binding=struct('paper_id',paper,'figure',figureId,'settings_sha256',configurationBefore,...
    'sources_before',{before},'matlab_version',version,'blas_version',version('-blas'),...
    'lapack_version',version('-lapack'),'runtime_binary_hashes_complete',false);
if isfile(startPath)
    previous=jsondecode(fileread(startPath));
    assert(strcmp(jsonencode(previous),jsonencode(binding)),'Actual MATLAB source/runtime binding changed; use a distinct output stem');
else
    assert(~isfile(outputPath)&&~isfolder(fullfile(folder,[stem,'_checkpoints'])),...
        'Unbound existing results cannot acquire a post-hoc execution certificate');
    write_json(startPath,binding);
end
failure=[];result=[];started=tic;
try
    if strcmp(paper,'mis-communications'),result=run_mis_communications(outputPath,figureId,settingsPath);
    else,result=run_mis_sensing(outputPath,figureId,settingsPath);end
catch exception
    failure=struct('identifier',exception.identifier,'message',exception.message,'stack',{exception.stack});
end
after=source_identity(base,package,paper);configurationAfter=file_hash(settingsPath);
unchanged=isequal(before,after)&&strcmp(configurationBefore,configurationAfter);
complete=false;numeric=false;
if isstruct(result)&&isscalar(result)&&isfield(result,'full_figure_execution_complete')
    complete=isequal(result.full_figure_execution_complete,true);
    numeric=isfield(result,'overall_full_success')&&isequal(result.overall_full_success,true);
end
rawSHA='';if isfile(outputPath),rawSHA=file_hash(outputPath);end
receipt=struct('paper_id',paper,'figure',figureId,'engine','matlab',...
    'scope','actual_native_full_figure_source_and_runtime_binding_NOT_historical_reference_certificate',...
    'binding',binding,'sources_before',{before},'sources_after',{after},...
    'settings_sha256_after',configurationAfter,'source_configuration_unchanged',unchanged,...
    'native_execution_returned_without_exception',isempty(failure),'failure',failure,...
    'elapsed_seconds',toc(started),'full_figure_execution_complete',complete,...
    'selected_aggregate_native_numeric_flags_passed',numeric,...
    'all_required_native_numeric_gates_passed',false,'full_start_population_summary_verified',false,'raw_result_sha256',rawSHA,...
    'original_reference_closeness_verified',false,'full_reproduction_pass',false);
write_json(fullfile(folder,[stem,'-execution-identity.json']),receipt);
assert(unchanged,'MIS numerical source/configuration changed during execution');
assert(isempty(failure),'Native MIS full figure failed; actual exception and checkpoints retained');
assert(complete&&numeric,'Native complete execution and selected aggregate flags required; full population is checked separately before rendering');
end

function records=source_identity(base,package,paper)
files=[dir(fullfile(package,'*.m'));dir(fullfile(package,'*.py'))];
records=cell(numel(files)+3,1);
for index=1:numel(files)
    records{index}=struct('relative_path',[paper,'/',files(index).name],...
        'sha256',file_hash(fullfile(package,files(index).name)));
end
for index=1:2
    names={'figures.json','source_map.json'};
    records{numel(files)+index}=struct('relative_path',[paper,'/',names{index}],...
        'sha256',file_hash(fullfile(package,names{index})));
end
records{end}=struct('relative_path','run_mis_matlab_figure_checked.m',...
    'sha256',file_hash(fullfile(base,'run_mis_matlab_figure_checked.m')));
end

function value=file_hash(path)
digest=java.security.MessageDigest.getInstance('SHA-256');fid=fopen(path,'rb');assert(fid>=0);
cleanup=onCleanup(@()fclose(fid));digest.update(fread(fid,Inf,'*uint8'));
raw=typecast(digest.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end

function write_json(path,value)
fid=fopen(path,'w','n','UTF-8');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));
fprintf(fid,'%s\n',jsonencode(value));
end
