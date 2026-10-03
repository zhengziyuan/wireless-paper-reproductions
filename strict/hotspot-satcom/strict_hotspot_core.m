function varargout=strict_hotspot_core(action,varargin)
% Real QT/SOCP, SDP randomization and author RGD; RCG is diagnostic only.
switch action
    case 'effective', [varargout{1:nargout}]=effective(varargin{:});
    case 'evaluate', [varargout{1:nargout}]=evaluate(varargin{:});
    case 'active_qt_update', [varargout{1:nargout}]=active_qt_update(varargin{:});
    case 'phase_sdr_update', [varargout{1:nargout}]=phase_sdr_update(varargin{:});
    case 'criterion_gradient', [varargout{1:nargout}]=criterion_gradient(varargin{:});
    case 'phase_rcg', [varargout{1:nargout}]=phase_rcg(varargin{:});
    case 'phase_rgd', [varargout{1:nargout}]=phase_rgd(varargin{:});
    case 'qt_loop', [varargout{1:nargout}]=qt_loop(varargin{:});
    case 'ao', [varargout{1:nargout}]=ao(varargin{:});
    case 'two_stage', [varargout{1:nargout}]=two_stage(varargin{:});
    otherwise, error('Unknown strict hotspot component');
end
end

function hu=effective(direct,R,phi)
[U,M,N]=size(R); hu=direct; phi=phi(:).';
for u=1:U, hu(u,:)=hu(u,:)+phi*reshape(R(u,:,:),M,N); end
end

function out=evaluate(hu,nhu,W,noise)
C=[hu;nhu]; received=abs(C*W).^2; desired=diag(received);
sinr=desired./(sum(received,2)-desired+noise);
out=struct('sinr',sinr,'hu_sum_rate',sum(log2(1+sinr(1:size(hu,1)))), ...
    'total_power',sum(abs(W(:)).^2));
end

function a=qt_parameters(hu,W,noise)
U=size(hu,1); received=hu*W; desired=zeros(U,1);
for u=1:U, desired(u)=received(u,u); end
a=desired./(sum(abs(received).^2,2)-abs(desired).^2+noise);
end

