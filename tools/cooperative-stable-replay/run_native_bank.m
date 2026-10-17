function run_native_bank(repo,inputBank,outDir)
% Full183 original input cases, all8 schemes/1000 moment draws. No reduced cases.
assert(~isfolder(outDir) && ~isfile(outDir),'Fresh campaign required');
addpath(fullfile(repo,'strict','cooperative-satcom'));
plan=jsondecode(fileread(fullfile(inputBank,'execution-plan.json')));
assert(plan.required_points==183 && numel(plan.required_schemes_per_point)==8);
assert(isequal(plan.required_schemes_per_point(:),{'AP-NoRIS';'AP-AO';'MR-S-NoRIS';'MR-S-PA';'MR-S-TS';'MR-TTS-NoRIS';'MR-TTS-PA';'MR-TTS-TS'}));
assert(plan.required_original_moment_draws_per_successfully_completed_point==1000);
mkdir(outDir); records=cell(183,1); started=tic;
emit(fullfile(outDir,'progress.json'),struct('expected',183,'finished',0,'active_case',0,'records',{{}},'all183_pass',false));
for number=0:182
    name=sprintf('case-%03d',number); config=fullfile(inputBank,name,'configuration.json');
    scene=jsondecode(fileread(config)); assert(scene.tuned_not_reported.monte_carlo_realizations==1000);
    output=fullfile(outDir,[name '-matlab.json']);
    emit(fullfile(outDir,'progress.json'),struct('expected',183,'finished',number,'active_case',number,'elapsed_seconds',toc(started),...
        'records',{records(1:number)},'all183_pass',false));
    record=struct('case_ordinal',number,'output',[name '-matlab.json'],'completed',false,'all_original_internal_gates_pass',false,'error','');
    try
        result=run_strict_cooperative_v3(config,output,'base');
        record.completed=true;
        record.all_original_internal_gates_pass=result.source_unchanged_during_run && result.overall_implemented_scope_success;
    catch exception
        record.error=exception.message;
        emit(fullfile(outDir,[name '-exception.json']),struct('identifier',exception.identifier,'message',exception.message,'stack',exception.stack));
    end
    records{number+1}=record;
    fprintf('Native full183 case %d/183: completed=%d original_gates=%d elapsed=%.1fs\n',number+1,record.completed,record.all_original_internal_gates_pass,toc(started));
    emit(fullfile(outDir,'progress.json'),struct('expected',183,'finished',number+1,'active_case',[],...
        'elapsed_seconds',toc(started),'records',{records(1:number+1)},'all183_pass',false));
end
summary=struct('expected',183,'finished',183,'records',{records},'elapsed_seconds',toc(started),...
    'all_original_internal_gates_pass',all(cellfun(@(r)r.all_original_internal_gates_pass,records)),...
    'independent_physics_or_original_reference_pass',false,'full_reproduction_pass',false);
emit(fullfile(outDir,'summary.json'),summary);
end

function emit(path,value)
partial=[path '.partial']; fid=fopen(partial,'w','n','UTF-8'); assert(fid>=0);
cleanup=onCleanup(@()fclose(fid)); fwrite(fid,jsonencode(value),'char'); clear cleanup;
movefile(partial,path,'f');
end
