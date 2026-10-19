function summary=replay_one_saved_coordinate_native_v1(fixturePath,configPath,outputDirectory,admissionPath,planPath)
% PREPARED only new frozen-source coordinate. No optimizer/sweep/RNG/MC.
plan=jsondecode(fileread(planPath));admission=jsondecode(fileread(admissionPath));fixture=jsondecode(fileread(fixturePath));config=jsondecode(fileread(configPath));
assert(admission.root_admitted_one_new_fixed_coordinate_source_replay&&strcmp(admission.lane,'native'));
assert(strcmp(named(admission,'case'),named(fixture,'case'))&&strcmp(admission.mode,fixture.mode)&&strcmp(admission.plan_SHA256,file_sha(planPath)));
assert(~isfolder(outputDirectory)&&~isfile(outputDirectory),'Fresh unique output required; do not repeat');
assert(strcmp(config.matlab_convex_solver,'certified_exact_2d'));
runtimeDirectory=fileparts(mfilename('fullpath'));
assert(strcmp(which('ma_exact_coordinate'),fullfile(runtimeDirectory,'ma_exact_coordinate.m'))&&strcmp(which('ma6_passive_capture_v1'),fullfile(runtimeDirectory,'ma6_passive_capture_v1.m')),'Actual native provider path mismatch; do not call coordinate');
inputs=plan.inputs;selected=false;
for index=1:numel(inputs),item=member(inputs,index);if strcmp(named(item,'case'),named(fixture,'case'))&&strcmp(item.mode,fixture.mode),assert(strcmp(item.SHA256,file_sha(fixturePath)));selected=true;end,end
assert(selected&&strcmp(plan.configuration.SHA256,file_sha(configPath)));
pins=plan.execution_source_pins;before=check_pins(pins);inputBefore={file_sha(fixturePath),file_sha(configPath),file_sha(admissionPath),file_sha(planPath)};
mkdir(outputDirectory);ma6_passive_capture_v1('initialize',[]);job=fixture.selected_original_job;overrides=fixture.optional_original_design_overrides;
names=fieldnames(overrides);for index=1:numel(names),job.(names{index})=overrides.(names{index});end
[design,unusedOriginalInitializer]=ma_scenario(config,job.N,job.M,job.kappa,job.power,job.A,job.geometry);
if isfield(job,'region_lower'),design.region_lower=job.region_lower(:);design.region_upper=job.region_upper(:);end
if isfield(job,'estimated_geometry'),[design,~]=ma_scenario(config,job.N,job.M,job.kappa,job.power,job.A,job.estimated_geometry);end
t=fixture.actual_pre_state;antenna=fixture.antenna_zero_based+1;mode=fixture.mode;assert(isequal(size(t),[6 2])&&job.N==6&&job.M==5&&antenna>=1&&antenna<=6);
ma6_passive_capture_v1('actual_complete_design_and_whole_saved_prestate',struct('c',design,'t',t,'antenna_one_based',antenna,'mode',mode,'unused_original_scenario_initializer',unusedOriginalInitializer));
returned=false;trial=[];record=[];actualException=[];started=tic;
try
    [trial,record]=ma_coordinate(t,design,antenna,mode);returned=true;
catch problem
    actualException=struct('identifier',problem.identifier,'message',problem.message,'stack',problem.stack);
end
observation=ma6_passive_capture_v1('finish',[]);after=check_pins(pins);inputAfter={file_sha(fixturePath),file_sha(configPath),file_sha(admissionPath),file_sha(planPath)};
comparison=[];
if returned
    comparison=struct('new_whole_endpoint_IEEE64_equal_historical_python',same_binary64(trial,fixture.actual_python_post_state),'new_whole_endpoint_IEEE64_equal_historical_native',same_binary64(trial,fixture.actual_matlab_post_state),...
        'maximum_new_minus_historical_python',max(abs(trial-fixture.actual_python_post_state),[],'all'),'maximum_new_minus_historical_native',max(abs(trial-fixture.actual_matlab_post_state),[],'all'),'not_proof_of_historical_local_arithmetic_reproduction',true);
end
sourceClosed=isequal(before,after)&&isequal(inputBefore,inputAfter);summary=struct('schema','actual-new-frozen-source-one-fixed-coordinate-replay-v1','lane','native','case_id',named(fixture,'case'),'mode',mode,...
    'coordinate_index_zero_based',fixture.coordinate_index_zero_based,'antenna_zero_based',fixture.antenna_zero_based,'original_function_returned',returned,'actual_exception',actualException,'source_input_interval_closed',sourceClosed,...
    'source_before',{before},'source_after',{after},'input_before',{inputBefore},'input_after',{inputAfter},'comparison_to_saved_endpoints',comparison,'observer_error_count',numel(observation.observer_errors),...
    'elapsed_seconds',toc(started),'new_coordinate_source_execution_not_historical_producer_replay',true,'original_subproblem_and_tolerances_unchanged',true,'no_optimize_run_job_instantaneous_benchmark_RNG_or_MP_calls',true,...
    'historical_path_gate_repaired_or_cause_proven',false,'independent_MP_coefficient_validation_pending',true);
save(fullfile(outputDirectory,'actual-original-coordinate-operands-candidates-and-return.mat'),'fixture','config','design','t','antenna','mode','trial','record','observation','summary','-v7');
summary.numeric_MAT_SHA256=file_sha(fullfile(outputDirectory,'actual-original-coordinate-operands-candidates-and-return.mat'));
fid=fopen(fullfile(outputDirectory,'ACTUAL_ONE_SOURCE_BOUND_FIXED_COORDINATE_CAPTURE_V1.json'),'w');assert(fid>=0);cleaner=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(summary));clear cleaner;
assert(returned&&sourceClosed&&isempty(observation.observer_errors),'Actual coordinate/observer/source failure retained; no retry.');
end
function x=member(items,index)
if iscell(items),x=items{index};else,x=items(index);end
end
function value=named(source,key)
if isfield(source,key),value=source.(key);else,value=source.(matlab.lang.makeValidName(key));end
end
function values=check_pins(pins)
values=cell(1,numel(pins));for index=1:numel(pins),item=member(pins,index);actual=file_sha(item.path);assert(strcmp(actual,item.SHA256),'Frozen source changed: %s',item.path);values{index}=struct('path',item.path,'SHA256',actual);end
end
function value=file_sha(path)
fid=fopen(path,'rb');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));raw=fread(fid,Inf,'*uint8');clear cleanup;digest=java.security.MessageDigest.getInstance('SHA-256');if ~isempty(raw),digest.update(raw);end;value=lower(reshape(dec2hex(typecast(digest.digest(),'uint8'),2).',1,[]));
end
function result=same_binary64(a,b)
result=isa(a,'double')&&isa(b,'double')&&isequal(size(a),size(b))&&isequal(typecast(a(:),'uint64'),typecast(b(:),'uint64'));
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
ma6_passive_capture_v1('actual_original_MRT_statistics_return',struct('gradient',gradient,'curvature',curvature,'gd',gd,'psi',psi,'weight',weight,'numerator',numerator,'denominator',denominator,'value',value,'rates',rates));
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
ma6_passive_capture_v1('actual_ZF_user_expansion',struct('u',u,'H',H,'scale',scale,'g',g,'Theta1',Theta1,'Theta2',Theta2,'inverse',inverse,'Y',Y,'a',a,'ell',ell,'X',X,'b',b,'lmax',lmax,'q',q,'chi',chi(u),'f0',f0(u),'gradient',gradient(u,:),'curvature',curvature(u),'ratio',ratio(u)));
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

