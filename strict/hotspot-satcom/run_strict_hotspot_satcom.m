function result=run_strict_hotspot_satcom(configPath,outputPath,sweepId,csi)
% Full author-thesis instantaneous algorithms at unmodified configured MC count.
% Statistical entry is an explicit original-model QT erratum, never a silent substitute.
config=jsondecode(fileread(configPath));
if nargin>=4 && strcmp(csi,'statistical')
    assert(nargin<3||isempty(sweepId)||strcmp(sweepId,'statistical'),'Statistical CSI uses its original figure3-10 grid');
    result=run_strict_hotspot_statistical_controlled(configPath,outputPath,'full');return;
elseif nargin>=4 && ~strcmp(csi,'instantaneous'),error('Unknown CSI regime');end
if nargin>=3&&strcmp(sweepId,'full-case')
    % Explicit diagnostic scope: ONE complete original-sized optimization,
    % all configured iterations and all 1000 original Gaussian SDR draws.
    % Never confuse this with the 1000-realization figure Monte Carlo bank.
    sourceHashes=strict_hotspot_runtime_hashes(configPath,'instantaneous');started=tic;rng(config.tuned_not_reported.seed,'twister');
    try,sample=full_sample(config);catch err,sample=struct('status','failed','error',err.message,'physical_constraint_pass',false,'convergence_pass',false,'solver_primal_pass',false,'qt_sdr_bound_pass',false,'valid_sample',false);end
    names={'physical_constraint_pass','convergence_pass','solver_primal_pass','qt_sdr_bound_pass'};checks=struct();for k=1:numel(names),checks.(names{k})=sample.(names{k});end
    result=struct('paper_id','hotspot-satcom','scope','full_dimension_complete_algorithm_representative_NOT_1000_realization_figure_bank', ...
        'sample',sample,'checks',checks,'configuration',config,'elapsed_seconds',toc(started),'representative_sample_count',1, ...
        'original_MC_figure_count',config.tuned_not_reported.monte_carlo_realizations,'full_MC_figure_bank_pass',false,'full_reproduction_pass',false, ...
        'executed_source_hashes',sourceHashes,'source_unchanged_during_run',isequal(sourceHashes,strict_hotspot_runtime_hashes(configPath,'instantaneous')));
    assert(result.source_unchanged_during_run,'Actual instantaneous runtime sources changed');
    folder=fileparts(outputPath);if ~isempty(folder)&&~exist(folder,'dir'),mkdir(folder);end
    fid=fopen(outputPath,'w');assert(fid>=0);clean=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(result));return;
end
sweeps=config.sweeps; if ~iscell(sweeps), sweeps=num2cell(sweeps); end
if nargin>=3 && strcmp(sweepId,'base')
    sweeps={struct('id','base','parameter','power_w','values',config.reported.power_w)};
elseif nargin>=3
    ids=cellfun(@(x)x.id,sweeps,'UniformOutput',false); sweeps=sweeps(strcmp(ids,sweepId)); assert(~isempty(sweeps),'Unknown sweep');
end
sourceHashes=strict_hotspot_runtime_hashes(configPath,'instantaneous');started=tic; records={};
for sidx=1:numel(sweeps)
    sweep=sweeps{sidx}; vals=sweep.values;
    if strcmp(sweep.parameter,'subsurface_elements'), count=size(vals,1); else, count=numel(vals); end
    for vi=1:count
        if strcmp(sweep.parameter,'subsurface_elements'), value=vals(vi,:); else, value=vals(vi); end
        scene=config; scene.reported.(sweep.parameter)=value;
        if isfield(sweep,'U'), scene.reported.U=sweep.U; end
        if isfield(sweep,'kappa_satellite_db'), scene.reported.kappa_satellite_db=sweep.kappa_satellite_db; end
        scene.reported.K=scene.reported.J-scene.reported.U; t=scene.tuned_not_reported; rng(t.seed,'twister');
        samples={};
        for realization=1:t.monte_carlo_realizations
            try,sample=full_sample(scene);sample.index=realization-1;
            catch exception,sample=struct('index',realization-1,'status','failed','error',exception.message,'physical_constraint_pass',false,'convergence_pass',false,'solver_primal_pass',false,'qt_sdr_bound_pass',false,'valid_sample',false);end
            samples{end+1}=sample; %#ok<AGROW>
            fprintf('Completed %s MC=%d/%d elapsed=%.1fs\n',sweep.id,realization,t.monte_carlo_realizations,toc(started));
        end
        raw=struct('AO',[],'AO20',[],'AO100',[],'TwoStage',[],'NoRIS',[],'RandRIS',[]);names={'AO','AO20','AO100','TwoStage','NoRIS','RandRIS'};
        for k=1:numel(names),if all(cellfun(@(x)isfield(x,names{k}),samples)),rates=cellfun(@(x)x.(names{k}).hu_sum_rate,samples);raw.(names{k})=mean(rates);end,end
        valid=numel(samples)==t.monte_carlo_realizations&&all(cellfun(@(x)x.valid_sample,samples));means=[];if valid,means=raw;end
        records{end+1}=struct('sweep',sweep.id,'parameter',sweep.parameter,'value',value,'samples',{samples}, ...
            'raw_unvalidated_means',raw,'means',means,'valid_figure_point',valid,'failed_or_capped_samples',sum(cellfun(@(x)~x.valid_sample,samples)), ...
            'mean_policy','No failed/capped sample is dropped; means are valid only when every required sample passes.'); %#ok<AGROW>
    end
