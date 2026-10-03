function result = mis_sensing_strict_engine(outputPath, figureName, settingsPath)
% Published product-manifold MIS solvers. Unit tests are not full figure runs.
% Base MATLAB only; rank-one echo evaluation is algebraically identical to G.
base=fileparts(mfilename('fullpath'));
if nargin<2, figureName="component-test"; end
if nargin<3, settingsPath=fullfile(base,'settings.json'); end
settings=jsondecode(fileread(settingsPath));
if any(string(figureName)==["component-test","component-test-guard"])
    result=component_test(base,settings.kind,string(figureName)=="component-test-guard");
elseif startsWith(string(figureName),"plan:")
    requested=extractAfter(string(figureName),5);
    figures=jsondecode(fileread(fullfile(base,'figures.json')));
    fig=findfigure(figures,requested);
    result=struct('paper_id','mis-sensing','scope','full_plan_no_execution','figure',fig,'settings',settings);
elseif startsWith(string(figureName),"full-start:")
    parts=split(string(figureName),":");assert(numel(parts)==3,'Use full-start:figN:startIndex');
    figures=jsondecode(fileread(fullfile(base,'figures.json')));fig=findfigure(figures,parts(2));
    result=diagnostic_start(fig,settings,str2double(parts(3)));
else
    figures=jsondecode(fileread(fullfile(base,'figures.json')));
    assert(settings.number_of_starts==6000&&settings.rcg_max_iterations==4000&&(string(settings.kind)=="communications"||settings.outer_iterations==30),'Full figures retain strict full budgets; reduced component tests are separate');
    fig=findfigure(figures,string(figureName));
    result=struct('paper_id','mis-sensing','scope','full_size_full_budget_independent_reimplementation','figure',fig.id,'settings',settings,'points',{{}});
    points=as_cells(fig.points);
    [outparent,outname,~]=fileparts(outputPath);checkpointdir=fullfile(outparent,[outname,'_checkpoints']);
    for j=1:numel(points)
        point=points{j}; model=make_model(point,settings,string(fig.objective)=="pslr");
        checkpointprefix=fullfile(checkpointdir,sprintf('point-%d-matlab',j-1));
        if string(fig.objective)=="closed_form_sinr"
            run=evaluate_closed(model);
        else
            run=optimize(model,settings,string(fig.objective),(j-1)*1000,[checkpointprefix,'-main.json']);
        end
        entry=struct('configuration',point,'result',run);
        if string(settings.kind)=="sensing"&&any(string(fig.id)==["fig2","fig3","fig4"])
            if string(fig.objective)=="closed_form_sinr"&&run.available
                entry.beampattern_samples=beampattern_samples(model,run.state,run.selected_positions);
            elseif string(fig.objective)~="closed_form_sinr"&&~isempty(run.best_feasible)
                best=run.best_feasible;[~,selected]=max(best.metrics.binary_schedule,[],2);
                entry.beampattern_samples=beampattern_samples(model,best.state,selected-1,string(fig.objective));
            end
        end
        baselines=string(fig.baselines);
        if any(baselines=="closed_form")
            entry.closed_form=evaluate_closed(make_model(point,settings,false));
        end
        if string(settings.kind)=="communications"
            if any(string(fig.id)==["fig7","fig8"])&&~isempty(run.best_feasible),entry.beampattern_samples=communication_beampattern_samples(model,run.best_feasible.state);end
            if any(contains(baselines,"SMS"))
                sms=point; sms.ms2=[0 0];
                if any(baselines=="same_total_SMS")
                    if isfield(point,'total'), sms.ms1=[sqrt(point.total),sqrt(point.total)];
                    else,error('Fixed-total comparison requires exact total and aperture shape');end
                end
                entry.SMS=optimize(make_model(sms,settings,false),settings,"communications",500000+j-1,[checkpointprefix,'-sms.json']);
                if any(string(fig.id)==["fig7","fig8"])&&~isempty(entry.SMS.best_feasible),entry.SMS.beampattern_samples=communication_beampattern_samples(make_model(sms,settings,false),entry.SMS.best_feasible.state);end
            end
            if any(baselines=="dynamic_RIS"), entry.dynamic_RIS=struct('minimum_snr',settings.reference_snr*model.M^2); end
        else
            if any(startsWith(baselines,"RIS_")), entry.RIS=ris_baselines(model,settings,checkpointprefix); end
            if any(startsWith(baselines,"ralm_reference"))
                reference=point;
                if any(baselines=="ralm_reference_n6"),reference.ms2=[6 6];end
                if any(baselines=="ralm_reference_gap4"),reference.ms2=reference.ms1-[4 4];end
                entry.RALM_reference=optimize(make_model(reference,settings,false),settings,"sinr",900000+j-1,[checkpointprefix,'-reference.json']);
            end
        end
        result.points{end+1}=entry;
        progress=figure_execution_status(result.points,numel(points));flags=fieldnames(progress);for n=1:numel(flags),result.(flags{n})=progress.(flags{n});end
        write_output(outputPath,result);
    end
end
write_output(outputPath,result);
end

