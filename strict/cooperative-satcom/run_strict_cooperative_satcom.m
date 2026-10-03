function result=run_strict_cooperative_satcom(configPath,outputPath,sweepId)
% Explicit full author-model run. No automatic count/cap/dimension reduction.
% External CVX required. Full defaults can be expensive; root coordinates runs.
config=jsondecode(fileread(configPath)); sweeps=num2cell(config.sweeps); comparison=config.multi_vs_single;
if comparison.enabled
    for kappa=comparison.kappa_leo_db(:).'
        sweeps{end+1}=struct('id',sprintf('multi_vs_single_multi_kL%g',kappa),'parameter','interference_to_noise_db', ...
            'values',comparison.interference_values_db,'kappa_leo_db',kappa,'satellite_mode','multi'); %#ok<AGROW>
        for offset=comparison.offsets_deg(:).'
            sweeps{end+1}=struct('id',sprintf('multi_vs_single_single_%g_kL%g',offset,kappa),'parameter','interference_to_noise_db', ...
                'values',comparison.interference_values_db,'kappa_leo_db',kappa,'satellite_mode','single','offset_deg',offset); %#ok<AGROW>
        end
    end
end
if nargin>=3 && strcmp(sweepId,'base')
    sweeps={struct('id','base','parameter','power_w','values',config.reported.power_w,'kappa_leo_db',config.reported.kappa_leo_db)};
elseif nargin>=3
    ids=cellfun(@(x)x.id,sweeps,'UniformOutput',false); sweeps=sweeps(strcmp(ids,sweepId)); assert(~isempty(sweeps),'Unknown sweep');
end
started=tic; records={};
for sidx=1:numel(sweeps)
    sweep=sweeps{sidx};
    for value=sweep.values(:).'
        scene=config; scene.reported.(sweep.parameter)=value; scene.reported.kappa_leo_db=sweep.kappa_leo_db;
        if isfield(sweep,'satellite_mode') && strcmp(sweep.satellite_mode,'single')
            scene.reported.J=1; scene.reported.N=comparison.single_N; scene.reported.power_w=comparison.single_power_w;
            scene.tuned_not_reported.satellite_latitudes_deg=sweep.offset_deg; scene.tuned_not_reported.upa_shape=comparison.single_upa_shape;
        end
        [data,pl,il]=strict_satcom_scenario(scene);
        try,schemes=strict_satcom_algorithms(data,scene.tuned_not_reported,pl,il);
        catch exception
            records{end+1}=struct('sweep',sweep.id,'parameter',sweep.parameter,'value',value,'status','failed','error',exception.message, ...
                'constraint_pass',false,'convergence_pass',false,'solver_primal_pass',false,'qt_bound_pass',false,'valid_figure_point',false); %#ok<AGROW>
            continue;
        end
        violations=0;
        for e=1:numel(schemes)
            violations=max([violations;schemes(e).evaluation.satellite_power-pl;schemes(e).evaluation.gt_interference-il]);
        end
        mc=moment_mc(data,scene.tuned_not_reported.monte_carlo_realizations,scene.tuned_not_reported.seed);
        convergence=true;primal=true;bound=true;
        for e=1:numel(schemes)
            status=schemes(e).status;convergence=convergence&&status.converged;if isfield(status,'phase_source_converged'),convergence=convergence&&status.phase_source_converged;end
            primal=primal&&status.numerical.solver_primal_pass;bound=bound&&status.numerical.qt_bound_pass;
        end
        physical=violations<scene.tuned_not_reported.solver_objective_tolerance;valid=physical&&convergence&&primal&&bound;reason='executed_but_capped_or_numerically_unvalidated';if valid,reason='converged_and_validated';end
        records{end+1}=struct('sweep',sweep.id,'parameter',sweep.parameter,'value',value,'schemes',schemes, ...
            'monte_carlo',mc,'constraint_pass',physical,'convergence_pass',convergence,'solver_primal_pass',primal,'qt_bound_pass',bound,'valid_figure_point',valid,'status',reason); %#ok<AGROW>
        fprintf('Completed author-model %s value=%g in %.1fs\n',sweep.id,value,toc(started));
    end
end
checks=struct('constraint_pass',all(cellfun(@(x)x.constraint_pass,records)),'convergence_pass',all(cellfun(@(x)x.convergence_pass,records)), ...
    'solver_primal_pass',all(cellfun(@(x)x.solver_primal_pass,records)),'qt_bound_pass',all(cellfun(@(x)x.qt_bound_pass,records)));
result=struct('paper_id','cooperative-satcom','source_version',config.source_version, ...
    'final_publisher_conformance',config.final_publisher_conformance, ...
    'scope','author_model_all_eight_algorithm_chains_full_dimensions_tuned_sweeps', ...
    'elapsed_seconds',toc(started),'results',{records},'checks',checks, ...
    'overall_implemented_scope_success',~isempty(records)&&all(cellfun(@(x)x.valid_figure_point,records)), ...
    'all_configured_sweeps_requested',nargin<3,'figure_validation_policy','Failed/capped/numerically-unvalidated points are retained and invalidate their selected sweep.', ...
    'full_reproduction_pass',false,'remaining',{{'Publisher-version conformance','Original unreported values and figure grids','Published-figure agreement'}});
folder=fileparts(outputPath); if ~isempty(folder) && ~exist(folder,'dir'), mkdir(folder); end
fid=fopen(outputPath,'w'); assert(fid>=0); clean=onCleanup(@()fclose(fid)); fprintf(fid,'%s\n',jsonencode(result));
end

function out=moment_mc(data,count,seed)
rng(seed,'twister'); [J,U,N]=size(data.d_mean); M=size(data.r_mean,2); phi=ones(U,M);
[~,~,Q,fourth,~]=strict_satcom_models('moments',data,phi); powers=zeros(J,U); fourths=zeros(J,U);
for realization=1:count
    for u=1:U
        r=data.r_mean(u,:).'+sqrt(data.r_var(u))*cn([M,1]);
        for j=1:J
            G=reshape(data.G_mean(j,u,:,:),N,M)+sqrt(data.G_var(j,u))*cn([N,M]);
            d=reshape(data.d_mean(j,u,:),N,1)+sqrt(data.d_var(j,u))*cn([N,1]); h=d+G*r;
            p=sum(abs(h).^2); powers(j,u)=powers(j,u)+p; fourths(j,u)=fourths(j,u)+p^2;
        end
    end
end
exact2=zeros(J,U); for j=1:J, for u=1:U, exact2(j,u)=real(trace(reshape(Q(j,u,:,:),N,N))); end, end
e2=abs(powers/count-exact2)./exact2; e4=abs(fourths/count-fourth)./fourth;
out=struct('count',count,'second_moment_max_relative_error',max(e2(:)),'fourth_moment_max_relative_error',max(e4(:)), ...
    'purpose','Independent finite-Rician channel validation, not fabricated performance data');
end
function x=cn(shape)
x=(randn(shape)+1i*randn(shape))/sqrt(2);
end
