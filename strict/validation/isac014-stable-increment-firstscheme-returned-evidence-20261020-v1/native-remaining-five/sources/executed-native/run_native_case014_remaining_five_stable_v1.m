function summary=run_native_case014_remaining_five_stable_v1(outputRoot,scenarioPath,configPath,planPath,admissionPath)
% Only five cold original scheme families, same disclosed stable controls.
plan=jsondecode(fileread(planPath));admission=jsondecode(fileread(admissionPath));
assert(admission.root_admitted_only_case014_remaining_five_stable_schemes,'False root admission');
assert(strcmp(admission.plan_SHA256,is_sha_file(planPath)),'Plan admission mismatch');
assert(isequal(admission.allowed_scheme_ordinals_by_lane.native(:),(2:6)'),'Wrong missing-only ordinal scope');
assert(strcmp(strrep(outputRoot,'\','/'),strrep(plan.lanes.native.fresh_output_directory,'\','/')),'Wrong native fresh output');
assert(~isfolder(outputRoot)&&~isfile(outputRoot),'Preserve every old/partial lane output');
assert(strcmp(is_sha_file(configPath),plan.complete_configuration_SHA256)&&strcmp(is_sha_file(scenarioPath),plan.original_scene_SHA256),'Wrong case014 input bytes');
c=jsondecode(fileread(scenarioPath));cfg=jsondecode(fileread(configPath));names=fieldnames(cfg);assert(numel(names)==28);
for k=1:numel(names),assert(isfield(c,names{k})&&isequal(c.(names{k}),cfg.(names{k})),'All28 controls must match original scene');end
assert(c.rho==10&&numel(c.noise)==2&&size(c.bs_coordinates,1)==4&&size(c.ris_coordinates,1)==36&&numel(c.desired_pattern)==66);
assert(c.RCG_solver.maximum_iterations==5000&&c.PGA_solver.maximum_iterations==5000&&c.AO_solver.maximum_iterations==500&&c.W_solver.maximum_iterations==10000);
assert(c.RCG_solver.gradient_tolerance==1e-6&&c.PGA_solver.gradient_tolerance==1e-6&&c.PGA_solver.relative_tolerance==1e-10);
assert(c.RCG_solver.initial_step==1&&c.RCG_solver.maximum_backtracks==80&&c.PGA_solver.maximum_backtracks==80);
assert(strcmp(c.RCG_solver.mode,'documented_non_ascent_restart')&&strcmp(c.PGA_solver.BB_interpretation,'ascent_sign_correction'));
% jsondecode cannot preserve arbitrary path keys as struct fields. The pinned
% source list therefore lives in the plan's parallel explicit array below.
before=is_guard_sources(plan.native_guard_sources);mkdir(outputRoot);started=tic;rows={};hostError=[];after=[];
allNames={'Rot-BS & Rot-RIS','Rot-BS & Fix-RIS','Fix-BS & Rot-RIS','Fix-BS & Fix-RIS','Rot-BS & No-RIS','Fix-BS & No-RIS'};
allFlags=[1,1,1;1,0,1;0,1,1;0,0,1;1,0,0;0,0,0];
try
    for selectedScheme=2:6
        folder=fullfile(outputRoot,sprintf('scheme-%02d',selectedScheme));assert(~isfolder(folder));mkdir(folder);localStarted=tic;
        scene=c;if ~allFlags(selectedScheme,3),scene.br_gain_re(:)=0;scene.br_gain_im(:)=0;end
        is_passive_return_capture('initialize',struct('scene',scene,'configuration',cfg,'original_scene',c,'scheme',allNames{selectedScheme},'scheme_ordinal',selectedScheme));
        result=is_full_scenario(c,true,selectedScheme);recording=is_passive_return_capture('snapshot',[]); %#ok<NASGU>
        result.mode='only_case014_remaining_single_scheme_current_stable_arithmetic';result.scheme_ordinal=selectedScheme;
        result.elapsed_seconds=toc(localStarted);result.original_controls=struct('W_solver',c.W_solver,'RCG_solver',c.RCG_solver,'PGA_solver',c.PGA_solver,'AO_solver',c.AO_solver);
        result.original_algorithm_full_stop=strcmp(result.checks{1}.status,'executed')&&result.checks{1}.full_converged;
        result.strict_RCG_returned_blocks_pass=[];result.strict_PGA_returned_blocks_pass=[];captureComplete=true;
        if strcmp(result.checks{1}.status,'executed')
            blocks=result.history{1}.blocks;expected=numel(blocks)*(2+allFlags(selectedScheme,3));
            captureComplete=numel(recording.returns)==expected;
            result.strict_PGA_returned_blocks_pass=all(arrayfun(@(b)b.rotation.final_projected_gradient_norm<=c.PGA_solver.gradient_tolerance,blocks));
            if allFlags(selectedScheme,3),result.strict_RCG_returned_blocks_pass=all(arrayfun(@(b)b.RIS.final_normalized_gradient_norm<=c.RCG_solver.gradient_tolerance,blocks));end
        end
        result.actual_returned_block_state_count=numel(recording.returns);result.RCG_gate_applicable=logical(allFlags(selectedScheme,3));
        result.capture_complete_for_returned_scheme=captureComplete;
        result.independent_physics_feasibility_MP_PASS=[];result.final_joint_stationarity_PASS=[];result.W_author_absolute_stationarity_gate=[];
        result.original_reference_or_full_paper_PASS=false;
        % Save full complex numeric returned states before scalar JSON. No
        % additional model evaluation is used for this transport operation.
        save(fullfile(folder,'actual-native-scheme-states.mat'),'result','scene','cfg','recording','-v7');
        is_put_json(fullfile(folder,'full-result.json'),result);
        code=2;if result.original_algorithm_full_stop,code=0;end
        if ~captureComplete,code=1;end
        row=struct('ordinal',selectedScheme,'scheme',allNames{selectedScheme},'actual_entry_exit',code,'algorithm_full_stop',result.original_algorithm_full_stop,...
            'strict_own_RCG',result.strict_RCG_returned_blocks_pass,'strict_own_PGA',result.strict_PGA_returned_blocks_pass,'independent_physics_and_final_joint_pending',true,'no_automatic_retry',true);
        rows{end+1}=row; %#ok<AGROW>
        is_put_json(fullfile(folder,'actual-scheme-entry-closure.json'),row);
        is_put_json(fullfile(outputRoot,sprintf('closed-scheme-%02d.json',selectedScheme)),row);
        if code==1,error('Host/capture incomplete; stop native lane with saved partial evidence');end
    end
catch exception
    hostError=struct('identifier',exception.identifier,'message',exception.message,'stack',exception.stack);
end
try,after=is_guard_sources(plan.native_guard_sources);catch exception
    hostError=struct('identifier',exception.identifier,'message',exception.message,'stack',exception.stack);
end
sourceClosed=isequal(before,after);code=2;
if ~isempty(hostError)||~sourceClosed,code=1;elseif numel(rows)==5&&all(cellfun(@(r)r.actual_entry_exit==0,rows)),code=0;end
summary=struct('schema','actual-remaining-five-only-native-case014-source-closure-v1','source_before',{before},'source_after',{after},...
    'source_and_input_interval_closed',sourceClosed,'host_error',hostError,'rows',{rows},'effective_entry_exit_code',code,...
    'elapsed_seconds',toc(started),'first_completed_scheme_repeated',false,'new_channel_MC_RNG_calls',0,...
    'algorithm_stops_not_independent_physics_or_final_joint_PASS',true);
is_put_json(fullfile(outputRoot,'actual-source-input-five-scheme-closure.json'),summary);
end

function rows=is_guard_sources(pins)
rows=cell(numel(pins),1);
for k=1:numel(pins)
    actual=is_sha_file(pins(k).path);assert(strcmp(actual,pins(k).SHA256),'Frozen source/input changed');
    rows{k}=struct('path',pins(k).path,'SHA256',actual);
end
end

function value=is_sha_file(path)
fid=fopen(path,'rb');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');
digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(bytes);raw=typecast(digest.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end

function is_put_json(path,value)
assert(~isfile(path),'Never overwrite actual evidence');fid=fopen(path,'w');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(value));
end

function fingerprint=is_fingerprint(configPath,scenarioPath)
digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(uint8('strict-v1'));digest.update(uint8(0));
fid=fopen(configPath,'rb');bytes=fread(fid,Inf,'*uint8');fclose(fid);digest.update(bytes);digest.update(uint8(0));
fid=fopen(scenarioPath,'rb');bytes=fread(fid,Inf,'*uint8');fclose(fid);digest.update(bytes);
raw=typecast(digest.digest(),'uint8');fingerprint=lower(reshape(dec2hex(raw,2).',1,[]));
end

function [R,dR]=is_rotation(r)
x=r(1);y=r(2);z=r(3);cx=cos(x);sx=sin(x);cy=cos(y);sy=sin(y);cz=cos(z);sz=sin(z);
rx=[1,0,0;0,cx,-sx;0,sx,cx];ry=[cy,0,sy;0,1,0;-sy,0,cy];rz=[cz,-sz,0;sz,cz,0;0,0,1];
dx=[0,0,0;0,-sx,-cx;0,cx,-sx];dy=[-sy,0,cy;0,0,0;-cy,0,-sy];dz=[-sz,-cz,0;cz,-sz,0;0,0,0];
R=rx*ry*rz;dR={dx*ry*rz,rx*dy*rz,rx*ry*dz};
end

function [a,da]=is_response(coords,center,u,r,c)
[R,dR]=is_rotation(r);u=u(:);cosine=R(:,3)'*u;wave=2*pi/c.wavelength;
t=exp(1i*wave*((coords*R'+center(:)')*u));
if cosine<=0,a=zeros(size(t));da=zeros(numel(t),3);return;end
b=c.directivity_exponent;amp=sqrt(c.maximum_gain)*cosine^(b/2);a=amp*t;da=zeros(numel(t),3);
for d=1:3
    damp=sqrt(c.maximum_gain)*(b/2)*cosine^(b/2-1)*(dR{d}(:,3)'*u);
    dphase=wave*(coords*dR{d}'*u);da(:,d)=t.*(damp+1i*amp*dphase);
end
end

function base=is_channel_base(r,c)
cb=c.bs_coordinates;cr=c.ris_coordinates;M=size(cb,1);N=size(cr,1);K=numel(c.noise);A=size(c.bt_directions,1);links=K+A;
h=zeros(M,links);g=zeros(N,links);dh=zeros(M,links,6);dg=zeros(N,links,6);
for k=1:K
    for p=1:size(c.bu_directions,2)
        [a,da]=is_response(cb,c.bs_center,reshape(c.bu_directions(k,p,:),3,1),r(1:3),c);
        gain=c.bu_gain_re(k,p)+1i*c.bu_gain_im(k,p);h(:,k)=h(:,k)+gain*a;dh(:,k,1:3)=dh(:,k,1:3)+reshape(gain*da,M,1,3);
        [a,da]=is_response(cr,c.ris_center,reshape(c.ru_directions(k,p,:),3,1),r(4:6),c);
        gain=c.ru_gain_re(k,p)+1i*c.ru_gain_im(k,p);g(:,k)=g(:,k)+gain*a;dg(:,k,4:6)=dg(:,k,4:6)+reshape(gain*da,N,1,3);
    end
end
for a=1:A
    [h(:,K+a),der]=is_response(cb,c.bs_center,c.bt_directions(a,:),r(1:3),c);dh(:,K+a,1:3)=reshape(der,M,1,3);
    [g(:,K+a),der]=is_response(cr,c.ris_center,c.rt_directions(a,:),r(4:6),c);dg(:,K+a,4:6)=reshape(der,N,1,3);
end
B=zeros(M,N);dB=zeros(M,N,6);
for p=1:size(c.br_directions,1)
    [ab,dab]=is_response(cb,c.bs_center,c.br_directions(p,:),r(1:3),c);
    [ar,dar]=is_response(cr,c.ris_center,c.rb_directions(p,:),r(4:6),c);
    gain=c.br_gain_re(p)+1i*c.br_gain_im(p);B=B+gain*ab*ar';
    for d=1:3,dB(:,:,d)=dB(:,:,d)+gain*dab(:,d)*ar';dB(:,:,d+3)=dB(:,:,d+3)+gain*ab*dar(:,d)';end
end
base={h,g,dh,dg,B,dB};
end

function [f,jac,B,g]=is_channels(theta,r,c,fixedRotationBase)
if nargin<4 || isempty(fixedRotationBase),fixedRotationBase=is_channel_base(r,c);end
h=fixedRotationBase{1};g=fixedRotationBase{2};dh=fixedRotationBase{3};dg=fixedRotationBase{4};B=fixedRotationBase{5};dB=fixedRotationBase{6};
[M,links]=size(h);f=h+B*(theta.*g);jac=zeros(M,links,6);
for d=1:6,jac(:,:,d)=dh(:,:,d)+dB(:,:,d)*(theta.*g)+B*(theta.*dg(:,:,d));end
end

function [metric,gw,gt,gr]=is_evaluate(W,theta,r,c,iota,fixedChannelBundle,fixedRotationBase)
% Full bundle: fixed-theta W block; base: fixed-r RIS block. No stale reuse.
if nargin<6 || isempty(fixedChannelBundle)
    if nargin<7,[f,jac,B,g]=is_channels(theta,r,c);else,[f,jac,B,g]=is_channels(theta,r,c,fixedRotationBase);end
else,f=fixedChannelBundle{1};jac=fixedChannelBundle{2};B=fixedChannelBundle{3};g=fixedChannelBundle{4};end
K=numel(c.noise);fc=f(:,1:K);fs=f(:,K+1:end);Y=fc'*W;Z=fs'*W;
powers=abs(Y).^2;mask=true(size(powers));mask(sub2ind(size(mask),(1:K)',(1:K)'))=false;
signal=abs(diag(Y(:,1:K))).^2;interference=c.noise(:)+sum(powers.*mask,2);total=signal+interference;
rate=sum(log1p(signal./interference))/log(2);p=sum(abs(Z).^2,2);pd=c.desired_pattern(:);energy=pd'*pd;
if nargin<5 || isempty(iota)
    overlap=pd'*p;if overlap<=c.iota_denominator_epsilon,error('Exact iota* undefined at zero overlap.');end
    iota=(p'*p)/overlap;
end
D=iota^2*energy;residual=p-iota*pd;nmse=(residual'*residual)/D;
metric=struct('utility',rate-c.rho*nmse,'rate',rate,'nmse',nmse,'iota',iota,'pattern',p','sinr',(signal./interference)');
if nargout<2,return;end
coefficient=repmat(-signal./(total.*interference),1,size(W,2));
for k=1:K,coefficient(k,k)=1/total(k);end
gw=2*fc*(coefficient.*Y)/log(2)-4*c.rho*fs*(residual.*Z)/D;
bw=B'*W;gt=zeros(numel(theta),1);
for k=1:K,gt=gt+2*conj(g(:,k)).*(bw*(coefficient(k,:).*conj(Y(k,:))).')/log(2);end
for a=1:numel(pd),gt=gt-4*c.rho*residual(a)/D*conj(g(:,K+a)).*(bw*conj(Z(a,:)).');end
gr=zeros(6,1);
for d=1:6
    dY=jac(:,1:K,d)'*W;dZ=jac(:,K+1:end,d)'*W;
    derivatives=2*real(conj(Y).*dY);ds=real(diag(derivatives(:,1:K)));dinterference=sum(derivatives.*mask,2);
    dr=sum(ds./total-signal./(total.*interference).*dinterference)/log(2);dp=2*real(sum(conj(Z).*dZ,2));gr(d)=dr-2*c.rho*residual'*dp/D;
end
end

function [W,theta,r]=is_initialize(c)
theta=ones(size(c.ris_coordinates,1),1);r=c.initial_angles(:);f=is_channels(theta,r,c);K=numel(c.noise);M=size(c.bs_coordinates,1);fc=f(:,1:K);
gram=fc'*fc;[u,s,v]=svd(gram);sing=diag(s);inverse=zeros(size(sing));active=sing>c.initial_pseudoinverse_tolerance*max(sing);inverse(active)=1./sing(active);
V=fc*v*diag(inverse)*u';W=[V,eye(M)*c.initial_sensing_amplitude];W=W*sqrt(c.power)/norm(W,'fro');
end

function [W,hist]=is_update_w(W,theta,r,c,iota,useFixedChannels)
if nargin<6,useFixedChannels=true;end
[f,jac,B,g]=is_channels(theta,r,c);fixedChannelBundle={f,jac,B,g};K=numel(c.noise);fc=f(:,1:K);fs=f(:,K+1:end);M=size(W,1);pd=c.desired_pattern(:);D=iota^2*(pd'*pd);
norms=sum(abs(fs).^2,1)';lip=12*c.power*norms.^2+4*iota*pd.*norms;spec=c.W_solver;
if useFixedChannels,met=is_evaluate(W,theta,r,c,iota,fixedChannelBundle);
else,met=is_evaluate(W,theta,r,c,iota);end
objective=met.utility;
records=struct('nu',{},'bisection_steps',{},'stationarity_residual',{},'power',{});
converged=false;reason='maximum_iterations_without_criterion_stop';relativeObjective=[];relative=[];
for iteration=1:spec.maximum_iterations
    Y=fc'*W;powers=abs(Y).^2;mask=true(size(powers));mask(sub2ind(size(mask),(1:K)',(1:K)'))=false;
    signal=abs(diag(Y(:,1:K))).^2;interference=c.noise(:)+sum(powers.*mask,2);total=signal+interference;mu=signal./interference;eta=diag(Y(:,1:K))./total;
    Q=(fc.*((1+mu).*abs(eta).^2)')*fc'/log(2);P=zeros(size(W));
    % .' is necessary: eta is not conjugated in the paper P_C.
    P(:,1:K)=fc.*transpose((1+mu).*eta)/log(2);
    Z=fs'*W;pattern=sum(abs(Z).^2,2);Ga=4*fs*((pattern-iota*pd).*Z);
    Q=Q+c.rho*sum(lip)/(2*D)*eye(M);P=P+c.rho/(2*D)*(sum(lip)*W-Ga);
    solved=solve_original_factor_QP_array_v1(W,fc,mu,eta,lip,Ga,D,c.rho,c.power,spec.bisection_tolerance);
    new=solved.solution;nu=solved.nu;bisects=solved.bisection_steps;
    if useFixedChannels,met=is_evaluate(new,theta,r,c,iota,fixedChannelBundle);
    else,met=is_evaluate(new,theta,r,c,iota);end
    if met.utility<objective(end)-c.verification_tolerance,error('QT/MM actual objective decreased.');end
    relative=norm(new-W,'fro')/max(norm(W,'fro'),realmin);
    records(end+1)=struct('nu',nu,'bisection_steps',bisects,'stationarity_residual',norm((Q+nu*eye(M))*new-P,'fro'),'power',sum(abs(new(:)).^2)); %#ok<AGROW>
    W=new;objective(end+1)=met.utility; %#ok<AGROW>
    relativeObjective=(objective(end)-objective(end-1))/max(abs(objective(end-1)),realmin);
    if relativeObjective<spec.relative_tolerance || relative<spec.relative_tolerance
        converged=true;if relativeObjective<spec.relative_tolerance,reason='relative_objective_tolerance';else,reason='relative_step_tolerance';end;break;
    end
end

hist=struct('objective',objective,'QCQP',records,'converged',converged,'termination_reason',reason,...
    'iterations',numel(records),'iteration_budget',spec.maximum_iterations,'budget_exhausted',numel(records)>=spec.maximum_iterations,...
    'capped_unconverged',~converged,'relative_objective_improvement',relativeObjective,'relative_step',relative,'relative_tolerance',spec.relative_tolerance);
end

function result=is_fixed_channel_test(c)
% The false branch retains original uncached is_evaluate calls/arithmetic.
% No budget, stopping condition, channel or original update is replaced.
assert(size(c.bs_coordinates,1)==4&&size(c.ris_coordinates,1)==36&&numel(c.desired_pattern)==66);
names={'Rot-BS & Rot-RIS','Rot-BS & Fix-RIS','Fix-BS & Rot-RIS','Fix-BS & Fix-RIS','Rot-BS & No-RIS','Fix-BS & No-RIS'};
groups=cell(2,1);schemeChecks=cell(6,1);
for scheme=1:6
    scene=c;group=1;if scheme>=5,group=2;scene.br_gain_re(:)=0;scene.br_gain_im(:)=0;end
    [W,theta,r]=is_initialize(scene);met=is_evaluate(W,theta,r,scene);iota=met.iota;
    if isempty(groups{group})
        started=tic;[original,oldHist]=is_update_w(W,theta,r,scene,iota,false);oldSeconds=toc(started);
        started=tic;[cached,newHist]=is_update_w(W,theta,r,scene,iota,true);newSeconds=toc(started);
        assert(isequal(original,cached)&&isequal(oldHist,newHist),'Full W states/objectives/QCQP/stop gates changed');
        groups{group}=struct('original_W_budget',scene.W_solver.maximum_iterations,'iterations',oldHist.iterations,'converged',oldHist.converged,...
            'all_objectives_states_QCQP_and_stop_gates_bitwise_equal',true,'original_seconds',oldSeconds,'new_production_seconds',newSeconds,...
            'speedup',oldSeconds/newSeconds,'W_re',real(cached),'W_im',imag(cached),'history',newHist);
    end
    W=groups{group}.W_re+1i*groups{group}.W_im;
    [f,jac,B,g]=is_channels(theta,r,scene);bundle={f,jac,B,g};
    [a,aw,at,ar]=is_evaluate(W,theta,r,scene,iota);[b,bw,bt,br]=is_evaluate(W,theta,r,scene,iota,bundle);
    assert(isequal(a,b)&&isequal(aw,bw)&&isequal(at,bt)&&isequal(ar,br),'Full metrics/gradients cache changed arithmetic');
    schemeChecks{scheme}=struct('scheme',names{scheme},'full_original_dimensions_preserved',true,...
        'cached_vs_uncached_metrics_and_all_gradients_bitwise_equal',true,'full_W_prefix_and_stops_bitwise_equal',true,'W_group',group);
end
result=struct('paper_id','rotatable-isac','mode','full_dimension_fixed_channel_cache_equivalence_not_full_bank',...
    'dimensions',struct('BS',4,'RIS',36,'sensing_samples',66,'schemes',6),'W_runs',{groups},'scheme_checks',{schemeChecks},...
    'all_six_schemes_verified',true,'new_full500_job_bank_or_figures_completed',false);
end

function v=is_tangent(theta,v)
v=v-real(v.*conj(theta)).*theta;
end

function [theta,hist]=is_update_theta(W,theta,r,c,iota,useFixedRotationBase)
if nargin<6,useFixedRotationBase=true;end
fixedRotationBase=[];if useFixedRotationBase,fixedRotationBase=is_channel_base(r,c);end
spec=c.RCG_solver;objective=[];coefficients=[];restarts=struct('iteration',{},'reason',{},'raw_PR',{},'raw_slope',{});oldg=[];oldd=[];nextSeed=spec.initial_step;
converged=false;reason='maximum_iterations_without_criterion_stop';checkedGradient=[];
for iteration=0:spec.maximum_iterations-1
    [met,~,ambient]=is_evaluate(W,theta,r,c,iota,[],fixedRotationBase);g=is_tangent(theta,ambient);objective(end+1)=met.utility; %#ok<AGROW>
    checkedGradient=norm(g)/sqrt(numel(theta));
    if checkedGradient<=spec.gradient_tolerance,converged=true;reason='gradient_tolerance';break;end
    beta=0;if ~isempty(oldg),beta=real(g'*(g-is_tangent(theta,oldg)))/real(oldg'*oldg);end
    direction=g;if ~isempty(oldg),direction=g+beta*is_tangent(theta,oldd);end
    slope=real(g'*direction);coefficients(end+1)=beta; %#ok<AGROW>
    if slope<=0
        if strcmp(spec.mode,'documented_non_ascent_restart')
            restarts(end+1)=struct('iteration',iteration,'reason','non_ascent_direction','raw_PR',beta,'raw_slope',slope); %#ok<AGROW>
            direction=g;slope=real(g'*g);
        else,error('Printed untruncated PR direction is not ascent. Literal diagnostic mode does not restart.');end
    end
    alpha=nextSeed;accepted=false;
    for backtrack=1:spec.maximum_backtracks
        trial=theta+alpha*direction;trial=trial./abs(trial);candidate=is_evaluate(W,trial,r,c,iota,[],fixedRotationBase);
        if candidate.utility>=met.utility+spec.armijo*alpha*slope,oldg=g;oldd=direction;theta=trial;accepted=true;nextSeed=2*alpha;break;end
        alpha=alpha*spec.backtrack_factor;
    end
    if ~accepted,error('Printed RCG Armijo line search failed.');end
end
[met,~,ambient]=is_evaluate(W,theta,r,c,iota,[],fixedRotationBase);hist=struct('objective',objective,'PR_coefficients',coefficients,'restarts',restarts,'mode',spec.mode,'final_objective',met.utility,...
    'applicable',true,'converged',converged,'termination_reason',reason,'iterations',numel(objective),'updates',numel(coefficients),...
    'iteration_budget',spec.maximum_iterations,'budget_exhausted',numel(objective)>=spec.maximum_iterations,'capped_unconverged',~converged,...
    'last_checked_normalized_gradient_norm',checkedGradient,'final_normalized_gradient_norm',norm(is_tangent(theta,ambient))/sqrt(numel(theta)),'gradient_tolerance',spec.gradient_tolerance);
end

function [r,hist]=is_update_rotation(W,theta,r,c,iota,lower,upper)
spec=c.PGA_solver;oldr=[];oldg=[];objective=[];bb=struct('raw',{},'clipped',{},'denominator',{});steps=[];
converged=false;reason='maximum_iterations_without_criterion_stop';checkedGradient=[];relative=[];
for iteration=1:spec.maximum_iterations
    [met,~,~,g]=is_evaluate(W,theta,r,c,iota);objective(end+1)=met.utility; %#ok<AGROW>
    residual=g;residual(r<=lower)=max(0,g(r<=lower));residual(r>=upper)=min(0,g(r>=upper));residual(lower==upper)=0;
    checkedGradient=norm(residual);
    if checkedGradient<=spec.gradient_tolerance,converged=true;reason='projected_gradient_tolerance';break;end
    alpha=spec.initial_step;
    if ~isempty(oldr)
        s=r-oldr;den=s'*(g-oldg);if strcmp(spec.BB_interpretation,'ascent_sign_correction'),den=-den;end
        if den==0,raw=Inf;else,raw=(s'*s)/den;end
        alpha=max(spec.minimum_step,min(spec.maximum_step,raw));stored=raw;if ~isfinite(stored),stored=[];end
        bb(end+1)=struct('raw',stored,'clipped',alpha,'denominator',den); %#ok<AGROW>
    end
    accepted=false;
    for backtrack=1:spec.maximum_backtracks
        delta=max(lower,min(upper,r+alpha*g))-r;candidate=is_evaluate(W,theta,r+delta,c,iota);
        if stable_rotation_utility_increment_native_v1(W,theta,r,r+delta,c,iota,struct('rotation',@is_rotation,'response',@is_response,'channel_base',@is_channel_base))>=spec.armijo*(g'*delta),oldr=r;oldg=g;r=r+delta;accepted=true;steps(end+1)=alpha;break;end %#ok<AGROW>
        alpha=alpha*spec.backtrack_factor;
    end
    if ~accepted,error('Paper PGA Armijo line search failed.');end
    relative=norm(r-oldr)/max(1,norm(oldr));
    if relative<=spec.relative_tolerance,converged=true;reason='relative_step_tolerance';break;end
end
[met,~,~,g]=is_evaluate(W,theta,r,c,iota);residual=g;residual(r<=lower)=max(0,g(r<=lower));residual(r>=upper)=min(0,g(r>=upper));residual(lower==upper)=0;
hist=struct('objective',objective,'BB',bb,'steps',steps,'final_objective',met.utility,'converged',converged,'termination_reason',reason,...
    'iterations',numel(objective),'updates',numel(steps),'iteration_budget',spec.maximum_iterations,'budget_exhausted',numel(objective)>=spec.maximum_iterations,...
    'capped_unconverged',~converged,'last_checked_projected_gradient_norm',checkedGradient,'final_projected_gradient_norm',norm(residual),...
    'gradient_tolerance',spec.gradient_tolerance,'relative_step',relative,'relative_tolerance',spec.relative_tolerance);
end

function [W,theta,r,hist]=is_optimize(c,lower,upper,withRIS,useFixedRotationBase)
if nargin<5,useFixedRotationBase=true;end
[W,theta,r]=is_initialize(c);is_passive_return_capture('initial',struct('W',W,'theta',theta,'r',r,'lower',lower,'upper',upper,'with_RIS',withRIS));objective=[];blocks=struct('iota',{},'W',{},'RIS',{},'rotation',{});converged=false;relativeObjective=[];
for iteration=1:c.AO_solver.maximum_iterations
    met=is_evaluate(W,theta,r,c,[]);iota=met.iota;if isempty(objective),objective=met.utility;end
    [W,hw]=is_update_w(W,theta,r,c,iota);
    is_passive_return_capture('returned',struct('AO_iteration',iteration,'block','W','W',W,'theta',theta,'r',r,'fixed_iota',iota,'original_status',hw));
    ht=struct('applicable',false,'converged',true,'capped_unconverged',false,'termination_reason','not_applicable_no_RIS','iterations',0,'iteration_budget',0,'budget_exhausted',false);
    if withRIS,[theta,ht]=is_update_theta(W,theta,r,c,iota,useFixedRotationBase);end
    if withRIS,is_passive_return_capture('returned',struct('AO_iteration',iteration,'block','RCG','W',W,'theta',theta,'r',r,'fixed_iota',iota,'original_status',ht));end
    [r,hr]=is_update_rotation(W,theta,r,c,iota,lower,upper);
    is_passive_return_capture('returned',struct('AO_iteration',iteration,'block','PGA','W',W,'theta',theta,'r',r,'fixed_iota',iota,'original_status',hr));
    met=is_evaluate(W,theta,r,c,[]);objective(end+1)=met.utility; %#ok<AGROW>
    if objective(end)<objective(end-1)-c.verification_tolerance,error('AO utility decreased.');end
    blocks(end+1)=struct('iota',iota,'W',hw,'RIS',ht,'rotation',hr); %#ok<AGROW>
    relativeObjective=(objective(end)-objective(end-1))/max(abs(objective(end-1)),realmin);
    if relativeObjective<c.AO_solver.relative_tolerance,converged=true;break;end
end
innerAll=~isempty(blocks);for index=1:numel(blocks),innerAll=innerAll&&blocks(index).W.converged&&blocks(index).RIS.converged&&blocks(index).rotation.converged;end
reason='maximum_iterations_without_criterion_stop';if converged,reason='relative_objective_tolerance';end
hist=struct('utility',objective,'blocks',blocks,'converged',converged,'inner_all_converged',innerAll,'full_converged',converged&&innerAll,...
    'iterations',numel(blocks),'iteration_budget',c.AO_solver.maximum_iterations,'budget_exhausted',numel(blocks)>=c.AO_solver.maximum_iterations,...
    'termination_reason',reason,'relative_objective_improvement',relativeObjective,'relative_tolerance',c.AO_solver.relative_tolerance);
end

function result=is_component(c)
[W,theta,r]=is_initialize(c);[met,gw,gt,gr]=is_evaluate(W,theta,r,c,[]);iota=met.iota;eps=1e-6;numr=zeros(6,1);numtheta=zeros(numel(theta),1);numw=zeros(size(W));
for a=1:size(W,1),for d=1:size(W,2)
    plus=W;minus=W;plus(a,d)=plus(a,d)+eps;minus(a,d)=minus(a,d)-eps;p=is_evaluate(plus,theta,r,c,iota);m=is_evaluate(minus,theta,r,c,iota);re=(p.utility-m.utility)/(2*eps);
    plus=W;minus=W;plus(a,d)=plus(a,d)+1i*eps;minus(a,d)=minus(a,d)-1i*eps;p=is_evaluate(plus,theta,r,c,iota);m=is_evaluate(minus,theta,r,c,iota);im=(p.utility-m.utility)/(2*eps);numw(a,d)=re+1i*im;
end,end
for d=1:6,plus=r;minus=r;plus(d)=plus(d)+eps;minus(d)=minus(d)-eps;p=is_evaluate(W,theta,plus,c,iota);m=is_evaluate(W,theta,minus,c,iota);numr(d)=(p.utility-m.utility)/(2*eps);end
for d=1:numel(theta),plus=theta;minus=theta;plus(d)=plus(d)*exp(1i*eps);minus(d)=minus(d)*exp(-1i*eps);p=is_evaluate(W,plus,r,c,iota);m=is_evaluate(W,minus,r,c,iota);numtheta(d)=(p.utility-m.utility)/(2*eps);end
test=c;test.W_solver.maximum_iterations=1;test.RCG_solver.maximum_iterations=2;test.PGA_solver.maximum_iterations=3;
[newW,hw]=is_update_w(W,theta,r,test,iota);[newtheta,ht]=is_update_theta(W,theta,r,test,iota);probe=test;probe.RCG_solver.mode='literal_printed';diagnostic=[];
try,is_update_theta(W,theta,r,probe,iota);catch exception,diagnostic=exception.message;end
bound=ones(6,1)*pi/2;printed=test;printed.PGA_solver.BB_interpretation='as_printed';[pr,hp]=is_update_rotation(W,theta,r,printed,iota,-bound,bound);
corrected=test;corrected.PGA_solver.BB_interpretation='ascent_sign_correction';[cr,hc]=is_update_rotation(W,theta,r,corrected,iota,-bound,bound);
pd=c.desired_pattern(:);pattern=met.pattern(:);phasegradient=real(conj(gt).*(1i*theta));
checks=struct('rotation_gradient_error',max(abs(gr-numr)),'RIS_gradient_error',max(abs(phasegradient-numtheta)),...
    'W_gradient_error',max(abs(gw(:)-numw(:))),'gradient_pass',max([max(abs(gr-numr)),max(abs(phasegradient-numtheta)),max(abs(gw(:)-numw(:)))])<1e-5,'QT_MM_non_decrease',hw.objective(end)>=hw.objective(1)-1e-8,...
    'power_feasible',sum(abs(newW(:)).^2)<=c.power+1e-10,'RCG_unit_modulus_error',max(abs(abs(newtheta)-1)),...
    'NMSE_identity_error',abs(met.nmse-(1-(pd'*pattern)^2/((pd'*pd)*(pattern'*pattern)))),...
    'full_model_BS_count',size(W,1),'full_model_RIS_count',numel(theta),'full_model_sensing_grid',numel(pattern),...
    'printed_BB_negative_denominator_observed',~isempty(hp.BB)&&any([hp.BB.denominator]<0),'printed_RCG_non_ascent_diagnostic',diagnostic,'finite',all(isfinite(newW(:))));
assert(checks.gradient_pass && checks.QT_MM_non_decrease && checks.power_feasible);
result=struct('paper_id','rotatable-isac','mode','component_test_not_full_run','metrics',struct('initial',met,'printed_BB_rotation',pr','corrected_BB_rotation',cr'),...
    'checks',checks,'history',struct('W',hw,'RIS',ht,'PGA_printed',hp,'PGA_correction_diagnostic',hc));
end

function result=is_full_scenario(c,useFixedRotationBase,selectedScheme)
if nargin<2,useFixedRotationBase=true;end
allNames={'Rot-BS & Rot-RIS','Rot-BS & Fix-RIS','Fix-BS & Rot-RIS','Fix-BS & Fix-RIS','Rot-BS & No-RIS','Fix-BS & No-RIS'};
allFlags=[1,1,1;1,0,1;0,1,1;0,0,1;1,0,0;0,0,0];
assert(nargin==3&&ismember(selectedScheme,2:6),'Only one remaining scheme, never firstscheme');
names=allNames(selectedScheme);flags=allFlags(selectedScheme,:);metrics=cell(1,1);histories=cell(1,1);checks=cell(1,1);
for s=1:1
    scene=c;if ~flags(s,3),scene.br_gain_re=zeros(size(c.br_gain_re));scene.br_gain_im=zeros(size(c.br_gain_im));end
    width=[ones(3,1)*pi/2*flags(s,1);ones(3,1)*pi/2*flags(s,2)];
    if isfield(c,'rotation_half_width'),width=width*c.rotation_half_width/(pi/2);end
    if isfield(c,'rotation_bs_half_width'),width(1:3)=c.rotation_bs_half_width*flags(s,1);end
    if isfield(c,'rotation_ris_half_width'),width(4:6)=c.rotation_ris_half_width*flags(s,2);end
    try
        [W,theta,r,hist]=is_optimize(scene,-width,width,logical(flags(s,3)),useFixedRotationBase);met=is_evaluate(W,theta,r,scene,[]);
        met.w_re=real(W);met.w_im=imag(W);met.theta_re=real(theta)';met.theta_im=imag(theta)';met.rotation=r';metrics{s}=met;histories{s}=hist;
        checks{s}=struct('status','executed','converged',hist.converged,'inner_all_converged',hist.inner_all_converged,'full_converged',hist.full_converged,'power_feasible',sum(abs(W(:)).^2)<=c.power+c.verification_tolerance,...
            'unit_modulus_error',max(abs(abs(theta)-1)),'rotation_feasible',all(abs(r)<=width+1e-12));
    catch exception,metrics{s}=struct('status','failed','error',exception.message);checks{s}=struct('status','failed');end
end
result=struct('paper_id','rotatable-isac','mode','full_scenario','scheme_names',{names},'metrics',{metrics},'checks',{checks},'history',{histories});
end

function result=is_fixed_rotation_base_test(c,active)
% Independent in-language exact arithmetic test, not a full100-channel figure.
assert(size(c.bs_coordinates,1)==4&&size(c.ris_coordinates,1)==36&&numel(c.desired_pattern)==66);
assert(active.RCG_solver.maximum_iterations==500&&c.RCG_solver.maximum_iterations==500,'Original selected budget unchanged');
previousRng=rng;restoreRng=onCleanup(@()rng(previousRng));rng(24605,'twister'); %#ok<NASGU>
names={'Rot-BS & Rot-RIS','Rot-BS & Fix-RIS','Fix-BS & Rot-RIS','Fix-BS & Fix-RIS','Rot-BS & No-RIS','Fix-BS & No-RIS'};
groups=cell(2,1);checks=cell(6,1);
for scheme=1:6
    scene=active;group=1;if scheme>=5,group=2;scene.br_gain_re(:)=0;scene.br_gain_im(:)=0;end
    [W,theta,r]=is_initialize(scene);theta=exp(1i*(2*pi*rand(size(theta))-pi));
    W=randn(size(W))+1i*randn(size(W));W=W*sqrt(scene.power)/norm(W,'fro');
    base=is_channel_base(r,scene);[f,jac,B,g]=is_channels(theta,r,scene);[cf,cjac,cB,cg]=is_channels(theta,r,scene,base);
    assert(isequal(f,cf)&&isequal(jac,cjac)&&isequal(B,cB)&&isequal(g,cg),'Original full channel/jac arithmetic differs');
    [a,aw,at,ar]=is_evaluate(W,theta,r,scene,[]);[b,bw,bt,br]=is_evaluate(W,theta,r,scene,[],[],base);
    assert(isequal(a,b)&&isequal(aw,bw)&&isequal(at,bt)&&isequal(ar,br),'A physical metric/gradient changed');
    if isempty(groups{group})
        started=tic;[original,oldHist]=is_update_theta(W,theta,r,scene,a.iota,false);oldSeconds=toc(started);
        started=tic;[cached,newHist]=is_update_theta(W,theta,r,scene,a.iota,true);newSeconds=toc(started);
        assert(isequal(original,cached)&&isequal(oldHist,newHist),'Full RCG theta/rawPR/restarts/Armijo/stops changed');
        groups{group}=struct('original_RCG_budget',scene.RCG_solver.maximum_iterations,'iterations',oldHist.iterations,...
            'converged',oldHist.converged,'capped_unconverged',oldHist.capped_unconverged,...
            'full_states_rawPR_objectives_and_stop_fields_bitwise_equal',true,'original_seconds',oldSeconds,'cached_seconds',newSeconds,...
            'speedup',oldSeconds/newSeconds,'theta_re',real(cached)','theta_im',imag(cached)','history',newHist);
    end
    checks{scheme}=struct('scheme',names{scheme},'channel_jac_all_metrics_and_three_gradients_bitwise_equal',true,...
        'RIS_ambient_gradient_norm',norm(at),'full_original4_36_66_dimensions_retained',true,'RCG_group',group);
end
Wchecks=is_fixed_channel_test(c);
started=tic;oldScenario=is_full_scenario(c,false);oldSeconds=toc(started);
started=tic;newScenario=is_full_scenario(c,true);newSeconds=toc(started);
assert(isequal(oldScenario,newScenario),'Entire same-input/all6 metrics/states/histories/stops changed');
result=struct('paper_id','rotatable-isac','mode','full_dimension_fixed_rotation_base_cache_equivalence_not_full_bank',...
    'all_six_channel_metric_gradient_checks_passed',true,'RCG_runs',{groups},'scheme_checks',{checks},'full_W_cache_checks',Wchecks,...
    'all_six_same_input_whole_scenario_metrics_states_histories_stops_bitwise_equal',true,...
    'original_whole_scenario_seconds',oldSeconds,'cached_whole_scenario_seconds',newSeconds,...
    'whole_scenario_checks',{newScenario.checks},'whole_scenario_histories',{newScenario.history},...
    'whole_scenario_metrics',{newScenario.metrics},'MC100_channel_points_or_full500_bank_complete',false,...
    'all_stop_thresholds_500_RCG_budget_and_rawPR_unchanged',true);
end

function qt=is_passive_QT_prefix(W,theta,r,c,iota)
[f,jac,B,g]=is_channels(theta,r,c);fixedChannelBundle={f,jac,B,g};K=numel(c.noise);fc=f(:,1:K);fs=f(:,K+1:end);M=size(W,1);pd=c.desired_pattern(:);D=iota^2*(pd'*pd);
norms=sum(abs(fs).^2,1)';lip=12*c.power*norms.^2+4*iota*pd.*norms;spec=c.W_solver;
    Y=fc'*W;powers=abs(Y).^2;mask=true(size(powers));mask(sub2ind(size(mask),(1:K)',(1:K)'))=false;
    signal=abs(diag(Y(:,1:K))).^2;interference=c.noise(:)+sum(powers.*mask,2);total=signal+interference;mu=signal./interference;eta=diag(Y(:,1:K))./total;
    Q=(fc.*((1+mu).*abs(eta).^2)')*fc'/log(2);P=zeros(size(W));
    % .' is necessary: eta is not conjugated in the paper P_C.
    P(:,1:K)=fc.*transpose((1+mu).*eta)/log(2);
    Z=fs'*W;pattern=sum(abs(Z).^2,2);Ga=4*fs*((pattern-iota*pd).*Z);
    Q=Q+c.rho*sum(lip)/(2*D)*eye(M);P=P+c.rho/(2*D)*(sum(lip)*W-Ga);

qt=struct('signal',signal,'interference',interference,'total',total,'mu',mu,'eta',eta,'q',Q,'p',P,'lip',lip,'ga',Ga);
end
function output=is_passive_return_capture(action,payload)
% Pure passive copies only. No objective/gradient/channel evaluation or RNG.
persistent recording
output=[];
switch action
    case 'initialize'
        recording=struct('schema','actual-native-first-scheme-returned-block-states-v1','source_inputs',payload,'initial_state',[],'returns',{{}},'extra_objective_gradient_RNG_calls',0);
    case 'initial'
        recording.initial_state=payload;
    case 'returned'
        recording.returns{end+1}=payload;
    case 'snapshot'
        output=recording;
    otherwise
        error('Unknown passive capture action');
end
end
