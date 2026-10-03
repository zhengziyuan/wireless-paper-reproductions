function [source,job,config,expected]=validate_corrected_zf_source_matlab(jobPath,sourcePath,configPath)
% Explicit full original-source receipt validation; no solver-status-only reuse.
job=jsondecode(fileread(jobPath));config=jsondecode(fileread(configPath));source=jsondecode(fileread(sourcePath));
assert(ismember(job.figure,[14 16])&&job.correlated&&config.geometry_realizations==100&&config.nlos_realizations_per_geometry==1000);
assert(strcmp(source.implementation_fingerprint,strict_ma_implementation_fingerprint()),'Frozen MATLAB source/runtime mismatch');
d=java.security.MessageDigest.getInstance('SHA-256');d.update(uint8('strict-v1'));d.update(uint8(0));
for path={configPath,jobPath}
    fid=fopen(path{1},'rb');assert(fid>=0);bytes=fread(fid,Inf,'*uint8');fclose(fid);d.update(bytes);if strcmp(path{1},configPath),d.update(uint8(0));end
end
raw=typecast(d.digest(),'uint8');expected=lower(reshape(dec2hex(raw,2).',1,[]));assert(strcmp(expected,source.input_fingerprint));
flags={'mrt_converged','zf_converged','mrt_nominal_design_spacing_feasible','zf_nominal_design_spacing_feasible','mrt_nominal_design_box_feasible','zf_nominal_design_box_feasible'};
for i=1:numel(flags),assert(source.checks.(flags{i}));end
for mode={'mrt','zf'}
    updates=source.history.(mode{1}).coordinate_updates;assert(~isempty(updates));
    for i=1:numel(updates)
        u=updates(i);cert=u.certificate;assert(u.original_subproblem_unchanged&&cert.certified_without_conic_solver_status);
        assert(isfinite(cert.global_objective_gap_upper_bound)&&cert.global_objective_gap_upper_bound>=0&&cert.global_objective_gap_upper_bound<=cert.global_objective_gap_tolerance);
        assert(isfinite(cert.maximum_normalized_constraint_violation)&&cert.maximum_normalized_constraint_violation>=0&&cert.maximum_normalized_constraint_violation<=cert.normalized_constraint_tolerance);
    end
end
for name={'MA_MRT','MA_ZF','FPA_MRT','FPA_ZF','FPA_OPT'}
    item=source.metrics.schemes.(name{1});assert(numel(item.sample_sum_rates)==1000&&all(isfinite(item.sample_sum_rates)));
    if isfield(item,'nonconverged_samples'),assert(item.nonconverged_samples==0);end
end
P=size(source.history.zf.positions,1);assert(P>=2&&numel(source.history.zf.objective)==P&&size(source.history.zf.positions,2)==job.N&&size(source.history.zf.positions,3)==2);
assert(numel(source.history.zf.instantaneous_MC_mean)==P&&numel(source.metrics.correlated_extension.ZF_correlated_MC_history)==P);
for name={'MA_MRT_MC','MA_ZF_MC'},item=source.metrics.correlated_extension.(name{1});assert(numel(item.sample_sum_rates)==1000&&all(isfinite(item.sample_sum_rates)));end
end
