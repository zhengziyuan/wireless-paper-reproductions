function result=strict_hotspot_statistical_test(fixturePath,outputPath)
% Paired independent full-dimensional moment/QT/analytic-gradient verification.
f=load(fixturePath);x=f.inputs;phi=f.phi(:).';[Q,Psi]=strict_hotspot_statistical('moments',x,phi);
P=strict_hotspot_statistical('projector_square',x);P0=strict_hotspot_statistical('projector',conj(x.nhu_mean(1,:)),x.nhu_variance(1,:));
[D,z]=strict_hotspot_statistical('auxiliaries',Q,Psi,f.W,f.noise);bounds=strict_hotspot_statistical('qt_bounds',D,z,f.W,f.noise);
[criterion,g]=strict_hotspot_statistical('criterion_gradient',x,phi,P);[rate,rg]=strict_hotspot_statistical('rate_gradient',x,phi,f.W,f.noise);
pair=strict_hotspot_statistical('pair_moment',x,phi,1,2);e=strict_hotspot_statistical('evaluate',Q,Psi,f.W,f.noise);
errors=struct('Q',max(abs(Q(:)-f.Q(:))),'Psi',max(abs(Psi(:)-f.Psi(:))), ...
    'projector_square',max(abs(P(:)-f.projector_square(:))),'projector0',max(abs(P0(:)-f.projector0(:))), ...
    'QT_bounds',max(abs(bounds(:)-f.qt_bounds(:))),'criterion',abs(criterion-f.criterion), ...
    'criterion_gradient',max(abs(g(:)-f.criterion_gradient(:))),'rate',abs(rate-f.rate), ...
    'rate_gradient',max(abs(rg(:)-f.rate_gradient(:))),'pair_fourth',abs(pair-f.pair_moment01));
names=fieldnames(errors);parity=true;for k=1:numel(names),parity=parity&&errors.(names{k})<1e-8;end
delta=1e-5;graderr=0;rateerr=0;
for m=1:numel(phi)
    plus=phi;minus=phi;plus(m)=plus(m)*exp(1i*delta);minus(m)=minus(m)*exp(-1i*delta);
    fp=strict_hotspot_statistical('criterion_gradient',x,plus,P);fm=strict_hotspot_statistical('criterion_gradient',x,minus,P);graderr=max(graderr,abs((fp-fm)/(2*delta)-real(conj(1i*phi(m))*g(m))));
    fp=strict_hotspot_statistical('rate_gradient',x,plus,f.W,f.noise);fm=strict_hotspot_statistical('rate_gradient',x,minus,f.W,f.noise);rateerr=max(rateerr,abs((fp-fm)/(2*delta)-real(conj(1i*phi(m))*rg(m))));
end
checks=struct('Python_MATLAB_moment_gradient_parity_pass',parity,'vector_QT_tightness_pass',max(abs(bounds-e.sinr))<1e-12, ...
    'criterion_gradient_pass',graderr<1e-7,'criterion_gradient_error',graderr,'rate_gradient_pass',rateerr<1e-7,'rate_gradient_error',rateerr);
result=struct('paper_id','hotspot-satcom','scope','full_dimension_corrected_QT_erratum_component_test_NOT_full_paper_reproduction', ...
    'dimensions',struct('N',16,'U',6,'K',10,'M',25),'checks',checks,'parity_errors',errors,'full_reproduction_pass',false);
if nargin>=2,fid=fopen(outputPath,'w');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(result));end
assert(parity&&checks.vector_QT_tightness_pass&&checks.criterion_gradient_pass&&checks.rate_gradient_pass,'Statistical evidence check failed');
end
