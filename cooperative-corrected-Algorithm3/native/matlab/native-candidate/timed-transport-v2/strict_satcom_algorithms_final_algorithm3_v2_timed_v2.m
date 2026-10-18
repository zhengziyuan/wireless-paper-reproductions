function [outputs,measuredClocks]=strict_satcom_algorithms_final_algorithm3_v2_timed_v2(data,settings,powerLimit,interferenceLimit)
% Prospective v3 same eight chains: exact circle/softmin increments; original RGD and gates.
componentClocks=struct('component',{},'scheme',{},'wall_seconds',{},'process_CPU_seconds',{},'include_in_method_numerical_total',{},'scope',{});
componentWall=tic;componentCPU=cputime;
[J,U,~]=size(data.d_mean); M=size(data.r_mean,2); phi=exp(1i*settings.initial_phase_radians)*ones(U,M);
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','shared_dimensions_initial_phase','scheme','shared','wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',true,'scope','shared_initialization_numeric');
componentWall=tic;componentCPU=cputime;
[W0,h0,s0]=ap_no_ris(data,phi,powerLimit,interferenceLimit,settings);
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','AP0_optimizer','scheme','AP-NoRIS','wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',true,'scope','optimizer_including_internal_QT_recording');
componentWall=tic;componentCPU=cputime;
[apPhi,W,hap,sap]=ap_ao(data,phi,W0,powerLimit,interferenceLimit,settings);
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','APAO_optimizer','scheme','AP-AO','wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',true,'scope','optimizer_including_internal_phase_QT_recording');
componentWall=tic;componentCPU=cputime;
[mu,C,~,~,off]=strict_satcom_models('moments',data,apPhi);
ap=strict_satcom_core_v3('ap_evaluate',W,mu,C,data.gt_second,off);
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','APAO_final_moments_evaluation','scheme','AP-AO','wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',true,'scope','outer_final_moments_and_evaluation');
componentWall=tic;componentCPU=cputime;
[mu,C,~,~,off]=strict_satcom_models('moments',data,phi,true);
base=strict_satcom_core_v3('ap_evaluate',W0,mu,C,data.gt_second,off);
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','AP0_delayed_final_moments_evaluation','scheme','AP-NoRIS','wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',true,'scope','outer_final_moments_and_evaluation_preserved_after_APAO');
componentWall=tic;componentCPU=cputime;
outputs=struct('scheme',{},'evaluation',{},'history',{},'status',{});
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','framework_output_schema','scheme','framework','wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',false,'scope','outer_output_metadata');
componentWall=tic;componentCPU=cputime;
outputs(1)=struct('scheme','AP-NoRIS','evaluation',base,'history',h0,'status',s0);
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','AP0_output_metadata','scheme','AP-NoRIS','wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',false,'scope','outer_output_metadata_no_new_evaluation');
componentWall=tic;componentCPU=cputime;
strict_satcom_capture('final',struct('scheme','AP-NoRIS','W',W0,'p',[],'phi',phi,'no_ris',true));
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','AP0_final_capture','scheme','AP-NoRIS','wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',false,'scope','separate_outer_final_state_capture');
componentWall=tic;componentCPU=cputime;
outputs(2)=struct('scheme','AP-AO','evaluation',ap,'history',hap,'status',sap);
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','APAO_output_metadata','scheme','AP-AO','wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',false,'scope','outer_output_metadata_no_new_evaluation');
componentWall=tic;componentCPU=cputime;
strict_satcom_capture('final',struct('scheme','AP-AO','W',W,'p',[],'phi',apPhi,'no_ris',false));
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','APAO_final_capture','scheme','AP-AO','wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',false,'scope','separate_outer_final_state_capture');
for tts=[false,true]
    componentWall=tic;componentCPU=cputime;
if tts, prefix='MR-TTS'; else, prefix='MR-S'; end
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','MR_prefix_metadata','scheme','framework','wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',false,'scope','outer_scheme_name_metadata');
    componentWall=tic;componentCPU=cputime;
