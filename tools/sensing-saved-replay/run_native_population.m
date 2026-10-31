function run_native_population(bank)
% Missing original Fig3 native slots; unchanged frozen scientific functions.
planPath=fullfile(bank,'native-population-plan.json');planHash=hashfile(planPath);plan=jsondecode(fileread(planPath));
self=[mfilename('fullpath'),'.m'];assert(strcmp(hashfile(self),plan.wrapper_sha256),'Native dispatcher source differs');
assert(plan.expected_starts==6000&&plan.missing_new_optimizer_starts==5999);
settings=jsondecode(fileread(fullfile(bank,'original-settings.json')));
assert(strcmp(hashfile(fullfile(bank,'original-settings.json')),plan.original_settings_sha256));
assert(settings.number_of_starts==6000&&settings.outer_iterations==30&&settings.rcg_max_iterations==4000);
assert(settings.initialization.seed==241219071&&settings.line_search.initial_step==1);
assert(strcmp(hashfile(plan.frozen_binding),plan.frozen_binding_sha256));
binding=jsondecode(fileread(plan.frozen_binding));verify_sources(plan,binding);
addpath(plan.scientific_package,'-begin');clear mis_sensing_strict_engine sorted_cone_rows_exact_binary_v2;
handle=@mis_sensing_strict_engine;selected=functions(handle);
assert(strcmp(canonical(selected.file),canonical(fullfile(plan.scientific_package,'mis_sensing_strict_engine.m'))));
assert(strcmp(hashfile(selected.file),plan.engine_sha256));
inputs=fullfile(bank,'inputs');results=fullfile(bank,'starts');temporary=fullfile(bank,'temporary-verification');
if ~isfolder(inputs),mkdir(inputs);end;if ~isfolder(results),mkdir(results);end;if ~isfolder(temporary),mkdir(temporary);end
records={};began=tic;
for n=1:6000
    identity=plan.cases(n);assert(identity.original_start==n);
    receiptPath=fullfile(results,sprintf('start-%04d-receipt.json',n));
    if isfile(receiptPath)
        record=jsondecode(fileread(receiptPath));assert(record.original_start==n&&strcmp(record.plan_sha256,planHash));
        if isfield(record,'payload_file'),assert(strcmp(hashfile(fullfile(results,record.payload_file)),record.payload_gzip_sha256));end
    else
        verify_sources(plan,binding);assert(strcmp(hashfile(self),plan.wrapper_sha256)&&strcmp(hashfile(planPath),planHash));
        rawPath=fullfile(results,sprintf('start-%04d-matlab.json',n));
        assert(~isfile(rawPath)&&~isfile([rawPath,'.gz']),'Preserve existing unclosed numeric output; inspect/reuse it before resuming');
        reused=n==377;caseSettings=settings;
        if reused
            assert(strcmp(hashfile(plan.reused_case.file),plan.reused_case.sha256));
            assert(strcmp(hashfile(plan.reused_case.binding_file),plan.reused_case.binding_sha256));
            result=jsondecode(fileread(plan.reused_case.file));copyfile(plan.reused_case.file,rawPath);
            inputHash=plan.original_settings_sha256;dispatcherStart=377;numericSeconds=0;
        else
            caseSettings.initialization.seed=identity.initial_rng_before;
            inputPath=fullfile(inputs,sprintf('start-%04d-settings.json',n));
            write_atomic(inputPath,caseSettings);inputHash=hashfile(inputPath);
            dispatcherStart=1;started=tic;
            try
                result=handle(rawPath,"full-start:fig3:1",inputPath);numericSeconds=toc(started);
                assert(strcmp(hashfile(inputPath),inputHash),'Original per-slot input changed during execution');
            catch error
                verify_sources(plan,binding);
                assert(strcmp(hashfile(inputPath),inputHash),'Original per-slot input changed during failed execution');
                assert(strcmp(hashfile(self),plan.wrapper_sha256)&&strcmp(hashfile(planPath),planHash));
                record=struct('original_start',n,'plan_sha256',planHash,'actual_execution_language','matlab',...
                    'source_unchanged_during_run',true,'actual_new_optimizer_executed',true,'reused_prior_actual_case',false,...
                    'execution_error',true,'error_identifier',error.identifier,'error_message',error.message,...
                    'error_stack',{error.stack},'original_convergence_feasibility_verified',false,'full_population_or_reference_pass',false);
                write_atomic(receiptPath,record);records{end+1}=record;write_progress(bank,records,began);continue
            end
        end
        verify_sources(plan,binding);
        assert(strcmp(hashfile(self),plan.wrapper_sha256)&&strcmp(hashfile(planPath),planHash));
        assert(result.start==dispatcherStart&&result.original_number_of_starts==6000);
        rawHash=hashfile(rawPath);compressed=gzip(rawPath);gzPath=compressed{1};
        % Preserve the exact returned JSON bytes while avoiding duplicate raw
        % storage. The temporary decompression is hashed before either raw copy
        % is removed; both generated paths are inside this explicit bank.
        restored=gunzip(gzPath,temporary);verifyPath=restored{1};
        assert(strcmp(hashfile(verifyPath),rawHash),'Lossless native JSON storage verification failed');
        assert(startsWith(canonical(rawPath),[canonical(bank),filesep])&&startsWith(canonical(verifyPath),[canonical(bank),filesep]));
        delete(verifyPath);delete(rawPath);
        z=result.state;phi=complex(z.phi.real(:),z.phi.imag(:));theta=complex(z.theta.real(:),z.theta.imag(:));
        domain=max([abs(abs(phi)-1);abs(abs(theta)-1);abs(sum(z.X,2)-1);0;-z.X(:)])<1e-12;
        binary=result.metrics.eta-result.metrics.min_binary_metric<=settings.feasibility_tolerance;
        feasible=domain&&result.metrics.maximum_constraint<=settings.feasibility_tolerance;
        [~,name,ext]=fileparts(gzPath);
        record=struct('original_start',n,'raw_dispatcher_start',dispatcherStart,'plan_sha256',planHash,...
            'actual_execution_language','matlab','actual_new_optimizer_executed',~reused,'reused_prior_actual_case',reused,...
            'initial_rng_before',identity.initial_rng_before,'initial_rng_after',identity.initial_rng_after,...
            'initializer_draws',881,'exact_original_serial_initialization_preserved',true,'transport_settings_sha256',inputHash,...
            'payload_file',[name,ext],'payload_original_json_sha256',rawHash,'payload_gzip_sha256',hashfile(gzPath),...
            'engine_sha256',plan.engine_sha256,'source_unchanged_during_run',true,'execution_error',false,...
            'original_domain_feasible',domain,'original_eta_binary_feasible',binary,'original_primal_feasible',feasible,...
            'original_convergence_feasibility_verified',logical(feasible&&binary&&result.solver_status.convergence_verified),...
            'actual_solver_status',result.solver_status,'actual_eta',result.metrics.eta,'actual_numeric_seconds',numericSeconds,...
            'full_population_or_reference_pass',false);
        write_atomic(receiptPath,record);
    end
    records{end+1}=record;write_progress(bank,records,began);
