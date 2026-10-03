function result=evaluate_correlated_zf_matlab(outputPath,jobPath,sourcePath,configPath)
% ALL accepted unchanged iid-Algorithm2 positions, both exact original models.
[source,job,config,expected]=validate_corrected_zf_source_matlab(jobPath,sourcePath,configPath);
[c,nlos]=corrected_zf_context_matlab(job,config);P=size(source.history.zf.positions,1);records=cell(P,1);started=tic;
names={'iid','correlated'};histories=struct();
for name=names,histories.(name{1})=struct('MC_mean',zeros(P,1),'exact_population_Jensen_plugin',zeros(P,1),'MC_minus_Jensen_plugin',zeros(P,1),...
    'MC_standard_error',zeros(P,1),'Jensen_outer_MC_standard_error_delta_method',zeros(P,1),'Jensen_quadrature_rate_error_estimate_first_order',zeros(P,1));end
for index=1:P
    t=reshape(source.history.zf.positions(index,:,:),job.N,2);record=corrected_zf_position_matlab(t,c,nlos);record.accepted_position_index=index-1;records{index}=record;
    for name=names
        s=record.models.(name{1});h=histories.(name{1});h.MC_mean(index)=s.actual_full1000_MC.mean_sum_rate;h.exact_population_Jensen_plugin(index)=s.exact_original_model_Jensen.sum_rate;
        h.MC_minus_Jensen_plugin(index)=s.MC_minus_population_Jensen_plugin;h.MC_standard_error(index)=s.MC_standard_error_within_geometry;
        h.Jensen_outer_MC_standard_error_delta_method(index)=s.population_Jensen_rate_outer_MC_standard_error_delta_method;
        h.Jensen_quadrature_rate_error_estimate_first_order(index)=s.population_Jensen_rate_quadrature_error_estimate_first_order;histories.(name{1})=h;
    end
end
assert(all(abs(histories.iid.MC_mean-source.history.zf.instantaneous_MC_mean(:))<=1e-9+1e-9*abs(source.history.zf.instantaneous_MC_mean(:))));
assert(all(abs(histories.correlated.MC_mean-source.metrics.correlated_extension.ZF_correlated_MC_history(:))<=1e-9+1e-9*abs(source.metrics.correlated_extension.ZF_correlated_MC_history(:))));
result=struct('paper_id','two-timescale-ma','figure',job.figure,'scope','corrected_original_model_Jensen_bound_not_printed_Eq75','input_fingerprint',expected,...
    'original_trajectory_implementation_fingerprint',source.implementation_fingerprint,'trajectory','unchanged_original_iid_Algorithm2',...
    'same_original_positions',true,'outer_expectation_samples_per_position',1000,'trajectory_positions_evaluated',P,'histories',histories,...
    'records',{records},'accepted_positions',source.history.zf.positions,'all_positions_full1000_MC_match_unchanged_source_receipt',true,...
    'modified_channel_or_Wishart_approximation',false,'printed_Eq74_closed_form_recovered',false,'original_curve_closeness_verified',false,...
    'finite_ensemble_bound_guaranteed',false,'theoretical_population_Jensen_bound_valid',true,...
    'corrected_evaluator_source_sha256',corrected_zf_matlab_fingerprint(),'source_result_sha256',file_digest(sourcePath),'elapsed_seconds',toc(started));
folder=fileparts(outputPath);if ~isempty(folder)&&~isfolder(folder),mkdir(folder);end
fid=fopen(outputPath,'w','n','UTF-8');assert(fid>=0);cleaner=onCleanup(@()fclose(fid));fprintf(fid,'%s',jsonencode(result,'PrettyPrint',true));
end

function value=file_digest(path)
d=java.security.MessageDigest.getInstance('SHA-256');fid=fopen(path,'rb');assert(fid>=0);b=fread(fid,Inf,'*uint8');fclose(fid);d.update(b);raw=typecast(d.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end
