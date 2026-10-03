function result=run_strict_hotspot_statistical_geometry(configPath,outputPath,scope)
% Full finite-Rician statistical designs; explicit original-QT mathematical erratum.
if nargin<3,scope='full';end
config=jsondecode(fileread(configPath));sourceHashes=strict_hotspot_geometry_hashes(configPath);t=config.tuned_not_reported;cases={};clock=tic;
if strcmp(scope,'full-case'),grid=[config.reported.U,config.reported.kappa_satellite_db];else,[u,b]=ndgrid(1:6,[0,10,20]);grid=[u(:),b(:)];end
for row=1:size(grid,1)
    scene=config;scene.reported.U=grid(row,1);scene.reported.K=16-grid(row,1);scene.reported.kappa_satellite_db=grid(row,2);scene.reported.kappa_ground_db=20;scene.reported.nhu_statistical_sinr_db=-3;
    rng(t.seed,'twister');
    try,c=designs(scene);c.status='executed';catch err,c=struct('status','failed','error',err.message,'checks',struct('physical_constraint_pass',false,'convergence_pass',false,'solver_primal_pass',false,'qt_sdr_bound_pass',false));end
    c.U=grid(row,1);c.kappa_satellite_db=grid(row,2);cases{end+1}=c; %#ok<AGROW>
end
keys={'physical_constraint_pass','convergence_pass','solver_primal_pass','qt_sdr_bound_pass'};checks=struct();
for k=1:numel(keys),checks.(keys{k})=all(cellfun(@(c)c.checks.(keys{k}),cases));end
result=struct('paper_id','hotspot-satcom','algorithm','corrected_QT_erratum_NOT_original_printed_invalid_SOC', ...
    'scope',scope,'source_settings',struct('ground_rician_db',20,'nhu_average_sinr_db',-3), ...
    'geometry_contract',config.geometry_contract,'historical_author_coordinates_recovered',false, ...
    'configuration',config,'cases',{cases},'checks',checks,'elapsed_seconds',toc(clock), ...
    'full_reproduction_pass',false,'original_printed_algorithm_reproduction_pass',false,'publisher_version_and_original_curve_agreement_verified',false, ...
    'executed_source_hashes',sourceHashes,'source_unchanged_during_run',isequal(sourceHashes,strict_hotspot_geometry_hashes(configPath)));
assert(result.source_unchanged_during_run,'Actual controlled runtime sources changed; no mixed-source certification');
folder=fileparts(outputPath);if ~exist(folder,'dir'),mkdir(folder);end
fid=fopen(outputPath,'w');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(result));
end

