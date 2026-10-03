function result = run_cooperative_satcom(outputPath)
% Independent deterministic-LoS MR core, not the full published experiments.
base = fileparts(mfilename('fullpath'));
if nargin < 1, outputPath = fullfile(base,'outputs','cooperative-satcom-matlab.json'); end
f = jsondecode(fileread(fullfile(base,'fixture.json')));
model = build_model(f); initial = exp(1i*f.initial_phase);
[p0,b0,~] = allocate(f,model,initial,false); baseline = evaluate(f,model,initial,p0,false);
[value,analytic] = utility_gradient(f,model,initial,p0);
numeric = zeros(size(analytic)); delta = f.gradient_step;
for u = 1:f.users
    for m = 1:f.subsurfaces
        plus=initial; minus=initial;
        plus(u,m)=plus(u,m)*exp(1i*delta); minus(u,m)=minus(u,m)*exp(-1i*delta);
        numeric(u,m)=(utility_gradient(f,model,plus,p0)-utility_gradient(f,model,minus,p0))/(2*delta);
    end
end
[phi,trace] = optimize(f,model,initial,p0);
[p,b,upper] = allocate(f,model,phi,false); optimized = evaluate(f,model,phi,p,false);
accepted = min(optimized.sinr) >= min(baseline.sinr);
if ~accepted
    phi=initial; p=p0; optimized=baseline; b=b0;
    [~,~,upper]=allocate(f,model,phi,false);
