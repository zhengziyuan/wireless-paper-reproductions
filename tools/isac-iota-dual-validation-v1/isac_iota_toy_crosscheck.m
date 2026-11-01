function isac_iota_toy_crosscheck(outputFile, helperPath)
% Synthetic fixed-state tests only. No paper inputs or optimizer.
if nargin~=2 || ~ischar(outputFile) || ~ischar(helperPath) || isfile(outputFile)
    error('crosscheck:badInputs','Unique output and helper path required');
end
addpath(fileparts(helperPath),'-begin');
actual=which('isac_iota_update');
if ~strcmpi(actual,helperPath), error('crosscheck:helperPath','Unexpected helper'); end
P={ [1 2], [1 2], [1 0], [1 0], [0 0], [1 2], [1 2], [1 2], [1e-15 1], [-1 1], [1 2] };
D={ [1 1], [1 1], [0 1], [0 1], [1 0], [0 0], [1 1], [1 1], [1 0], [1 1], [1 1] };
Modes={'exact','safeguarded','exact','safeguarded','exact','exact','safeguarded','safeguarded','exact','exact','exact'};
E={ [],.25,[],.5,[],[],[],Inf,[],[],.1 };
Src={ [],'synthetic epsilon',[],'synthetic epsilon',[],[],[], 'synthetic epsilon',[],[], 'synthetic epsilon' };
Prev={ 1.5,1.5,1,1,1,1,1,1,1,1,1 };
results=cell(1,numel(P));
for k=1:numel(P)
    results{k}=isac_iota_update(P{k},D{k},Prev{k},Modes{k},E{k},Src{k});
end
payload=struct('schema','ISAC_IOTA_SYNTHETIC_MATLAB_RESULTS_V1',...
    'case_count',numel(P),'results',{results},'uses_paper_data',false,...
    'scientific_acceptance',false);
fid=fopen(outputFile,'w');
if fid<0, error('crosscheck:output','Could not create output'); end
cleanup=onCleanup(@()fclose(fid));
encoded=jsonencode(payload);
written=fwrite(fid,encoded,'char');
if written~=numel(encoded), error('crosscheck:output','Short or missing output'); end
end