coef0=strict_satcom_models('mr_components',data,phi,tts,true);
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','MR_NoRIS_coefficients','scheme',[prefix,'-NoRIS'],'wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',true,'scope','outer_coefficient_assembly');
    componentWall=tic;componentCPU=cputime;
pinit=mr_initial(coef0,powerLimit,interferenceLimit);
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','MR_NoRIS_initial_power','scheme',[prefix,'-NoRIS'],'wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',true,'scope','outer_power_initialization'); componentWall=tic;componentCPU=cputime;
[p0,h,stop]=mr_power(coef0,pinit,powerLimit,interferenceLimit,settings);
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','MR_NoRIS_optimizer','scheme',[prefix,'-NoRIS'],'wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',true,'scope','optimizer_including_internal_QT_recording');
    componentWall=tic;componentCPU=cputime;
outputs(end+1)=struct('scheme',[prefix,'-NoRIS'],'evaluation',mr_evaluate(p0,coef0),'history',h,'status',stop); %#ok<AGROW>
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','MR_NoRIS_final_eval_embedded_metadata','scheme',[prefix,'-NoRIS'],'wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',true,'scope','final_evaluation_with_unchanged_embedded_output_metadata');
componentWall=tic;componentCPU=cputime;
strict_satcom_capture('final',struct('scheme',[prefix,'-NoRIS'],'W',[],'p',p0,'phi',phi,'no_ris',true));
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','MR_NoRIS_final_capture','scheme',[prefix,'-NoRIS'],'wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',false,'scope','separate_outer_final_state_capture');
    componentWall=tic;componentCPU=cputime;
coef=strict_satcom_models('mr_components',data,apPhi,tts);
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','MR_PA_coefficients','scheme',[prefix,'-PA'],'wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',true,'scope','outer_coefficient_assembly');
    componentWall=tic;componentCPU=cputime;
[p,h,stop]=mr_power(coef,p0,powerLimit,interferenceLimit,settings);
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','MR_PA_optimizer','scheme',[prefix,'-PA'],'wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',true,'scope','optimizer_including_internal_QT_recording'); componentWall=tic;componentCPU=cputime;
stop.phase_source_converged=sap.converged;stop.algorithm_success=stop.algorithm_success&&sap.algorithm_success;
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','MR_PA_phase_source_status','scheme',[prefix,'-PA'],'wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',true,'scope','unchanged_phase_source_success_propagation');
    componentWall=tic;componentCPU=cputime;
outputs(end+1)=struct('scheme',[prefix,'-PA'],'evaluation',mr_evaluate(p,coef),'history',h,'status',stop); %#ok<AGROW>
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','MR_PA_final_eval_embedded_metadata','scheme',[prefix,'-PA'],'wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',true,'scope','final_evaluation_with_unchanged_embedded_output_metadata');
componentWall=tic;componentCPU=cputime;
strict_satcom_capture('final',struct('scheme',[prefix,'-PA'],'W',[],'p',p,'phi',apPhi,'no_ris',false));
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','MR_PA_final_capture','scheme',[prefix,'-PA'],'wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',false,'scope','separate_outer_final_state_capture');
    componentWall=tic;componentCPU=cputime;
[tsPhi,p,h,stop]=mr_two_stage(data,phi,p0,powerLimit,interferenceLimit,settings,tts);
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','MR_TS_complete_optimizer','scheme',[prefix,'-TS'],'wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',true,'scope','complete_P9_P7_smoothing_final_power_with_internal_recording_no_nested_timer');
    componentWall=tic;componentCPU=cputime;
coef=strict_satcom_models('mr_components',data,tsPhi,tts);
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','MR_TS_final_coefficients','scheme',[prefix,'-TS'],'wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',true,'scope','outer_final_coefficient_assembly');
    componentWall=tic;componentCPU=cputime;
