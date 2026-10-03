function result=run_strict_two_timescale_ma_full_v2(outputPath,jobPath,configPath)
% Versioned MATLAB-only history-container repair; original numeric updates unchanged.
% Component call uses full N=6,M=5; it is not a full Monte Carlo figure.
base=fileparts(mfilename('fullpath'));if nargin<3 || isempty(configPath),configPath=fullfile(base,'full_config.json');end
config=jsondecode(fileread(configPath));
[beforeIdentity,runtimeIdentity]=strict_ma_full_v2_implementation_fingerprint(configPath);
if ~strcmp(config.matlab_convex_solver,'certified_exact_2d')&&exist('cvx_begin','file')~=2,error('Selected optional original conic backend requires external CVX.');end
if nargin<2 || isempty(jobPath),result=ma_component(config,base);else,result=ma_job(jsondecode(fileread(jobPath)),config);result.input_fingerprint=ma_fingerprint(configPath,jobPath);end
afterIdentity=strict_ma_full_v2_implementation_fingerprint(configPath);
assert(strcmp(beforeIdentity,afterIdentity),'Versioned scientific/runtime sources changed during scenario execution.');
result.implementation_fingerprint=beforeIdentity;result.runtime_source_identity=runtimeIdentity;
result.matlab_source_version='MATLAB-full-v2-history-storage';
result.history_container_repair=struct('first_empty_history_array_initialized_from_actual_record',true,'numeric_updates_changed',false,'original_frozen_MAT_files_modified',false);
if nargin>0 && ~isempty(outputPath)
    folder=fileparts(outputPath);if ~isempty(folder)&&~isfolder(folder),mkdir(folder);end
    fid=fopen(outputPath,'w');cleaner=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(result));
