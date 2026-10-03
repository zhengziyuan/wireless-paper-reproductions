function binding = run_sorted_cone_v2_bound_regression(fixturePath, witnessPath, outputPath, bindingPath)
% WORK v2 same-cone1010 plus six exact raw-order small-component witnesses.
% Every actual source/input is bound before/after this NEW native execution.
% Original v1 sources and their passing limited checks are never rewritten.
if exist(outputPath,'file') || exist(bindingPath,'file')
    error('sensing:freshConeV2Outputs','New component and binding paths required');
end
if ~usejava('jvm'), error('sensing:coneV2JVM','Native JVM required'); end
clear sorted_cone_rows_exact_binary sorted_cone_rows_exact_binary_v2
oldHandle = @sorted_cone_rows_exact_binary;
newHandle = @sorted_cone_rows_exact_binary_v2;
oldInfo = functions(oldHandle); newInfo = functions(newHandle);
paths = struct('original_v1_helper',canonical(oldInfo.file), ...
    'v2_helper',canonical(newInfo.file),'shared_fixture',canonical(fixturePath), ...
    'exact_raw_order_witnesses',canonical(witnessPath), ...
    'binding_wrapper',canonical([mfilename('fullpath') '.m']));
expected = struct('original_v1_helper','6c47eebf6b2556447f6181fd33e6cda2614d354ed3d7809252db580d1fee6387', ...
    'v2_helper','f11097f4af7fbba53f89283757b9ac23686207806db7d1b8778d9f22f00a29eb', ...
    'shared_fixture','ba1531842021b0b9419f19407e953ae76eb8669179f83af96d0b8c396c2c6869', ...
    'exact_raw_order_witnesses','8f118b6576479e2586984b33a89ee2a52e60fe503f9fbcf96900d9fc84a7622b');
before = hashes(paths); expectedFields = fieldnames(expected);
for index=1:numel(expectedFields)
    name = expectedFields{index};
    if ~strcmp(before.(name),expected.(name))
        error('sensing:coneV2FrozenBytes','Actual selected helper or input bytes differ from frozen expectations');
    end
end
fixture = jsondecode(fileread(paths.shared_fixture));
witness = jsondecode(fileread(paths.exact_raw_order_witnesses));
sharedChecks = cell(fixture.case_count,1); fallbackCount=0;
for index=1:fixture.case_count
    item = at(fixture.cases,index); X=item.X(:).'; raw=item.raw_y(:).';
    expectedProjection = item.expected_projection(:).';
    [actual,info] = newHandle(X,raw);
    errorValue=max(abs(actual-expectedProjection)); mandatory=X>0;
    passed=errorValue<=item.component_bound && all(actual(~mandatory)>=0);
    if index==2, passed=passed && all(actual(~mandatory)>0); end
    fallbackCount=fallbackCount+strcmp(info{1}.method,'exact_binary_BigDecimal_row_only');
    sharedChecks{index}=struct('name',item.name,'passed',logical(passed), ...
        'maximum_error',errorValue,'bound',item.component_bound,'method',info{1}.method);
end
regressionChecks=cell(2*numel(witness.cases),1); oldFailureCount=0;
for index=1:numel(witness.cases)
    item=at(witness.cases,index);
    for permutation=1:2
        X=item.X(:).'; raw=item.raw_y(:).';
        expectedProjection=item.exact_expected_projection(:).';
        bounds=item.expected_projection_per_component_bounds(:).';
        if permutation==2
            raw([3 4])=raw([4 3]);
            expectedProjection([3 4])=expectedProjection([4 3]); bounds([3 4])=bounds([4 3]);
        end
        [oldProjection,oldInfo]=oldHandle(X,raw);
        [newProjection,newInfo]=newHandle(X,raw);
        oldErrors=abs(oldProjection-expectedProjection); newErrors=abs(newProjection-expectedProjection);
        oldFails=any(oldErrors>bounds) || oldInfo{1}.optional_active_count~=1;
        oldFailureCount=oldFailureCount+oldFails;
        newPass=all(newErrors<=bounds) && newInfo{1}.optional_active_count==1 && ...
            newInfo{1}.optional_order_from_exact_raw_binary_values_not_centered_ties;
        regressionChecks{2*(index-1)+permutation}=struct('name',item.name, ...
            'optional_low_high_permutation',permutation, ...
            'passed',logical(newPass),'old_v1_exact_raw_order_regression_failed',logical(oldFails), ...
            'maximum_old_small_optional_error',max(oldErrors(3:4)), ...
            'maximum_new_small_optional_error',max(newErrors(3:4)), ...
            'small_optional_component_bounds',bounds(3:4), ...
            'old_optional_active_count',oldInfo{1}.optional_active_count, ...
            'new_optional_active_count',newInfo{1}.optional_active_count);
    end
