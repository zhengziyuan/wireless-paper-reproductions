function varargout = strict_satcom_core(action,varargin)
% Finite-Rician moment/QT blocks. Never a gated full-paper reproduction.
switch action
    case 'moments', [varargout{1:nargout}]=moments(varargin{:});
    case 'statistical_mr_coefficients', [varargout{1:nargout}]=statistical_mr_coefficients(varargin{:});
    case 'tts_mr_coefficients', [varargout{1:nargout}]=tts_mr_coefficients(varargin{:});
    case 'mr_evaluate', [varargout{1:nargout}]=mr_evaluate(varargin{:});
    case 'mr_qt_update', [varargout{1:nargout}]=mr_qt_update(varargin{:});
    case 'ap_evaluate', [varargout{1:nargout}]=ap_evaluate(varargin{:});
    case 'ap_qt_update', [varargout{1:nargout}]=ap_qt_update(varargin{:});
    otherwise, error('Unknown strict component action');
end
end

function out=moments(d,dvar,G,Gvar,r,rvar,phi)
d=d(:); r=r(:); phi=phi(:); [N,M]=size(G);
assert(numel(d)==N && numel(r)==M && numel(phi)==M,'Inconsistent channel dimensions');
assert(max(abs(abs(phi)-1))<=1e-10,'Unit-modulus phase required');
assert(min([dvar,Gvar,rvar])>=0,'Negative NLoS variance');
A=G.*phi.'; mu=d+A*r; Cb=rvar*(A*A');
er2=real(r'*r)+M*rvar; eb2=real(mu'*mu)+real(trace(Cb));
C=Cb+(dvar+Gvar*er2)*eye(N); Q=C+mu*mu';
eb4=eb2^2+real(trace(Cb*Cb))+2*real(mu'*Cb*mu);
er4=er2^2+M*rvar^2+2*rvar*real(r'*r);
er2b2=er2*eb2+rvar^2*sum(abs(A(:)).^2)+2*rvar*real(r'*A'*mu);
evb2=dvar*eb2+Gvar*er2b2;
ev2=dvar^2+2*dvar*Gvar*er2+Gvar^2*er4;
fourth=eb4+2*(N+1)*evb2+N*(N+1)*ev2;
out=struct('mean',mu,'covariance',C,'second',Q,'norm_fourth',fourth);
end

function [signal,cross,power,leak]=statistical_mr_coefficients(mu,Q,Qgt)
[J,U,N]=size(mu); K=size(Qgt,2); signal=zeros(J,U); cross=zeros(J,U,U); power=zeros(J,U); leak=zeros(J,U,K);
for j=1:J
    for u=1:U
        m=reshape(mu(j,u,:),N,1); power(j,u)=real(m'*m); signal(j,u)=power(j,u)^2;
        for i=1:U
            mi=reshape(mu(j,i,:),N,1); cross(j,u,i)=real(mi'*reshape(Q(j,u,:,:),N,N)*mi);
        end
        for k=1:K, leak(j,u,k)=real(m'*reshape(Qgt(j,k,:,:),N,N)*m); end
    end
end
end

function [signal,cross,power,leak]=tts_mr_coefficients(Q,fourth,Qgt)
[J,U,N,~]=size(Q); K=size(Qgt,2); signal=zeros(J,U); cross=zeros(J,U,U); power=zeros(J,U); leak=zeros(J,U,K);
for j=1:J
    for u=1:U
        Qu=reshape(Q(j,u,:,:),N,N); power(j,u)=real(trace(Qu)); signal(j,u)=power(j,u)^2;
        for i=1:U
            if i==u, cross(j,u,i)=fourth(j,u); else, cross(j,u,i)=real(trace(Qu*reshape(Q(j,i,:,:),N,N))); end
        end
        for k=1:K, leak(j,u,k)=real(trace(reshape(Qgt(j,k,:,:),N,N)*Qu)); end
    end
end
end

function out=mr_evaluate(p,signal,cross,power,leak,offset)
[J,U]=size(p); numerator=sum(p.*signal,1).'; denominator=offset(:);
for u=1:U, denominator(u)=denominator(u)+sum(sum(p.*reshape(cross(:,u,:),J,U)))-numerator(u); end
assert(min(denominator)>0,'Nonpositive MR denominator');
K=size(leak,3); interference=zeros(K,1);
for k=1:K, interference(k)=sum(sum(p.*leak(:,:,k))); end
out=struct('sinr',numerator./denominator,'denominator',denominator, ...
    'satellite_power',sum(p.*power,2),'gt_interference',interference);
end

function [pout,info]=mr_qt_update(p0,signal,cross,power,leak,offset,powerLimit,interferenceLimit)
assert(exist('cvx_begin','file')==2,'Install and configure external CVX before strict solver tests');
[J,U]=size(p0); before=mr_evaluate(p0,signal,cross,power,leak,offset);
y=sqrt(max(p0.*signal,0))./before.denominator.';
B=cross;
for u=1:U
    B(:,u,u)=B(:,u,u)-signal(:,u);
end
assert(min(B(:))>=-1e-9,'Desired/cross coefficient inconsistency'); B=max(B,0);
scale=powerLimit(:)./max(power,1e-300);
for k=1:size(leak,3), scale=min(scale,interferenceLimit(k)./max(leak(:,:,k),1e-300)); end
objectiveScale=max(1e-6,max(sum(scale.*signal,1).'./offset(:)));
cvx_begin quiet
    variable scaledPower(J,U) nonnegative
    expression p(J,U)
    p=scale.*scaledPower;
    variable minSinr
    maximize(minSinr)
    subject to
    for u=1:U
        denom=offset(u)+sum(sum(reshape(B(:,u,:),J,U).*p));
        minSinr <= (sum(2*y(:,u).*sqrt(signal(:,u)).*sqrt(p(:,u)))-sum(y(:,u).^2)*denom)/objectiveScale;
    end
    for j=1:J, sum((power(j,:)/powerLimit(j)).*p(j,:))<=1; end
    for k=1:size(leak,3), sum(sum((leak(:,:,k)/interferenceLimit(k)).*p))<=1; end
cvx_end
assert(contains(cvx_status,'Solved'),'MR QT solver failed: %s',cvx_status);
pout=max(scale.*scaledPower,0); after=mr_evaluate(pout,signal,cross,power,leak,offset);
qt=sum(2*y.*sqrt(p0.*signal),1).'-sum(y.^2,1).'.*before.denominator;
newqt=sum(2*y.*sqrt(pout.*signal),1).'-sum(y.^2,1).'.*after.denominator;
primal=max([0;-scaledPower(:);minSinr-newqt/objectiveScale;after.satellite_power./powerLimit(:)-1;after.gt_interference./interferenceLimit(:)-1]);
diagnostics=struct('solver','external_CVX','status',cvx_status,'reported_solver_tolerance',cvx_slvtol,'constraint_max_relative_violation',primal);
info=struct('solver_status',cvx_status,'surrogate_minimum_sinr',minSinr*objectiveScale, ...
    'solver_diagnostics',diagnostics,'qt_bound_max_violation',max(0,minSinr*objectiveScale-min(after.sinr)), ...
    'qt_tightness_error',max(abs(qt-before.sinr)),'before',before,'after',after);
end

function out=ap_evaluate(W,mu,C,Qgt,offset)
[J,N,U]=size(W); numerator=zeros(U,1); denominator=offset(:);
for u=1:U
    for j=1:J
        m=reshape(mu(j,u,:),N,1); numerator(u)=numerator(u)+abs(m'*reshape(W(j,:,u),N,1))^2;
        for i=1:U
            Q=reshape(C(j,u,:,:),N,N); if i~=u, Q=Q+m*m'; end
            w=reshape(W(j,:,i),N,1); denominator(u)=denominator(u)+real(w'*Q*w);
        end
    end
end
power=zeros(J,1); for j=1:J, block=reshape(W(j,:,:),N,U); power(j)=sum(abs(block(:)).^2); end
interference=zeros(size(Qgt,2),1);
for k=1:numel(interference)
    for j=1:J
        for i=1:U
            w=reshape(W(j,:,i),N,1); interference(k)=interference(k)+real(w'*reshape(Qgt(j,k,:,:),N,N)*w);
        end
    end
end
out=struct('sinr',numerator./denominator,'denominator',denominator,'satellite_power',power,'gt_interference',interference);
end

function [out,info]=ap_qt_update(W0,mu,C,Qgt,offset,powerLimit,interferenceLimit)
assert(exist('cvx_begin','file')==2,'External CVX setup required');
[J,N,U]=size(W0); before=ap_evaluate(W0,mu,C,Qgt,offset); z=complex(zeros(J,U));
for j=1:J
    for u=1:U, z(j,u)=reshape(mu(j,u,:),N,1)'*reshape(W0(j,:,u),N,1)/before.denominator(u); end
end
cvx_begin quiet
    variable W(N,U,J) complex
    variable minSinr
    maximize(minSinr)
    subject to
    for u=1:U
        linear=0; denom=offset(u);
        for j=1:J
            m=reshape(mu(j,u,:),N,1); linear=linear+2*real(conj(z(j,u))*(m'*W(:,u,j)));
            for i=1:U
                Q=reshape(C(j,u,:,:),N,N); if i~=u, Q=Q+m*m'; end
                denom=denom+quad_form(W(:,i,j),Q);
            end
        end
        minSinr<=linear-sum(abs(z(:,u)).^2)*denom;
    end
    for j=1:J, sum_square_abs(reshape(W(:,:,j),[],1))<=powerLimit(j); end
    for k=1:size(Qgt,2)
        leakage=0;
        for j=1:J
            for i=1:U, leakage=leakage+quad_form(W(:,i,j),reshape(Qgt(j,k,:,:),N,N)); end
        end
        leakage<=interferenceLimit(k);
    end
cvx_end
assert(contains(cvx_status,'Solved'),'AP QT solver failed: %s',cvx_status);
out=permute(W,[3,1,2]); after=ap_evaluate(out,mu,C,Qgt,offset); signal=complex(zeros(J,U));
for j=1:J
    for u=1:U, signal(j,u)=reshape(mu(j,u,:),N,1)'*reshape(W0(j,:,u),N,1); end
end
qt=sum(2*real(conj(z).*signal),1).'-sum(abs(z).^2,1).'.*before.denominator;
newsignal=complex(zeros(J,U));
for j=1:J,for u=1:U,newsignal(j,u)=reshape(mu(j,u,:),N,1)'*reshape(out(j,:,u),N,1);end,end
newqt=sum(2*real(conj(z).*newsignal),1).'-sum(abs(z).^2,1).'.*after.denominator;
primal=max([0;(minSinr-newqt)./max(1,abs(newqt));after.satellite_power./powerLimit(:)-1;after.gt_interference./interferenceLimit(:)-1]);
diagnostics=struct('solver','external_CVX','status',cvx_status,'reported_solver_tolerance',cvx_slvtol,'constraint_max_relative_violation',primal);
info=struct('solver_status',cvx_status,'surrogate_minimum_sinr',minSinr, ...
    'solver_diagnostics',diagnostics,'qt_bound_max_violation',max(0,minSinr-min(after.sinr)), ...
    'qt_tightness_error',max(abs(qt-before.sinr)),'before',before,'after',after);
end
