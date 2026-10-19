function receipt=run_native_pattern_controls(planPath)
% Exact copied production scalar function; no optimizer, RNG or full scenario.
plan=jsondecode(fileread(planPath)); assert(~isfile(plan.output_csv)&&~isfile(plan.output_receipt),'Preserve prior scalar output');
before=bindings(plan,planPath); assert(strcmp(before.original_native,plan.original_native_sha256));
assert(strcmp(before.native_function,plan.native_function_sha256));
assert(strcmp(which('itu1428_native_copy'),plan.native_function_path),'Unexpected scalar implementation resolution');
cases=readmatrix(plan.input_csv); assert(size(cases,2)==2&&size(cases,1)==plan.expected_cases,'Missing scalar cases');
actual=zeros(size(cases,1),3);
for n=1:size(cases,1)
    q=cases(n,1); angle=cases(n,2); actual(n,:)=[q,angle,itu1428_native_copy(angle,q)];
end
assert(all(isfinite(actual),'all')&&all(actual(:,3)>0),'Invalid scalar pattern return');
fid=fopen(plan.output_csv,'w'); assert(fid>=0); closer=onCleanup(@()fclose(fid));
fprintf(fid,'%.17g,%.17g,%.17g\n',actual.'); clear closer
after=bindings(plan,planPath);
receipt=struct('scope','Actual MATLAB scalar direction-pattern arithmetic; not full scenario execution', ...
    'PID',feature('getpid'),'MATLAB_version',version,'actual_cases',size(cases,1), ...
    'selected_scalar_function',which('itu1428_native_copy'),'source_before',before,'source_after',after, ...
    'source_and_inputs_unchanged',isequal(before,after),'actual_scalar_execution_complete',true, ...
    'output_csv_sha256',digest(plan.output_csv),'optimizer_or_random_draw_calls',0, ...
    'original_author_inputs_or_curve_or_paper_pass',false);
fid=fopen(plan.output_receipt,'w'); assert(fid>=0); cleaner=onCleanup(@()fclose(fid));
fwrite(fid,jsonencode(receipt),'char'); clear cleaner
assert(receipt.source_and_inputs_unchanged,'Scalar source/input mutation retained');
end

function result=bindings(plan,planPath)
result=struct('original_native',digest(plan.original_native_path), ...
    'native_function',digest(plan.native_function_path),'runner',digest([mfilename('fullpath'),'.m']), ...
    'input_csv',digest(plan.input_csv),'plan',digest(planPath));
end

function value=digest(path)
fid=fopen(path,'rb'); assert(fid>=0); guard=onCleanup(@()fclose(fid));
bytes=fread(fid,Inf,'*uint8'); algorithm=java.security.MessageDigest.getInstance('SHA-256');
algorithm.update(bytes); value=lower(reshape(dec2hex(typecast(algorithm.digest(),'uint8'),2).',1,[]));
end