function status=figure_execution_status(points,fullcount)
complete=numel(points)==fullcount;verified=complete;
for j=1:numel(points)
entry=points{j};run=entry.result;
if isfield(run,'available'),ok=run.available&&isfield(run,'minimum_sinr')&&isfinite(run.minimum_sinr);complete=complete&&ok;verified=verified&&ok;
else,complete=complete&&run.full_start_budget_execution_complete;verified=verified&&run.overall_full_success;end
names={'SMS','RALM_reference'};
for n=1:numel(names),b=names{n};if isfield(entry,b),complete=complete&&entry.(b).full_start_budget_execution_complete;verified=verified&&entry.(b).overall_full_success;end,end
if isfield(entry,'RIS'),complete=complete&&entry.RIS.available;verified=verified&&isfield(entry.RIS,'optimization_convergence_verified')&&entry.RIS.optimization_convergence_verified;end
end
status=struct('full_figure_execution_complete',complete,'overall_full_success',verified,'original_figure_reproduction_certified',false);
end
function write_output(path,result)
[parent,~,~]=fileparts(path); if ~isempty(parent)&&~isfolder(parent), mkdir(parent); end
fid=fopen(path,'w','n','UTF-8'); assert(fid>=0,'Cannot create result file'); cleaner=onCleanup(@()fclose(fid));
fprintf(fid,'%s',jsonencode(result,'PrettyPrint',true));
end
function cells=as_cells(x)
if iscell(x),cells=x;elseif isempty(x),cells={};else,cells=arrayfun(@(y)y,x,'UniformOutput',false);end
end
function fig=findfigure(figures,id)
cells=as_cells(figures); for i=1:numel(cells),if string(cells{i}.id)==id,fig=cells{i};return;end,end
error('Unknown full paper figure %s',id);
end
function model=build_model(cfg)
mr=cfg.ms1(1);mc=cfg.ms1(2);nr=cfg.ms2(1);nc=cfg.ms2(2);
model.M=mr*mc;model.N=nr*nc;model.config=cfg;
if nr==0||nc==0,ix=zeros(1,0);else
assert(nr<=mr&&nc<=mc);ix=zeros((mr-nr+1)*(mc-nc+1),nr*nc);u=0;
for r=0:mr-nr,for c=0:mc-nc,u=u+1;n=0;for i=0:nr-1,for j=0:nc-1,n=n+1;ix(u,n)=(r+i)*mc+c+j+1;end,end,end,end
end
model.indices=ix;model.U=size(ix,1);coords=zeros(model.M,2);m=0;
for r=0:mr-1,for c=0:mc-1,m=m+1;coords(m,:)=[r c];end,end
az=deg2rad(cfg.azimuth_deg(:));el=deg2rad(cfg.elevation_deg(:));
direction=[sin(el).*cos(az),sin(el).*sin(az)];
model.c=exp(2i*pi*cfg.spacing_over_wavelength*(direction*coords.'));
model.c=model.c.*exp(2i*pi*cfg.spacing_over_wavelength*(coords*cfg.incidence_direction_cosines(:))).';
model.K=numel(az);if isfield(cfg,'number_of_targets'),model.targets=cfg.number_of_targets;else,model.targets=model.K;end
if isfield(cfg,'echo_beta_squared'),b=cfg.echo_beta_squared;else,b=1;end
if isscalar(b),model.beta=repmat(b,model.K,1);else,model.beta=b(:);end
end
function [bar,v,q,a]=fields(model,z)
bar=ones(model.U,model.M);
for u=1:model.U,bar(u,model.indices(u,:))=z.theta.';end
v=bar.*z.phi.';q=model.c*v.';a=abs(q).^2;
end
function [gamma,gp,gt]=metric(model,z,objective,W)
[bar,~,q,a]=fields(model,z);targets=model.targets;doGradient=nargin>=4;
if objective=="communications"
gamma=model.config.reference_snr*a;
elseif objective=="sinr"
S=model.beta.*a.^2;D=sum(S,1)-S(1:targets,:)+model.config.noise_over_power;gamma=S(1:targets,:)./D;
if doGradient,total=sum(W.*S(1:targets,:)./D.^2,1);coeff=-repmat(total,model.K,1);coeff(1:targets,:)=coeff(1:targets,:)+W./D+W.*S(1:targets,:)./D.^2;end
elseif objective=="pslr"
S=model.beta.*a.^2;mu=model.config.pslr_mu;e=model.config.pslr_epsilon;gamma=zeros(targets,model.U);coeff=zeros(size(S));
opponents=as_cells(model.config.pslr_opponents);
for k=1:targets
idx=opponents{k}(:)+1;ratios=S(k,:)./(S(idx,:)+e);mn=min(ratios,[],1);ex=exp(-(ratios-mn)/mu);pi=ex./sum(ex,1);gamma(k,:)=mn-mu*log(sum(ex,1));
if doGradient,wpi=W(k,:).*pi;coeff(k,:)=coeff(k,:)+sum(wpi./(S(idx,:)+e),1);coeff(idx,:)=coeff(idx,:)-wpi.*S(k,:)./(S(idx,:)+e).^2;end
end
else,error('Unknown objective');end
if ~doGradient,gp=[];gt=[];return;end
if objective=="communications",aq=2*model.config.reference_snr*W.*q;else,aq=4*coeff.*model.beta.*a.*q;end
gv=model.c'*aq;gp=sum(conj(bar.').*gv,2);gt=zeros(model.N,1);
for u=1:model.U,idx=model.indices(u,:);gt=gt+conj(z.phi(idx)).*gv(idx,u);end
end
function [f,eg,detail]=comm_objective(model,z,mu,convention)
gamma=metric(model,z,"communications");g=sum(z.X.*gamma,2);mn=min(g);ex=exp(-(g-mn)/mu);weights=ex/sum(ex);softmin=mn-mu*log(sum(ex));
[~,gp,gt]=metric(model,z,"communications",weights.*z.X);
if convention=="maximize_negative_softmin",signvalue=-1;elseif convention=="literal_paper_descent_of_f",signvalue=1;else,error('Select source-sign interpretation');end
f=signvalue*softmin;eg=struct('phi',signvalue*gp,'theta',signvalue*gt,'X',signvalue*weights.*gamma);detail=struct('softmin',softmin,'min_relaxed_snr',min(g));
end
function [f,eg,detail]=augmented(model,z,lambda,rho,objective)
gamma=metric(model,z,objective);q=z.eta-sum(z.X.*gamma,2);chi=max(0,lambda+rho*q);f=-z.eta+sum(chi.^2)/(2*rho);
[~,gp,gt]=metric(model,z,objective,-chi.*z.X);
eg=struct('phi',gp,'theta',gt,'X',-chi.*gamma,'eta',-1+sum(chi));detail=struct('q',q,'gamma',gamma);
end
function value=ip(a,b),value=real(sum(conj(a(:)).*b(:)));end
function g=project(z,eg)
g=eg;names=fieldnames(eg);for n=1:numel(names),b=names{n};
if strcmp(b,'phi')||strcmp(b,'theta'),g.(b)=eg.(b)-real(eg.(b).*conj(z.(b))).*z.(b);elseif strcmp(b,'X'),g.X=eg.X-mean(eg.X,2);end,end
end
function value=gnorm(g),names=fieldnames(g);value=0;for n=1:numel(names),value=value+ip(g.(names{n}),g.(names{n}));end,value=sqrt(value);end
function value=projected_kkt_norm(z,g),residual=g;residual.X=z.X-simplex(z.X-g.X);value=gnorm(residual);end
function X=simplex(Y)
X=zeros(size(Y));for k=1:size(Y,1),v=sort(Y(k,:),'descend');cs=cumsum(v)-1;j=1:numel(v);r=find(v-cs./j>0,1,'last');tau=cs(r)/r;X(k,:)=max(Y(k,:)-tau,0);end
end
function candidate=retract(z,d,alpha)
candidate=z;names=fieldnames(d);for n=1:numel(names),b=names{n};value=z.(b)+alpha*d.(b);
if strcmp(b,'phi')||strcmp(b,'theta'),candidate.(b)=value./abs(value);elseif strcmp(b,'X'),candidate.X=simplex(value);else,candidate.(b)=value;end,end
end
function [candidate,d,info,reason]=block_backtracking(z,g,d,evaluate,f,opts)
% Original distinct alpha per block; joint-coupling scaling is disclosed.
guard=isfield(opts,'non_descent_policy')&&string(opts.non_descent_policy)=="documented_non_descent_restart";
names=fieldnames(g);alphas=struct();backtracks=struct();restarts=struct();rawactual=struct();inactive=struct();rawslopes=struct();restartreasons=struct();reason='';candidate=z;
for n=1:numel(names)
b=names{n};alpha=opts.initial_step;if isfield(opts,'initial_steps')&&isfield(opts.initial_steps,b),alpha=opts.initial_steps.(b);end
if ip(g.(b),g.(b))==0,alphas.(b)=0;backtracks.(b)=0;inactive.(b)=true;rawactual.(b)=0;restarts.(b)=false;rawslopes.(b)=0;restartreasons.(b)={};continue;end
one=struct();one.(b)=d.(b);probe=retract(z,one,alpha);delta=probe.(b)-z.(b);rawactual.(b)=ip(g.(b),delta);restarts.(b)=false;
rawslopes.(b)=ip(g.(b),d.(b));restartreasons.(b)={};
if guard&&(rawslopes.(b)>=0||rawactual.(b)>=0)&&ip(g.(b),g.(b))>0
if rawslopes.(b)>=0,restartreasons.(b){end+1}='raw_non_descent';end
if rawactual.(b)>=0,restartreasons.(b){end+1}='projected_non_descent';end
d.(b)=-g.(b);one.(b)=d.(b);restarts.(b)=true;probe=retract(z,one,alpha);delta=probe.(b)-z.(b);
end
if ip(delta,delta)==0,alphas.(b)=0;backtracks.(b)=0;inactive.(b)=true;continue;end
inactive.(b)=false;rawslope=ip(g.(b),d.(b));accepted=false;
for ls=1:opts.max_backtracks
trialcandidate=retract(z,one,alpha);actual=ip(g.(b),trialcandidate.(b)-z.(b));if guard,predicted=actual;else,predicted=alpha*rawslope;end
trial=evaluate(trialcandidate);if isfinite(trial)&&predicted<0&&trial<=f+opts.armijo_constant*predicted,accepted=true;break;end
alpha=alpha*opts.backtrack_factor;
end
alphas.(b)=alpha;backtracks.(b)=ls-1;
if ~accepted
info=struct('block_step_sizes',alphas,'block_backtracks',backtracks,'block_non_descent_restarts',restarts,'block_raw_direction_slopes',rawslopes,'block_restart_reasons',restartreasons,'raw_projected_displacement_slopes',rawactual,'inactive_projected_blocks',inactive,'non_descent_restart',any(structfun(@(v)v,restarts)));
reason=['block_line_search_exhausted_',b];return;
end
end
info=struct('block_step_sizes',alphas,'block_backtracks',backtracks,'block_non_descent_restarts',restarts,'block_raw_direction_slopes',rawslopes,'block_restart_reasons',restartreasons,'raw_projected_displacement_slopes',rawactual,'raw_projected_displacement_slope',sum(structfun(@(v)v,rawactual)),'inactive_projected_blocks',inactive,'non_descent_restart',any(structfun(@(v)v,restarts)));
if ~any(structfun(@(v)v,alphas)>0)
if projected_kkt_norm(z,g)<opts.gradient_tolerance,reason='gradient_tolerance';else,reason='zero_projected_PR_direction';end,return;
end
scaled=struct();for n=1:numel(names),b=names{n};scaled.(b)=alphas.(b)*d.(b);end
coupling=1;accepted=false;
for ls=1:opts.max_backtracks
trialcandidate=retract(z,scaled,coupling);actual=0;rawpred=0;
for n=1:numel(names),b=names{n};actual=actual+ip(g.(b),trialcandidate.(b)-z.(b));rawpred=rawpred+alphas.(b)*ip(g.(b),d.(b));end
if guard,predicted=actual;else,predicted=coupling*rawpred;end
trial=evaluate(trialcandidate);if isfinite(trial)&&predicted<0&&trial<=f+opts.armijo_constant*predicted,accepted=true;break;end
coupling=coupling*opts.backtrack_factor;
end
info.coupling_scale=coupling;info.coupling_backtracks=ls-1;info.accepted_displacement_slope=actual;
if accepted,candidate=trialcandidate;else,reason='coupling_line_search_exhausted';end
end
function [z,history,stop]=rcg(z,evaluate,opts)
assert(any(string(opts.line_search_policy)==["common_product_armijo","original_per_block_backtracking"]));oldg=[];oldd=[];history={};reason='iteration_cap';
for iteration=0:opts.max_iterations-1
[f,eg]=evaluate(z);g=project(z,eg);ng=gnorm(g);guard=isfield(opts,'non_descent_policy')&&string(opts.non_descent_policy)=="documented_non_descent_restart";kkt=projected_kkt_norm(z,g);history{end+1}=struct('iteration',iteration,'objective',f,'gradient_norm',ng,'projected_kkt_norm',kkt);
if guard,stoppingnorm=kkt;else,stoppingnorm=ng;end
if iteration>0&&stoppingnorm<opts.gradient_tolerance,reason='gradient_tolerance';break;end
names=fieldnames(g);d=struct();betas=struct();if ~isempty(oldd),transport=project(z,oldd);end
for n=1:numel(names),b=names{n};beta=0;if ~isempty(oldg),den=ip(oldg.(b),oldg.(b));if den>0,beta=ip(g.(b),g.(b)-oldg.(b))/den;end,end
d.(b)=-g.(b);betas.(b)=beta;if ~isempty(oldg),d.(b)=d.(b)+beta*transport.(b);end,end
slope=0;for n=1:numel(names),b=names{n};slope=slope+ip(g.(b),d.(b));end
history{end}.raw_pr_beta=betas;history{end}.raw_pr_slope=slope;history{end}.non_descent_restart=false;
if string(opts.line_search_policy)=="original_per_block_backtracking"
[candidate,d,info,exitreason]=block_backtracking(z,g,d,evaluate,f,opts);infonames=fieldnames(info);for n=1:numel(infonames),history{end}.(infonames{n})=info.(infonames{n});end
if ~isempty(exitreason),reason=exitreason;break;end
oldg=g;oldd=d;z=candidate;continue;
end
probe=retract(z,d,opts.initial_step);actualslope=0;for n=1:numel(names),b=names{n};actualslope=actualslope+ip(g.(b),probe.(b)-z.(b));end
history{end}.raw_projected_displacement_slope=actualslope;if guard,nondescent=actualslope>=0;else,nondescent=slope>=0;end
if nondescent
if guard&&ng>0
for n=1:numel(names),b=names{n};d.(b)=-g.(b);end,slope=-ng^2;history{end}.non_descent_restart=true;
else,reason='non_descent_raw_PR_direction';break;end
end
alpha=opts.initial_step;accepted=false;
for ls=1:opts.max_backtracks,candidate=retract(z,d,alpha);trial=evaluate(candidate);
feasibleslope=0;for n=1:numel(names),b=names{n};feasibleslope=feasibleslope+ip(g.(b),candidate.(b)-z.(b));end
if guard,predicted=feasibleslope;else,predicted=alpha*slope;end
if isfinite(trial)&&predicted<0&&trial<=f+opts.armijo_constant*predicted,accepted=true;break;end,alpha=alpha*opts.backtrack_factor;end
if ~accepted,reason='line_search_exhausted';break;end
oldg=g;oldd=d;z=candidate;
end
[f,eg]=evaluate(z);rg=project(z,eg);if isfield(opts,'non_descent_policy')&&string(opts.non_descent_policy)=="documented_non_descent_restart",measure='projected_simplex_KKT';else,measure='printed_rowmean_gradient';end
stop=struct('reason',reason,'objective',f,'gradient_norm',gnorm(rg),'projected_kkt_norm',projected_kkt_norm(z,rg),'stationarity_measure',measure);
end
function [z,history,metrics]=comm_solve(model,z,opts)
mu=opts.initial_mu;history={};
while mu>=opts.terminal_mu
[z,h,stop]=rcg(z,@(x)comm_objective(model,x,mu,string(opts.objective_convention)),opts.rcg);
history{end+1}=struct('mu',mu,'inner',{h},'stop',stop);mu=mu*.5;
end
gamma=metric(model,z,"communications");binary=threshold(z.X);
metrics=struct('min_relaxed_snr',min(sum(z.X.*gamma,2)),'min_binary_snr',min(sum(binary.*gamma,2)),'binary_schedule',binary);
end
function [z,history,metrics]=sense_solve(model,z,opts,objective)
rho=opts.rho_initial;lambda=repmat(opts.lambda_initial,model.targets,1);epsilon=opts.epsilon_initial;factor=(opts.epsilon_min/epsilon)^(1/opts.outer_iterations);oldiota=[];history={};
for outer=1:opts.outer_iterations
oldz=z;inneropts=opts.rcg;inneropts.gradient_tolerance=epsilon;
[z,h,stop]=rcg(z,@(x)augmented(model,x,lambda,rho,objective),inneropts);[~,~,detail]=augmented(model,z,lambda,rho,objective);q=detail.q;
iota=max(q,-lambda/rho);newlambda=min(opts.lambda_max,max(opts.lambda_min,lambda+rho*q));
if outer==1||max(iota)<=opts.iota_progress_ratio*max(oldiota),newrho=rho;else,newrho=rho*opts.rho_factor;end
names=fieldnames(z);step=0;for n=1:numel(names),b=names{n};step=step+ip(z.(b)-oldz.(b),z.(b)-oldz.(b));end,step=sqrt(step);if outer==opts.outer_iterations,newepsilon=opts.epsilon_min;else,newepsilon=max(opts.epsilon_min,factor*epsilon);end
history{end+1}=struct('outer_iteration',outer,'rho_used',rho,'rho_next',newrho,'epsilon_used',epsilon,'epsilon_next',newepsilon,'eta',z.eta,'lambda',newlambda,'q',q,'iota',iota,'step',step,'inner',{h},'stop',stop);
stepstop=step<=opts.minimum_step;epsstop=newepsilon<=opts.epsilon_min;
lambda=newlambda;rho=newrho;epsilon=newepsilon;oldiota=iota;
if string(opts.outer_stopping_logic)=="algorithm_OR",finished=stepstop||epsstop;else,finished=stepstop&&epsstop;end
if finished,break;end
end
gamma=metric(model,z,objective);binary=threshold(z.X);q=z.eta-sum(z.X.*gamma,2);
metrics=struct('eta',z.eta,'min_relaxed_metric',min(sum(z.X.*gamma,2)),'min_binary_metric',min(sum(binary.*gamma,2)),'maximum_constraint',max(q),'multipliers',lambda,'penalty',rho,'binary_schedule',binary);
end
function binary=threshold(X)
[~,selected]=max(X,[],2);binary=zeros(size(X));for k=1:size(X,1),binary(k,selected(k))=1;end
end
function state=serialize(z)
state=struct();names=fieldnames(z);for n=1:numel(names),b=names{n};v=z.(b);if strcmp(b,'phi')||strcmp(b,'theta'),state.(b)=struct('real',real(v),'imag',imag(v));else,state.(b)=v;end,end
end
function errors=gradient_check(z,evaluate)
[~,eg]=evaluate(z);g=project(z,eg);names=fieldnames(g);errors=struct();h=1e-6;
for n=1:numel(names),b=names{n};d=struct();for j=1:numel(names),other=names{j};d.(other)=zeros(size(g.(other)));end
if strcmp(b,'phi')||strcmp(b,'theta'),d.(b)=1i*z.(b).*cos((0:numel(z.(b))-1)'+.3);
elseif strcmp(b,'X'),raw=reshape(cos((0:numel(z.X)-1)+.4),size(z.X,2),size(z.X,1)).';d.X=raw-mean(raw,2);else,d.eta=.31;end
fp=evaluate(retract(z,d,h));fm=evaluate(retract(z,d,-h));fd=(fp-fm)/(2*h);ana=ip(g.(b),d.(b));errors.(b)=abs(fd-ana)/max([1,abs(fd),abs(ana)]);
end
end
function result=component_test(base,kind,guarded)
fixture=jsondecode(fileread(fullfile(base,'unit_fixture.json')));model=build_model(fixture.model);
z=struct('phi',exp(1i*fixture.phi_angles(:)),'theta',exp(1i*fixture.theta_angles(:)),'X',fixture.X,'eta',fixture.eta);opts=fixture.unit_options;
if guarded,opts.line_search_policy='original_per_block_backtracking';opts.non_descent_policy='documented_non_descent_restart';end
if string(kind)=="communications"
z=rmfield(z,'eta');errors=gradient_check(z,@(x)comm_objective(model,x,1.3,"maximize_negative_softmin"));
options=struct('rcg',opts,'initial_mu',1.3,'terminal_mu',.65,'objective_convention','maximize_negative_softmin');[z,h,metrics]=comm_solve(model,z,options);
else
errors=gradient_check(z,@(x)augmented(model,x,[.31;.21;.27],1.7,"sinr"));
options=struct('rcg',opts,'outer_iterations',3,'epsilon_initial',1e-3,'epsilon_min',1e-6,'rho_initial',1,'rho_factor',1.2,'iota_progress_ratio',.8,'lambda_initial',0,'lambda_min',0,'lambda_max',1e10,'minimum_step',1e-10,'outer_stopping_logic','numerical_text_AND');[z,h,metrics]=sense_solve(model,z,options,"sinr");
end
[~,v,~,a]=fields(model,z);reconstructed=zeros(size(a));
% Independent Hermitian quadratic: v^H G v. v stored as an ordinary row.
for k=1:model.K,G=conj(model.c(k,:)).'*model.c(k,:);for u=1:model.U,vcol=v(u,:).';reconstructed(k,u)=real(vcol'*G*vcol);end,end
values=struct2array_local(errors);
loopq=zeros(size(a));for k=1:model.K,for u=1:model.U,for m=1:model.M,loopq(k,u)=loopq(k,u)+model.c(k,m)*v(u,m);end,end,end
[~,~,matrixq]=fields(model,z);
checks=struct('gradient_errors',errors,'gradient_pass',max(values)<1e-6,'quadratic_identity_error',max(abs(a(:)-reconstructed(:)))/max(1,max(a(:))),...
'ordinary_transpose_amplitude_error',max(abs(matrixq(:)-loopq(:)))/max(1,max(abs(matrixq(:)))),...
'quartic_echo_identity_error',max(abs(a(:).^2-reconstructed(:).^2))/max(1,max(a(:).^2)),...
'number_of_positions_correct',model.U==(model.config.ms1(1)-model.config.ms2(1)+1)*(model.config.ms1(2)-model.config.ms2(2)+1),...
'constraint_pass',max(abs(abs(z.phi)-1))<1e-12&&max(abs(abs(z.theta)-1))<1e-12&&max(abs(sum(z.X,2)-1))<1e-12&&min(z.X(:))>=0);
if guarded,checks.production_line_search_regression=line_search_checks(opts);end
if string(kind)=="sensing"
lastlambda=zeros(model.targets,1);lastiota=[];penaltyerror=0;multipliererror=0;iotaerror=0;epsilonerror=0;
for j=1:numel(h),entry=h{j};q=entry.q;rho=entry.rho_used;ii=max(q,-lastlambda/rho);ll=min(1e10,max(0,lastlambda+rho*q));
if j==1||max(ii)<=.8*max(lastiota),rr=rho;else,rr=1.2*rho;end
penaltyerror=max(penaltyerror,abs(rr-entry.rho_next));multipliererror=max(multipliererror,max(abs(ll-entry.lambda)));iotaerror=max(iotaerror,max(abs(ii-entry.iota)));epsilonerror=max(epsilonerror,abs(max(1e-6,(1e-6/1e-3)^(1/3)*entry.epsilon_used)-entry.epsilon_next));lastlambda=ll;lastiota=ii;end
checks.ralm_update_errors=struct('penalty',penaltyerror,'multipliers',multipliererror,'iota',iotaerror,'epsilon',epsilonerror);checks.ralm_update_pass=max([penaltyerror,multipliererror,iotaerror,epsilonerror])<1e-12;
cfg=fixture.model;cfg.azimuth_deg=[32 51 68 44 61];cfg.elevation_deg=[18 46 76 31 59];cfg.number_of_targets=3;cfg.pslr_opponents={[1 2 3 4],[0 2 3 4],[0 1 3 4]};cfg.pslr_mu=.7;cfg.pslr_epsilon=1e-9;pm=build_model(cfg);
initial=struct('phi',exp(1i*fixture.phi_angles(:)),'theta',exp(1i*fixture.theta_angles(:)),'X',fixture.X,'eta',.4);
pg=gradient_check(initial,@(x)augmented(pm,x,[.31;.21;.27],1.7,"pslr"));checks.pslr_gradient_errors=pg;checks.pslr_gradient_pass=max(struct2array_local(pg))<1e-6;
end
result=struct('paper_id','mis-sensing','scope','component_unit_test_not_paper_figure','metrics',metrics,'checks',checks,'history',{h},'state',serialize(z));
end
function values=struct2array_local(s),names=fieldnames(s);values=zeros(1,numel(names));for k=1:numel(names),values(k)=s.(names{k});end,end
function [draws,state]=random_values(n,state)
draws=zeros(n,1);for k=1:n,state=mod(16807*state,2147483647);draws(k)=state/2147483647;end
end
function [z,state]=initialize(model,settings,state)
[x,state]=random_values(model.targets*model.U,state);X=reshape(x,model.U,model.targets).';X=X./sum(X,2);
[p,state]=random_values(model.M,state);[t,state]=random_values(model.N,state);
z=struct('phi',exp(2i*pi*p),'theta',exp(2i*pi*t),'X',X);
if string(settings.kind)=="sensing",z.eta=settings.initialization.eta_initial;end
end
function checks=line_search_checks(opts)
opts.line_search_policy='original_per_block_backtracking';opts.non_descent_policy='documented_non_descent_restart';
z=struct('phi',1+0i,'theta',ones(2,1),'X',1);w=[1;2];g=struct('phi',0+0i,'theta',1i*w,'X',0);d=struct('phi',0+0i,'theta',1i*[10;-1],'X',0);
evaluate=@(x)sum(w.*imag(x.theta)+2*(1-real(x.theta)));
[new,~,info,reason]=block_backtracking(z,g,d,evaluate,evaluate(z),opts);raw=ip(g.theta,d.theta);actual=info.raw_projected_displacement_slopes.theta;
rawpass=isempty(reason)&&raw>=0&&actual<0&&any(strcmp(info.block_restart_reasons.theta,'raw_non_descent'))&&evaluate(new)<evaluate(z)&&max(abs(abs(new.theta)-1))<1e-12;
z=struct('phi',1+0i,'theta',zeros(0,1),'X',[.5 .5 0]);g=struct('phi',0+0i,'theta',zeros(0,1),'X',[-2 -1 3]);d=struct('phi',0+0i,'theta',zeros(0,1),'X',[-2 4 -2]);
evaluate=@(x)sum(g.X.*x.X);
[new,~,info,reason]=block_backtracking(z,g,d,evaluate,evaluate(z),opts);
projectedpass=isempty(reason)&&info.block_raw_direction_slopes.X<0&&info.raw_projected_displacement_slopes.X>0&&numel(info.block_restart_reasons.X)==1&&strcmp(info.block_restart_reasons.X{1},'projected_non_descent')&&evaluate(new)<evaluate(z);
z=struct('phi',1+0i,'theta',zeros(0,1),'X',1,'eta',0);g=struct('phi',0+0i,'theta',zeros(0,1),'X',0,'eta',-1);d=struct('phi',0+0i,'theta',zeros(0,1),'X',0,'eta',1);
evaluate=@(x).5*(x.eta-1)^2;
[new,~,info,reason]=block_backtracking(z,g,d,evaluate,evaluate(z),opts);
emptypass=isempty(reason)&&new.eta==1&&info.inactive_projected_blocks.phi&&info.inactive_projected_blocks.theta&&info.inactive_projected_blocks.X;
z=struct('phi',1+0i,'theta',zeros(0,1),'X',[1 0]);
[~,~,stop]=rcg(z,@vertex_test_objective,opts);vertexpass=strcmp(stop.reason,'gradient_tolerance')&&stop.gradient_norm>.5&&stop.projected_kkt_norm==0;
checks=struct('circle_raw_slope_counterexample',raw,'circle_initial_actual_slope_counterexample',actual,'raw_non_descent_restart_pass',rawpass,'projected_non_descent_restart_pass',projectedpass,'empty_stationary_blocks_pass',emptypass,'closed_simplex_KKT_pass',vertexpass);
assert(rawpass&&projectedpass&&emptypass&&vertexpass,'Production line-search guard regression failed');
end
function [f,eg,detail]=vertex_test_objective(z)
f=-z.X(1);eg=struct('phi',0+0i,'theta',zeros(0,1),'X',[-1 0]);detail=struct();
end
function opts=solver_options(settings)
rcgopts=settings.line_search;rcgopts.max_iterations=settings.rcg_max_iterations;
if string(settings.kind)=="communications"
rcgopts.gradient_tolerance=settings.rcg_gradient_tolerance;opts=struct('rcg',rcgopts,'initial_mu',settings.initial_mu_values(1),'terminal_mu',settings.terminal_mu,'objective_convention',settings.objective_convention);
else
opts=struct('rcg',rcgopts);names={'outer_iterations','epsilon_initial','epsilon_min','rho_initial','rho_factor','iota_progress_ratio','lambda_min','lambda_max','minimum_step','outer_stopping_logic'};
for k=1:numel(names),opts.(names{k})=settings.(names{k});end,opts.lambda_initial=settings.initialization.lambda_initial;
end
end
function model=make_model(point,settings,pslr)
if string(settings.kind)=="communications"
K=point.K;if K==1,az=0;else,az=linspace(-60,60,K);end,el=45*ones(1,K);
else
% Original EPS axes/markers recover phi0/45/90, theta30/50/70.
% Eq3c defines phi=azimuth, theta=elevation; numerical text swaps ranges.
kp=point.Kphi;kt=point.Ktheta;if kp==1,azimuth=45;else,azimuth=linspace(0,90,kp);end
if kt==1,elevation=50;else,elevation=linspace(30,70,kt);end
az=repmat(azimuth,1,kt);el=repelem(elevation,kp);K=numel(az);
end
cfg=struct('ms1',point.ms1,'ms2',point.ms2,'azimuth_deg',az,'elevation_deg',el,'spacing_over_wavelength',settings.spacing_over_wavelength,'incidence_direction_cosines',settings.incidence_direction_cosines,'number_of_targets',K,'reference_snr',.01);
if string(settings.kind)=="communications",cfg.reference_snr=settings.reference_snr;else
cfg.echo_beta_squared=10^(settings.reference_echo_db/10);P=settings.power_dbm;if isfield(point,'power_dbm'),P=point.power_dbm;end
cfg.noise_over_power=1/10^((P-30)/10);
end
if pslr
gp=settings.pslr_grid(1);gt=settings.pslr_grid(2);caz=repmat(linspace(0,90,gp),1,gt);cel=repelem(linspace(30,70,gt),gp);
cfg.azimuth_deg=[az,caz];cfg.elevation_deg=[el,cel];cfg.echo_beta_squared=[repmat(10^(settings.reference_echo_db/10),1,K),repmat(10^(settings.reference_echo_db/10)*settings.clutter_relative_echo,1,gp*gt)];
cfg.pslr_opponents=cell(K,1);
for k=1:K,outside=abs(caz-az(k))>settings.mainlobe_guard_azimuth_deg|abs(cel-el(k))>settings.mainlobe_guard_elevation_deg;cfg.pslr_opponents{k}=[setdiff(0:K-1,k-1),K+find(outside)-1];end
cfg.pslr_mu=settings.pslr_mu_initial;cfg.pslr_epsilon=settings.pslr_epsilon;
end
model=build_model(cfg);
end
function status=solver_diagnostics(h,settings,objective)
comm=string(settings.kind)=="communications";groups={h};
if ~comm&&objective=="pslr",groups={};for j=1:numel(h),groups{end+1}=as_cells(h{j}.outer);end,end
entries={};for j=1:numel(groups),entries=[entries,as_cells(groups{j})];end
guard=isfield(settings.line_search,'non_descent_policy')&&string(settings.line_search.non_descent_policy)=="documented_non_descent_restart";
norms=zeros(1,numel(entries));tolerances=norms;stationary=false(size(norms));reasons=cell(size(norms));
for j=1:numel(entries)
x=entries{j};if guard,norms(j)=x.stop.projected_kkt_norm;else,norms(j)=x.stop.gradient_norm;end
if comm,tolerances(j)=settings.rcg_gradient_tolerance;else,tolerances(j)=x.epsilon_used;end
stationary(j)=isfinite(norms(j))&&norms(j)<=tolerances(j);reasons{j}=x.stop.reason;
end
if comm,outermet=true;continuation=numel(h)>0&&h{end}.mu*.5<settings.terminal_mu;
else
decisions=false(1,numel(groups));
for j=1:numel(groups),group=groups{j};last=group{end};stepstop=last.step<=settings.minimum_step;epsstop=last.epsilon_next<=settings.epsilon_min;
if string(settings.outer_stopping_logic)=="algorithm_OR",decisions(j)=stepstop||epsstop;else,decisions(j)=stepstop&&epsstop;end,end
outermet=all(decisions);continuation=true;
end
failure=sum(contains(string(reasons),"line_search")|contains(string(reasons),"non_descent")|contains(string(reasons),"zero_projected"));
status=struct('final_inner_stationary',stationary(end),'all_inner_tolerances_satisfied',all(stationary),'final_inner_residual',norms(end),'final_inner_tolerance',tolerances(end),'outer_stopping_applicable',~comm,'outer_stopping_met',outermet,'continuation_complete',continuation,'inner_iteration_cap_exits',sum(string(reasons)=="iteration_cap"),'inner_failure_exits',failure,'convergence_verified',all(stationary)&&outermet&&continuation&&failure==0,'final_inner_exit_reason',reasons{end});
end
function result=diagnostic_start(fig,settings,start)
assert(settings.number_of_starts==6000&&settings.rcg_max_iterations==4000&&(string(settings.kind)=="communications"||settings.outer_iterations==30),'Full-size diagnostics retain strict per-start budgets');
assert(start>=1&&start<=settings.number_of_starts&&start==floor(start),'Diagnostic start outside original start bank');
points=as_cells(fig.points);point=points{1};objective=string(fig.objective);assert(objective~="closed_form_sinr",'Closed form has no random optimization start');
model=make_model(point,settings,objective=="pslr");state=settings.initialization.seed;
for j=1:start,[z,state]=initialize(model,settings,state);end
opts=solver_options(settings);
if string(settings.kind)=="communications"
opts.initial_mu=settings.initial_mu_values(mod(start-1,numel(settings.initial_mu_values))+1);[z,h,metrics]=comm_solve(model,z,opts);
elseif objective=="pslr"
mu=settings.pslr_mu_initial;h={};
while mu>=settings.pslr_mu_terminal,model.config.pslr_mu=mu;[z,outer,metrics]=sense_solve(model,z,opts,objective);h{end+1}=struct('mu',mu,'outer',{outer});mu=mu*settings.pslr_mu_factor;end
else,[z,h,metrics]=sense_solve(model,z,opts,objective);
end
result=struct('paper_id','mis-sensing','scope','single_original_full_start_diagnostic_not_full_figure','figure',fig.id,'start',start,'original_number_of_starts',settings.number_of_starts,'configuration',point,'settings',settings,'metrics',metrics,'solver_status',solver_diagnostics(h,settings,objective),'history',{h},'state',serialize(z),'implementation_digest',implementation_digest());
end
function out=optimize(model,settings,objective,seedoffset,checkpointpath)
if nargin<5,checkpointpath='';end
state=settings.initialization.seed+seedoffset;opts=solver_options(settings);summaries={};best=[];if isfield(settings,'outer_iterations'),nouter=settings.outer_iterations;else,nouter=1;end
means=zeros(1,nouter);violations=zeros(1,nouter);counts=zeros(1,nouter);
source=implementation_digest();signature=jsonencode(struct('schema_version',2,'implementation_digest',source,'settings',settings,'model',model.config,'objective',objective,'seed_offset',seedoffset));bestpath=[checkpointpath,'.best.json'];
if ~isempty(checkpointpath)&&isfile(checkpointpath)
saved=jsondecode(fileread(checkpointpath));assert(isfield(saved,'schema_version')&&saved.schema_version==2&&isfield(saved,'implementation_digest')&&strcmp(saved.implementation_digest,source),'Legacy/different implementation checkpoint rejected; preserve it and use a new output directory');assert(strcmp(saved.signature,signature),'Checkpoint settings/model differ; choose a new output path');summaries=as_cells(saved.all_start_summaries);state=saved.random_state;means=saved.mean_outer_sum(:).';violations=saved.mean_violation_sum(:).';counts=saved.mean_outer_counts(:).';if saved.has_best,best=jsondecode(fileread(bestpath));end
end
for start=numel(summaries)+1:settings.number_of_starts
[z,state]=initialize(model,settings,state);
if string(settings.kind)=="communications"
opts.initial_mu=settings.initial_mu_values(mod(start-1,numel(settings.initial_mu_values))+1);[z,h,metrics]=comm_solve(model,z,opts);feasible=true;score=metrics.min_binary_snr;binarymetric=metrics.min_binary_snr;
else
if objective=="pslr"
mu=settings.pslr_mu_initial;stages={};while mu>=settings.pslr_mu_terminal
model.config.pslr_mu=mu;[z,h,metrics]=sense_solve(model,z,opts,objective);stages{end+1}=struct('mu',mu,'outer',{h});mu=mu*settings.pslr_mu_factor;
end,h=stages;
else
[z,h,metrics]=sense_solve(model,z,opts,objective);for j=1:nouter,entry=h{min(j,numel(h))};means(j)=means(j)+entry.eta;violations(j)=violations(j)+max(0,max(entry.q));counts(j)=counts(j)+1;end
end
feasible=metrics.maximum_constraint<=settings.feasibility_tolerance;score=metrics.eta;binarymetric=metrics.min_binary_metric;
end
diagnostic=solver_diagnostics(h,settings,objective);
if string(settings.kind)=="communications",binaryfeasible=true;else,binaryfeasible=metrics.eta-metrics.min_binary_metric<=settings.feasibility_tolerance;end
if feasible&&diagnostic.convergence_verified,status='converged_feasible';elseif feasible,status='feasible_not_convergence_verified';else,status='infeasible';end
summaries{end+1}=struct('start',start,'feasible',feasible,'binary_eta_feasible',binaryfeasible,'score',score,'solver_status',diagnostic,'exit_status',status,'min_binary_metric',binarymetric);
if feasible&&(isempty(best)||score>best.score),best=struct('score',score,'start',start,'metrics',metrics,'history',{h},'state',serialize(z),'solver_status',diagnostic,'binary_eta_feasible',binaryfeasible);if ~isempty(checkpointpath),write_output(bestpath,best);end,end
if ~isempty(checkpointpath)
saved=struct('schema_version',2,'implementation_digest',source,'signature',signature,'completed_starts',numel(summaries),'random_state',state,'all_start_summaries',{summaries},'mean_outer_sum',means,'mean_violation_sum',violations,'mean_outer_counts',counts,'has_best',~isempty(best));
temporary=[checkpointpath,'.tmp'];write_output(temporary,saved);movefile(temporary,checkpointpath,'f');
end
end
means(counts>0)=means(counts>0)./counts(counts>0);
violations(counts>0)=violations(counts>0)./counts(counts>0);
complete=numel(summaries)==settings.number_of_starts;certified=complete&&~isempty(best)&&best.solver_status.convergence_verified&&best.binary_eta_feasible;
out=struct('implementation_digest',source,'best_feasible',best,'all_start_summaries',{summaries},'full_start_budget_execution_complete',complete,'selected_best_convergence_verified',certified,'overall_full_success',certified,'original_figure_reproduction_certified',false,'mean_outer_eta',means,'mean_outer_violation',violations,'mean_outer_counts',counts,'number_of_starts',settings.number_of_starts);
end
function digest=implementation_digest()
base=fileparts(mfilename('fullpath'));files=[dir(fullfile(base,'*.py'));dir(fullfile(base,'*.m'));dir(fullfile(base,'source_map.json'))];[~,order]=sort({files.name});files=files(order);md=java.security.MessageDigest.getInstance('SHA-256');
for k=1:numel(files),fid=fopen(fullfile(base,files(k).name),'rb');assert(fid>=0);bytes=fread(fid,Inf,'*uint8');fclose(fid);md.update(uint8(unicode2native([files(k).name,char(0)],'UTF-8')));md.update(bytes);end
md.update(uint8(unicode2native([char(0),version,char(0),computer],'UTF-8')));
raw=typecast(md.digest(),'uint8');digest=lower(reshape(dec2hex(raw,2).',1,[]));
end
function out=evaluate_closed(model)
mr=model.config.ms1(1);mc=model.config.ms1(2);nr=model.config.ms2(1);nc=model.config.ms2(2);ur=mr-nr+1;uc=mc-nc+1;
if min(ur,uc)<=1,out=struct('available',false,'reason','Published closed-form A is singular when Ur or Uc equals one');return;end
d=model.config.spacing_over_wavelength;A=pi/d*max(1/(ur-1),1/(uc-1));phase=zeros(model.M,1);nphase=zeros(model.N,1);m=0;
for r=0:mr-1,for c=0:mc-1,m=m+1;phase(m)=A*d*d*(r*r+c*c);end,end
n=0;for r=0:nr-1,for c=0:nc-1,n=n+1;nphase(n)=-A*d*d*((r+ur-1)^2+(c+uc-1)^2);end,end
z=struct('phi',exp(1i*phase),'theta',exp(1i*nphase),'X',zeros(model.targets,model.U),'eta',0);gm=metric(model,z,"sinr");
az=deg2rad(model.config.azimuth_deg(1:model.targets));el=deg2rad(model.config.elevation_deg(1:model.targets));rows=min(ur-1,max(0,floor((ur-1)-pi/(A*d)*sin(el).*cos(az)+.5)));cols=min(uc-1,max(0,floor((uc-1)-pi/(A*d)*sin(el).*sin(az)+.5)));selected=rows(:)*uc+cols(:)+1;values=zeros(model.targets,1);
for k=1:model.targets,z.X(k,selected(k))=1;values(k)=gm(k,selected(k));end
out=struct('available',true,'minimum_sinr',min(values),'selected_positions',selected-1,'state',serialize(z));
end
function out=communication_beampattern_samples(model,state)
az=-90:.5:90;cfg=model.config;cfg.azimuth_deg=az;cfg.elevation_deg=45*ones(size(az));cfg.number_of_targets=numel(az);grid=build_model(cfg);
z=struct('phi',state.phi.real(:)+1i*state.phi.imag(:),'theta',state.theta.real(:)+1i*state.theta.imag(:));snr=metric(grid,z,"communications");[~,selected]=max(state.X,[],2);
out=struct('scope','model_evaluated_complete_azimuth_cut_not_original_curve_copy','azimuth_deg',az,'elevation_deg',45,'resolution_deg',.5,'pattern_snr',snr,'number_of_patterns',model.U,'user_azimuth_deg',model.config.azimuth_deg,'user_pattern',selected-1,'user_snr_by_pattern',metric(model,z,"communications"));
end
function out=beampattern_samples(model,state,selected,objective)
if nargin<4,objective="sinr";end
az=-180:180;el=0:90;cfg=model.config;cfg.azimuth_deg=repelem(az,numel(el));cfg.elevation_deg=repmat(el,1,numel(az));cfg.echo_beta_squared=1;cfg.number_of_targets=numel(az)*numel(el);grid=build_model(cfg);
z=struct('phi',state.phi.real(:)+1i*state.phi.imag(:),'theta',state.theta.real(:)+1i*state.theta.imag(:));[~,~,~,powers]=fields(grid,z);[~,~,~,original]=fields(model,z);all_echo=model.beta.*original.^2;echo=all_echo(1:model.targets,:);maps=cell(model.targets,1);
if objective=="pslr",smooth=metric(model,z,"pslr");opponents=as_cells(model.config.pslr_opponents);end
for k=1:model.targets,u=selected(k)+1;raw=reshape(powers(:,u),numel(el),numel(az));denominator=sum(echo(:,u))-echo(k,u)+model.config.noise_over_power;
maps{k}=struct('target',k-1,'pattern',u-1,'normalized_gain',raw/max(raw(:)),'sinr',model.beta(k)*raw.^2/denominator,'target_azimuth_deg',model.config.azimuth_deg(k),'target_elevation_deg',model.config.elevation_deg(k),'target_metric_name','SINR','target_metric',echo(k,u)/denominator);
if objective=="pslr",peak=max(all_echo(opponents{k}+1,u));exact=[];if peak>0,exact=all_echo(k,u)/peak;end,maps{k}.target_metric_name='PSLR';maps{k}.target_metric=exact;maps{k}.smoothed_target_metric=smooth(k,u);maps{k}.sidelobe_echo_peak=peak;end
end
out=struct('scope','full_front_hemisphere_independent_samples','resolution_deg',1,'objective',char(objective),'azimuth_deg',az,'elevation_deg',el,'maps',{maps});
end
function out=ris_baselines(model,settings,checkpointprefix)
if nargin<3,checkpointprefix='';end
continuous=zeros(1,model.targets);onebit=continuous;twobit=continuous;converged=true;
for k=1:model.targets
order=[k,setdiff(1:model.targets,k)];cfg=model.config;cfg.ms2=[0,0];cfg.number_of_targets=1;cfg.azimuth_deg=cfg.azimuth_deg(order);cfg.elevation_deg=cfg.elevation_deg(order);cfg.echo_beta_squared=model.beta(order);
ris=build_model(cfg);if isempty(checkpointprefix),cp='';else,cp=[checkpointprefix,sprintf('-ris-target-%d.json',k-1)];end
run=optimize(ris,settings,"sinr",100000+k-1,cp);
if isempty(run.best_feasible),out=struct('available',false,'reason','At least one RIS target has no feasible run');return;end
converged=converged&&run.overall_full_success;raw=run.best_feasible.state.phi;phi=raw.real+1i*raw.imag;z=struct('phi',phi,'theta',zeros(0,1),'X',1,'eta',0);g=metric(ris,z,"sinr");continuous(k)=g(1);
for bits=1:2,step=2*pi/(2^bits);z.phi=exp(1i*step*floor(angle(phi)/step+.5));g=metric(ris,z,"sinr");if bits==1,onebit(k)=g(1);else,twobit(k)=g(1);end,end
end
out=struct('available',true,'optimization_convergence_verified',converged,'continuous',continuous,'one_bit',onebit,'two_bit',twobit);
end