end
[pn,~,~]=allocate(f,model,initial,true); no=evaluate(f,model,initial,pn,true);
[h,z]=channels(model,phi,false); directSinr=zeros(f.users,1);
for u=1:f.users
    signal=0; interference=0;
    for j=1:f.satellites
        hu=reshape(h(j,u,:),[],1);
        for k=1:f.users
            w=sqrt(p(j,k))*reshape(h(j,k,:),[],1); received=abs(hu'*w)^2;
            if k==u, signal=signal+received; else, interference=interference+received; end
        end
    end
    directSinr(u)=signal/(interference+abs(z(u))^2+f.noise(u));
end
gradError=max(abs(analytic(:)-numeric(:))); identityError=max(abs(directSinr-optimized.sinr));
powerViolation=max(0,max(optimized.sat_power-f.satellite_power_limit(:)));
leakViolation=max(0,optimized.leakage-f.gt_interference_limit);
result.paper_id='cooperative-satcom';
result.metrics=struct('minimum_sinr',min(optimized.sinr),'initial_ris_minimum_sinr',min(baseline.sinr), ...
    'no_ris_minimum_sinr',min(no.sinr),'sinr',optimized.sinr(:).', ...
    'satellite_power',optimized.sat_power(:).','gt_interference',optimized.leakage, ...
    'power_allocation',p,'fixed_share_bisection_upper',upper, ...
    'initial_phase_utility',value,'phase_candidate_accepted',accepted);
result.checks=struct('gradient_pass',gradError<1e-7,'gradient_max_error',gradError, ...
    'identity_pass',identityError<1e-10,'identity_max_error',identityError, ...
    'constraint_pass',powerViolation<1e-9 && leakViolation<1e-9, ...
    'power_violation',powerViolation,'interference_violation',leakViolation, ...
    'unit_modulus_error',max(abs(abs(phi(:))-1)), ...
    'phase_objective_monotone',all(diff(trace)>=-1e-12), ...
    'bisection_gap',upper-min(optimized.sinr),'bisection_pass',abs(upper-min(optimized.sinr))<1e-8);
result.history=struct('phase_utility',trace,'power_bisection_lower',b);
folder=fileparts(outputPath); if ~isempty(folder) && ~isfolder(folder), mkdir(folder); end
fid=fopen(outputPath,'w'); assert(fid>=0,'Cannot open output file'); cleanup=onCleanup(@()fclose(fid));
fprintf(fid,'%s\n',jsonencode(result));
assert(result.checks.gradient_pass && result.checks.identity_pass && result.checks.constraint_pass && result.checks.bisection_pass,'Validation failed');
disp(result.checks);
end

function a=array_response(n,frequency)
a=exp(1i*pi*(0:n-1).'*frequency);
end

function model=build_model(f)
J=f.satellites; U=f.users; N=f.antennas; M=f.subsurfaces;
model.direct=complex(zeros(J,U,N)); model.cascade=complex(zeros(J,U,N,M));
hr=complex(zeros(U,M)); model.gt=complex(zeros(J,N));
for u=1:U, hr(u,:)=f.ris_user_amplitude(u)*array_response(M,f.ris_user_frequency(u)).'; end
for j=1:J
    for u=1:U
        model.direct(j,u,:)=f.direct_amplitude(j,u)*array_response(N,f.direct_frequency(j,u));
        G=f.satellite_ris_amplitude(j,u)*array_response(N,f.satellite_ris_frequency(j,u))*array_response(M,f.ris_arrival_frequency(j,u))';
        model.cascade(j,u,:,:)=G.*hr(u,:);
    end
    model.gt(j,:)=f.leo_gt_amplitude(j)*array_response(N,f.leo_gt_frequency(j)).';
end
model.geo_direct=f.geo_direct_real(:)+1i*f.geo_direct_imag(:);
model.geo_cascade=complex(zeros(U,M));
for u=1:U
    gr=f.geo_ris_amplitude(u)*array_response(M,f.geo_ris_frequency(u));
    model.geo_cascade(u,:)=conj(hr(u,:)).*conj(gr.');
end
end

function [h,z]=channels(model,phi,noRis)
h=model.direct; z=model.geo_direct;
if ~noRis
    for j=1:size(h,1)
        for u=1:size(h,2)
            h(j,u,:)=reshape(h(j,u,:),[],1)+reshape(model.cascade(j,u,:,:),size(h,3),[])*phi(u,:).';
        end
    end
    z=z+sum(model.geo_cascade.*phi,2);
end
end

function e=evaluate(f,model,phi,p,noRis)
[h,z]=channels(model,phi,noRis); J=f.satellites; U=f.users;
num=zeros(U,1); den=f.noise(:)+abs(z).^2; sat=zeros(J,1); leak=0;
for j=1:J
    for u=1:U
        hu=reshape(h(j,u,:),[],1); norm2=real(hu'*hu);
        num(u)=num(u)+p(j,u)*norm2^2; sat(j)=sat(j)+p(j,u)*norm2;
        gt=model.gt(j,:).'; leak=leak+p(j,u)*abs(gt'*hu)^2;
        for k=1:U
            if k~=u, den(u)=den(u)+p(j,k)*abs(hu'*reshape(h(j,k,:),[],1))^2; end
        end
    end
end
e=struct('sinr',num./den,'numerator',num,'denominator',den,'sat_power',sat,'leakage',leak);
end

function [p,trace,upper]=allocate(f,model,phi,noRis)
[h,z]=channels(model,phi,noRis); J=f.satellites; U=f.users; share=f.satellite_share(:);
signal=zeros(U,1); cross=zeros(U,U); power=zeros(J,U); leak=zeros(1,U);
for j=1:J
    for u=1:U
        hu=reshape(h(j,u,:),[],1); norm2=real(hu'*hu);
        signal(u)=signal(u)+share(j)*norm2^2; power(j,u)=share(j)*norm2;
        leak(u)=leak(u)+share(j)*abs(conj(model.gt(j,:))*hu)^2;
        for k=1:U
            if k~=u, cross(u,k)=cross(u,k)+share(j)*abs(hu'*reshape(h(j,k,:),[],1))^2; end
        end
    end
end
offset=f.noise(:)+abs(z).^2; limits=f.satellite_power_limit(:); bounds=zeros(U,1);
for u=1:U, bounds(u)=signal(u)*min(limits./power(:,u))/offset(u); end
upper=min(bounds); lower=0; best=zeros(U,1); trace=zeros(1,f.bisection_steps);
for it=1:f.bisection_steps
    target=(lower+upper)/2; A=eye(U)-target*(cross./signal);
    if rcond(A)>1e-14
        q=A\(target*offset./signal);
        ok=all(q>=0) && all(power*q<=limits) && leak*q<=f.gt_interference_limit && max(abs(A*q-target*offset./signal))<1e-7;
    else
        ok=false; q=zeros(U,1);
    end
    if ok, lower=target; best=q; else, upper=target; end
    trace(it)=lower;
end
p=share*best.';
end

function [value,g]=utility_gradient(f,model,phi,p)
e=evaluate(f,model,phi,p,false); [h,z]=channels(model,phi,false);
J=f.satellites; U=f.users; M=f.subsurfaces; mu=f.smoothing; rho=f.penalty_weight;
shift=min(e.sinr); weights=exp(-(e.sinr-shift)/mu);
softmin=shift-mu*log(sum(weights)); weights=weights/sum(weights);
residual=e.leakage-f.gt_interference_limit; value=softmin-rho*residual^2; g=zeros(U,M);
for v=1:U
    for m=1:M
        dh=complex(zeros(size(h)));
        for j=1:J, dh(j,v,:)=1i*phi(v,m)*reshape(model.cascade(j,v,:,m),[],1); end
        dz=complex(zeros(U,1)); dz(v)=1i*phi(v,m)*model.geo_cascade(v,m);
        ds=zeros(U,1); dd=2*real(conj(z).*dz); dl=0;
        for j=1:J
            gt=model.gt(j,:).';
            for u=1:U
                hu=reshape(h(j,u,:),[],1); dhu=reshape(dh(j,u,:),[],1); norm2=real(hu'*hu);
                ds(u)=ds(u)+4*p(j,u)*norm2*real(hu'*dhu);
                c=gt'*hu; dc=gt'*dhu; dl=dl+2*p(j,u)*real(conj(c)*dc);
                for k=1:U
                    if k~=u
                        hk=reshape(h(j,k,:),[],1); dhk=reshape(dh(j,k,:),[],1);
                        c=hu'*hk; dc=dhu'*hk+hu'*dhk;
                        dd(u)=dd(u)+2*p(j,k)*real(conj(c)*dc);
                    end
                end
            end
        end
        dr=(ds.*e.denominator-e.numerator.*dd)./e.denominator.^2;
        g(v,m)=weights.'*dr-2*rho*residual*dl;
    end
end
end

function [phi,history]=optimize(f,model,phi,p)
[value,g]=utility_gradient(f,model,phi,p); history=value;
for it=1:f.iterations
    if norm(g(:))<1e-10, break; end
    step=1; accepted=false;
    for search=1:35
        candidate=phi+step*1i*phi.*g; candidate=candidate./abs(candidate);
        [trial,gg]=utility_gradient(f,model,candidate,p);
        if trial>=value+1e-4*step*sum(g(:).^2), accepted=true; break; end
        step=step/2;
    end
    if ~accepted, break; end
    phi=candidate; value=trial; g=gg; history(end+1)=value; %#ok<AGROW>
end
end