outputs(end+1)=struct('scheme',[prefix,'-TS'],'evaluation',mr_evaluate(p,coef),'history',h,'status',stop); %#ok<AGROW>
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','MR_TS_final_eval_embedded_metadata','scheme',[prefix,'-TS'],'wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',true,'scope','final_evaluation_with_unchanged_embedded_output_metadata');
componentWall=tic;componentCPU=cputime;
strict_satcom_capture('final',struct('scheme',[prefix,'-TS'],'W',[],'p',p,'phi',tsPhi,'no_ris',false));
componentCPUSeconds=cputime-componentCPU;componentWallSeconds=toc(componentWall);
componentClocks(end+1)=struct('component','MR_TS_final_capture','scheme',[prefix,'-TS'],'wall_seconds',componentWallSeconds,'process_CPU_seconds',componentCPUSeconds,'include_in_method_numerical_total',false,'scope','separate_outer_final_state_capture');
end
clockSchemes={'AP-NoRIS','AP-AO','MR-S-NoRIS','MR-S-PA','MR-S-TS','MR-TTS-NoRIS','MR-TTS-PA','MR-TTS-TS'};
clockDependencies={{'AP-NoRIS'},{'AP-NoRIS','AP-AO'},{'MR-S-NoRIS'},{'AP-NoRIS','AP-AO','MR-S-NoRIS','MR-S-PA'},{'MR-S-NoRIS','MR-S-TS'},{'MR-TTS-NoRIS'},{'AP-NoRIS','AP-AO','MR-TTS-NoRIS','MR-TTS-PA'},{'MR-TTS-NoRIS','MR-TTS-TS'}};
clockMethods=struct('scheme',{},'own_numerical_wall_seconds',{},'own_numerical_process_CPU_seconds',{},'shared_initialization_wall_seconds',{},'shared_initialization_process_CPU_seconds',{},'complete_own_plus_shared_wall_component_sum',{},'complete_own_plus_shared_CPU_component_sum',{},'dependency_inclusive_wall_component_sum',{},'dependency_inclusive_CPU_component_sum',{},'included_dependency_schemes',{});
clockNumeric=[componentClocks.include_in_method_numerical_total];clockAttribution={componentClocks.scheme};
clockShared=clockNumeric&strcmp(clockAttribution,'shared');clockSharedWall=sum([componentClocks(clockShared).wall_seconds]);clockSharedCPU=sum([componentClocks(clockShared).process_CPU_seconds]);
for clockIndex=1:numel(clockSchemes)
    clockOwn=clockNumeric&strcmp(clockAttribution,clockSchemes{clockIndex});clockDependencyMask=clockShared;
    for clockDependencyIndex=1:numel(clockDependencies{clockIndex}),clockDependencyMask=clockDependencyMask|(clockNumeric&strcmp(clockAttribution,clockDependencies{clockIndex}{clockDependencyIndex}));end
    clockOwnWall=sum([componentClocks(clockOwn).wall_seconds]);clockOwnCPU=sum([componentClocks(clockOwn).process_CPU_seconds]);
    clockMethods(end+1)=struct('scheme',clockSchemes{clockIndex},'own_numerical_wall_seconds',clockOwnWall,'own_numerical_process_CPU_seconds',clockOwnCPU,'shared_initialization_wall_seconds',clockSharedWall,'shared_initialization_process_CPU_seconds',clockSharedCPU,'complete_own_plus_shared_wall_component_sum',clockOwnWall+clockSharedWall,'complete_own_plus_shared_CPU_component_sum',clockOwnCPU+clockSharedCPU,'dependency_inclusive_wall_component_sum',sum([componentClocks(clockDependencyMask).wall_seconds]),'dependency_inclusive_CPU_component_sum',sum([componentClocks(clockDependencyMask).process_CPU_seconds]),'included_dependency_schemes',{clockDependencies{clockIndex}}); %#ok<AGROW>
