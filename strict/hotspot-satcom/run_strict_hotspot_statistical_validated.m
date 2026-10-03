function result=run_strict_hotspot_statistical_validated(configPath,outputPath,scope)
% Original full chains; explicit QT erratum and uniform declared feasible ensemble.
% No hidden phase cap success, missing starts, or survivor means are accepted.
if nargin<3,scope='full';end
assert(any(strcmp(scope,{'full','full-case'})));config=jsondecode(fileread(configPath));sourceHashes=strict_hotspot_validated_hashes(configPath);cases={};clock=tic;
if strcmp(scope,'full-case'),grid=[config.reported.U,config.reported.kappa_satellite_db];else,[u,b]=ndgrid(1:6,[0,10,20]);grid=[u(:),b(:)];end
for row=1:size(grid,1)
    scene=config;scene.reported.U=grid(row,1);scene.reported.K=16-grid(row,1);scene.reported.kappa_satellite_db=grid(row,2);scene.reported.kappa_ground_db=20;scene.reported.nhu_statistical_sinr_db=-3;
    rng(scene.tuned_not_reported.seed,'twister');c=designs(scene);c.U=grid(row,1);c.kappa_satellite_db=grid(row,2);c.status='executed';cases{end+1}=c; %#ok<AGROW>
    assert(isequal(sourceHashes,strict_hotspot_validated_hashes(configPath)),'Executed sources changed');
end
gates={'physical_constraint_pass','convergence_pass','solver_primal_pass','qt_sdr_bound_pass'};checks=struct();for k=1:numel(gates),checks.(gates{k})=all(cellfun(@(c)c.checks.(gates{k}),cases));end
result=struct('paper_id','hotspot-satcom','algorithm','corrected_QT_erratum_NOT_original_printed_invalid_SOC', ...
    'scope',scope,'source_settings',struct('ground_rician_db',20,'nhu_average_sinr_db',-3), ...
    'configuration',config,'cases',{cases},'checks',checks,'elapsed_seconds',toc(clock),'geometry_contract',config.geometry_contract, ...
    'historical_author_coordinates_recovered',false,'full_reproduction_pass',false,'original_printed_algorithm_reproduction_pass',false, ...
    'publisher_version_and_original_curve_agreement_verified',false,'executed_source_hashes',sourceHashes, ...
    'source_unchanged_during_run',isequal(sourceHashes,strict_hotspot_validated_hashes(configPath)), ...
    'all_declared_starts_required_for_certification',true,'reference_ordinates_used',false);
write(outputPath,result);
end

function c=designs(config)
t=config.tuned_not_reported;f=strict_hotspot_geometry(config);x=f.mean_inputs;U=size(x.direct_mean,1);P=strict_hotspot_statistical('projector_square',x);clock=tic;
phases=strict_hotspot_ensemble('phases',f.phi0,t.seed,U);names={'NoRIS','TwoStage','AO'};outputs=struct();states=struct();
for k=1:3
    name=names{k};records=cell(1,U+1);
    for startID=0:U
        try,r=execute(name,config,f,phases{startID+1},startID,P);
        catch err,r=struct('start_id',startID,'scheme',name,'executed',true,'exception',err.message,'exception_type',err.identifier, ...
                'checks',struct('physical_constraint_pass',false,'convergence_pass',false,'solver_primal_pass',false,'qt_sdr_bound_pass',false));end
        records{startID+1}=r;fprintf('Statistical validated U=%d beta=%g scheme=%s start=%d stop=%d\n',U,config.reported.kappa_satellite_db,name,startID,r.checks.convergence_pass);
    end
    [ensemble,selected]=strict_hotspot_ensemble('summarize',records,0:U);
    if isempty(selected)
        outputs.(name)=struct('ensemble',ensemble,'all_start_records',{records},'status',struct('converged',false,'algorithm_success',false, ...
            'numerical',struct('solver_primal_pass',ensemble.checks.solver_primal_pass,'qt_sdr_bound_pass',ensemble.checks.qt_sdr_bound_pass)));continue;
    end
    blocks=cell(1,U+1);primal=0;bound=0;
    for id=1:U+1
        r=records{id};b={};if isfield(r,'status'),b=r.status.blocks;n=r.status.numerical;primal=max(primal,n.maximum_primal_relative_violation);bound=max(bound,n.maximum_qt_sdr_bound_violation);end
        blocks{id}=struct('start_id',id-1,'actual_blocks',{b});
    end
    numerical=struct('solver_primal_pass',ensemble.checks.solver_primal_pass,'qt_sdr_bound_pass',ensemble.checks.qt_sdr_bound_pass, ...
        'maximum_primal_relative_violation',primal,'maximum_qt_sdr_bound_violation',bound,'solver_primal_relative_tolerance',t.solver_primal_relative_tolerance,'qt_bound_tolerance',t.qt_bound_tolerance);
    status=struct('converged',ensemble.checks.convergence_pass,'algorithm_success',ensemble.all_required_starts_pass, ...
        'termination','all prescribed original stops checked individually','blocks_by_start',{blocks},'numerical',numerical);
    outputs.(name)=struct('evaluation',selected.evaluation,'history',selected.history,'selected_actual_status',selected.status, ...
        'ensemble',ensemble,'all_start_records',{records},'status',status);
    s=selected.final_state;states.(name)=struct('phi',decode(s.phi),'W',decode(s.W),'no_ris',s.no_ris);
