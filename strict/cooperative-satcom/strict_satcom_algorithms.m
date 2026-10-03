function outputs=strict_satcom_algorithms(data,settings,powerLimit,interferenceLimit)
% All eight author/thesis algorithm chains, unrestricted J-by-U MR powers.
[J,U,~]=size(data.d_mean); M=size(data.r_mean,2); phi=exp(1i*settings.initial_phase_radians)*ones(U,M);
[W0,h0,s0]=ap_no_ris(data,phi,powerLimit,interferenceLimit,settings);
[apPhi,W,hap,sap]=ap_ao(data,phi,W0,powerLimit,interferenceLimit,settings);
[mu,C,~,~,off]=strict_satcom_models('moments',data,apPhi);
ap=strict_satcom_core('ap_evaluate',W,mu,C,data.gt_second,off);
[mu,C,~,~,off]=strict_satcom_models('moments',data,phi,true);
base=strict_satcom_core('ap_evaluate',W0,mu,C,data.gt_second,off);
outputs=struct('scheme',{},'evaluation',{},'history',{},'status',{});
outputs(1)=struct('scheme','AP-NoRIS','evaluation',base,'history',h0,'status',s0);
outputs(2)=struct('scheme','AP-AO','evaluation',ap,'history',hap,'status',sap);
for tts=[false,true]
    if tts, prefix='MR-TTS'; else, prefix='MR-S'; end
    coef0=strict_satcom_models('mr_components',data,phi,tts,true);
    pinit=mr_initial(coef0,powerLimit,interferenceLimit); [p0,h,stop]=mr_power(coef0,pinit,powerLimit,interferenceLimit,settings);
    outputs(end+1)=struct('scheme',[prefix,'-NoRIS'],'evaluation',mr_evaluate(p0,coef0),'history',h,'status',stop); %#ok<AGROW>
    coef=strict_satcom_models('mr_components',data,apPhi,tts);
    [p,h,stop]=mr_power(coef,p0,powerLimit,interferenceLimit,settings); stop.phase_source_converged=sap.converged;stop.algorithm_success=stop.algorithm_success&&sap.algorithm_success;
    outputs(end+1)=struct('scheme',[prefix,'-PA'],'evaluation',mr_evaluate(p,coef),'history',h,'status',stop); %#ok<AGROW>
    [tsPhi,p,h,stop]=mr_two_stage(data,phi,p0,powerLimit,interferenceLimit,settings,tts);
    coef=strict_satcom_models('mr_components',data,tsPhi,tts);
    outputs(end+1)=struct('scheme',[prefix,'-TS'],'evaluation',mr_evaluate(p,coef),'history',h,'status',stop); %#ok<AGROW>
end
end

function e=mr_evaluate(p,c)
e=strict_satcom_core('mr_evaluate',p,c.signal,c.cross,c.power,c.leak,c.offset);
end

function p=mr_initial(c,powerLimit,interferenceLimit)
p=ones(size(c.power)); scale=1;
for j=1:size(p,1), scale=min(scale,powerLimit(j)/sum(c.power(j,:))); end
for k=1:size(c.leak,3)
    total=sum(sum(c.leak(:,:,k))); if total>0, scale=min(scale,interferenceLimit(k)/total); end
end
p=p*scale*0.95;
end

function [p,history,status]=mr_power(c,p,powerLimit,interferenceLimit,s)
scale=1;
for j=1:size(p,1), total=sum(p(j,:).*c.power(j,:)); if total>0, scale=min(scale,powerLimit(j)/total); end, end
for k=1:size(c.leak,3), total=sum(sum(p.*c.leak(:,:,k))); if total>0, scale=min(scale,interferenceLimit(k)/total); end, end
p=p*scale; % Only restore warm-start feasibility; J*U powers remain free.
e=mr_evaluate(p,c); history=min(e.sinr);records={};
for it=1:s.qt_max_iterations
    [candidate,info]=strict_satcom_core('mr_qt_update',p,c.signal,c.cross,c.power,c.leak,c.offset,powerLimit,interferenceLimit);
    records{end+1}=solver_record(info); %#ok<AGROW>
    value=min(info.after.sinr); assert(value>=history(end)-s.solver_objective_tolerance,'MR QT monotonicity failure');
    p=candidate; history(end+1)=value; %#ok<AGROW>
    if (value-history(end-1))/max(abs(history(end-1)),1e-12)<s.relative_tolerance, break; end
end
status=scheme_status({relative_stop(history,s.qt_max_iterations,s.relative_tolerance)},records,s);
end