end
measuredClocks=struct('schema','disjoint_complete_top_level_components_v2','components',componentClocks,'methods',clockMethods,'same_scientific_statement_order',true,'original_internal_capture_overhead_in_optimizer_spans',true,'outer_capture_separate',true,'component_sums_are_not_direct_cold_standalone_wall_measurements',true,'scientific_or_author_historical_timing_pass',false);
end

function e=mr_evaluate(p,c)
e=strict_satcom_core_v3('mr_evaluate',p,c.signal,c.cross,c.power,c.leak,c.offset);
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
    [candidate,info]=strict_satcom_qt_guard_v3('mr',p,c.signal,c.cross,c.power,c.leak,c.offset,powerLimit,interferenceLimit);
    records{end+1}=solver_record(info); %#ok<AGROW>
    value=min(info.after.sinr); assert(value>=history(end)-s.solver_objective_tolerance,'MR QT monotonicity failure');
    p=candidate; history(end+1)=value; %#ok<AGROW>
    if (value-history(end-1))/max(abs(history(end-1)),1e-12)<s.relative_tolerance, break; end
end
status=scheme_status({relative_stop(history,s.qt_max_iterations,s.relative_tolerance)},records,s);
end

function [phi,history,status]=rmo(phi,fg,s,vectorObjective,increment)
initialPhi=phi;
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
        curvature=sum(step.*(oldTheta-newTheta),2);distance=sum(step.^2,2);yy=sum((oldTheta-newTheta).^2,2);seed=2*alpha;positive=curvature>0&distance>0;
        if mod(it,2)==1,seed(positive)=curvature(positive)./yy(positive);else,seed(positive)=distance(positive)./curvature(positive);end
    else
        curvature=sum(sum(step.*(oldTheta-newTheta)));distance=sum(step(:).^2);yy=sum(sum((oldTheta-newTheta).^2));
        if curvature>0&&distance>0,if mod(it,2)==1,seed=curvature/yy;else,seed=distance/curvature;end,else,seed=2*alpha;end
    end
    seed=min(max(seed,1e-12),1e12);
    improvement=min(trial)-min(value); phi=candidate; value=trial; g=newg; history(end+1)=min(value); %#ok<AGROW>
end
status=gradient_stop(norm(g(:)),numel(history)-1,s.rmo_max_iterations,s.gradient_tolerance);
status.initial_step_contract='alternating_positive_BB1_BB2_seeds_in_original_RGD_direction_before_original_Armijo; no gradient-threshold relaxation';
if nargin>=5,status.objective_increment_contract='exact_original_moment_polynomial_ratio_logsumexp_increment';else,status.objective_increment_contract='direct_objective_difference';end
details=functions(fg); context=struct(); sourceContext=details.workspace{1};
for name={'data','W','p0','mu','interferenceLimit','tts'}
    if isfield(sourceContext,name{1}),context.(name{1})=sourceContext.(name{1});end
end
strict_satcom_capture('phase',struct('initial_phi',initialPhi,'final_phi',phi,'gradient',g,'value',value,'history',history,'status',status,'context',context,'vector_objective',vectorObjective));
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
W=W.*(scale*0.95); e=strict_satcom_core_v3('ap_evaluate',W,mu,C,data.gt_second,off); history=min(e.sinr);records={};
for it=1:s.qt_max_iterations
    [W,info]=strict_satcom_qt_guard_v3('ap',W,mu,C,data.gt_second,off,powerLimit,interferenceLimit);
    records{end+1}=solver_record(info); %#ok<AGROW>
    value=min(info.after.sinr); history(end+1)=value; %#ok<AGROW>
    assert(value>=history(end-1)-s.solver_objective_tolerance,'AP QT monotonicity failure');
    if (value-history(end-1))/max(abs(history(end-1)),1e-12)<s.relative_tolerance, break; end
end
status=scheme_status({relative_stop(history,s.qt_max_iterations,s.relative_tolerance)},records,s);
end