end
% Fresh paired channel draws; selected fixed designs, no mean across starts.
rng(t.seed+271828+U,'twister');samples=zeros(t.monte_carlo_realizations,3);rp=zeros(16,16,3);
for draw=1:t.monte_carlo_realizations
    channel=strict_hotspot_geometry(config);
    for k=1:3
        name=names{k};if ~isfield(states,name),continue;end
        state=states.(name);hu=channel.direct;if ~state.no_ris,hu=strict_hotspot_core('effective',hu,channel.cascade,state.phi);end
        e=strict_hotspot_core('evaluate',hu,channel.nhu,state.W,f.noise);samples(draw,k)=e.hu_sum_rate;rp(:,:,k)=rp(:,:,k)+abs([hu;channel.nhu]*state.W).^2;
    end
end
for k=1:3
    name=names{k};if ~isfield(states,name),continue;end
    received=rp(:,:,k)/t.monte_carlo_realizations;desired=diag(received);snr=desired./(sum(received,2)-desired+f.noise);
    outputs.(name).independent_MC=struct('count',t.monte_carlo_realizations,'exact_ergodic_sum_rate_estimate',mean(samples(:,k)), ...
        'standard_error',std(samples(:,k))/sqrt(t.monte_carlo_realizations),'ratio_of_empirical_expected_powers_sum_rate',sum(log2(1+snr(1:U))), ...
        'ratio_of_expected_powers_source_approximation_is_not_exact_E_log',true,'hu_rate_samples',samples(:,k));
end
gates={'physical_constraint_pass','convergence_pass','solver_primal_pass','qt_sdr_bound_pass'};checks=struct();for k=1:numel(gates),checks.(gates{k})=all(cellfun(@(name)outputs.(name).ensemble.checks.(gates{k}),names));end
c=struct('schemes',outputs,'checks',checks,'model','full_finite_Rician_original_ratio_of_expected_powers','algorithm','corrected_QT_erratum', ...
    'phase_method','original RGD direction/retraction/Armijo/threshold; declared positive step controls', ...
    'initialization_policy',config.initialization_ensemble,'elapsed_seconds',toc(clock), ...
    'declared_HU_pair_distance_contract_pass',true,'all_original_source_constraints_verified',false,'historical_author_coordinates_recovered',false,'reference_ordinates_used',false);
end

function r=execute(name,config,f,phi,startID,P)
clock=tic;t=config.tuned_not_reported;x=f.mean_inputs;noise=f.noise;power=f.power;U=size(x.direct_mean,1);target=10^(-3/10)*ones(size(x.nhu_mean,1),1);
noRIS=strcmp(name,'NoRIS');[Q,Psi,mu]=strict_hotspot_statistical('moments',x,phi,noRIS);
W0=strict_hotspot_statistical('initialize',Q,Psi,mu,x.nhu_mean,noise,power,target);[W0,proof]=strict_hotspot_ensemble('initialize',Q,Psi,W0,noise,power,target,startID);
if noRIS
    [W,h,stop,records]=strict_hotspot_statistical('qt_loop',Q,Psi,W0,noise,power,target,t);status=strict_hotspot_termination('scheme',{stop},records,t);finalPhi=phi;
elseif strcmp(name,'TwoStage')
    [finalPhi,hp,sp]=strict_hotspot_rgd_spectral('phase',phi,x,'criterion',P,noise,t);Q=strict_hotspot_statistical('moments',x,finalPhi);
    [W,hr,sr,records]=strict_hotspot_statistical('qt_loop',Q,Psi,W0,noise,power,target,t);h=struct('phase',hp,'QT',hr);status=strict_hotspot_termination('scheme',{sp,sr},records,t);
else
    finalPhi=phi;W=W0;e=strict_hotspot_statistical('evaluate',Q,Psi,W,noise);h=e.hu_sum_rate;stops={};records={};
    for it=1:t.ao_max_iterations
        Q=strict_hotspot_statistical('moments',x,finalPhi);[W,info]=strict_hotspot_statistical('active_qt_update',Q,Psi,W,noise,power,target);records{end+1}=info.solver_diagnostics; %#ok<AGROW>
        [finalPhi,~,sp]=strict_hotspot_rgd_spectral('phase',finalPhi,x,'rate',W,noise,t);stops{end+1}=sp;Q=strict_hotspot_statistical('moments',x,finalPhi);e=strict_hotspot_statistical('evaluate',Q,Psi,W,noise); %#ok<AGROW>
        assert(e.hu_sum_rate>=h(end)-1e-6,'Original exact AO objective decreased');h(end+1)=e.hu_sum_rate; %#ok<AGROW>
        if (h(end)-h(end-1))/max(abs(h(end-1)),1e-12)<t.relative_tolerance,break;end
    end
    stops{end+1}=strict_hotspot_termination('relative',h,t.ao_max_iterations,t.relative_tolerance);status=strict_hotspot_termination('scheme',stops,records,t);
end
e=strict_hotspot_statistical('evaluate',Q,Psi,W,noise);checks=struct('physical_constraint_pass',e.total_power<=power*(1+1e-5)&&min(e.sinr(U+1:end)-target)>=-1e-5, ...
    'convergence_pass',status.converged,'solver_primal_pass',status.numerical.solver_primal_pass,'qt_sdr_bound_pass',status.numerical.qt_sdr_bound_pass);
r=struct('start_id',startID,'scheme',name,'executed',true,'status',status,'checks',checks,'evaluation',e,'history',h, ...
    'initial_feasibility_proof',proof,'initial_state',struct('phi',encode(phi),'W',encode(W0)), ...
    'final_state',struct('phi',encode(finalPhi),'W',encode(W),'no_ris',noRIS),'elapsed_seconds',toc(clock));
end
function value=encode(a),value=struct('real',real(a),'imag',imag(a));end
function value=decode(a),value=a.real+1i*a.imag;end
function write(path,value)
folder=fileparts(path);if ~exist(folder,'dir'),mkdir(folder);end,fid=fopen(path,'w');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(value));
end
