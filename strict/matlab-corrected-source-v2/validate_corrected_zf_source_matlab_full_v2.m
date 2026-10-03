function [source,job,config,expected]=validate_corrected_zf_source_matlab_full_v2(jobPath,sourcePath,configPath)
% Strictly accept actual NEW MATLAB full-v2 source receipts, never old-FP retrofit.
job=jsondecode(fileread(jobPath));config=jsondecode(fileread(configPath));source=jsondecode(fileread(sourcePath));
assert(ismember(job.figure,[14 16])&&job.correlated&&config.geometry_realizations==100&&config.nlos_realizations_per_geometry==1000);
assert(strcmp(source.matlab_source_version,'MATLAB-full-v2-history-storage'));
assert(strcmp(source.implementation_fingerprint,strict_ma_full_v2_implementation_fingerprint(configPath)),'Actual new full-v2 MATLAB source/runtime mismatch');
assert(source.runtime_source_identity.fresh_before_after_not_persistent_cache&&~source.history_container_repair.numeric_updates_changed);
d=java.security.MessageDigest.getInstance('SHA-256');d.update(uint8('strict-v1'));d.update(uint8(0));
for path={configPath,jobPath}
    fid=fopen(path{1},'rb');assert(fid>=0);bytes=fread(fid,Inf,'*uint8');fclose(fid);d.update(bytes);if strcmp(path{1},configPath),d.update(uint8(0));end
end
raw=typecast(d.digest(),'uint8');expected=lower(reshape(dec2hex(raw,2).',1,[]));assert(strcmp(expected,source.input_fingerprint));
assert(isequal(size(job.nlos_re),[1000 job.N job.M])&&isequal(size(job.nlos_im),[1000 job.N job.M]));
assert(source.checks.full_N==job.N&&source.checks.full_M==job.M&&source.checks.nlos_samples==1000);
flags={'mrt_converged','zf_converged','mrt_nominal_design_spacing_feasible','zf_nominal_design_spacing_feasible','mrt_nominal_design_box_feasible','zf_nominal_design_box_feasible',...
    'mrt_realized_positions_spacing_feasible','zf_realized_positions_spacing_feasible','mrt_realized_positions_box_feasible','zf_realized_positions_box_feasible'};
for i=1:numel(flags),assert(source.checks.(flags{i}));end
[c,~]=corrected_zf_context_matlab(job,config);
for mode={'mrt','zf'}
    h=source.history.(mode{1});obj=h.objective;P=numel(obj);assert(P>=2&&all(isfinite(obj))&&all(diff(obj)>=-config.verification_tolerance));
    assert(h.converged&&strcmp(h.termination,'fractional_increase')&&(obj(end)-obj(end-1))/abs(obj(end-1))<config.fractional_increase_threshold,'Original criterion stop not verified');
    assert(isequal(size(h.positions),[P job.N 2])&&numel(h.coordinate_updates)==(P-1)*job.N);
    for position=1:P
        t=reshape(h.positions(position,:,:),job.N,2);assert(all(isfinite(t),'all'));
        distance=sqrt(sum((reshape(t,job.N,1,2)-reshape(t,1,job.N,2)).^2,3))+eye(job.N)*1e9;
        assert(min(distance,[],'all')>=c.minimum_distance-config.verification_tolerance);
        assert(all(t>=c.region_lower(:).'-config.verification_tolerance,'all')&&all(t<=c.region_upper(:).'+config.verification_tolerance,'all'));
    end
    for i=1:numel(h.coordinate_updates)
        u=h.coordinate_updates(i);cert=u.certificate;assert(u.original_subproblem_unchanged&&cert.original_subproblem_unchanged&&cert.certified_without_conic_solver_status);
        assert(u.sweep==floor((i-1)/job.N)&&u.antenna==mod(i-1,job.N));
        vals=[cert.global_objective_gap_upper_bound,cert.global_objective_gap_tolerance,cert.maximum_normalized_constraint_violation,cert.normalized_constraint_tolerance];
        assert(all(isfinite(vals))&&all(vals>=0)&&cert.global_objective_gap_upper_bound<=cert.global_objective_gap_tolerance&&cert.maximum_normalized_constraint_violation<=cert.normalized_constraint_tolerance);
        assert(u.after>=u.before-config.verification_tolerance&&u.lower_bound_gap>=-config.verification_tolerance);
        assert(abs(u.surrogate-u.before-cert.minorant_increment)<=config.verification_tolerance&&abs(u.after-u.surrogate-u.lower_bound_gap)<=config.verification_tolerance);
    end
end
for name={'MA_MRT','MA_ZF','FPA_MRT','FPA_ZF','FPA_OPT'}
    item=source.metrics.schemes.(name{1});assert(numel(item.sample_sum_rates)==1000&&all(isfinite(item.sample_sum_rates))&&abs(mean(item.sample_sum_rates)-item.mean_sum_rate)<=config.verification_tolerance);
    if isfield(item,'nonconverged_samples'),assert(item.nonconverged_samples==0);end
end
P=size(source.history.zf.positions,1);assert(numel(source.history.zf.instantaneous_MC_mean)==P&&all(isfinite(source.history.zf.instantaneous_MC_mean)));
assert(numel(source.metrics.correlated_extension.ZF_correlated_MC_history)==P&&all(isfinite(source.metrics.correlated_extension.ZF_correlated_MC_history)));
for name={'MA_MRT_MC','MA_ZF_MC'}
    item=source.metrics.correlated_extension.(name{1});assert(numel(item.sample_sum_rates)==1000&&all(isfinite(item.sample_sum_rates)));
    assert(abs(mean(item.sample_sum_rates)-item.mean_sum_rate)<=config.verification_tolerance&&numel(item.powers)==1000&&all(isfinite(item.powers)));
end
end
