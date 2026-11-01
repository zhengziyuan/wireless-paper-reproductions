function result=portable_native_entry_v1(jobPath)
% Parameterized fresh-process host only; every scientific provider is unchanged.
job=jsondecode(fileread(jobPath));
assert(strcmp(job.schema,'portable-corrected-native-single-case-job-v1'),'Explicit portable job required');
assert(any(strcmp(job.mode,{'io-only','full8','saved-two-TS','reuse-A088'})),'Explicit one-case mode required');
root=job.source_root;dataDir=job.data_dir;
assert(isfolder(root)&&isfolder(dataDir),'Explicit source and data roots must exist');
assert(strcmp(normal(prefdir),normal(fullfile(dataDir,'prefs'))),'Fresh process-local preference root required');
assert(strcmp(normal(tempdir),normal(fullfile(dataDir,'temp'))),'Fresh process-local temporary root required');
restoredefaultpath;maxNumCompThreads(1);
addpath(fullfile(root,'matlab','base'),'-begin');
addpath(fullfile(root,'matlab','native-candidate'),'-begin');
addpath(fullfile(root,'matlab','native-candidate','timed-transport-v2'),'-begin');
addpath(fullfile(root,'matlab','native-candidate','timed-transport-v3'),'-begin');
addpath(fullfile(root,'matlab','saved'),'-begin');
addpath(fullfile(root,'adapter'),'-begin');
before=check_pins(job.source_pins);
try
    % Pure reversible-codec control. It does not validate any scientific model.
    codecReceipt=strict_satcom_complex_json_transport_selftest_v1();assert(codecReceipt.passed,'Codec control failed');
    codecReceipt.control_is_scientific_acceptance=false;codecReceipt.scientific_algorithm_executed=false;
    export_copy(codecReceipt,fullfile(dataDir,'actual-codec-control.json'),'codecReceipt');
    if strcmp(job.mode,'io-only')
        result=struct('scope','PURE_NATIVE_CODEC_AND_EXPLICIT_PATH_IO_ONLY','source_root',root,'data_dir',dataDir,...
            'actual_scientific_algorithms_executed',0,'actual_new_MC_draws',0,'source_before',{before},...
            'source_after',{check_pins(job.source_pins)},'scientific_PASS',false);
        export_copy(result,fullfile(dataDir,'actual-native-IO-only-result.json'),'result');
        fprintf('PORTABLE_NATIVE_IO_ONLY_RETURNED_NO_SCIENCE\n');return;
    end
    if any(strcmp(job.mode,{'full8','saved-two-TS'}))
        % Use an already installed CVX in this fresh process. No cvx_setup,
        % savepath, cvx_save_prefs, global preference edit, or installation.
        assert(isfolder(job.cvx_root)&&isfile(fullfile(job.cvx_root,'cvx_startup.m')),'Explicit installed CVX required');
        assert(isfile(fullfile(prefdir,'cvx_prefs.mat')),'Explicit configured CVX preferences must be copied process-locally');
        addpath(job.cvx_root,'-begin');
        cvx_startup(true);cvx_solver('SDPT3');
        assert(strcmp(normal(which('cvx_startup')),normal(fullfile(job.cvx_root,'cvx_startup.m'))),'Use exactly the supplied installed CVX');
        % Restore only the staged application entries to the front after CVX.
        addpath(fullfile(root,'matlab','base'),'-begin');
        addpath(fullfile(root,'matlab','native-candidate'),'-begin');
        addpath(fullfile(root,'matlab','native-candidate','timed-transport-v2'),'-begin');
        addpath(fullfile(root,'matlab','native-candidate','timed-transport-v3'),'-begin');
        addpath(fullfile(root,'matlab','saved'),'-begin');
        addpath(fullfile(root,'adapter'),'-begin');
    end
    if strcmp(job.mode,'full8')
        assert(strcmp(normal(which('run_strict_cooperative_final_algorithm3_timed_v3')),normal(fullfile(root,'matlab','native-candidate','timed-transport-v3','run_strict_cooperative_final_algorithm3_timed_v3.m'))),'Exact corrected full8 V3 runner');
        result=run_strict_cooperative_final_algorithm3_timed_v3(job.configuration,fullfile(dataDir,'actual-native-complete-timed-result.json'),'base');
    elseif strcmp(job.mode,'saved-two-TS')
        assert(strcmp(normal(which('strict_satcom_algorithms_only_saved_TS_v1')),normal(fullfile(root,'matlab','saved','strict_satcom_algorithms_only_saved_TS_v1.m'))),'Exact saved-only corrected scientific dispatcher');
        result=run_native_two_TS_saved_input_refresh_v1(job.native_saved_job_path,'execute');
    else
        % Exact saved old6 plus corrected A2 only. Original A host1 is retained
        % by the unchanged assembler; no solver, scenario, or MC is invoked.
        result=assemble_native_A088_saved_two_TS_reuse_v1(job.native_saved_job_path);
        assert(result.original_corrected_A_host_exit_code==1&&~result.original_corrected_A_host_terminal0_claimed,'Never relabel original A host1');
    end
    after=check_pins(job.source_pins);assert(isequal(before,after),'Source interval must close');
    receipt=struct('mode',job.mode,'source_before',{before},'source_after',{after},...
        'entry_returned',true,'recorded_internal_scope_success',result.overall_implemented_scope_success,...
        'actual_natural_host_exit_not_inferred_here',true,'original_A_host1_must_remain_if_reused',true,...
        'independent_math_dual_original_reference_or_paper_PASS',false);
    export_copy(receipt,fullfile(dataDir,'actual-portable-entry-return.json'),'receipt');
    assert(result.overall_implemented_scope_success,'Retain actual failed/capped/unverified scientific outcome');
    fprintf('PORTABLE_NATIVE_SINGLE_CASE_RETURNED mode=%s\n',job.mode);
catch exception
    failure=struct('mode',job.mode,'identifier',exception.identifier,'message',exception.message,...
        'report',getReport(exception,'extended','hyperlinks','off'),'partial_and_raw_outputs_retained',true,...
        'scientific_or_paper_PASS',false);
    export_copy(failure,fullfile(dataDir,'actual-portable-native-exception.json'),'failure');
    rethrow(exception);
end
end

function export_copy(value,path,variableName)
% Preserve raw MATLAB value BEFORE making an encoded JSON copy.
assert(~isfile(path)&&~isfile([path,'.full-result-before-JSON.mat']),'Exclusive new output only');
raw=struct();raw.(variableName)=value;save([path,'.full-result-before-JSON.mat'],'-struct','raw','-v7');
copy=strict_satcom_complex_json_transport_v1('encode',value);
fid=fopen(path,'w');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(copy));
end
function out=check_pins(pins)
out=pins;for k=1:numel(pins),assert(strcmp(sha256(pins(k).path),pins(k).sha256),['Source/input changed: ',pins(k).path]);end
end
function out=normal(path)
out=strrep(path,'\','/');while endsWith(out,'/'),out=out(1:end-1);end
end
function value=sha256(path)
fid=fopen(path,'rb');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(bytes);raw=typecast(digest.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end
