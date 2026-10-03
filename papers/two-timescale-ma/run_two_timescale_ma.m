function result = run_two_timescale_ma(outputPath)
%RUN_TWO_TIMESCALE_MA Independent reduced-size MRT AO/SCA, arXiv2410.05912v2.
% Base MATLAB only. The deterministic fixture is not an ergodic-rate sample.
f = jsondecode(fileread(fullfile(fileparts(mfilename('fullpath')),'fixture.json')));
t0 = f.initial_positions;
t = t0;
[v,~,~,~] = ttsma_statistical(t,f,0);
history = v;
gaps = [];
for sweep = 1:f.sweeps
    for a = 1:size(t,1)
        [v,g,L,~] = ttsma_statistical(t,f,a);
        if L <= 1e-14, continue; end
        candidate = ttsma_project(t(a,:)+g(a,:)/L,t,a,f);
        delta = candidate-t(a,:);
        lower = v+g(a,:)*delta'-0.5*L*(delta*delta');
        trial = t; trial(a,:) = candidate;
        actual = ttsma_statistical(trial,f,0);
        gaps(end+1) = actual-lower; %#ok<AGROW>
        assert(actual >= v-1e-10,'SCA update lowered Eq.13 objective');
        t = trial;
    end
    history(end+1) = ttsma_statistical(t,f,0); %#ok<AGROW>
end
[~,g,~,~] = ttsma_statistical(t0,f,0);
gn = zeros(size(t0));
for a = 1:size(t0,1)
    for d = 1:2
        p = t0; m = t0;
        p(a,d) = p(a,d)+1e-6; m(a,d) = m(a,d)-1e-6;
        gn(a,d) = (ttsma_statistical(p,f,0)-ttsma_statistical(m,f,0))/2e-6;
    end
end
dmin = inf;
for a = 1:size(t,1)
    for b = a+1:size(t,1), dmin = min(dmin,norm(t(a,:)-t(b,:))); end
end
[mrt0,zf0,p0,l0] = ttsma_instantaneous(t0,f);
[mrt1,zf1,p1,l1] = ttsma_instantaneous(t,f);
rayleigh = f; rayleigh.rician = zeros(size(f.rician));
rdiff = abs(ttsma_statistical(t0,rayleigh,0)-ttsma_statistical(t,rayleigh,0));
result.paper_id = 'two-timescale-ma';
result.metrics = struct('initial_positions',t0,'optimized_positions',t,...
    'mrt_statistical_initial',history(1),'mrt_statistical_optimized',history(end),...
    'zf_bound_initial',ttsma_zf_bound(t0,f),'zf_bound_at_mrt_positions',ttsma_zf_bound(t,f),...
    'mrt_fixture_initial',mrt0,'mrt_fixture_optimized',mrt1,...
    'zf_fixture_initial',zf0,'zf_fixture_at_mrt_positions',zf1);
result.checks = struct('gradient_max_error',max(abs(g(:)-gn(:))),...
    'gradient_pass',max(abs(g(:)-gn(:)))<1e-7,...
    'minimum_distance',dmin,'spacing_feasible',dmin>=f.minimum_distance-1e-10,...
    'box_feasible',all(t(:)>=f.region(1)-1e-10)&all(t(:)<=f.region(2)+1e-10),...
    'objective_monotone',min(diff(history))>=-1e-10,...
    'surrogate_lower_bound_min_gap',min(gaps),'power_max_error',max(p0,p1),...
    'zf_max_offdiagonal',max(l0,l1),'rayleigh_position_invariance_error',rdiff);
result.history.mrt_statistical_sum_rate = history;
assert(result.checks.gradient_max_error<1e-7);
assert(result.checks.spacing_feasible && result.checks.box_feasible && result.checks.objective_monotone);
assert(min(gaps)>-1e-9 && max(p0,p1)<1e-10 && max(l0,l1)<1e-10 && rdiff<1e-12);
if nargin>0 && ~isempty(outputPath)
    fid = fopen(outputPath,'w'); assert(fid>=0,'Cannot open output');
    cleaner = onCleanup(@()fclose(fid)); %#ok<NASGU>
    fprintf(fid,'%s\n',jsonencode(result));
end
end

