function matlab_synthetic_entry_prepared()
% Synthetic-only entry. An independently reviewed guard must supply paths.
toolDir=getenv('HOTSPOT_STOP_AUDIT_TOOLS');productionDir=getenv('HOTSPOT_STOP_AUDIT_PRODUCTION');
assert(~isempty(toolDir)&&~isempty(productionDir),'reviewed paths required');
assert(strcmpi(which('matlab_synthetic_entry_prepared'),fullfile(toolDir,'matlab_synthetic_entry_prepared.m')),'unexpected entry');
addpath(productionDir,'-begin');
assert(strcmpi(which('strict_hotspot_termination'),fullfile(productionDir,'strict_hotspot_termination.m')),'unexpected production stop source');
names={'test_strict_hotspot_recorded_history_audit','strict_hotspot_recorded_history_audit','strict_hotspot_gradient_norm_audit'};
for k=1:numel(names)
    assert(strcmpi(which(names{k}),fullfile(toolDir,[names{k},'.m'])),'unexpected audit source');
end
test_strict_hotspot_recorded_history_audit();
old=strict_hotspot_termination('relative',[10,9.9999995],20,1e-5);
audit=strict_hotspot_recorded_history_audit([10,9.9999995],1e-5,true);
assert(old.converged&&audit.production_signed_stop_recomputed&&~audit.independent_recorded_stop_and_nondecrease_gate);
old=strict_hotspot_termination('gradient',-1e-9,1,20,1e-6);
audit=strict_hotspot_gradient_norm_audit(-1e-9,1e-6);
assert(old.converged&&audit.production_gradient_stop_recomputed&&~audit.independent_recorded_gradient_gate);
for h={[],10}
    old=strict_hotspot_termination('relative',h{1},20,1e-5);
    audit=strict_hotspot_recorded_history_audit(h{1},1e-5,true);
    assert(~old.converged&&isempty(audit.production_signed_stop_recomputed));
end
fprintf('SYNTHETIC_CASE13_STOP_AUDIT_PASS\n');
end
