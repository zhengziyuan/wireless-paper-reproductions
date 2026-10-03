function result=run_sensing_v5_native_bound(mode,outputPath,bindingReceiptPath,expectedBindingPath)
% OUTSIDE live package: exact selected v5 source/input binding, fresh outputs.
% Component success is not a full figure; full-start retains original budgets.
assert(~exist(outputPath,'file')&&~exist(bindingReceiptPath,'file'),'Fresh native receipt paths required');
base=fileparts(mfilename('fullpath'));binding=jsondecode(fileread(expectedBindingPath));
bindingHash=hashfile(expectedBindingPath);wrapperPath=[mfilename('fullpath'),'.m'];
assert(strcmp(hashfile(wrapperPath),binding.wrapper_sha256),'Unexpected bound wrapper bytes');
package=fullfile(base,'scientific-source-v5');addpath(package,'-begin');
clear mis_sensing_strict_engine sorted_cone_rows_exact_binary_v2
handle=@mis_sensing_strict_engine;selected=functions(handle);
assert(strcmp(canonical(selected.file),canonical(fullfile(package,'mis_sensing_strict_engine.m'))),'Unexpected selected scientific function');
before=source_hashes(base,binding.entries);began=tic;
if string(mode)=="cone-component"
    fixture=jsondecode(fileread(fullfile(package,'tests','sorted_cone_shared_exact_fixture.json')));
    witness=jsondecode(fileread(fullfile(package,'tests','matlab_centered_optional_order_exact_counterexamples.json')));
    actual377=jsondecode(fileread(fullfile(base,'actual377-cone-forward-fixture.json')));
    checks={};
    for j=1:numel(fixture.cases)
        item=at(fixture.cases,j);[out,info]=sorted_cone_rows_exact_binary_v2(item.X(:).',item.raw_y(:).');
        checks{end+1}=struct('name',item.name,'passed',max(abs(out-item.expected_projection(:).'))<=item.component_bound,...
            'maximum_error',max(abs(out-item.expected_projection(:).')),'method',info{1}.method);
    end
    for j=1:numel(witness.cases)
        item=at(witness.cases,j);
        for permutation=1:2
            raw=item.raw_y(:).';truth=item.exact_expected_projection(:).';bounds=item.expected_projection_per_component_bounds(:).';
            if permutation==2,raw([3 4])=raw([4 3]);truth([3 4])=truth([4 3]);bounds([3 4])=bounds([4 3]);end
            [out,info]=sorted_cone_rows_exact_binary_v2(item.X(:).',raw);
            checks{end+1}=struct('name',[item.name,'-permutation-',num2str(permutation)],'passed',all(abs(out-truth)<=bounds),...
                'maximum_error',max(abs(out-truth)),'method',info{1}.method,'per_component_bound_check',true);
        end
    end
    for j=1:numel(actual377.cases)
        item=at(actual377.cases,j);[out,info]=sorted_cone_rows_exact_binary_v2(item.X(:).',item.raw_y(:).');
        checks{end+1}=struct('name',item.name,'passed',all(abs(out-item.expected_projection(:).')<=item.expected_projection_per_component_bounds(:).'),...
            'maximum_error',max(abs(out-item.expected_projection(:).')),'method',info{1}.method,'per_component_bound_check',true);
    end
    assert(numel(checks)==1025,'All prescribed component cases required');
    result=struct('scope','v5 SAME Euclidean cone1025 actual-selected native component NOT full6000',...
        'all_checks_pass',all(cellfun(@(c)c.passed,checks)),'checks',{checks},'case_count',numel(checks));
    write_json(outputPath,result);
elseif string(mode)=="full-start377"
    settingsPath=fullfile(package,'settings_corrected.json');settings=jsondecode(fileread(settingsPath));
    assert(settings.number_of_starts==6000&&settings.outer_iterations==30&&settings.rcg_max_iterations==4000);
    assert(settings.initialization.eta_initial==0&&settings.initialization.lambda_initial==0&&settings.line_search.initial_step==1);
    result=handle(outputPath,"full-start:fig3:377",settingsPath);
else,error('sensing:v5UnknownMode','Use cone-component or full-start377');end
after=source_hashes(base,binding.entries);
unchanged=isequaln(before,after)&&strcmp(bindingHash,hashfile(expectedBindingPath));
receipt=struct('scope','Actual native v5 selected-source interval; no old certificate transfer or full6000 claim',...
    'mode',char(mode),'source_before',{before},'source_after',{after},'source_unchanged_during_run',unchanged,...
    'binding_sha256',bindingHash,'wrapper_sha256',hashfile(wrapperPath),'selected_function_workspace_relative','scientific-source-v5/mis_sensing_strict_engine.m',...
    'selected_function_sha256',hashfile(selected.file),'output_sha256',hashfile(outputPath),'elapsed_seconds',toc(began),...
    'full6000_complete',false,'reported_budgets_unchanged',true);
if string(mode)=="full-start377"
    receipt.start=377;receipt.original_cold_seed=241219071;receipt.draws_per_start=881;
    rng=241219071;for j=1:376*881,rng=mod(rng*16807,2147483647);end
    receipt.initial_rng_before=rng;for j=1:881,rng=mod(rng*16807,2147483647);end,receipt.initial_rng_after=rng;
    receipt.all_inner_tolerances_satisfied=result.solver_status.all_inner_tolerances_satisfied;
    receipt.original_problem_kkt_verified=result.solver_status.original_problem_kkt_verified;
    receipt.convergence_verified=result.solver_status.convergence_verified;
end
write_json(bindingReceiptPath,receipt);assert(unchanged,'Source/input interval changed');
if string(mode)=="cone-component",assert(result.all_checks_pass,'Same-cone component failure');end
end
function item=at(items,j),if iscell(items),item=items{j};else,item=items(j);end,end
function out=canonical(path),out=char(java.io.File(path).getCanonicalPath());end
function entries=source_hashes(base,entries)
for j=1:numel(entries),actual=hashfile(fullfile(base,entries(j).relative_path));assert(strcmp(actual,entries(j).sha256),'Bound source/input bytes changed: %s',entries(j).relative_path);end
end
function digest=hashfile(path)
fid=fopen(path,'rb');assert(fid>=0);cleaner=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');
md=java.security.MessageDigest.getInstance('SHA-256');md.update(bytes);raw=typecast(md.digest(),'uint8');digest=lower(reshape(dec2hex(raw,2).',1,[]));
end
function write_json(path,value)
[parent,~,~]=fileparts(path);if ~isempty(parent)&&~isfolder(parent),mkdir(parent);end
fid=fopen(path,'w','n','UTF-8');assert(fid>=0);cleaner=onCleanup(@()fclose(fid));fprintf(fid,'%s',jsonencode(value,'PrettyPrint',true));
end
