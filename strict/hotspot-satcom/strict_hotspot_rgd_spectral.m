function varargout=strict_hotspot_rgd_spectral(action,varargin)
% Original RGD direction/retraction/Armijo with unreported numerical controls.
% Exact algebraic objective increments avoid subtracting two large objectives.
switch action
    case 'phase',[varargout{1:nargout}]=phase(varargin{:});
    case 'rate_increment',varargout{1}=rate_increment(varargin{:});
    case 'criterion_increment',varargout{1}=criterion_increment(varargin{:});
    otherwise,error('Unknown original-RGD numerical control action');
end
end

function y=square_increment(x,dx)
y=2*real(conj(x).*dx)+abs(dx).^2;
end

function value=rate_increment(x,old,new,W,noise)
[Q,~,means]=strict_hotspot_statistical('moments',x,old);U=size(Q,1);N=size(W,1);J=size(W,2);received=zeros(U,J);
for u=1:U,q=reshape(Q(u,:,:),N,N);received(u,:)=real(sum(conj(W).*(q*W),1));end
delta=complex(zeros(U,N));
for u=1:U,delta(u,:)=(new-old)*(x.ground_mean(u,:).'.*x.matrix_mean);end
change=square_increment(means*W,delta*W);total=sum(received,2)+noise;desired=diag(received(:,1:U));
dt=sum(change,2);dd=dt-diag(change(:,1:U));
value=sum(log1p(dt./total)-log1p(dd./(total-desired)))/log(2);
end

function value=criterion_increment(x,old,new,P)
A=x.matrix_mean.'.*old(:).';dA=x.matrix_mean.'.*(new(:).'-old(:).');
B=A'*A+diag(sum(x.matrix_variance,2));dB=A'*dA+dA'*A+dA'*dA;gv=x.matrix_variance;value=0;
for u=1:size(x.ground_mean,1)
    du=x.direct_mean(u,:).';ru=x.ground_mean(u,:).';vu=x.ground_variance(u,:).';bu=du+A*ru;dbu=dA*ru;
    value=value+2*real(bu'*P.'*dbu)+real(dbu'*P.'*dbu);
    for v=1:u-1
        dv=x.direct_mean(v,:).';rv=x.ground_mean(v,:).';vv=x.ground_variance(v,:).';bv=dv+A*rv;dbv=dA*rv;
        eu=x.direct_variance(u,:).'+gv.'*(abs(ru).^2+vu);ev=x.direct_variance(v,:).'+gv.'*(abs(rv).^2+vv);
        b=du'*A+ru'*B;c=A'*dv+B*rv;t=du'*dv+du'*A*rv+ru'*A'*dv+ru'*B*rv;
        db=du'*dA+ru'*dB;dc=dA'*dv+dB*rv;dt=du'*dA*rv+ru'*dA'*dv+ru'*dB*rv;
        debu=square_increment(bu,dbu)+square_increment(A,dA)*vu;
        debv=square_increment(bv,dbv)+square_increment(A,dA)*vv;
        value=value-square_increment(t,dt)-sum(vv.'.*square_increment(b,db))-sum(vu.*square_increment(c,dc)) ...
            -sum(sum((vu*vv.').*square_increment(B,dB)))-debu.'*ev-debv.'*eu;
    end
end
end

function [phi,h,stop]=phase(phi,x,mode,param,noise,s)
if strcmp(mode,'criterion')
    fg=@(v)strict_hotspot_statistical('criterion_gradient',x,v,param);
    increment=@(a,b)criterion_increment(x,a,b,param);
elseif strcmp(mode,'rate')
    fg=@(v)strict_hotspot_statistical('rate_gradient',x,v,param,noise);
    increment=@(a,b)rate_increment(x,a,b,param,noise);
else,error('No exact original objective-increment contract');end
phi=phi(:).';[value,g]=fg(phi);h=value;seed=1/max(norm(g),realmin);backtracks=0;
for it=1:s.rgd_max_iterations
    norm2=sum(abs(g).^2);if sqrt(norm2)<=s.gradient_tolerance,break;end
    alpha=seed;accepted=false;
    for search=1:60
        trialphi=phi+alpha*g;trialphi=trialphi./abs(trialphi);delta=increment(phi,trialphi);
        if delta>=1e-4*alpha*norm2,accepted=true;break;end
        alpha=alpha/2;backtracks=backtracks+1;
    end
    assert(accepted,'Original RGD exact-increment Armijo exhausted; no stop or gate relaxed');
    [trial,newg]=fg(trialphi);step=angle(conj(phi).*trialphi);
    oldtheta=real(conj(1i*phi).*g);newtheta=real(conj(1i*trialphi).*newg);
    curvature=sum(step.*(oldtheta-newtheta));distance=sum(step.^2);
    if curvature>0&&distance>0
        yy=sum((oldtheta-newtheta).^2);if mod(it,2)==1,seed=curvature/yy;else,seed=distance/curvature;end
    else,seed=2*alpha;end
    seed=min(max(seed,1e-12),1e12);phi=trialphi;value=trial;g=newg;h(end+1)=value; %#ok<AGROW>
end
stop=strict_hotspot_termination('gradient',norm(g),numel(h)-1,s.rgd_max_iterations,s.gradient_tolerance);
stop.numerical_controls='original_RGD_direction_retraction_Armijo_with_alternating_BB1_BB2_positive_step_seeds_and_exact_polynomial_increment';
stop.total_backtracks=backtracks;stop.gradient_threshold_unchanged=true;
end