function [phi,W,history,status]=ap_ao(data,phi,W,powerLimit,interferenceLimit,s)
[mu,C,~,~,off]=strict_satcom_models('moments',data,phi); e=strict_satcom_core_v3('ap_evaluate',W,mu,C,data.gt_second,off); history=min(e.sinr);records={};stops={};
for it=1:s.ao_max_iterations
    [W,info]=strict_satcom_qt_guard_v3('ap',W,mu,C,data.gt_second,off,powerLimit,interferenceLimit);records{end+1}=solver_record(info); %#ok<AGROW>
    fg=@(x) strict_satcom_models('ap_phase',data,x,W);increment=@(a,b)strict_satcom_increments_v2('ap',data,a,b,W);[phi,~,stop]=rmo(phi,fg,s,true,increment);stops{end+1}=stop; %#ok<AGROW>
    [mu,C,~,~,off]=strict_satcom_models('moments',data,phi); e=strict_satcom_core_v3('ap_evaluate',W,mu,C,data.gt_second,off); value=min(e.sinr);
    assert(value>=history(end)-s.solver_objective_tolerance,'AP-AO monotonicity failure'); history(end+1)=value; %#ok<AGROW>
    if (value-history(end-1))/max(abs(history(end-1)),1e-12)<s.relative_tolerance, break; end
end
stops{end+1}=relative_stop(history,s.ao_max_iterations,s.relative_tolerance);status=scheme_status(stops,records,s);
end

function [phi,p,history,status]=mr_two_stage(data,phi,p0,powerLimit,interferenceLimit,s,tts)
mu=s.smoothing_initial; phases=struct('mu',{},'objective',{});stops={};
% Final publisher Algorithm3 line2 reconstruction: one full P9, then one P7 QT update.
% P9 means the complete existing RMO solve; the author executable is not recovered.
preambleInputPower=p0; preambleInitialPhase=phi;
preambleFG=@(x) strict_satcom_models('mr_phase',data,x,p0,mu,interferenceLimit,tts);
preambleIncrement=@(a,b)strict_satcom_increments_v2('mr',data,a,b,p0,mu,interferenceLimit,tts);
[phi,preamblePhaseHistory,preamblePhaseStatus]=rmo(phi,preambleFG,s,false,preambleIncrement);
stops{end+1}=preamblePhaseStatus;
preambleCoef=strict_satcom_models('mr_components',data,phi,tts);
% One logical fixed-auxiliary P7 update; same-input precision retries are retained.
% The original MR QT provider recomputes Eq32 auxiliaries at p0 and this new phase.
[p0,preambleInfo]=preamble_single_P7_guard(p0,preambleCoef.signal,preambleCoef.cross,preambleCoef.power,preambleCoef.leak,preambleCoef.offset,powerLimit,interferenceLimit);
preamble=struct('publisher_algorithm','Algorithm3_line2_pre_loop_P9_then_single_P7', ...
    'P9_reconstruction','one_complete_existing_RMO_solve_at_initial_mu_with_unchanged_controls', ...
    'P7_reconstruction','one_logical_original_QT_subproblem_with_fresh_Eq32_auxiliaries_not_complete_Algorithm2', ...
    'author_executable_recovered',false,'per_smoothing_iteration_power_refresh',false, ...
    'initial_mu',mu,'input_p_INIT',preambleInputPower,'updated_p_INIT',p0, ...
    'initial_phi',preambleInitialPhase,'phase_after_P9',phi,'P9_history',preamblePhaseHistory, ...
    'P9_status',preamblePhaseStatus,'P7_logical_QT_updates',1,'P7_info',preambleInfo);
