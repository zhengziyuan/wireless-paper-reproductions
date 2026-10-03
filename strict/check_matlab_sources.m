function report=check_matlab_sources(outputPath)
% Static diagnostics only; this does not execute or certify full simulations.
base=fileparts(mfilename('fullpath')); files=dir(fullfile(base,'**','*.m'));
entries=cell(numel(files),1);
for k=1:numel(files)
    source=fullfile(files(k).folder,files(k).name);
    relative=strrep(source,[base,filesep],'');
    diagnostics=checkcode(source,'-id');
    entries{k}=struct('file',strrep(relative,'\','/'),'diagnostics',diagnostics);
end
report=struct('scope','MATLAB source analysis only; NOT full reproduction', ...
    'matlab_version',version,'matlab_release',version('-release'), ...
    'source_count',numel(files),'files',{entries},'full_reproduction_pass',false);
if nargin>0 && ~isempty(outputPath)
    folder=fileparts(outputPath);if ~isempty(folder)&&~isfolder(folder),mkdir(folder);end
    fid=fopen(outputPath,'w');assert(fid>=0);cleaner=onCleanup(@()fclose(fid));
    fprintf(fid,'%s\n',jsonencode(report));
end
end