end
sharedPass=all(cellfun(@(x)x.passed,sharedChecks)); regressionPass=all(cellfun(@(x)x.passed,regressionChecks));
result=struct('scope','ACTUAL WORK MATLAB v2 SAME Euclidean cone1010 plus6 strict small-coordinate raw-order regressions; no full30/original4000/all6000 claim', ...
    'shared_case_count',fixture.case_count,'shared_checks',{sharedChecks}, ...
    'shared_all_checks_pass',logical(sharedPass),'exact_binary_row_fallback_count',fallbackCount, ...
    'strict_raw_order_case_count',numel(regressionChecks),'strict_raw_order_checks',{regressionChecks}, ...
    'strict_raw_order_all_checks_pass',logical(regressionPass),'actual_old_v1_failure_count',oldFailureCount, ...
    'old_v1_failure_reproduced_in_each_scale_using_both_optional_orders',logical(oldFailureCount>=3), ...
    'only_v2_algorithmic_difference','Re-sort original raw binary optional values inside exact fallback, not rounded centered ties', ...
    'no_metric_direction_support_pruning_tolerance_budget_or_model_change',true, ...
    'all_checks_pass',logical(sharedPass && regressionPass && oldFailureCount>=3));
write_json(outputPath,result);
after=hashes(paths);
selectedUnchanged=strcmp(paths.original_v1_helper,canonical(which('sorted_cone_rows_exact_binary'))) && ...
    strcmp(paths.v2_helper,canonical(which('sorted_cone_rows_exact_binary_v2')));
sourceUnchanged=isequal(before,after) && selectedUnchanged;
binding=struct('scope','ACTUAL fresh native cone v2 component and regression execution, actual selected bytes bound before/after; not retrofit or full solver certificate', ...
    'matlab_version',version,'computer',computer,'actual_selected_source_paths',paths, ...
    'expected_frozen_component_hashes',expected,'source_sha256_before',before,'source_sha256_after',after, ...
    'source_unchanged',logical(sourceUnchanged),'component_output_sha256',sha256(outputPath), ...
    'component_output_path',canonical(outputPath),'component_all_checks_pass',logical(result.all_checks_pass), ...
    'shared_case_count',result.shared_case_count,'strict_raw_order_case_count',result.strict_raw_order_case_count, ...
    'actual_old_v1_failure_count',result.actual_old_v1_failure_count, ...
    'all_checks_pass',logical(sourceUnchanged && result.all_checks_pass));
write_json(bindingPath,binding);
fprintf('Cone v2 bound checks: shared1010=%d, strict6=%d, original-v1 failures=%d, source unchanged=%d\n', ...
    sharedPass,regressionPass,oldFailureCount,sourceUnchanged);
assert(binding.all_checks_pass,'sensing:coneV2RegressionFailure','Source-bound cone v2 checks failed');
end

function item=at(items,index)
if iscell(items),item=items{index};else,item=items(index);end
end

function write_json(path,value)
handle=fopen(path,'w','n','UTF-8');
if handle<0,error('sensing:coneV2Write','Cannot create fresh output');end
cleanup=onCleanup(@()fclose(handle));fwrite(handle,jsonencode(value),'char');
end

function path=canonical(path)
file=javaObject('java.io.File',char(path));path=char(file.getCanonicalPath());
end

function result=hashes(paths)
result=struct();names=fieldnames(paths);
for index=1:numel(names),name=names{index};result.(name)=sha256(paths.(name));end
end

function result=sha256(path)
handle=fopen(path,'rb');
if handle<0,error('sensing:coneV2HashRead','Cannot read actual selected bytes');end
cleanup=onCleanup(@()fclose(handle));bytes=fread(handle,Inf,'*uint8');
digest=javaMethod('getInstance','java.security.MessageDigest','SHA-256');
digest.update(typecast(bytes,'int8'));value=typecast(digest.digest(),'uint8');
result=lower(reshape(dec2hex(value,2).',1,[]));
end
