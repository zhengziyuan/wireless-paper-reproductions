function varargout=strict_hotspot_statistical(action,varargin)
% Explicit corrected vector-QT erratum; full finite-Rician moment model.
switch action
    case 'moments',[varargout{1:nargout}]=moments(varargin{:});
    case 'evaluate',[varargout{1:nargout}]=evaluate(varargin{:});
    case 'auxiliaries',[varargout{1:nargout}]=auxiliaries(varargin{:});
    case 'qt_bounds',[varargout{1:nargout}]=qt_bounds(varargin{:});
    case 'active_qt_update',[varargout{1:nargout}]=active_qt_update(varargin{:});
    case 'initialize',[varargout{1:nargout}]=initialize(varargin{:});
    case 'qt_loop',[varargout{1:nargout}]=qt_loop(varargin{:});
    case 'rate_gradient',[varargout{1:nargout}]=rate_gradient(varargin{:});
    case 'projector',[varargout{1:nargout}]=projector(varargin{:});
    case 'projector_square',[varargout{1:nargout}]=projector_square(varargin{:});
    case 'pair_moment',[varargout{1:nargout}]=pair_moment(varargin{:});
    case 'criterion_gradient',[varargout{1:nargout}]=criterion_gradient(varargin{:});
    case 'phase_rgd',[varargout{1:nargout}]=phase_rgd(varargin{:});
    case 'printed_soc_update',error('Printed Eq3-46 is not equivalent to full-rank QoS; use explicit corrected_QT_erratum.');
    otherwise,error('Unknown statistical action');
end
end