function c=designs(config)
t=config.tuned_not_reported;f=strict_hotspot_geometry(config);x=f.mean_inputs;phi=f.phi0;noise=f.noise;power=f.power;U=size(x.direct_mean,1);target=10^(-3/10)*ones(size(x.nhu_mean,1),1);
[Q,Psi,mu]=strict_hotspot_statistical('moments',x,phi);[Q0,~,mu0]=strict_hotspot_statistical('moments',x,phi,true);
W0=strict_hotspot_statistical('initialize',Q,Psi,mu,x.nhu_mean,noise,power,target);
init=strict_hotspot_statistical('initialize',Q0,Psi,mu0,x.nhu_mean,noise,power,target);
[W,h,stop,records]=strict_hotspot_statistical('qt_loop',Q0,Psi,init,noise,power,target,t);
outputs.NoRIS=struct('evaluation',strict_hotspot_statistical('evaluate',Q0,Psi,W,noise),'history',h,'status',scheme({stop},records,t));states.NoRIS=struct('phi',phi,'W',W,'no_ris',true);
fprintf('Statistical NoRIS completed\n');
P=strict_hotspot_statistical('projector_square',x);
[tsphi,hp,sp]=strict_hotspot_rgd_spectral('phase',phi,x,'criterion',P,noise,t);
tsQ=strict_hotspot_statistical('moments',x,tsphi);[tsW,hr,sr,records]=strict_hotspot_statistical('qt_loop',tsQ,Psi,W0,noise,power,target,t);
outputs.TwoStage=struct('evaluation',strict_hotspot_statistical('evaluate',tsQ,Psi,tsW,noise),'history',struct('phase',hp,'QT',hr),'status',scheme({sp,sr},records,t));states.TwoStage=struct('phi',tsphi,'W',tsW,'no_ris',false);
fprintf('Statistical TwoStage completed\n');
aophi=phi;W=W0;e=strict_hotspot_statistical('evaluate',Q,Psi,W,noise);h=e.hu_sum_rate;stops={};records={};
for it=1:t.ao_max_iterations
    Q=strict_hotspot_statistical('moments',x,aophi);[W,info]=strict_hotspot_statistical('active_qt_update',Q,Psi,W,noise,power,target);records{end+1}=info.solver_diagnostics; %#ok<AGROW>
    [aophi,~,sp]=strict_hotspot_rgd_spectral('phase',aophi,x,'rate',W,noise,t);stops{end+1}=sp; %#ok<AGROW>
    Q=strict_hotspot_statistical('moments',x,aophi);e=strict_hotspot_statistical('evaluate',Q,Psi,W,noise);assert(e.hu_sum_rate>=h(end)-1e-6);h(end+1)=e.hu_sum_rate; %#ok<AGROW>
    fprintf('Statistical AO iteration=%d rate=%.9g phaseStop=%d\n',it,e.hu_sum_rate,sp.converged);
    if (h(end)-h(end-1))/max(abs(h(end-1)),1e-12)<t.relative_tolerance,break;end
end
stops{end+1}=strict_hotspot_termination('relative',h,t.ao_max_iterations,t.relative_tolerance);
outputs.AO=struct('evaluation',e,'history',h,'status',scheme(stops,records,t));states.AO=struct('phi',aophi,'W',W,'no_ris',false);
names={'NoRIS','TwoStage','AO'};samples=zeros(t.monte_carlo_realizations,3);rp=zeros(16,16,3);
for draw=1:t.monte_carlo_realizations
    f=strict_hotspot_geometry(config);
    for k=1:3
        state=states.(names{k});hu=f.direct;if ~state.no_ris,hu=strict_hotspot_core('effective',f.direct,f.cascade,state.phi);end
        eval=strict_hotspot_core('evaluate',hu,f.nhu,state.W,noise);samples(draw,k)=eval.hu_sum_rate;rp(:,:,k)=rp(:,:,k)+abs([hu;f.nhu]*state.W).^2;
    end
end
physical=true;converged=true;primal=true;bound=true;
for k=1:3
    name=names{k};received=rp(:,:,k)/t.monte_carlo_realizations;desired=diag(received);snr=desired./(sum(received,2)-desired+noise);
    outputs.(name).independent_MC=struct('count',t.monte_carlo_realizations,'exact_ergodic_sum_rate_estimate',mean(samples(:,k)), ...
        'standard_error',std(samples(:,k))/sqrt(t.monte_carlo_realizations),'ratio_of_empirical_expected_powers_sum_rate',sum(log2(1+snr(1:U))), ...
        'ratio_of_expected_powers_source_approximation_is_not_exact_E_log',true,'hu_rate_samples',samples(:,k));
    eval=outputs.(name).evaluation;status=outputs.(name).status;physical=physical&&eval.total_power<=power*(1+1e-5)&&min(eval.sinr(U+1:end)-target)>=-1e-5;
    converged=converged&&status.converged;primal=primal&&status.numerical.solver_primal_pass;bound=bound&&status.numerical.qt_sdr_bound_pass;
end
c=struct('schemes',outputs,'checks',struct('physical_constraint_pass',physical,'convergence_pass',converged, ...
    'solver_primal_pass',primal,'qt_sdr_bound_pass',bound),'model','full_finite_Rician_original_ratio_of_expected_powers','algorithm','corrected_QT_erratum','phase_method','original_RGD_with_exact_statistical_moments_alternating_BB1_BB2_step_seeds_stable_exact_increment');
end

function s=scheme(stops,records,t)
s=strict_hotspot_termination('scheme',stops,records,t);
end
