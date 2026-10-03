function receipt=replay_cooperative_native_v4_moment_draws_work(statePath,actualResultPath,outputPath)
% Independent read/replay only. No production imports, optimizer, SDP or CVX.
% Exact original randn call nesting and arithmetic ordering. Preserves caller RNG.
% Must run AFTER actual native recording. Synthetic/source inspection is not proof.
assert(~exist(outputPath,'file'),'Fresh replay receipt required');
sourcePath=[mfilename('fullpath'),'.m'];before=bindings({sourcePath,statePath,actualResultPath});
raw=load(statePath,'recordedCases','recordingMetadata');result=jsondecode(fileread(actualResultPath));
assert(numel(raw.recordedCases)==1 && numel(result.results)==1);
caseRecord=raw.recordedCases{1};assert(caseRecord.complete_original_return);
assert(raw.recordingMetadata.adapter_source_unchanged_during_run);
assert(result.source_unchanged_during_run);
assert(strcmpi(result.recording_only_protocol.state_file_sha256(1).sha256,hash_file(statePath)));
record=caseRecord.actual_moment_draw_record;data=record.data;
[J,U,N]=size(data.d_mean);M=size(data.r_mean,2);count=record.actual_count;
assert(count==1000 && caseRecord.configuration.tuned_not_reported.monte_carlo_realizations==1000);
assert(isequal(record.phi,ones(U,M)),'Original moment MC requires the recorded all-one phase');
callerRng=rng;restoreRng=onCleanup(@()rng(callerRng)); %#ok<NASGU>
rng(record.actual_rng_before);seededRng=rng;started=tic;
powers=zeros(J,U);fourths=zeros(J,U);allBitwise=true;maximumError=0;
for realization=1:count
    for u=1:U
        r=data.r_mean(u,:).'+sqrt(data.r_var(u))*independent_cn([M,1]);
        for j=1:J
            G=reshape(data.G_mean(j,u,:,:),N,M)+sqrt(data.G_var(j,u))*independent_cn([N,M]);
            d=reshape(data.d_mean(j,u,:),N,1)+sqrt(data.d_var(j,u))*independent_cn([N,1]);h=d+G*r;
            actual=reshape(record.actual_effective_channels(j,u,:,realization),N,1);
            allBitwise=allBitwise&&isequal(h,actual);maximumError=max(maximumError,max(abs(h-actual)));
            p=sum(abs(h).^2);powers(j,u)=powers(j,u)+p;fourths(j,u)=fourths(j,u)+p^2;
        end
    end
end
finalRng=rng;second=abs(powers/count-record.actual_analytic_second_moments)./record.actual_analytic_second_moments;
fourth=abs(fourths/count-record.actual_analytic_fourth_moments)./record.actual_analytic_fourth_moments;
entry=result.results(1);mc=entry.monte_carlo;
checks=struct('all1000_actual_effective_channels_bitwise_replayed',allBitwise, ...
    'actual_saved_rng_before_restored_exactly',isequal(seededRng,record.actual_rng_before), ...
    'actual_saved_rng_after_replayed_exactly',isequal(finalRng,record.actual_rng_after), ...
    'original_accumulated_second_powers_bitwise',isequal(powers,record.actual_accumulated_second_powers), ...
    'original_accumulated_fourth_powers_bitwise',isequal(fourths,record.actual_accumulated_fourth_powers), ...
    'reported_second_MC_error_exact',isequal(max(second(:)),mc.second_moment_max_relative_error), ...
    'reported_fourth_MC_error_exact',isequal(max(fourth(:)),mc.fourth_moment_max_relative_error), ...
    'same_original1000_count',count==mc.count&&count==1000);
after=bindings({sourcePath,statePath,actualResultPath});
checks.input_and_replay_source_unchanged_during_run=isequal(before,after);
receipt=struct('scope','ACTUAL_native_v4_independent_rng_replay_of_original1000_moment_draws_NOT_optimization_or_performance_MC', ...
    'actual_native_saved_states_sha256',hash_file(statePath),'actual_native_result_sha256',hash_file(actualResultPath), ...
    'replay_source_and_inputs_before',{before},'replay_source_and_inputs_after',{after}, ...
    'checks',checks,'all_actual_native_rng_replay_checks_pass',all(structfun(@(x)isequal(x,true),checks)), ...
    'original_rng_type',record.actual_rng_before.Type,'actual_draw_count',count, ...
    'maximum_actual_effective_channel_replay_error',maximumError, ...
    'independent_phase_or_QT_audit_complete',false,'full183_or_historical_reproduction_pass',false, ...
    'actual_seconds',toc(started));
fid=fopen(outputPath,'w');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(receipt));
fprintf('Native v4 original1000 independent replay pass=%d\n',receipt.all_actual_native_rng_replay_checks_pass);
end
function out=independent_cn(shape)
out=(randn(shape)+1i*randn(shape))/sqrt(2);
end
function out=bindings(paths)
out=cell(size(paths));for k=1:numel(paths)
    [~,name,extension]=fileparts(paths{k});out{k}=struct('filename',[name,extension],'sha256',hash_file(paths{k}));
end
end
function value=hash_file(path)
fid=fopen(path,'rb');assert(fid>=0);bytes=fread(fid,Inf,'*uint8');fclose(fid);
md=java.security.MessageDigest.getInstance('SHA-256');md.update(bytes);
value=lower(reshape(dec2hex(typecast(md.digest(),'uint8'),2).',1,[]));
end