function [value,grad,curv,rates] = ttsma_statistical(t,f,antenna)
N = size(t,1); U = numel(f.beta);
beta = f.beta(:); kap = f.rician(:); wave = 2*pi/f.wavelength;
num = beta.^2.*(N^2+N*(2*kap+1)./(kap+1).^2);
den = f.noise(:)*N*sum(beta)/f.power;
gd = zeros(U,N,2); ld = zeros(U,1);
for m = 1:U
    bound = zeros(2);
    for j = 1:U
        if j==m, continue; end
        v = f.directions(m,:)-f.directions(j,:);
        e = exp(1i*wave*(t*v')); total = sum(e);
        coeff = beta(m)*beta(j)*kap(m)*kap(j)/((kap(m)+1)*(kap(j)+1));
        den(m) = den(m)+coeff*abs(total)^2+beta(m)*beta(j)*N*(kap(m)+kap(j)+1)/((kap(m)+1)*(kap(j)+1));
        addition = 2*coeff*real(conj(total)*(1i*wave*e*v));
        for d=1:2, gd(m,:,d)=reshape(gd(m,:,d),1,N)+addition(:,d)'; end
        if antenna>0, bound = bound+coeff*abs(total-e(antenna))*abs(v'*v); end
    end
    ld(m) = 2*wave^2*max(eig(bound));
end
weight = num./(log(2)*den.*(den+num));
rates = log2(1+num./den); value = sum(rates);
grad = zeros(N,2);
for m=1:U, grad = grad-weight(m)*reshape(gd(m,:,:),N,2); end
curv = weight'*ld;
end

function z = ttsma_project(z,t,a,f)
lo=f.region(1); hi=f.region(2);
poly=[lo,lo;hi,lo;hi,hi;lo,hi]; normals=[]; bounds=[];
x=t(a,:);
for i=1:size(t,1)
    if i==a, continue; end
    d=x-t(i,:); normal=2*d;
    b=f.minimum_distance^2-d*d'+normal*x';
    normals(end+1,:)=normal; bounds(end+1,1)=b; %#ok<AGROW>
    poly=ttsma_clip(poly,normal,b);
    assert(~isempty(poly),'Empty SCA polygon');
end
if all(z>=lo)&&all(z<=hi)&&all(normals*z'>=bounds-1e-12), return; end
best=[]; distance=inf;
for i=1:size(poly,1)
    p=poly(i,:); q=poly(mod(i,size(poly,1))+1,:); v=q-p;
    alpha=max(0,min(1,(z-p)*v'/max(v*v',1e-30)));
    c=p+alpha*v; dc=(z-c)*(z-c)';
    if dc<distance, best=c; distance=dc; end
end
z=best;
end

function out = ttsma_clip(poly,normal,bound)
out=[];
for i=1:size(poly,1)
    p=poly(i,:); q=poly(mod(i,size(poly,1))+1,:);
    dp=normal*p'-bound; dq=normal*q'-bound;
    pin=dp>=-1e-12; qin=dq>=-1e-12;
    if pin, out(end+1,:)=p; end %#ok<AGROW>
    if pin~=qin, out(end+1,:)=p+(q-p)*dp/(dp-dq); end %#ok<AGROW>
end
end

function rate = ttsma_zf_bound(t,f)
kap=f.rician(:); beta=f.beta(:); U=numel(beta); N=size(t,1);
hbar=exp(1i*2*pi/f.wavelength*(t*f.directions'));
scale=sqrt(kap./(1+kap));
Sigma=diag(1./(1+kap))+(hbar'*hbar)/N.*(scale*scale');
iv=Sigma\eye(U); diagonal=real(diag(iv));
rate=sum(log2(1+f.power/U./f.noise(:).*beta*(N-U)./diagonal));
end

function [rm,rz,pe,le] = ttsma_instantaneous(t,f)
beta=f.beta(:)'; kap=f.rician(:)'; U=numel(beta);
hbar=exp(1i*2*pi/f.wavelength*(t*f.directions'));
samples=size(f.nlos_re,1); rm=zeros(1,samples); rz=rm; pe=0; le=0;
for s=1:samples
    sample=squeeze(f.nlos_re(s,:,:))+1i*squeeze(f.nlos_im(s,:,:));
    H=hbar.*sqrt(beta.*kap./(kap+1))+sample.*sqrt(beta./(kap+1));
    Wm=H*sqrt(f.power/sum(abs(H(:)).^2));
    V=H/(H'*H); Wz=V./sqrt(sum(abs(V).^2,1))*sqrt(f.power/U);
    gain=abs(H'*Wm).^2; desired=diag(gain);
    rm(s)=sum(log2(1+desired./(sum(gain,2)-desired+f.noise(:))));
    gain=abs(H'*Wz).^2; desired=diag(gain);
    rz(s)=sum(log2(1+desired./(sum(gain,2)-desired+f.noise(:))));
    pe=max([pe,abs(sum(abs(Wm(:)).^2)-f.power),abs(sum(abs(Wz(:)).^2)-f.power)]);
    off=H'*Wz; off=off-diag(diag(off)); le=max(le,max(abs(off(:))));
end
end