end
end
function fingerprint=ma_fingerprint(configPath,jobPath)
digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(uint8('strict-v1'));digest.update(uint8(0));
fid=fopen(configPath,'rb');bytes=fread(fid,Inf,'*uint8');fclose(fid);digest.update(bytes);digest.update(uint8(0));
fid=fopen(jobPath,'rb');bytes=fread(fid,Inf,'*uint8');fclose(fid);digest.update(bytes);
raw=typecast(digest.digest(),'uint8');fingerprint=lower(reshape(dec2hex(raw,2).',1,[]));
end

function [c,t]=ma_scenario(config,N,M,kappa,power,A,geometry)
c=config;field=matlab.lang.makeValidName(num2str(N));if ~isfield(config.antenna_factorization,field),error('Explicit factorization needed.');end
factor=config.antenna_factorization.(field);nr=factor(1);nc=factor(2);
c.wavelength=1;c.minimum_distance=0.5;c.power=power;c.noise=ones(M,1)*1e-11;c.region_lower=[-nr*A/2;-nc*A/2];c.region_upper=-c.region_lower;c.rician=ones(M,1)*kappa;
theta=geometry.elevation(:);phi=geometry.azimuth(:);c.directions=[cos(theta).*sin(phi),sin(theta)];c.beta=1e-4*geometry.distances_m(:).^(-2.8);
x=((0:nr-1)-(nr-1)/2)/2;y=((0:nc-1)-(nc-1)/2)/2;t=zeros(N,2);index=1;
for a=x,for b=y,t(index,:)=[a,b];index=index+1;end,end
end

function H=ma_los(t,c)
H=exp(2i*pi/c.wavelength*(t*c.directions'));
end

function [value,gradient,curvature,rates]=ma_mrt(t,c,antenna)
if nargin<3,antenna=[];end
N=size(t,1);M=numel(c.beta);beta=c.beta(:);kap=c.rician(:);directions=c.directions;wave=2*pi/c.wavelength;
numerator=beta.^2.*(N^2+N*(2*kap+1)./(kap+1).^2);denominator=c.noise(:)*N*sum(beta)/c.power;
gd=zeros(M,N,2);psi=zeros(M,1);
for u=1:M
    bound=zeros(2);
    for v=1:M
        if v==u,continue;end
        d=directions(u,:)-directions(v,:);e=exp(1i*wave*(t*d'));z=sum(e);q=beta(u)*beta(v)*kap(u)*kap(v)/((kap(u)+1)*(kap(v)+1));
        denominator(u)=denominator(u)+q*abs(z)^2+beta(u)*beta(v)*N*(kap(u)+kap(v)+1)/((kap(u)+1)*(kap(v)+1));
        der=2*q*real(conj(z)*1i*wave*(e.*d));gd(u,:,:)=gd(u,:,:)+reshape(der,1,N,2);
        if ~isempty(antenna),bound=bound+q*abs(z-e(antenna))*abs(d'*d);end
    end
    if ~isempty(antenna)
        if strcmp(c.interpretations.mrt_curvature,'equation_29a_max_eigenvalue'),psi(u)=2*wave^2*max(eig(bound));
        elseif strcmp(c.interpretations.mrt_curvature,'equation_29b_as_printed')
            rad=(bound(1,1)-bound(2,2))^2-4*bound(1,2)^2;if rad<0,error('Printed Eq29b has negative radicand.');end
            psi(u)=wave^2*(trace(bound)+sqrt(rad));
        else,error('MRT curvature interpretation required.');end
    end
end
weight=numerator./(log(2)*denominator.*(denominator+numerator));rates=log2(1+numerator./denominator);value=sum(rates);
gradient=-reshape(sum(gd.*reshape(weight,M,1,1),1),N,2);curvature=weight'*psi;
end

function [value,rates,Sigma,eta]=ma_zf(t,c)
H=ma_los(t,c);[N,M]=size(H);if N<=M,error('ZF bound requires N>M.');end
kap=c.rician(:);scale=sqrt(kap./(kap+1));Sigma=diag(1./(kap+1))+(H'*H).*(scale*scale')/N;
inverse=Sigma\eye(M);eta=c.power*c.beta(:)*(N-M)./(M*c.noise(:));rates=log2(1+eta./real(diag(inverse)));value=sum(rates);
end

function s=ma_zf_surrogate(t,c,antenna)
H=ma_los(t,c);[N,M]=size(H);scale=diag(sqrt(c.rician(:)./(c.rician(:)+1)));g=conj(H(antenna,:)).';
Theta1=H'*H-g*g';Theta2=diag(1./(c.rician(:)+1))+scale*Theta1*scale/N;inverse=Theta2\eye(M);Y=N/M*eye(M)+scale*inverse*scale;
chi=zeros(M,1);f0=zeros(M,1);gradient=zeros(M,2);curvature=zeros(M,1);ratio=zeros(M,1);qrows=zeros(M,M);a=real(g'*Y*g);wave=2*pi/c.wavelength;
for u=1:M
    row=inverse*scale;ell=conj(row(u,:)).';X=real(inverse(u,u))*Y-ell*ell';b=real(g'*X*g);lmax=max(real(eig((X+X')/2)));
    q=2/b*(g'*(Y-a/b*(X-lmax*eye(M))));chi(u)=-a/b^2*(2*lmax*M-b);
    phase=wave*(c.directions*t(antenna,:)')-angle(q).';f0(u)=sum(abs(q).'.*cos(phase));gradient(u,:)=-wave*(abs(q).'.*sin(phase))'*c.directions;
    bound=zeros(2);for v=1:M,d=c.directions(v,:);bound=bound+abs(q(v))*abs(d'*d);end
    curvature(u)=wave^2*max(eig(bound));ratio(u)=a/b;qrows(u,:)=q;
end
s=struct('chi',chi,'f0',f0,'gradient',gradient,'curvature',curvature,'ratio',ratio,'q',qrows,'Y',Y);
end

function [trial,record]=ma_coordinate(t,c,antenna,mode)
if strcmp(c.matlab_convex_solver,'certified_exact_2d')
    if strcmp(mode,'MRT')
        [value,gradient,curvature]=ma_mrt(t,c,antenna);[delta,certificate]=ma_exact_coordinate(t,c,antenna,mode,gradient(antenna,:)',curvature,[],[],[],value);
    else
        if ~strcmp(c.interpretations.zf_spacing,'P5n_with_equation_30_spacing'),error('Explicit original ZF spacing required');end
        [value,~,~,eta]=ma_zf(t,c);s=ma_zf_surrogate(t,c,antenna);[delta,certificate]=ma_exact_coordinate(t,c,antenna,mode,[],[],s.ratio+1./eta,s.gradient,s.curvature,value);
    end
    trial=t;trial(antenna,:)=trial(antenna,:)+delta';if strcmp(mode,'MRT'),actual=ma_mrt(trial,c);else,actual=ma_zf(trial,c);end
    lower=value+certificate.minorant_increment;
    if actual<lower-c.verification_tolerance||actual<value-c.verification_tolerance,error('Exact2D source surrogate/update validation failed');end
    record=struct('before',value,'after',actual,'surrogate',lower,'lower_bound_gap',actual-lower,'solver_status','certified_global_2d',...
        'solver_iterations',[],'original_subproblem_unchanged',true,'certificate',certificate);return;
end
if strcmp(mode,'MRT'),[value,gradient,curvature]=ma_mrt(t,c,antenna);variableScale=sqrt(max(curvature,1));objectiveConstant=value;
else
    if ~strcmp(c.interpretations.zf_spacing,'P5n_with_equation_30_spacing'),error('ZF spacing interpretation required.');end
    [value,~,~,eta]=ma_zf(t,c);s=ma_zf_surrogate(t,c,antenna);base=s.ratio+1./eta;
    localCurvature=(sum(s.curvature./base)*eye(2)+s.gradient'*((1./base.^2).*s.gradient))/log(2);
    variableScale=sqrt(max(max(eig(localCurvature)),1));objectiveConstant=sum(log2(eta.*base));
end
cvx_solver(c.matlab_convex_solver);
cvx_begin quiet
    cvx_precision(c.matlab_cvx_precision)
    variable u(2)
    expression x(2)
    expression delta(2)
    delta=u/variableScale;x=t(antenna,:)'+delta;
    if strcmp(mode,'MRT')
        maximize(gradient(antenna,:)*delta-curvature/2*sum_square(delta))
    else
        % Exact tangency chi+f0=a/b and log identity; no new minorant.
        maximize(sum(log(1+(s.gradient*delta-s.curvature/2*sum_square(delta))./base))/log(2))
    end
    subject to
        x>=c.region_lower(:);x<=c.region_upper(:);
        for v=1:size(t,1)
            if v~=antenna,d=t(antenna,:)-t(v,:);2*d*delta+d*d'>=c.minimum_distance^2;end
        end
cvx_end
if ~strcmp(cvx_status,'Solved'),error('Original convex subproblem status %s; no substitute update.',cvx_status);end
trial=t;trial(antenna,:)=x';if strcmp(mode,'MRT'),actual=ma_mrt(trial,c);else,actual=ma_zf(trial,c);end
sourceSurrogate=cvx_optval+objectiveConstant;
if actual<sourceSurrogate-c.verification_tolerance || actual<value-c.verification_tolerance,error('Original surrogate/update validation failed.');end
record=struct('before',value,'after',actual,'surrogate',sourceSurrogate,'lower_bound_gap',actual-sourceSurrogate,...
    'canonicalization','bijective_curvature_scaled_centered_displacement_and_constant_objective_removal','variable_scale',variableScale,...
    'solver_status',cvx_status,'solver_iterations',[],'original_subproblem_unchanged',true);
end

function [t,hist]=ma_optimize(t,c,mode)
if strcmp(mode,'MRT'),value=ma_mrt(t,c);else,value=ma_zf(t,c);end
objective=value;positions=reshape(t,1,size(t,1),2);records=struct([]);converged=false;
for sweep=0:c.maximum_AO_iterations-1
    for antenna=1:size(t,1),[t,record]=ma_coordinate(t,c,antenna,mode);record.sweep=sweep;record.antenna=antenna-1;if isempty(records),records=record;else,records(end+1)=record;end;end %#ok<AGROW>
    if strcmp(mode,'MRT'),value=ma_mrt(t,c);else,value=ma_zf(t,c);end
    objective(end+1)=value; %#ok<AGROW>
    positions(end+1,:,:)=reshape(t,1,size(t,1),2); %#ok<AGROW>
    if (objective(end)-objective(end-1))/abs(objective(end-1))<c.fractional_increase_threshold,converged=true;break;end
end
termination='configured_iteration_cap';if converged,termination='fractional_increase';end
hist=struct('objective',objective,'positions',positions,'coordinate_updates',records,'converged',converged,'termination',termination);
end

function S=ma_covariance(t,c)
distance=sqrt(sum((reshape(t,size(t,1),1,2)-reshape(t,1,size(t,1),2)).^2,3));S=besselj(0,2*pi*distance/c.wavelength);
end

function value=ma_correlated_mrt(t,c)
H=ma_los(t,c);[N,M]=size(H);S=ma_covariance(t,c);beta=c.beta(:);kap=c.rician(:);q=real(sum(conj(H).*(S*H),1))';traceS=trace(S*S);
numerator=beta.^2.*(N^2+(2*kap.*q+traceS)./(kap+1).^2);denominator=c.noise(:)*N*sum(beta)/c.power;gram=abs(H'*H).^2;
for u=1:M,for v=1:M,if v~=u,denominator(u)=denominator(u)+beta(u)*beta(v)*(kap(u)*kap(v)*gram(u,v)+kap(u)*q(u)+kap(v)*q(v)+traceS)/((kap(u)+1)*(kap(v)+1));end,end,end
value=sum(log2(1+numerator./denominator));
end

function out=ma_instantaneous(t,c,nlos,mode,correlated)
if nargin<5,correlated=false;end
Hbar=ma_los(t,c);[N,M]=size(Hbar);sampleCount=size(nlos,1);rates=zeros(1,sampleCount);powers=rates;leakage=rates;
root=eye(N);if correlated,S=ma_covariance(t,c);[V,L]=eig((S+S')/2);lambda=real(diag(L));if min(lambda)<-c.verification_tolerance,error('Bessel covariance not PSD.');end;root=V*diag(sqrt(max(lambda,0)))*V';end
for index=1:sampleCount
    sample=root*reshape(nlos(index,:,:),N,M);H=Hbar.*sqrt(c.beta(:).*c.rician(:)./(c.rician(:)+1))'+sample.*sqrt(c.beta(:)./(c.rician(:)+1))';
    if strcmp(mode,'MRT'),W=H*sqrt(c.power/sum(abs(H(:)).^2));else,V=H/(H'*H);W=V./vecnorm(V,2,1)*sqrt(c.power/M);end
    gain=abs(H'*W).^2;signal=diag(gain);rates(index)=sum(log2(1+signal./(sum(gain,2)-signal+c.noise(:))));powers(index)=sum(abs(W(:)).^2);
    hw=H'*W;off=hw-diag(diag(hw));leakage(index)=max(abs(off(:)));
end
out=struct('sample_sum_rates',rates,'mean_sum_rate',mean(rates),'powers',powers,'off_diagonal_amplitude',leakage);
end

function out=ma_diagonal_qcqp(q,b,power,tolerance)
q=q(:);energy=sum(abs(b).^2,2);active=q>0;out=zeros(size(b));out(active,:)=b(active,:)./q(active);
if all(energy(~active)<=tolerance^2) && sum(abs(out(:)).^2)<=power,return;end
lo=0;hi=1;evaluate=@(nu)sum(energy./(q+nu).^2);while evaluate(hi)>power,hi=2*hi;end
while hi-lo>tolerance*max(1,hi),mid=(lo+hi)/2;if evaluate(mid)>power,lo=mid;else,hi=mid;end,end
out=b./(q+hi);
end

function rate=ma_channel_rate(H,W)
gain=abs(H'*W).^2;signal=diag(gain);rate=sum(log2(1+signal./(sum(gain,2)-signal+1)));
end

function [rate,hist]=ma_fixed_benchmark(H,c,kind)
H=H./sqrt(c.noise(:))';[N,M]=size(H);p=c.power;spec=c.benchmark_solver;
if strcmp(kind,'FPA-ZF')
    V=H/(H'*H);V=V./vecnorm(V,2,1);gain=abs(diag(H'*V)).^2;cost=1./gain;lo=0;hi=p+max(cost);
    while hi-lo>spec.bisection_tolerance,mid=(lo+hi)/2;if sum(max(mid-cost,0))>p,hi=mid;else,lo=mid;end,end
    W=V.*sqrt(max(lo-cost,0))';rate=ma_channel_rate(H,W);hist=struct('iterations',0,'converged',true);return;
end
V=H./vecnorm(H,2,1);W=V*sqrt(p/M);objective=ma_channel_rate(H,W);converged=false;
for iteration=1:spec.maximum_iterations
    Z=H'*W;total=sum(abs(Z).^2,2)+1;signal=abs(diag(Z)).^2;mu=signal./(total-signal);eta=diag(Z)./total;
    if strcmp(kind,'FPA-MRT')
        HV=H'*V;q=sum(((1+mu).*abs(eta).^2).*abs(HV).^2,1)'/log(2);b=(1+mu).*real(conj(eta).*diag(HV))/log(2);
        amp=ma_diagonal_qcqp(q,b,p,spec.bisection_tolerance);W=V.*amp';
    else
        Q=(H.*((1+mu).*abs(eta).^2)')*H'/log(2);B=H.*transpose((1+mu).*eta)/log(2);[U,L]=eig((Q+Q')/2);lambda=real(diag(L));
        if min(lambda)<-spec.spectral_zero_tolerance*max(max(lambda),1),error('QT QCQP failed PSD identity.');end
        lambda(lambda<0)=0;projected=U'*B;W=U*ma_diagonal_qcqp(lambda,projected,p,spec.bisection_tolerance);
    end
    objective(end+1)=ma_channel_rate(H,W); %#ok<AGROW>
    if objective(end)<objective(end-1)-c.verification_tolerance,error('Fixed-array QT decreased objective.');end
    if (objective(end)-objective(end-1))/abs(objective(end-1))<spec.fractional_tolerance,converged=true;break;end
end
rate=objective(end);hist=struct('iterations',numel(objective)-1,'converged',converged,'objective',objective);
end

function result=ma_component(config,base)
f=jsondecode(fileread(fullfile(base,'fixture.json')));[c,t]=ma_scenario(config,6,5,f.rician_linear,1,2,f);t=f.positions;
[value,grad]=ma_mrt(t,c);numerical=zeros(size(t));eps=f.finite_difference_step;
for n=1:size(t,1),for d=1:2,plus=t;minus=t;plus(n,d)=plus(n,d)+eps;minus(n,d)=minus(n,d)-eps;numerical(n,d)=(ma_mrt(plus,c)-ma_mrt(minus,c))/(2*eps);end,end
[zf,~,Sigma]=ma_zf(t,c);s=ma_zf_surrogate(t,c,1);inverse=Sigma\eye(5);identity=1./real(diag(inverse));tangent=s.chi+s.f0;
[mrtT,mrtUpdate]=ma_coordinate(t,c,1,'MRT');[zfT,zfUpdate]=ma_coordinate(t,c,1,'ZF');sample=[2,1.5;1.5,1];closed=(trace(sample)+sqrt((sample(1,1)-sample(2,2))^2+4*sample(1,2)^2))/2;
distance=sqrt(sum((reshape(zfT,6,1,2)-reshape(zfT,1,6,2)).^2,3))+eye(6)*1e9;
checks=struct('mrt_gradient_max_error',max(abs(grad(:)-numerical(:))),'gradient_pass',max(abs(grad(:)-numerical(:)))<1e-6,...
    'zf_woodbury_identity_error',max(abs(s.ratio-identity)),'zf_MM_tangency_error',max(abs(tangent-s.ratio)),...
    'Eq29a_corrected_closed_form_error',abs(closed-max(eig(sample))),'mrt_surrogate_lower_bound_gap',mrtUpdate.lower_bound_gap,...
    'zf_surrogate_lower_bound_gap',zfUpdate.lower_bound_gap,'spacing_feasible',min(distance(:))>=.5-1e-7,...
    'box_feasible',all(all(zfT>=c.region_lower' & zfT<=c.region_upper')),'correlated_zf_closed_form_implemented',false,'finite',all(isfinite(zfT(:))));
checks.box_feasible=all(all(zfT>=c.region_lower' & zfT<=c.region_upper'));
assert(checks.gradient_pass && checks.zf_woodbury_identity_error<1e-10 && checks.zf_MM_tangency_error<1e-10 && checks.spacing_feasible);
result=struct('paper_id','two-timescale-ma','mode','component_test_not_full_run','metrics',struct('mrt_statistical',value,'zf_statistical',zf,...
    'correlated_mrt',ma_correlated_mrt(t,c),'mrt_one_coordinate',mrtT,'zf_one_coordinate',zfT),'checks',checks,'history',struct('mrt',mrtUpdate,'zf',zfUpdate));
end

function result=ma_job(job,config)
[c,t]=ma_scenario(config,job.N,job.M,job.kappa,job.power,job.A,job.geometry);if isfield(job,'initial_positions'),t=job.initial_positions;end
if isfield(job,'region_lower'),c.region_lower=job.region_lower(:);c.region_upper=job.region_upper(:);end
nlos=job.nlos_re+1i*job.nlos_im;if size(nlos,1)~=config.nlos_realizations_per_geometry,error('Full NLoS count mismatch.');end
design=c;if isfield(job,'estimated_geometry'),[design,~]=ma_scenario(config,job.N,job.M,job.kappa,job.power,job.A,job.estimated_geometry);end
[mrtPos,mrtHist]=ma_optimize(t,design,'MRT');[zfPos,zfHist]=ma_optimize(t,design,'ZF');schemes=struct();jitter=zeros(size(t));if isfield(job,'antenna_position_error'),jitter=job.antenna_position_error;end
schemes.MA_MRT=ma_instantaneous(mrtPos+jitter,c,nlos,'MRT',false);schemes.MA_ZF=ma_instantaneous(zfPos+jitter,c,nlos,'ZF',false);
names={'FPA_MRT','FPA_ZF','FPA_OPT'};kinds={'FPA-MRT','FPA-ZF','FPA-OPT'};rates=zeros(3,size(nlos,1));caps=zeros(3,1);Hbar=ma_los(t,c);
for index=1:size(nlos,1)
    sample=reshape(nlos(index,:,:),job.N,job.M);H=Hbar.*sqrt(c.beta(:).*c.rician(:)./(c.rician(:)+1))'+sample.*sqrt(c.beta(:)./(c.rician(:)+1))';
    for kind=1:3,[rates(kind,index),hist]=ma_fixed_benchmark(H,c,kinds{kind});caps(kind)=caps(kind)+~hist.converged;end
end
for kind=1:3,schemes.(names{kind})=struct('sample_sum_rates',rates(kind,:),'mean_sum_rate',mean(rates(kind,:)),'nonconverged_samples',caps(kind));end
if ismember(job.figure,[3,13,15])
    curve=zeros(1,size(mrtHist.positions,1));for index=1:numel(curve),item=ma_instantaneous(reshape(mrtHist.positions(index,:,:),job.N,2),c,nlos,'MRT',false);curve(index)=item.mean_sum_rate;end
    mrtHist.instantaneous_MC_mean=curve;
end
if ismember(job.figure,[4,14,16])
    curve=zeros(1,size(zfHist.positions,1));for index=1:numel(curve),item=ma_instantaneous(reshape(zfHist.positions(index,:,:),job.N,2),c,nlos,'ZF',false);curve(index)=item.mean_sum_rate;end
    zfHist.instantaneous_MC_mean=curve;
end
extension=struct();if isfield(job,'correlated')&&job.correlated
    extension.MA_MRT_MC=ma_instantaneous(mrtPos,c,nlos,'MRT',true);extension.MA_ZF_MC=ma_instantaneous(zfPos,c,nlos,'ZF',true);
    extension.MRT_Eq69_at_MRT_positions=ma_correlated_mrt(mrtPos,c);extension.ZF_Eq75_status='blocked_by_Eq72_74_dimension_mismatch';
    mrtCurve=zeros(1,size(mrtHist.positions,1));zfCurve=zeros(1,size(zfHist.positions,1));
    for index=1:numel(mrtCurve),item=ma_instantaneous(reshape(mrtHist.positions(index,:,:),job.N,2),c,nlos,'MRT',true);mrtCurve(index)=item.mean_sum_rate;end
    for index=1:numel(zfCurve),item=ma_instantaneous(reshape(zfHist.positions(index,:,:),job.N,2),c,nlos,'ZF',true);zfCurve(index)=item.mean_sum_rate;end
    extension.MRT_correlated_MC_history=mrtCurve;extension.ZF_correlated_MC_history=zfCurve;
    eq69Curve=zeros(1,size(mrtHist.positions,1));for index=1:numel(eq69Curve),eq69Curve(index)=ma_correlated_mrt(reshape(mrtHist.positions(index,:,:),job.N,2),c);end
    extension.MRT_Eq69_history=eq69Curve;
    extension.comparison_protocol=struct('trajectory','iid_Algorithm1_for_MRT_iid_Algorithm2_for_ZF','same_exported_NLoS_ensemble',true,...
        'source_supported_interpretation',true,'original_experiment_record_recovered',false,'original_curve_closeness_verified',false);
end
checks=struct('mrt_converged',mrtHist.converged,'zf_converged',zfHist.converged,'each_algorithm_owns_its_positions',true,'full_N',job.N,'full_M',job.M,'nlos_samples',size(nlos,1));
for item=1:2
    if item==1,pos=mrtPos;name='mrt';else,pos=zfPos;name='zf';end
    distance=sqrt(sum((reshape(pos,job.N,1,2)-reshape(pos,1,job.N,2)).^2,3))+eye(job.N)*1e9;
    checks.([name,'_nominal_design_spacing_feasible'])=min(distance(:))>=.5-c.verification_tolerance;
    checks.([name,'_nominal_design_box_feasible'])=all(all(pos>=c.region_lower'-c.verification_tolerance & pos<=c.region_upper'+c.verification_tolerance));
    realized=pos+jitter;distance=sqrt(sum((reshape(realized,job.N,1,2)-reshape(realized,1,job.N,2)).^2,3))+eye(job.N)*1e9;
    checks.([name,'_realized_positions_spacing_feasible'])=min(distance(:))>=.5-c.verification_tolerance;
    checks.([name,'_realized_positions_box_feasible'])=all(all(realized>=c.region_lower'-c.verification_tolerance & realized<=c.region_upper'+c.verification_tolerance));
end
checks.perfect_instantaneous_CSI_for_beamforming=true;
brute=struct();if isfield(job,'brute_force_D')
    for item=1:2
        if item==1,mode='MRT';else,mode='ZF';end
        [winner,record]=ma_exhaustive(c,job.N,job.brute_force_D,mode,nlos);brute.(mode)=struct('search',record,'positions',winner,'MC',ma_instantaneous(winner,c,nlos,mode,false));
    end
end
metadata=struct('N',job.N,'M',job.M,'kappa',job.kappa,'power',job.power,'A',job.A,'figure',job.figure,'point',job.point,'realization',job.realization);
result=struct('paper_id','two-timescale-ma','mode','full_scenario','job_metadata',metadata,...
    'metrics',struct('schemes',schemes,'correlated_extension',extension,'brute_force',brute,'mrt_positions',mrtPos,'zf_positions',zfPos,'mrt_realized_positions',mrtPos+jitter,'zf_realized_positions',zfPos+jitter),...
    'checks',checks,'history',struct('mrt',mrtHist,'zf',zfHist));
end

function [winner,record]=ma_exhaustive(c,N,D,mode,nlos)
% Actual complete finite-MC objective: all ordered layouts, no hidden cap.
x=linspace(c.region_lower(1),c.region_upper(1),D);y=linspace(c.region_lower(2),c.region_upper(2),D);grid=zeros(D^2,2);index=1;
for a=x,for b=y,grid(index,:)=[a,b];index=index+1;end,end
actualMC=strcmp(c.brute_force_objective,'instantaneous_MC');best=-Inf;winner=[];tested=0;pruned=0;started=tic;visit([],1);
if isempty(winner),error('No feasible complete grid geometry.');end
record=struct('D',D,'N',N,'mode',mode,'evaluated_feasible_geometries',tested,'pruned_partial_branches',pruned,...
    'objective',best,'elapsed_seconds',toc(started),'complete',true,'permutation_symmetry_reduction',~actualMC,'objective_protocol',c.brute_force_objective);
    function visit(indices,startIndex)
        if numel(indices)==N
            positions=grid(indices,:);
            if actualMC,item=ma_instantaneous(positions,c,nlos,mode,false);value=item.mean_sum_rate;
            elseif strcmp(c.brute_force_objective,'paper_statistical_design_objective'),if strcmp(mode,'MRT'),value=ma_mrt(positions,c);else,value=ma_zf(positions,c);end
            else,error('Explicit brute-force objective protocol required.');end
            tested=tested+1;if value>best,best=value;winner=positions;end;return;
        end
        remaining=N-numel(indices);
        if actualMC,pointRange=1:size(grid,1);else,pointRange=startIndex:size(grid,1)-remaining+1;end
        for point=pointRange
            if ~isempty(indices)&&any(vecnorm(grid(indices,:)-grid(point,:),2,2)<c.minimum_distance),pruned=pruned+1;continue;end
            if actualMC,next=1;else,next=point+1;end;visit([indices,point],next);
        end
    end
end