function D=factor(Q)
[E,L]=eig((Q+Q')/2);v=real(diag(L));assert(min(v)>=-1e-10*max(1,max(abs(v))),'Non-PSD channel moment');D=diag(sqrt(max(v,0)))*E';
end

function [Q,Psi,mu,C]=moments(x,phi,noRis)
if nargin<3,noRis=false;end
[U,N]=size(x.direct_mean);M=size(x.matrix_mean,1);phi=phi(:).';assert(max(abs(abs(phi)-1))<1e-10);
mu=x.direct_mean;Q=complex(zeros(U,N,N));C=Q;
for u=1:U
    cov=diag(x.direct_variance(u,:));
    if ~noRis
        mu(u,:)=mu(u,:)+phi*(x.ground_mean(u,:).'.*x.matrix_mean);
        cov=cov+x.matrix_mean'*diag(x.ground_variance(u,:))*x.matrix_mean;
        cov=cov+diag(sum(x.matrix_variance.*(abs(x.ground_mean(u,:)).^2+x.ground_variance(u,:)).',1));
    end
    C(u,:,:)=cov;Q(u,:,:)=cov+mu(u,:)'*mu(u,:);
end
K=size(x.nhu_mean,1);Psi=complex(zeros(K,N,N));
for k=1:K,Psi(k,:,:)=diag(x.nhu_variance(k,:))+x.nhu_mean(k,:)'*x.nhu_mean(k,:);end
end

function out=evaluate(Q,Psi,W,noise)
allQ=cat(1,Q,Psi);J=size(W,2);received=zeros(J,J);N=size(W,1);
for u=1:J,q=reshape(allQ(u,:,:),N,N);received(u,:)=real(sum(conj(W).*(q*W),1));end
desired=diag(received);den=sum(received,2)-desired+noise;assert(min(den)>0);
snr=desired./den;out=struct('sinr',snr,'hu_sum_rate',sum(log2(1+snr(1:size(Q,1)))), ...
    'total_power',sum(abs(W(:)).^2),'metric','source_ratio_of_expected_powers_NOT_exact_ergodic_rate');
end

function [D,z,den]=auxiliaries(Q,Psi,W,noise)
allQ=cat(1,Q,Psi);J=size(W,2);N=size(W,1);D=cell(1,J);received=zeros(J,J);
for j=1:J,D{j}=factor(reshape(allQ(j,:,:),N,N));received(j,:)=sum(abs(D{j}*W).^2,1);end
den=sum(received,2)-diag(received)+noise;z=complex(zeros(J,N));
for j=1:J,z(j,:)=(D{j}*W(:,j)/den(j)).';end
end

function bounds=qt_bounds(D,z,W,noise)
J=size(W,2);bounds=zeros(J,1);
for j=1:J,other=setdiff(1:J,j);dw=D{j}*W(:,other);den=sum(abs(dw(:)).^2)+noise;bounds(j)=2*real(conj(z(j,:))*D{j}*W(:,j))-sum(abs(z(j,:)).^2)*den;end
end

function [W,info]=active_qt_update(Q,Psi,W0,noise,power,target)
[U,N,~]=size(Q);K=size(Psi,1);J=U+K;[D,z,~]=auxiliaries(Q,Psi,W0,noise);
cvx_begin quiet
    variable V(N,J) complex
    expression lower(J)
    for j=1:J
        other=setdiff(1:J,j);dz=D{j}*sqrt(power/noise);az=z(j,:)*sqrt(noise);
        dw=norm(az)*(dz*V(:,other));
        lower(j)=2*real(conj(az)*dz*V(:,j))-sum_square_abs(dw(:))-norm(az)^2;
    end
    maximize(sum(log(1+lower(1:U)))/log(2))
    subject to
    sum_square_abs(V(:))<=1;
    lower(U+1:J)>=target(:);
cvx_end
assert(contains(cvx_status,'Solved'),'Corrected statistical QT failed');W=V*sqrt(power);
before=evaluate(Q,Psi,W0,noise);after=evaluate(Q,Psi,W,noise);old=qt_bounds(D,z,W0,noise);new=qt_bounds(D,z,W,noise);
primal=max([0;after.total_power/power-1;target(:)-after.sinr(U+1:end);target(:)-new(U+1:end)]);
diagnostics=struct('solver','external_CVX','status',cvx_status,'reported_solver_tolerance',cvx_slvtol, ...
    'constraint_max_relative_violation',primal,'qt_bound_max_violation',max([0;new-after.sinr]));
info=struct('before',before,'after',after,'solver_status',cvx_status,'solver_diagnostics',diagnostics, ...
    'qt_tightness_error',max(abs(old-before.sinr)),'qt_bound_max_violation',diagnostics.qt_bound_max_violation, ...
    'qos_lower_bounds',new(U+1:end),'qos_auxiliaries_are_exact_vector_QT',true);
end

function W=initialize(Q,Psi,mu,nhuMu,noise,power,target)
[U,N]=size(mu);K=size(Psi,1);J=U+K;D=cell(1,K);for k=1:K,D{k}=factor(reshape(Psi(k,:,:),N,N))*sqrt(power/noise);end
cvx_begin quiet
    variable V(N,J) complex
    expression terms(U)
    for u=1:U,terms(u)=real(mu(u,:)*V(:,u));end
    maximize(sum(terms))
    subject to
    sum_square_abs(V(:))<=1;
    for k=1:K
        j=U+k;other=setdiff(1:J,j);des=nhuMu(k,:)*V(:,j)*sqrt(power/noise);dw=D{k}*V(:,other);
        imag(des)==0;norm([dw(:);1])<=real(des)/sqrt(target(k));
    end
cvx_end
assert(contains(cvx_status,'Solved'),'Statistical initializer failed');W=V*sqrt(power);e=evaluate(Q,Psi,W,noise);
assert(e.total_power<=power*(1+1e-5)&&min(e.sinr(U+1:end)-target(:))>=-1e-5,'Full-moment initialization failed');
end

function [W,h,stop,records]=qt_loop(Q,Psi,W,noise,power,target,s)
e=evaluate(Q,Psi,W,noise);h=e.hu_sum_rate;records={};
for it=1:s.qt_max_iterations
    [trial,info]=active_qt_update(Q,Psi,W,noise,power,target);value=info.after.hu_sum_rate;assert(value>=h(end)-1e-6);
    records{end+1}=info.solver_diagnostics;W=trial;h(end+1)=value; %#ok<AGROW>
    if (h(end)-h(end-1))/max(abs(h(end-1)),1e-12)<s.relative_tolerance,break;end
end
stop=strict_hotspot_termination('relative',h,s.qt_max_iterations,s.relative_tolerance);
end

function [value,g]=rate_gradient(x,phi,W,noise)
[Q,~,mu]=moments(x,phi);U=size(Q,1);N=size(W,1);J=size(W,2);received=zeros(U,J);
for u=1:U,q=reshape(Q(u,:,:),N,N);received(u,:)=real(sum(conj(W).*(q*W),1));end
total=sum(received,2)+noise;desired=diag(received(:,1:U));den=total-desired;value=sum(log2(total./den));projection=mu*W;theta=zeros(1,numel(phi));
for m=1:numel(phi)
    dm=1i*phi(m)*x.ground_mean(:,m).*x.matrix_mean(m,:);dr=2*real(conj(projection).*(dm*W));dt=sum(dr,2);dd=dt-diag(dr(:,1:U));theta(m)=sum(dt./total-dd./den)/log(2);
end
g=1i*phi(:).'.*theta;
end

function P=projector(m,v)
m=m(:);v=v(:);scale=sum(abs(m).^2+v);m=m/sqrt(scale);v=v/scale;
if max(v)==0,P=(m*m')/real(m'*m);return;end
P=integral(@(s)projector_integrand(s,m,v),0,1,'ArrayValued',true,'AbsTol',1e-11,'RelTol',1e-11);P=(P+P')/2;assert(abs(trace(P)-1)<1e-8);
end

function P=projector_integrand(s,m,v)
if s>=1,P=zeros(numel(m));return;end
t=s/(1-s);iv=1./(1+t*v);lap=exp(-sum(log1p(t*v))-t*sum(abs(m).^2.*iv));q=m.*iv;P=lap*(diag(v.*iv)+q*q')/(1-s)^2;
end

function B=projector_square(x)
K=size(x.nhu_mean,1);N=size(x.nhu_mean,2);P=cell(1,K);B=eye(N);
for k=1:K,P{k}=projector(conj(x.nhu_mean(k,:)),x.nhu_variance(k,:));B=B-P{k};end
for k=1:K,for j=1:K,if k~=j,B=B+P{k}*P{j};end,end,end
B=(B+B')/2;
end

function [value,change]=pair_moment(x,phi,u,v,dA)
A=x.matrix_mean.'.*phi(:).';B=A'*A+diag(sum(x.matrix_variance,2));mu=x.ground_mean(u,:).';mv=x.ground_mean(v,:).';vu=x.ground_variance(u,:).';vv=x.ground_variance(v,:).';du=x.direct_mean(u,:).';dv=x.direct_mean(v,:).';
bu=du+A*mu;bv=dv+A*mv;eu=x.direct_variance(u,:).'+x.matrix_variance.'*(abs(mu).^2+vu);ev=x.direct_variance(v,:).'+x.matrix_variance.'*(abs(mv).^2+vv);
ebu=abs(bu).^2+abs(A).^2*vu;ebv=abs(bv).^2+abs(A).^2*vv;b=du'*A+mu'*B;c=A'*dv+B*mv;t=du'*dv+du'*A*mv+mu'*A'*dv+mu'*B*mv;
value=abs(t)^2+sum(vv.'.*abs(b).^2)+sum(vu.*abs(c).^2)+sum(sum((vu*vv.').*abs(B).^2))+ebu.'*ev+ebv.'*eu+eu.'*ev;
if nargin<5,return;end
dB=dA'*A+A'*dA;db=du'*dA+mu'*dB;dc=dA'*dv+dB*mv;dt=du'*dA*mv+mu'*dA'*dv+mu'*dB*mv;
debu=2*real(conj(bu).*(dA*mu))+2*real(conj(A).*dA)*vu;debv=2*real(conj(bv).*(dA*mv))+2*real(conj(A).*dA)*vv;
change=2*real(conj(t)*dt+sum(vv.'.*conj(b).*db)+sum(vu.*conj(c).*dc)+sum(sum((vu*vv.').*conj(B).*dB)))+debu.'*ev+debv.'*eu;
end

function [value,g]=criterion_gradient(x,phi,P)
% Exact sparse-row/column derivatives, not a different phase objective.
[Q,~,means]=moments(x,phi);U=size(Q,1);N=size(Q,2);M=numel(phi);
A=x.matrix_mean.'.*phi(:).';T=A'*A;gv=x.matrix_variance;B=T+diag(sum(gv,2));f5=0;f6=0;theta=zeros(M,1);
for u=1:U
    f5=f5+real(trace(reshape(Q(u,:,:),N,N)*P));
    ru=x.ground_mean(u,:).';theta=theta+2*real(1i*ru.*(conj(means(u,:))*P.'*A).');
    for v=1:u-1
        du=x.direct_mean(u,:).';dv=x.direct_mean(v,:).';rv=x.ground_mean(v,:).';vu=x.ground_variance(u,:).';vv=x.ground_variance(v,:).';
        bu=du+A*ru;bv=dv+A*rv;eu=x.direct_variance(u,:).'+gv.'*(abs(ru).^2+vu);ev=x.direct_variance(v,:).'+gv.'*(abs(rv).^2+vv);
        ebu=abs(bu).^2+abs(A).^2*vu;ebv=abs(bv).^2+abs(A).^2*vv;
        b=du'*A+ru'*B;c=A'*dv+B*rv;t=du'*dv+du'*A*rv+ru'*A'*dv+ru'*B*rv;
        f6=f6+abs(t)^2+sum(vv.*abs(b.').^2)+sum(vu.*abs(c).^2)+sum(sum((vu*vv.').*abs(B).^2))+ebu.'*ev+ebv.'*eu+eu.'*ev;
        bt=du'*A+ru'*T;ct=A'*dv+T*rv;
        db=1i*diag(bt)-1i*conj(ru).*T;dc=1i*rv.*T.'-1i*diag(ct);dt=1i*(bt.'.*rv-conj(ru).*ct);
        dBsum=1i*vv.*sum(vu.*conj(B).*T,1).'-1i*vu.*sum(vv.'.*conj(B).*T,2);
        change=2*real(conj(t)*dt+db*(vv.*conj(b.'))+dc*(vu.*conj(c))+dBsum ...
            +1i*ru.*((conj(bu).*ev).'*A).'+1i*rv.*((conj(bv).*eu).'*A).');
        theta=theta-change;
    end
end
value=f5-f6;g=1i*phi(:).'.*theta.';
end

function [phi,h,stop]=phase_rgd(phi,fg,s)
phi=phi(:).';[value,g]=fg(phi);h=value;
for it=1:s.rgd_max_iterations
    norm2=sum(abs(g).^2);if sqrt(norm2)<=s.gradient_tolerance,break;end
    alpha=1/sqrt(norm2);accepted=false;
    for search=1:60
        trialphi=phi+alpha*g;trialphi=trialphi./abs(trialphi);[trial,newg]=fg(trialphi);
        if trial-value>=1e-4*alpha*norm2,accepted=true;break;end
        alpha=alpha/2;
    end
    assert(accepted,'Statistical original RGD Armijo failed');phi=trialphi;value=trial;g=newg;h(end+1)=value; %#ok<AGROW>
end
stop=strict_hotspot_termination('gradient',norm(g),numel(h)-1,s.rgd_max_iterations,s.gradient_tolerance);
end