function [out,info,a]=active_qt_update(hu,nhu,W0,noise,power,target,a)
assert(exist('cvx_begin','file')==2,'External CVX must be configured');
if nargin<7, a=qt_parameters(hu,W0,noise); end
[U,N]=size(hu); K=size(nhu,1); J=U+K;
scale=sqrt(power/noise); hs=hu*scale; ns=nhu*scale; az=a*sqrt(noise);
cvx_begin quiet
    variable W(N,J) complex
    variables lambda(U) auxSinr(U)
    maximize(sum(log(1+auxSinr))/log(2))
    subject to
    sum_square_abs(W(:))<=1;
    for u=1:U
        indexes=setdiff(1:J,u);
        % Same QT problem with weighted epigraph lambda'=|a|^2*denominator.
        sum_square_abs((conj(az(u))*(hs(u,:)*W(:,indexes))).')+abs(az(u))^2<=lambda(u);
        auxSinr(u)<=2*real(conj(az(u))*(hs(u,:)*W(:,u)))-lambda(u);
    end
    for k=1:K
        index=U+k; indexes=setdiff(1:J,index); desired=ns(k,:)*W(:,index);
        imag(desired)==0;
        norm([ns(k,:)*W(:,indexes),1])<=real(desired)/sqrt(target(k));
    end
cvx_end
assert(contains(cvx_status,'Solved'),'Hotspot QT/SOCP failed: %s',cvx_status);
out=W*sqrt(power); before=evaluate(hu,nhu,W0,noise); after=evaluate(hu,nhu,out,noise);
received=hu*W0; desired=zeros(U,1); for u=1:U, desired(u)=received(u,u); end
den=sum(abs(received).^2,2)-abs(desired).^2+noise;
qt=2*real(conj(a).*desired)-abs(a).^2.*den;
scaledReceived=hs*W;newdesired=diag(scaledReceived(:,1:U));
newden=sum(abs(scaledReceived).^2,2)-abs(newdesired).^2+1;
weightedDen=abs(az).^2.*newden;
newqt=2*real(conj(az).*newdesired)-lambda;
primal=max([0;sum(abs(W(:)).^2)-1;(weightedDen-lambda)./max(1,abs(weightedDen));(auxSinr-newqt)./max(1,abs(newqt))]);
for k=1:K
    index=U+k;indexes=setdiff(1:J,index);des=ns(k,:)*W(:,index);left=norm([ns(k,:)*W(:,indexes),1]);right=real(des)/sqrt(target(k));
    primal=max([primal,abs(imag(des))/max(1,abs(des)),(left-right)/max([1,left,abs(right)])]);
end
diagnostics=struct('solver','external_CVX','status',cvx_status,'reported_solver_tolerance',cvx_slvtol,'constraint_max_relative_violation',primal,'qt_bound_max_violation',max([0;auxSinr-after.sinr(1:U)]), ...
    'epigraph_scaling','lambda_prime_equals_abs_a_squared_times_physical_interference');
info=struct('solver_status',cvx_status,'surrogate_rate',cvx_optval, ...
    'solver_diagnostics',diagnostics,'qt_bound_max_violation',diagnostics.qt_bound_max_violation, ...
    'qt_tightness_error',max(abs(qt-before.sinr(1:U))),'before',before,'after',after);
end

function value=phase_surrogate(direct,R,phi,W,a,noise)
hu=effective(direct,R,phi); U=size(hu,1); received=hu*W; desired=zeros(U,1);
for u=1:U, desired(u)=received(u,u); end
den=sum(abs(received).^2,2)-abs(desired).^2+noise;
q=2*real(conj(a).*desired)-abs(a).^2.*den;
if any(1+q<=0), value=-inf; else, value=sum(log2(1+q)); end
end

function [phi,info]=phase_sdr_update(direct,R,phi0,W,a,noise,normals)
assert(exist('cvx_begin','file')==2,'External CVX SDP/exponential support required');
[U,M,N]=size(R); J=size(W,2);
assert(size(normals,1)==M+1 && size(normals,2)>=1,'Shared CN draws shape mismatch');
L=complex(zeros(M+1,M+1,U)); Q=complex(zeros(M+1,M+1,U,J)); desired=zeros(U,1);
for u=1:U
    Ru=reshape(R(u,:,:),M,N); b=conj(a(u))*Ru*W(:,u);
    L(1:M,M+1,u)=b/2; L(M+1,1:M,u)=b'/2;
    desired(u)=2*real(conj(a(u))*(direct(u,:)*W(:,u)));
    for j=1:J
        c=[Ru*W(:,j);direct(u,:)*W(:,j)]; Q(:,:,u,j)=c*c';
    end
end
cvx_begin sdp quiet
    variable V(M+1,M+1) hermitian
    expression terms(U)
    for u=1:U
        q=desired(u)+2*real(trace(L(:,:,u)*V))-abs(a(u))^2*noise;
        for j=1:J
            if j~=u, q=q-abs(a(u))^2*real(trace(Q(:,:,u,j)*V)); end
        end
        terms(u)=log(1+q)/log(2);
    end
    maximize(sum(terms))
    subject to
    V>=0;
    diag(V)==1;
cvx_end
assert(contains(cvx_status,'Solved'),'Phase SDP failed: %s',cvx_status);
relaxation=(V+V')/2; [E,D]=eig(relaxation); values=real(diag(D));
assert(min(values)>=-1e-5,'Non-PSD relaxation beyond numerical tolerance');
% Principal root avoids eigenvector gauge differences in paired-language draws.
factor=E*diag(sqrt(max(values,0)))*E'; samples=factor*normals;
phi=phi0(:).'; best=phase_surrogate(direct,R,phi,W,a,noise);
for ell=1:size(samples,2)
    sample=samples(:,ell);
    if abs(sample(end))<1e-14, continue; end
    candidate=conj(sample(1:M)/sample(end)).'; candidate=candidate./abs(candidate);
    value=phase_surrogate(direct,R,candidate,W,a,noise);
    if value>best, phi=candidate; best=value; end
end
info=struct('solver_status',cvx_status,'sdr_upper_bound',cvx_optval, ...
    'solver_diagnostics',struct('solver','external_CVX','status',cvx_status,'reported_solver_tolerance',cvx_slvtol,'constraint_max_relative_violation',max([0;-min(values);abs(diag(relaxation)-1)]),'sdr_bound_max_violation',max(0,best-cvx_optval)), ...
    'rounded_surrogate',best,'unit_modulus_error',max(abs(abs(phi)-1)), ...
    'diagonal_error',max(abs(diag(relaxation)-1)), ...
    'smallest_sdp_eigenvalue',min(values),'randomization_count',size(normals,2));
end

function [value,g]=criterion_gradient(direct,R,nhu,phi)
phi=phi(:).'; c=effective(direct,R,phi); [U,M,N]=size(R); A=eye(N);
for k=1:size(nhu,1)
    h=nhu(k,:)'; A=A-(h*h')/real(h'*h);
end
ca=c*A; f2=sum(abs(ca(:)).^2); f3=0;
for u=1:U
    for v=1:u-1, f3=f3+abs(c(u,:)*c(v,:)')^2; end
end
phaseGradient=zeros(1,M);
for m=1:M
    dc=1i*phi(m)*reshape(R(:,m,:),U,N); dca=dc*A;
    d2=2*real(sum(conj(ca(:)).*dca(:))); d3=0;
    for u=1:U
        for v=1:u-1
            t=c(u,:)*c(v,:)'; dt=dc(u,:)*c(v,:)'+c(u,:)*dc(v,:)';
            d3=d3+2*real(conj(t)*dt);
        end
    end
    phaseGradient(m)=d2-d3;
end
value=f2-f3; g=1i*phi.*phaseGradient;
end

function out=transport(vector,point)
out=vector-real(vector.*conj(point)).*point;
end

function [phi,history,status]=phase_rcg(direct,R,nhu,phi,maxIterations,gradientTolerance)
% Explicit PR+ diagnostic only, never selected by the formal two-stage chain.
[phi,history,status]=phase_optimizer(direct,R,nhu,phi,maxIterations,gradientTolerance,true,false);
end

function [phi,history,status]=phase_rgd(direct,R,nhu,phi,maxIterations,gradientTolerance,literalSign)
if nargin<7,literalSign=false;end
[phi,history,status]=phase_optimizer(direct,R,nhu,phi,maxIterations,gradientTolerance,false,literalSign);
end

function [phi,history,status]=phase_optimizer(direct,R,nhu,phi,maxIterations,gradientTolerance,conjugate,literalSign)
sign=1;if literalSign,sign=-1;end
phi=phi(:).'; [value,g]=criterion_gradient(direct,R,nhu,phi); direction=sign*g; history=value;
for it=1:maxIterations
    norm2=real(g*g'); if sqrt(norm2)<=gradientTolerance, break; end
    if ~conjugate,direction=sign*g;end
    slope=real((sign*g)*direction');
    if slope<=0, direction=g; slope=norm2; end
    alpha=1; accepted=false;
    for search=1:50
        candidate=phi+alpha*direction; candidate=candidate./abs(candidate);
        [trial,newg]=criterion_gradient(direct,R,nhu,candidate);
        if sign*(trial-value)>=1e-4*alpha*slope, accepted=true; break; end
        alpha=alpha/2;
    end
    assert(accepted,'RGD/explicit diagnostic search failed; no replacement algorithm used');
    if conjugate
        oldg=transport(g,candidate); olddir=transport(direction,candidate);beta=max(0,real(newg*(newg-oldg)')/norm2);direction=newg+beta*olddir;
    end
    phi=candidate; value=trial; g=newg; history(end+1)=value; %#ok<AGROW>
end
status=strict_hotspot_termination('gradient',norm(g),numel(history)-1,maxIterations,gradientTolerance);
status.phase_method='author_Algorithm_3-2_RGD_minimize_negative_F';status.printed_sign_interpretation='argmax_F_equivalent_minimize_negative_F';
if conjugate,status.phase_method='PR_plus_RCG_diagnostic_NOT_paper_method';end
if literalSign,status.phase_method='literal_negative_grad_F_diagnostic_NOT_argmax_F';status.printed_sign_interpretation='literal_diagnostic';end
end

function [W,history,status,diagnostics]=qt_loop(hu,nhu,W0,noise,power,target,maxIterations,relativeTolerance)
W=W0; e=evaluate(hu,nhu,W,noise); history=e.hu_sum_rate;diagnostics={};
for it=1:maxIterations
    [candidate,info,~]=active_qt_update(hu,nhu,W,noise,power,target);
    diagnostics{end+1}=info.solver_diagnostics; %#ok<AGROW>
    value=info.after.hu_sum_rate; assert(value>=history(end)-1e-6,'QT objective decreased');
    W=candidate; history(end+1)=value; %#ok<AGROW>
    if (history(end)-history(end-1))/max(abs(history(end-1)),1e-12)<relativeTolerance, break; end
end
status=strict_hotspot_termination('relative',history,maxIterations,relativeTolerance);
end

function [phi,W,history,status,diagnostics,endpoints]=ao(direct,R,nhu,phi0,W0,noise,power,target,normals,maxIterations,tolerance)
phi=phi0; W=W0; hu=effective(direct,R,phi); e=evaluate(hu,nhu,W,noise); history=e.hu_sum_rate;diagnostics={};
endpoints=struct();
assert(numel(normals)>=maxIterations,'Supply shared draws for every AO iteration');
for it=1:maxIterations
    a=qt_parameters(hu,W,noise); [W,active,~]=active_qt_update(hu,nhu,W,noise,power,target,a);
    a=qt_parameters(hu,W,noise);
    phaseClock=tic;[phi,phase]=phase_sdr_update(direct,R,phi,W,a,noise,normals{it});phase.solver_diagnostics.phase_cpu_seconds=toc(phaseClock);
    diagnostics{end+1}=struct('active',active.solver_diagnostics,'phase',phase.solver_diagnostics); %#ok<AGROW>
    hu=effective(direct,R,phi); e=evaluate(hu,nhu,W,noise); value=e.hu_sum_rate;
    assert(value>=history(end)-1e-5,'AO objective decreased beyond solver accuracy');
    history(end+1)=value; %#ok<AGROW>
    if any(it==[20,100]),endpoints.(sprintf('AO%d',it))=struct('evaluation',e,'executed_outer_iterations',it, ...
            'requested_outer_budget',it,'interpretation','reported_fixed_budget_endpoint_NOT_stationarity_claim','solver_diagnostics',{diagnostics});end
    if (history(end)-history(end-1))/max(abs(history(end-1)),1e-12)<tolerance, break; end
end
status=strict_hotspot_termination('relative',history,maxIterations,tolerance);
for budget=[20,100]
    name=sprintf('AO%d',budget);
    if ~isfield(endpoints,name)&&numel(history)-1<budget&&status.converged
        endpoints.(name)=struct('evaluation',e,'executed_outer_iterations',numel(history)-1,'requested_outer_budget',budget, ...
            'interpretation','original_relative_stop_reached_before_reported_budget_NO_trace_padding','solver_diagnostics',{diagnostics});
    end
end
end

function [phi,W,history]=two_stage(direct,R,nhu,phi0,W0,noise,power,target,rgdIterations,gradTolerance,qtIterations,qtTolerance)
phaseClock=tic;[phi,phaseHistory,pstatus]=phase_rgd(direct,R,nhu,phi0,rgdIterations,gradTolerance);phaseSeconds=toc(phaseClock);
[W,rateHistory,qstatus,diagnostics]=qt_loop(effective(direct,R,phi),nhu,W0,noise,power,target,qtIterations,qtTolerance);
history=struct('phase_criterion',phaseHistory,'qt_rate',rateHistory,'termination',struct('phase',pstatus,'QT',qstatus),'solver_diagnostics',{diagnostics},'phase_method','author_Algorithm_3-2_RGD_minimize_negative_F','phase_cpu_seconds',phaseSeconds);
end