end
keys={'physical_constraint_pass','convergence_pass','solver_primal_pass','qt_sdr_bound_pass'};checks=struct();
for k=1:numel(keys),checks.(keys{k})=all(cellfun(@(r)all(cellfun(@(x)x.(keys{k}),r.samples)),records));end
result=struct('paper_id','hotspot-satcom','source_version','author_thesis','final_publisher_conformance','unverified', ...
    'scope','instantaneous_author_model_original_AO_QT_SDR_and_RGD_QT_full_dimensions_full_configured_MC','phase_method','author_Algorithm_3-2_RGD_minimize_negative_F', ...
    'elapsed_seconds',toc(started),'results',{records},'checks',checks, ...
    'overall_implemented_scope_success',~isempty(records)&&all(cellfun(@(x)x.valid_figure_point,records)),'all_configured_sweeps_requested',nargin<3, ...
    'full_reproduction_pass',false,'remaining',{{'Final publication equivalence','Published-figure agreement'}}, ...
    'executed_source_hashes',sourceHashes,'source_unchanged_during_run',isequal(sourceHashes,strict_hotspot_runtime_hashes(configPath,'instantaneous')));
assert(result.source_unchanged_during_run,'Actual instantaneous runtime sources changed; no mixed-source certification');
folder=fileparts(outputPath); if ~isempty(folder) && ~exist(folder,'dir'), mkdir(folder); end
fid=fopen(outputPath,'w'); assert(fid>=0); clean=onCleanup(@()fclose(fid)); fprintf(fid,'%s\n',jsonencode(result));
end

function sample=full_sample(scene)
t=scene.tuned_not_reported;f=strict_hotspot_scenario(scene);U=size(f.direct,1);hu=strict_hotspot_core('effective',f.direct,f.cascade,f.phi0);
W0=initialize([hu;f.nhu],[t.initial_hu_sinr*ones(U,1);f.nhu_target],f.noise,f.power);normals=cell(1,t.ao_max_iterations);
for a=1:numel(normals),normals{a}=(randn(numel(f.phi0)+1,t.randomization_count)+1i*randn(numel(f.phi0)+1,t.randomization_count))/sqrt(2);end
clock=tic;[apPhi,W,h,astop,diagnostics,endpoints]=strict_instantaneous_ao_guarded(f.direct,f.cascade,f.nhu,f.phi0,W0,f.noise,f.power,f.nhu_target,normals,t.ao_max_iterations,t.relative_tolerance);
aoTime=toc(clock);aEval=strict_hotspot_core('evaluate',strict_hotspot_core('effective',f.direct,f.cascade,apPhi),f.nhu,W,f.noise);
clock=tic;[tsPhi,tsW,hts]=strict_hotspot_core('two_stage',f.direct,f.cascade,f.nhu,f.phi0,W0,f.noise,f.power,f.nhu_target,t.rgd_max_iterations,t.gradient_tolerance,t.qt_max_iterations,t.relative_tolerance);
tsTime=toc(clock);tEval=strict_hotspot_core('evaluate',strict_hotspot_core('effective',f.direct,f.cascade,tsPhi),f.nhu,tsW,f.noise);
clock=tic;baseInit=initialize([f.direct;f.nhu],[t.initial_hu_sinr*ones(U,1);f.nhu_target],f.noise,f.power);
[baseW,hbase,bstop,bdiag]=strict_hotspot_core('qt_loop',f.direct,f.nhu,baseInit,f.noise,f.power,f.nhu_target,t.qt_max_iterations,t.relative_tolerance);
bEval=strict_hotspot_core('evaluate',f.direct,f.nhu,baseW,f.noise);baseTime=toc(clock);
% Same randomly sampled unit-modulus phi0; optimize only W by original QT.
clock=tic;[randW,hrand,rstop,rdiag]=strict_hotspot_core('qt_loop',hu,f.nhu,W0,f.noise,f.power,f.nhu_target,t.qt_max_iterations,t.relative_tolerance);
rEval=strict_hotspot_core('evaluate',hu,f.nhu,randW,f.noise);randTime=toc(clock);violations=0;
for e={aEval,tEval,bEval,rEval},item=e{1};violations=max([violations,item.total_power-f.power,max(f.nhu_target-item.sinr(U+1:end))]);end
statuses=struct('AO',strict_hotspot_termination('scheme',{astop},diagnostics,t), ...
    'TwoStage',strict_hotspot_termination('scheme',{hts.termination.phase,hts.termination.QT},hts.solver_diagnostics,t), ...
    'NoRIS',strict_hotspot_termination('scheme',{bstop},bdiag,t),'RandRIS',strict_hotspot_termination('scheme',{rstop},rdiag,t));