function [phi,history,status]=rmo(phi,fg,s,vectorObjective,increment)
[value,g]=fg(phi); history=min(value);
if vectorObjective,initialSlope=sum(abs(g).^2,2);else,initialSlope=sum(abs(g(:)).^2);end
seed=1./sqrt(max(initialSlope,realmin));
for it=1:s.rmo_max_iterations
    if norm(g(:))<s.gradient_tolerance, break; end
    if vectorObjective, slope=sum(abs(g).^2,2); else, slope=sum(abs(g(:)).^2); end
    alpha=seed;accepted=false;
    if vectorObjective
        stationary=sqrt(slope)<s.gradient_tolerance/sqrt(numel(slope));alpha(stationary)=0;slope(stationary)=0;
    end
    for search=1:60
        candidate=phi+alpha.*g; candidate=candidate./abs(candidate); [trial,newg]=fg(candidate);
        if vectorObjective,candidate(stationary,:)=phi(stationary,:);[trial,newg]=fg(candidate);end
        if nargin<5,difference=trial-value;else,difference=increment(phi,candidate);end
        failed=difference<1e-4*alpha.*slope;
        if ~any(failed), accepted=true; break; end
        if vectorObjective,alpha(failed)=alpha(failed)/2;else,alpha=alpha/2;end
    end
    assert(accepted,'Original RGD Armijo search failed');
    step=angle(conj(phi).*candidate);oldTheta=real(conj(1i*phi).*g);newTheta=real(conj(1i*candidate).*newg);
    if vectorObjective
        curvature=sum(step.*(oldTheta-newTheta),2);distance=sum(step.^2,2);seed=2*alpha;positive=curvature>0&distance>0;seed(positive)=distance(positive)./curvature(positive);
    else
        curvature=sum(sum(step.*(oldTheta-newTheta)));distance=sum(step(:).^2);if curvature>0&&distance>0,seed=distance/curvature;else,seed=2*alpha;end
    end
    seed=min(max(seed,1e-12),1e12);
    improvement=min(trial)-min(value); phi=candidate; value=trial; g=newg; history(end+1)=min(value); %#ok<AGROW>
end
status=gradient_stop(norm(g(:)),numel(history)-1,s.rmo_max_iterations,s.gradient_tolerance);
status.initial_step_contract='positive_BB_seed_in_original_RGD_direction_before_original_Armijo; no gradient-threshold relaxation';
if nargin>=5,status.objective_increment_contract='exact_original_moment_polynomial_ratio_logsumexp_increment';else,status.objective_increment_contract='direct_objective_difference';end
end

