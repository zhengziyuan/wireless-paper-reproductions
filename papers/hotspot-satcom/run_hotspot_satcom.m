function result = run_hotspot_satcom(outputPath)
% RIS two-stage criterion core; journal equation labels not yet verified.
base=fileparts(mfilename('fullpath'));
if nargin<1, outputPath=fullfile(base,'outputs','hotspot-satcom-matlab.json'); end
f=jsondecode(fileread(fullfile(base,'fixture.json'))); model=build_model(f);
initial=exp(1i*f.initial_phase(:).'); [value0,analytic,~,~]=objective_gradient(model,initial);
numeric=zeros(size(analytic)); delta=f.gradient_step;
for m=1:f.subsurfaces
    plus=initial; minus=initial; plus(m)=plus(m)*exp(1i*delta); minus(m)=minus(m)*exp(-1i*delta);
    numeric(m)=(objective_gradient(model,plus)-objective_gradient(model,minus))/(2*delta);
end
[phi,trace]=optimize(f,model,initial); [final,~,f2,f3]=objective_gradient(model,phi);
initialZf=zf_qos_baseline(f,model,initial,false); optimized=zf_qos_baseline(f,model,phi,false);
no=zf_qos_baseline(f,model,phi,true); U=f.hotspot_users; manual=zeros(size(optimized.sinr));
for user=1:size(optimized.C,1)
    desired=0; interference=0;
    for beam=1:size(optimized.W,2)
        r=abs(optimized.C(user,:)*optimized.W(:,beam))^2;
        if beam==user, desired=desired+r; else, interference=interference+r; end
    end
    manual(user)=desired/(interference+f.noise);
end
identityError=max(abs(manual-optimized.sinr)); gradError=max(abs(analytic-numeric));
actualPower=sum(abs(optimized.W(:)).^2); powerViolation=max(0,actualPower-f.total_power);
qosViolation=max(0,max(f.nonhotspot_sinr_target(:)-optimized.sinr(U+1:end)));
result.paper_id='hotspot-satcom';
result.metrics=struct('ris_criterion_initial',value0,'ris_criterion_final',final, ...
    'semi_orthogonal_gain',f2,'pairwise_correlation_penalty',f3, ...
    'hotspot_sum_rate_zf',optimized.sum_rate,'initial_ris_hotspot_sum_rate_zf',initialZf.sum_rate, ...
    'no_ris_hotspot_sum_rate_zf',no.sum_rate,'user_sinr',optimized.sinr(:).', ...
    'beam_power',optimized.power(:).','total_transmit_power',actualPower);
result.checks=struct('gradient_pass',gradError<1e-7,'gradient_max_error',gradError, ...
    'identity_pass',identityError<1e-8,'identity_max_error',identityError, ...
    'constraint_pass',powerViolation<1e-8 && qosViolation<1e-8, ...
    'power_violation',powerViolation,'qos_violation',qosViolation, ...
    'unit_modulus_error',max(abs(abs(phi)-1)),'zf_residual',optimized.zf_residual, ...
    'zf_pass',optimized.zf_residual<1e-8,'criterion_monotone',all(diff(trace)>=-1e-12));
result.history=struct('ris_criterion',trace);
folder=fileparts(outputPath); if ~isempty(folder) && ~isfolder(folder), mkdir(folder); end
fid=fopen(outputPath,'w'); assert(fid>=0,'Cannot open output file'); cleanup=onCleanup(@()fclose(fid));
fprintf(fid,'%s\n',jsonencode(result));
assert(result.checks.gradient_pass && result.checks.identity_pass && result.checks.constraint_pass && result.checks.zf_pass,'Validation failed');
disp(result.checks);
end

function a=array_response(n,frequency)
a=exp(1i*pi*(0:n-1)*frequency);
end

function model=build_model(f)
N=f.antennas; M=f.subsurfaces; U=f.hotspot_users; K=f.nonhotspot_users;
model.hu=complex(zeros(U,N)); model.nhu=complex(zeros(K,N));
for u=1:U, model.hu(u,:)=f.hotspot_amplitude(u)*conj(array_response(N,f.hotspot_frequency(u))); end
for k=1:K, model.nhu(k,:)=f.nonhotspot_amplitude(k)*conj(array_response(N,f.nonhotspot_frequency(k))); end
G=f.satellite_ris_amplitude*array_response(M,f.ris_arrival_frequency).'*conj(array_response(N,f.satellite_ris_frequency));
model.R=complex(zeros(U,M,N)); model.G=G;
for u=1:U
    r=f.ris_user_amplitude(u)*array_response(M,f.ris_user_frequency(u));
    model.R(u,:,:)=conj(r(:)).*G;
end
% Keep the published semi-orthogonal sum, not a substituted true projector.
model.A=eye(N);
for k=1:K
    h=conj(model.nhu(k,:)).'; model.A=model.A-(h*h')/real(h'*h);
end
end

function c=effective(model,phi,noRis)
c=model.hu;
if ~noRis
    for u=1:size(c,1), c(u,:)=c(u,:)+phi*reshape(model.R(u,:,:),numel(phi),size(c,2)); end
end
end

function [value,g,f2,f3]=objective_gradient(model,phi)
c=effective(model,phi,false); transformed=c*model.A; f2=sum(abs(transformed(:)).^2); f3=0;
for u=1:size(c,1)
    for v=1:u-1, f3=f3+abs(c(u,:)*c(v,:)')^2; end
end
g=zeros(size(phi));
for m=1:numel(phi)
    dc=1i*phi(m)*reshape(model.R(:,m,:),size(c,1),size(c,2)); dt=dc*model.A;
    d2=2*real(sum(conj(transformed(:)).*dt(:))); d3=0;
    for u=1:size(c,1)
        for v=1:u-1
            inner=c(u,:)*c(v,:)'; derivative=dc(u,:)*c(v,:)'+c(u,:)*dc(v,:)';
            d3=d3+2*real(conj(inner)*derivative);
        end
    end
    g(m)=d2-d3;
end
value=f2-f3;
end

function [phi,history]=optimize(f,model,phi)
[value,g,~,~]=objective_gradient(model,phi); history=value;
for it=1:f.iterations
    if norm(g)<1e-10, break; end
    step=1; accepted=false;
    for search=1:35
        candidate=phi+step*1i*phi.*g; candidate=candidate./abs(candidate);
        [trial,gg,~,~]=objective_gradient(model,candidate);
        if trial>=value+1e-4*step*sum(g.^2), accepted=true; break; end
        step=step/2;
    end
    if ~accepted, break; end
    phi=candidate; value=trial; g=gg; history(end+1)=value; %#ok<AGROW>
end
end

function e=zf_qos_baseline(f,model,phi,noRis)
hu=effective(model,phi,noRis); C=[hu;model.nhu]; J=size(C,1);
V=C'*((C*C')\eye(J)); V=V./sqrt(sum(abs(V).^2,1)); gain=abs(diag(C*V)).^2;
U=f.hotspot_users; K=f.nonhotspot_users; power=zeros(U+K,1);
power(U+1:end)=f.nonhotspot_sinr_target(:)*f.noise./gain(U+1:end);
remaining=f.total_power-sum(power(U+1:end)); assert(remaining>=0,'Infeasible NHU QoS under ZF baseline');
lower=0; upper=remaining+max(f.noise./gain(1:U));
for it=1:60
    level=(lower+upper)/2; allocation=max(level-f.noise./gain(1:U),0);
    if sum(allocation)>remaining, upper=level; else, lower=level; end
end
power(1:U)=max(lower-f.noise./gain(1:U),0); W=V.*sqrt(power).'; received=abs(C*W).^2;
sinr=diag(received)./(sum(received,2)-diag(received)+f.noise);
residual=C*V-diag(diag(C*V));
e=struct('C',C,'W',W,'sinr',sinr,'power',power,'gain',gain, ...
    'sum_rate',sum(log2(1+sinr(1:U))),'zf_residual',max(abs(residual(:))));
end
