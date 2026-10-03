function result=strict_hotspot_component_test(inputPath,outputPath)
% Full N=16/U=6/K=10/M=25 synthetic mathematical test, not paper curves.
f=load(inputPath); phi=f.phi0(:).'; target=f.nhu_target(:);
hu=strict_hotspot_core('effective',f.direct,f.cascade,phi);
[W,active,a]=strict_hotspot_core('active_qt_update',hu,f.nhu,f.W0,f.noise,f.power,target);
[rounded,sdr]=strict_hotspot_core('phase_sdr_update',f.direct,f.cascade,phi,W,a,f.noise,f.normal_draws);
after=strict_hotspot_core('evaluate',strict_hotspot_core('effective',f.direct,f.cascade,rounded),f.nhu,W,f.noise);
[~,g]=strict_hotspot_core('criterion_gradient',f.direct,f.cascade,f.nhu,phi);
[U,M,N]=size(f.cascade);x=[conj(phi(:));1];V=x*x';lifted=zeros(U,1);unlifted=zeros(U,1);received=hu*W;
for u=1:U
    R=reshape(f.cascade(u,:,:),M,N);b=conj(a(u))*R*W(:,u);L=complex(zeros(M+1));L(1:M,M+1)=b/2;L(M+1,1:M)=b'/2;
    q=2*real(conj(a(u))*(f.direct(u,:)*W(:,u)))+2*real(trace(L*V))-abs(a(u))^2*f.noise;
    for j=1:size(W,2),if j~=u,c=[R*W(:,j);f.direct(u,:)*W(:,j)];q=q-abs(a(u))^2*real(trace((c*c')*V));end,end
    lifted(u)=q;unlifted(u)=2*real(conj(a(u))*received(u,u))-abs(a(u))^2*(sum(abs(received(u,:)).^2)-abs(received(u,u))^2+f.noise);
end
liftIdentity=abs(sum(log2(1+lifted))-sum(log2(1+unlifted)));
delta=1e-6; errors=zeros(1,numel(phi));
for m=1:numel(phi)
    plus=phi; minus=phi; plus(m)=plus(m)*exp(1i*delta); minus(m)=minus(m)*exp(-1i*delta);
    fp=strict_hotspot_core('criterion_gradient',f.direct,f.cascade,f.nhu,plus);
    fm=strict_hotspot_core('criterion_gradient',f.direct,f.cascade,f.nhu,minus);
    errors(m)=abs((fp-fm)/(2*delta)-real(conj(1i*phi(m))*g(m)));
end
[~,history]=strict_hotspot_core('phase_rgd',f.direct,f.cascade,f.nhu,phi,5,1e-8);
violation=max([0,after.total_power-f.power,max(target-after.sinr(size(hu,1)+1:end))]);
checks=struct('qt_identity_pass',active.qt_tightness_error<1e-8,'qt_identity_error',active.qt_tightness_error, ...
    'physical_constraint_pass',violation<1e-5,'physical_constraint_violation',violation, ...
    'sdr_psd_pass',sdr.smallest_sdp_eigenvalue>=-1e-5,'sdr_diagonal_pass',sdr.diagonal_error<1e-5, ...
    'rounding_unit_modulus_pass',sdr.unit_modulus_error<1e-12, ...
    'surrogate_bound_pass',sdr.rounded_surrogate<=sdr.sdr_upper_bound+1e-5, ...
    'phase_gradient_pass',max(errors)<1e-7,'phase_gradient_error',max(errors), ...
    'phase_gradient_tangent_pass',max(abs(real(conj(phi).*g)))<1e-10, ...
    'phase_lift_objective_identity_pass',liftIdentity<1e-10,'phase_lift_objective_identity_error',liftIdentity, ...
    'phase_criterion_monotone',all(diff(history)>=-1e-12));
metrics=struct('initial_hu_rate',active.before.hu_sum_rate,'qt_hu_rate',active.after.hu_sum_rate, ...
    'sdr_rounded_hu_rate',after.hu_sum_rate,'sdr_upper_bound',sdr.sdr_upper_bound,'rounded_surrogate',sdr.rounded_surrogate);
result=struct('paper_id','hotspot-satcom','scope','synthetic_full-dimensional_component_test_NOT_paper_reproduction', ...
    'phase_method','author_Algorithm_3-2_RGD_minimize_negative_F', ...
    'dimensions',struct('N',16,'U',6,'K',10,'M',25),'metrics',metrics,'checks',checks,'full_reproduction_pass',false);
if nargin>=2
    folder=fileparts(outputPath); if ~isempty(folder) && ~exist(folder,'dir'), mkdir(folder); end
    fid=fopen(outputPath,'w'); assert(fid>=0,'Cannot create output'); clean=onCleanup(@()fclose(fid));
    fprintf(fid,'%s\n',jsonencode(result));
end
end
