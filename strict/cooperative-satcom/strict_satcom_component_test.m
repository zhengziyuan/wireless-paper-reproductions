function result=strict_satcom_component_test(outputPath)
% Same deterministic finite-Rician test inputs as Python, full paper counts.
J=3; U=2; N=16; M=25; K=1;
mu=complex(zeros(J,U,N)); C=complex(zeros(J,U,N,N)); Q=C; fourth=zeros(J,U);
gt=complex(zeros(J,K,N,N)); gaussianIdentity=0;
for j=1:J
    a=exp(1i*pi*(0:N-1).'*(0.12+0.07*(j-1))); gm=0.01*a;
    gt(j,1,:,:)=gm*gm'+0.0002*eye(N);
    for u=1:U
        n=(0:N-1).'; m=(0:M-1).';
        d=0.12*exp(1i*pi*n*(0.02+0.12*(u-1)+0.04*(j-1)));
        G=0.015*exp(1i*pi*n*(0.01+0.15*(u-1)-0.04*(j-1)))*exp(-1i*pi*m*(0.04+0.01*(j-1))).';
        r=0.2*exp(1i*pi*m*(0.08-0.07*(u-1))); phi=exp(1i*(0.2+0.01*m+0.1*(u-1)));
        q=strict_satcom_core('moments',d,0.005,G,0.0001,r,0.003,phi);
        mu(j,u,:)=q.mean; C(j,u,:,:)=q.covariance; Q(j,u,:,:)=q.second; fourth(j,u)=q.norm_fourth;
        g=strict_satcom_core('moments',d,0.005,G,0,r,0.003,phi);
        expected=real(trace(g.second))^2+real(trace(g.covariance*g.covariance))+2*real(g.mean'*g.covariance*g.mean);
        gaussianIdentity=max(gaussianIdentity,abs(expected-g.norm_fourth));
    end
end
p0=0.2*ones(J,U); offset=[1.1;1.2]; powerLimit=50*ones(J,1); interferenceLimit=0.4;
[s,b,p,l]=strict_satcom_core('statistical_mr_coefficients',mu,Q,gt);
[~,stat]=strict_satcom_core('mr_qt_update',p0,s,b,p,l,offset,powerLimit,interferenceLimit);
[s,b,p,l]=strict_satcom_core('tts_mr_coefficients',Q,fourth,gt);
[~,tts]=strict_satcom_core('mr_qt_update',p0,s,b,p,l,offset,powerLimit,interferenceLimit);
[~,ap]=strict_satcom_core('ap_qt_update',permute(mu,[1,3,2])*0.2,mu,C,gt,offset,powerLimit,interferenceLimit);
violation=0; records={stat,tts,ap}; tight=0;
for i=1:numel(records)
    x=records{i}; violation=max([violation,max(x.after.satellite_power-powerLimit),max(x.after.gt_interference-interferenceLimit)]);
    tight=max(tight,x.qt_tightness_error);
end
jensen=true;
for j=1:J, for u=1:U, jensen=jensen && fourth(j,u)>=real(trace(reshape(Q(j,u,:,:),N,N)))^2; end, end
checks=struct('qt_identity_pass',tight<1e-10,'qt_identity_error',tight, ...
    'physical_constraint_pass',violation<1e-5,'physical_constraint_violation',violation, ...
    'gaussian_limit_identity_pass',gaussianIdentity<1e-10,'gaussian_limit_identity_error',gaussianIdentity, ...
    'finite_cascade_fourth_jensen_pass',jensen,'ap_qt_lower_bound_pass',ap.surrogate_minimum_sinr<=min(ap.after.sinr)+1e-5);
metrics=struct('stat_mr_before_min',min(stat.before.sinr),'stat_mr_after_min',min(stat.after.sinr), ...
    'tts_mr_before_min',min(tts.before.sinr),'tts_mr_after_min',min(tts.after.sinr), ...
    'ap_before_min',min(ap.before.sinr),'ap_after_min',min(ap.after.sinr));
result=struct('paper_id','cooperative-satcom','scope','synthetic_full-dimensional_component_test_NOT_paper_reproduction', ...
    'dimensions',struct('J',J,'U',U,'N',N,'M',M,'K',K),'metrics',metrics,'checks',checks,'full_reproduction_pass',false);
if nargin>=1
    folder=fileparts(outputPath); if ~isempty(folder) && ~exist(folder,'dir'), mkdir(folder); end
    fid=fopen(outputPath,'w'); assert(fid>=0,'Cannot create output'); clean=onCleanup(@()fclose(fid));
    fprintf(fid,'%s\n',jsonencode(result));
end
end
