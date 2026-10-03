function [phi,W,history,status,diagnostics,endpoints]=strict_instantaneous_ao_guarded(direct,R,nhu,phi0,W0,noise,power,target,normals,maxIterations,tolerance)
% Original AO/QT/SDR chain with independently checked post-rounding upper gate.
phi=phi0;W=W0;hu=strict_hotspot_core('effective',direct,R,phi);e=strict_hotspot_core('evaluate',hu,nhu,W,noise);history=e.hu_sum_rate;diagnostics={};endpoints=struct();
assert(numel(normals)>=maxIterations,'Supply all original draws for every allowed AO iteration');
for it=1:maxIterations
    [W,active]=strict_hotspot_core('active_qt_update',hu,nhu,W,noise,power,target);
    received=hu*W;U=size(hu,1);desired=diag(received(:,1:U));a=desired./(sum(abs(received).^2,2)-abs(desired).^2+noise);
    clock=tic;[phi,phase]=strict_instantaneous_sdr_guard(direct,R,phi,W,a,noise,normals{it});phase.solver_diagnostics.phase_cpu_seconds=toc(clock);
    diagnostics{end+1}=struct('active',active.solver_diagnostics,'phase',phase.solver_diagnostics); %#ok<AGROW>
    hu=strict_hotspot_core('effective',direct,R,phi);e=strict_hotspot_core('evaluate',hu,nhu,W,noise);value=e.hu_sum_rate;
    assert(value>=history(end)-1e-5,'Original AO objective decreased beyond unchanged numerical gate');history(end+1)=value; %#ok<AGROW>
    if any(it==[20,100]),endpoints.(sprintf('AO%d',it))=struct('evaluation',e,'executed_outer_iterations',it,'requested_outer_budget',it,'interpretation','reported_fixed_budget_endpoint_NOT_stationarity_claim','solver_diagnostics',{diagnostics});end
    if (history(end)-history(end-1))/max(abs(history(end-1)),1e-12)<tolerance,break;end
end
status=strict_hotspot_termination('relative',history,maxIterations,tolerance);
for budget=[20,100]
    name=sprintf('AO%d',budget);
    if ~isfield(endpoints,name)&&numel(history)-1<budget&&status.converged
        endpoints.(name)=struct('evaluation',e,'executed_outer_iterations',numel(history)-1,'requested_outer_budget',budget,'interpretation','original_relative_stop_reached_before_reported_budget_NO_trace_padding','solver_diagnostics',{diagnostics});
    end
end
end