function [W,history,status]=ap_no_ris(data,phi,powerLimit,interferenceLimit,s)
[mu,C,~,~,off]=strict_satcom_models('moments',data,phi,true); W=permute(mu,[1,3,2]); scale=1;
[J,N,U]=size(W);
for j=1:J, block=reshape(W(j,:,:),N,U); scale=min(scale,sqrt(powerLimit(j)/sum(abs(block(:)).^2))); end
for k=1:size(data.gt_second,2)
    leak=0;
    for j=1:J, for u=1:U, w=reshape(W(j,:,u),N,1); leak=leak+real(w'*reshape(data.gt_second(j,k,:,:),N,N)*w); end, end
    if leak>0, scale=min(scale,sqrt(interferenceLimit(k)/leak)); end
end
W=W.*(scale*0.95); e=strict_satcom_core('ap_evaluate',W,mu,C,data.gt_second,off); history=min(e.sinr);records={};
for it=1:s.qt_max_iterations
    [W,info]=strict_satcom_core('ap_qt_update',W,mu,C,data.gt_second,off,powerLimit,interferenceLimit);
    records{end+1}=solver_record(info); %#ok<AGROW>
    value=min(info.after.sinr); history(end+1)=value; %#ok<AGROW>
    assert(value>=history(end-1)-s.solver_objective_tolerance,'AP QT monotonicity failure');
    if (value-history(end-1))/max(abs(history(end-1)),1e-12)<s.relative_tolerance, break; end
end
status=scheme_status({relative_stop(history,s.qt_max_iterations,s.relative_tolerance)},records,s);
end

function [phi,W,history,status]=ap_ao(data,phi,W,powerLimit,interferenceLimit,s)
[mu,C,~,~,off]=strict_satcom_models('moments',data,phi); e=strict_satcom_core('ap_evaluate',W,mu,C,data.gt_second,off); history=min(e.sinr);records={};stops={};
for it=1:s.ao_max_iterations
    [W,info]=strict_satcom_core('ap_qt_update',W,mu,C,data.gt_second,off,powerLimit,interferenceLimit);records{end+1}=solver_record(info); %#ok<AGROW>
    fg=@(x) strict_satcom_models('ap_phase',data,x,W);increment=@(a,b)strict_satcom_increments('ap',data,a,b,W);[phi,~,stop]=rmo(phi,fg,s,true,increment);stops{end+1}=stop; %#ok<AGROW>
    [mu,C,~,~,off]=strict_satcom_models('moments',data,phi); e=strict_satcom_core('ap_evaluate',W,mu,C,data.gt_second,off); value=min(e.sinr);
    assert(value>=history(end)-s.solver_objective_tolerance,'AP-AO monotonicity failure'); history(end+1)=value; %#ok<AGROW>
    if (value-history(end-1))/max(abs(history(end-1)),1e-12)<s.relative_tolerance, break; end
end
stops{end+1}=relative_stop(history,s.ao_max_iterations,s.relative_tolerance);status=scheme_status(stops,records,s);
end

function [phi,p,history,status]=mr_two_stage(data,phi,p0,powerLimit,interferenceLimit,s,tts)
mu=s.smoothing_initial; phases=struct('mu',{},'objective',{});stops={};
while mu>=s.smoothing_final
    fg=@(x) strict_satcom_models('mr_phase',data,x,p0,mu,interferenceLimit,tts); stopped=false;
    for inner=1:s.smoothing_max_repeats
        before=fg(phi);increment=@(a,b)strict_satcom_increments('mr',data,a,b,p0,mu,interferenceLimit,tts);[phi,h,stop]=rmo(phi,fg,s,false,increment);stops{end+1}=stop;phases(end+1)=struct('mu',mu,'objective',h); %#ok<AGROW>
        if h(end)-before<=s.smoothing_progress_tolerance, stopped=true; break; end
    end
    assert(stopped,'Smoothing repeat cap reached while improving'); mu=mu/2;
end
c=strict_satcom_models('mr_components',data,phi,tts); [p,h,pstatus]=mr_power(c,p0,powerLimit,interferenceLimit,s);
history=struct('phase',phases,'power',h);
status=scheme_status([stops,pstatus.blocks],pstatus.solver_diagnostics,s);status.smoothing_schedule_completed=mu<s.smoothing_final;
end

function out=relative_stop(history,cap,tolerance)
residual=[];if numel(history)>=2,residual=(history(end)-history(end-1))/max(abs(history(end-1)),1e-12);end
done=~isempty(residual)&&isfinite(residual)&&isfinite(tolerance)&&tolerance>0&&residual<tolerance;reason='configured_iteration_cap';if done,reason='relative_improvement';end
out=struct('converged',done,'termination',reason,'iterations',numel(history)-1,'iteration_cap',cap,'stop_rule','signed_relative_objective_increase','threshold',tolerance,'final_residual',residual);
end
function out=gradient_stop(value,iterations,cap,tolerance)
done=isfinite(value)&&isfinite(tolerance)&&tolerance>0&&value<tolerance;reason='configured_iteration_cap';if done,reason='gradient_tolerance';end
out=struct('converged',done,'termination',reason,'iterations',iterations,'iteration_cap',cap,'stop_rule','Riemannian_gradient_norm','threshold',tolerance,'final_residual',value);
end
function out=solver_record(info)
out=struct('solver_diagnostics',info.solver_diagnostics,'qt_bound_max_violation',info.qt_bound_max_violation);
end
function out=scheme_status(stops,records,s)
converged=~isempty(stops)&&all(cellfun(@stop_valid,stops));primal=0;bound=0;primalValid=~isempty(records);boundValid=~isempty(records);
for k=1:numel(records)
    r=records{k};valid=isfield(r,'solver_diagnostics')&&isfield(r.solver_diagnostics,'constraint_max_relative_violation');
    if valid,v=r.solver_diagnostics.constraint_max_relative_violation;valid=isscalar(v)&&isfinite(v)&&v>=0;if valid,primal=max(primal,v);end,end
    primalValid=primalValid&&valid;valid=isfield(r,'qt_bound_max_violation');
    if valid,v=r.qt_bound_max_violation;valid=isscalar(v)&&isfinite(v)&&v>=0;if valid,bound=max(bound,v);end,end
    boundValid=boundValid&&valid;
end
ptol=1e-5;btol=1e-5;if isfield(s,'solver_primal_relative_tolerance'),ptol=s.solver_primal_relative_tolerance;end;if isfield(s,'qt_bound_tolerance'),btol=s.qt_bound_tolerance;end
numerical=struct('solver_primal_pass',primalValid&&isfinite(ptol)&&ptol>0&&primal<=ptol,'qt_bound_pass',boundValid&&isfinite(btol)&&btol>0&&bound<=btol,'solver_primal_relative_tolerance',ptol,'qt_bound_tolerance',btol,'maximum_primal_relative_violation',primal,'maximum_qt_bound_violation',bound);
reason='one_or_more_configured_caps';if converged,reason='all_original_stop_rules_reached';end
out=struct('converged',converged,'termination',reason,'blocks',{stops},'numerical',numerical,'solver_diagnostics',{records},'algorithm_success',converged&&numerical.solver_primal_pass&&numerical.qt_bound_pass);
end
function valid=stop_valid(s)
valid=isfield(s,'converged')&&isequal(s.converged,true)&&isfield(s,'final_residual')&&isfield(s,'threshold')&&isfield(s,'stop_rule');
if ~valid,return;end
v=s.final_residual;t=s.threshold;valid=isscalar(v)&&isfinite(v)&&isscalar(t)&&isfinite(t)&&t>0&&v<t&&any(strcmp(s.stop_rule,{'signed_relative_objective_increase','Riemannian_gradient_norm'}));
end