% The paper defines Phi* only after improvement; use the post-preamble phase if none occurs.
preamble.P7_minimum_SINR_before=min(preambleInfo.before.sinr);
preamble.P7_minimum_SINR_after=min(preambleInfo.after.sinr);
phiStar=phi; phiStarStrictUpdates=0;
while mu>=s.smoothing_final
    fg=@(x) strict_satcom_models('mr_phase',data,x,p0,mu,interferenceLimit,tts); stopped=false;
    for inner=1:s.smoothing_max_repeats
        before=fg(phi);increment=@(a,b)strict_satcom_increments_v2('mr',data,a,b,p0,mu,interferenceLimit,tts);[phi,h,stop]=rmo(phi,fg,s,false,increment);stops{end+1}=stop;phases(end+1)=struct('mu',mu,'objective',h); %#ok<AGROW>
        if h(end)>before, phiStar=phi; phiStarStrictUpdates=phiStarStrictUpdates+1; else, stopped=true; break; end
    end
    assert(stopped,'Smoothing repeat cap reached while improving'); mu=mu/2;
end
phi=phiStar;
phaseSelection=struct('comparison','strict_h_end_greater_than_before', ...
    'phiStar_initialization','post_preamble_phase_disclosed_fallback', ...
    'strict_improvement_updates',phiStarStrictUpdates,'used_initial_fallback',phiStarStrictUpdates==0, ...
    'configured_smoothing_progress_tolerance_used_in_branch',false,'phi_star',phiStar);
c=strict_satcom_models('mr_components',data,phi,tts); [p,h,pstatus]=mr_power(c,p0,powerLimit,interferenceLimit,s);
history=struct('phase',phases,'power',h);
history.final_algorithm3_preamble=preamble;
history.final_algorithm3_phase_selection=phaseSelection;
status=scheme_status([stops,pstatus.blocks],[{solver_record(preambleInfo)},pstatus.solver_diagnostics],s);status.smoothing_schedule_completed=mu<s.smoothing_final;
status.final_algorithm3_preamble=preamble;
status.final_algorithm3_phase_selection=phaseSelection;
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

function [candidate,info]=preamble_single_P7_guard(varargin)
% Preamble-only original QT: changed phase can make old p_INIT infeasible; no incumbent monotonicity premise.
previous=cvx_precision;restore=onCleanup(@()cvx_precision(previous));controls={'high','best'};attempts={};last='';
for k=1:numel(controls)
    cvx_precision(controls{k});
    try
        [value,out]=strict_satcom_core_v3('mr_qt_update',varargin{:});d=out.solver_diagnostics;before=min(out.before.sinr);after=min(out.after.sinr);
        accepted=isfinite(after)&&isfinite(d.constraint_max_relative_violation)&&d.constraint_max_relative_violation<=1e-5 ...
            &&isfinite(out.qt_bound_max_violation)&&out.qt_bound_max_violation<=1e-5;
        attempts{end+1}=struct('numerical_precision',controls{k},'solver_status',out.solver_status, ...
            'primal_relative_violation',d.constraint_max_relative_violation,'qt_bound_violation',out.qt_bound_max_violation, ...
            'before_minimum_sinr',before,'after_minimum_sinr',after,'accepted',accepted); %#ok<AGROW>
        if accepted,candidate=value;info=out;info.solver_diagnostics.same_original_QT_numerical_attempts=attempts;
            info.solver_diagnostics.preamble_incumbent_physical_feasibility=struct('satellite_power',out.before.satellite_power,'power_limit',varargin{7}(:),'gt_interference',out.before.gt_interference,'interference_limit',varargin{8}(:),'feasible_without_tolerance',all(out.before.satellite_power(:)<=varargin{7}(:))&&all(out.before.gt_interference(:)<=varargin{8}(:)));
            info.solver_diagnostics.preamble_incumbent_monotonicity_required=false;info.solver_diagnostics.preamble_omitted_predicate_reason='P9_changes_phase_so_original_p_INIT_need_not_be_feasible_for_P7_at_this_phase';return;end
        last='Original preamble P7 finite/primal/QT gates rejected the numeric solution';
    catch err,last=err.message;attempts{end+1}=struct('numerical_precision',controls{k},'error',last,'accepted',false);end %#ok<AGROW>
end
error('Same-input preamble P7 precision controls exhausted; original primal/QT bounds retained: %s',last);
end