end
verify_sources(plan,binding);assert(strcmp(hashfile(self),plan.wrapper_sha256)&&strcmp(hashfile(planPath),planHash));
end

function write_progress(bank,records,began)
passed=sum(cellfun(@(x)x.original_convergence_feasibility_verified,records));
new=sum(cellfun(@(x)x.actual_new_optimizer_executed,records));reused=sum(cellfun(@(x)x.reused_prior_actual_case,records));
errors=sum(cellfun(@(x)x.execution_error,records));last=records{end}.original_start;
progress=struct('expected_starts',6000,'finished',numel(records),'passed_original_gates',passed,...
    'retained_failed_or_unverified',numel(records)-passed,'actual_new_optimizer_starts',new,'actual_old_case_reused',reused,...
    'execution_errors',errors,'last_original_start',last,'elapsed_seconds',toc(began),...
    'full6000_execution_complete',numel(records)==6000,'all6000_original_convergence_pass',numel(records)==6000&&passed==6000,...
    'independent_physics_dual_language_or_reference_pass',false);
write_atomic(fullfile(bank,'progress.json'),progress);fprintf('%s\n',jsonencode(progress));
end

function verify_sources(plan,binding)
for j=1:numel(binding.entries)
    entry=binding.entries(j);assert(strcmp(hashfile(fullfile(plan.frozen_binding_base,entry.relative_path)),entry.sha256),'Frozen scientific/input bytes changed');
end
end

function write_atomic(path,value)
temporary=[path,'.partial'];fid=fopen(temporary,'w','n','UTF-8');assert(fid>=0);
fprintf(fid,'%s',jsonencode(value,'PrettyPrint',true));fclose(fid);
for attempt=1:100
    [ok,~]=movefile(temporary,path,'f');if ok,return;end;pause(.05);
end
error('sensing:checkpointLocked','Atomic saved-state checkpoint remained unavailable');
end

function digest=hashfile(path)
fid=fopen(path,'rb');assert(fid>=0,'Missing source or numerical payload');cleaner=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');
md=java.security.MessageDigest.getInstance('SHA-256');md.update(bytes);raw=typecast(md.digest(),'uint8');digest=lower(reshape(dec2hex(raw,2).',1,[]));
end
function out=canonical(path),out=char(java.io.File(path).getCanonicalPath());end