convergence=true;primal=true;bound=true;for name={'AO','TwoStage','NoRIS','RandRIS'},s=statuses.(name{1});convergence=convergence&&s.converged;primal=primal&&s.numerical.solver_primal_pass;bound=bound&&s.numerical.qt_sdr_bound_pass;end
physical=violations<t.physical_constraint_tolerance;
sample=struct('status','executed','AO',aEval,'TwoStage',tEval,'NoRIS',bEval,'RandRIS',rEval,'scheme_status',statuses, ...
    'solver_diagnostics',struct('AO',{diagnostics},'TwoStage',{hts.solver_diagnostics},'NoRIS',{bdiag},'RandRIS',{rdiag}), ...
    'history',struct('AO',h,'TwoStage',hts,'NoRIS',hbase,'RandRIS',hrand), ...
    'cpu_seconds',struct('AO',aoTime,'AO_phase',sum(cellfun(@(x)x.phase.phase_cpu_seconds,diagnostics)), ...
        'TwoStage',tsTime,'TwoStage_phase',hts.phase_cpu_seconds,'NoRIS',baseTime,'RandRIS',randTime), ...
    'physical_constraint_pass',physical,'convergence_pass',convergence,'solver_primal_pass',primal,'qt_sdr_bound_pass',bound,'valid_sample',physical&&convergence&&primal&&bound);
budgetReceipts=struct();
for budget=[20,100]
    name=sprintf('AO%d',budget);available=isfield(endpoints,name);receipt=[];physicalEndpoint=false;
    if available
        receipt=endpoints.(name);sample.(name)=receipt.evaluation;records=receipt.solver_diagnostics;
        physicalEndpoint=receipt.evaluation.total_power-f.power<t.physical_constraint_tolerance&&max(f.nhu_target-receipt.evaluation.sinr(U+1:end))<t.physical_constraint_tolerance;
    else,records={};end
    temporaryStatus=strict_hotspot_termination('scheme',{},records,t);numerical=temporaryStatus.numerical;
    validEndpoint=available&&physicalEndpoint&&numerical.solver_primal_pass&&numerical.qt_sdr_bound_pass;
    budgetReceipts.(name)=struct('available',available,'receipt',receipt,'numerical',numerical,'physical_constraint_pass',physicalEndpoint, ...
        'convergence_not_required_for_reported_fixed_budget',true,'valid_budget_endpoint',validEndpoint);
    sample.valid_sample=sample.valid_sample&&validEndpoint;
end
sample.reported_budget_endpoints=budgetReceipts;
end

function Wout=initialize(C,targets,noise,power)
[J,N]=size(C);
cvx_begin quiet
    variable W(N,J) complex
    minimize(sum_square_abs(W(:)))
    subject to
    sum_square_abs(W(:))<=power;
    for u=1:J
        desired=C(u,:)*W(:,u); indexes=setdiff(1:J,u); imag(desired)==0;
        norm([C(u,:)*W(:,indexes),sqrt(noise)])<=real(desired)/sqrt(targets(u));
    end
cvx_end
assert(contains(cvx_status,'Solved'),'SOCP initialization infeasible; no QoS relaxation'); Wout=W;
end
