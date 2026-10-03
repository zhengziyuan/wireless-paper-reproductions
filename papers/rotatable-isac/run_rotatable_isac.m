function result = run_rotatable_isac(outputPath)
%RUN_ROTATABLE_ISAC Independent Eqs2-24 model and disclosed AO ascent variant.
% Not the paper's QT/MM + RCG subsolvers. Requires only base MATLAB.
f=jsondecode(fileread(fullfile(fileparts(mfilename('fullpath')),'fixture.json')));
W=f.initial_w_re+1i*f.initial_w_im;
W=W/norm(W,'fro')*sqrt(f.power);
x0=[real(W(:));imag(W(:));f.initial_phases(:);f.initial_bs_angles(:);f.initial_ris_angles(:)];
[base,hb]=risac_optimize(x0,f,false);
[joint,hj]=risac_optimize(x0,f,true);
[metric,gradient]=risac_evaluate(x0,f,[],true);
numerical=zeros(size(x0));
for d=1:numel(x0)
    p=x0; m=x0; p(d)=p(d)+1e-6; m(d)=m(d)-1e-6;
    mp=risac_evaluate(p,f,metric.iota,false); mm=risac_evaluate(m,f,metric.iota,false);
    numerical(d)=(mp.utility-mm.utility)/2e-6;
end
[W,phase,angles]=risac_unpack(joint,f);
final=risac_evaluate(joint,f,[],false);
pd=f.desired_pattern(:); pattern=final.pattern;
identity=abs(final.nmse-(1-(pd'*pattern)^2/((pattern'*pattern)*(pd'*pd))));
reduced=abs(final.utility-(final.rate-f.rho*final.nmse));
names={'bu_directions','ru_directions','br_directions','rb_directions','bt_directions','rt_directions'};
unitError=0;
for i=1:numel(names)
    array=f.(names{i});
    if ndims(array)==3, array=reshape(array,[],3); end
    unitError=max(unitError,max(abs(sqrt(sum(array.^2,2))-1)));
end
result.paper_id='rotatable-isac';
result.metrics=struct('initial',risac_summary(x0,f),'fixed_arrays',risac_summary(base,f),'joint_rotations',risac_summary(joint,f));
result.checks=struct('gradient_max_error',max(abs(gradient-numerical)),...
    'gradient_pass',max(abs(gradient-numerical))<1e-7,...
    'power',sum(abs(W(:)).^2),'power_feasible',sum(abs(W(:)).^2)<=f.power+1e-10,...
    'unit_modulus_max_error',max(abs(abs(exp(1i*phase))-1)),...
    'rotation_feasible',all(abs(angles-x0(end-5:end))<=f.rotation_half_width+1e-10),...
    'joint_objective_monotone',min(diff(hj))>=-1e-10,'fixed_objective_monotone',min(diff(hb))>=-1e-10,...
    'nmse_identity_error',identity,'utility_identity_error',reduced,...
    'direction_unit_norm_max_error',unitError,'finite',all(isfinite(joint)));
result.history=struct('fixed_arrays_utility',hb,'joint_rotations_utility',hj);
assert(result.checks.gradient_pass && result.checks.power_feasible && result.checks.rotation_feasible);
assert(result.checks.joint_objective_monotone && result.checks.fixed_objective_monotone);
assert(identity<1e-12 && reduced<1e-12 && unitError<1e-12);
if nargin>0 && ~isempty(outputPath)
    fid=fopen(outputPath,'w'); assert(fid>=0,'Cannot open output');
    cleaner=onCleanup(@()fclose(fid)); %#ok<NASGU>
    fprintf(fid,'%s\n',jsonencode(result));
end
end

function [Q,D] = risac_rotation(r)
x=r(1); y=r(2); z=r(3);
cx=cos(x); sx=sin(x); cy=cos(y); sy=sin(y); cz=cos(z); sz=sin(z);
Rx=[1,0,0;0,cx,-sx;0,sx,cx]; Ry=[cy,0,sy;0,1,0;-sy,0,cy]; Rz=[cz,-sz,0;sz,cz,0;0,0,1];
Dx=[0,0,0;0,-sx,-cx;0,cx,-sx]; Dy=[-sy,0,cy;0,0,0;-cy,0,-sy]; Dz=[-sz,-cz,0;cz,-sz,0;0,0,0];
Q=Rx*Ry*Rz; D=cat(3,Dx*Ry*Rz,Rx*Dy*Rz,Rx*Ry*Dz);
end

function [a,da] = risac_response(coords,center,u,r,f)
[Q,D]=risac_rotation(r); cosine=Q(:,3)'*u(:);
positions=coords*Q'+center(:)'; wave=2*pi/f.wavelength;
steering=exp(1i*wave*(positions*u(:)));
if cosine<=0, a=zeros(size(coords,1),1); da=zeros(size(coords,1),3); return; end
b=f.directivity_exponent; amplitude=sqrt(f.maximum_gain)*cosine^(b/2);
a=amplitude*steering; da=zeros(size(coords,1),3);
for i=1:3
    dc=D(:,3,i)'*u(:);
    damp=sqrt(f.maximum_gain)*(b/2)*cosine^(b/2-1)*dc;
    dp=wave*(coords*D(:,:,i)'*u(:));
    da(:,i)=steering.*(damp+1i*amplitude*dp);
end
end

function [field,derivatives] = risac_channels(phases,angles,f)
cb=f.bs_coordinates; cr=f.ris_coordinates; ob=f.bs_center; or=f.ris_center;
M=size(cb,1); N=size(cr,1); U=numel(f.noise); A=size(f.bt_directions,1); links=U+A;
rB=angles(1:3); rR=angles(4:6);
h=zeros(M,links); g=zeros(N,links); dh=zeros(M,links,6); dg=zeros(N,links,6);
for k=1:U
    for p=1:size(f.bu_directions,2)
        u=squeeze(f.bu_directions(k,p,:));
        [a,da]=risac_response(cb,ob,u,rB,f);
        gain=f.bu_gain_re(k,p)+1i*f.bu_gain_im(k,p);
        h(:,k)=h(:,k)+gain*a; dh(:,k,1:3)=dh(:,k,1:3)+reshape(gain*da,M,1,3);
        u=squeeze(f.ru_directions(k,p,:));
        [a,da]=risac_response(cr,or,u,rR,f);
        gain=f.ru_gain_re(k,p)+1i*f.ru_gain_im(k,p);
        g(:,k)=g(:,k)+gain*a; dg(:,k,4:6)=dg(:,k,4:6)+reshape(gain*da,N,1,3);
    end
end
for a=1:A
    [h(:,U+a),da]=risac_response(cb,ob,f.bt_directions(a,:),rB,f);
    dh(:,U+a,1:3)=reshape(da,M,1,3);
    [g(:,U+a),da]=risac_response(cr,or,f.rt_directions(a,:),rR,f);
    dg(:,U+a,4:6)=reshape(da,N,1,3);
end
B=zeros(M,N); dB=zeros(M,N,6);
for p=1:size(f.br_directions,1)
    [ab,dab]=risac_response(cb,ob,f.br_directions(p,:),rB,f);
    [ar,dar]=risac_response(cr,or,f.rb_directions(p,:),rR,f);
    gain=f.br_gain_re(p)+1i*f.br_gain_im(p);
    B=B+gain*ab*ar';
    for d=1:3
        dB(:,:,d)=dB(:,:,d)+gain*dab(:,d)*ar';
        dB(:,:,3+d)=dB(:,:,3+d)+gain*ab*dar(:,d)';
    end
end
theta=exp(1i*phases(:)); field=h+B*(theta.*g);
derivatives=zeros(M,links,N+6);
for d=1:N, derivatives(:,:,d)=B(:,d)*(1i*theta(d)*g(d,:)); end
for d=1:6
    derivatives(:,:,N+d)=dh(:,:,d)+dB(:,:,d)*(theta.*g)+B*(theta.*dg(:,:,d));
end
end

function [W,phases,angles] = risac_unpack(x,f)
M=size(f.bs_coordinates,1); N=size(f.ris_coordinates,1); S=numel(f.noise)+M; count=M*S;
W=reshape(x(1:count)+1i*x(count+1:2*count),M,S);
phases=x(2*count+1:2*count+N); angles=x(end-5:end);
end

function [metric,gradient] = risac_evaluate(x,f,iota,needGradient)
[W,phase,angles]=risac_unpack(x,f); [field,df]=risac_channels(phase,angles,f);
U=numel(f.noise); fc=field(:,1:U); fs=field(:,U+1:end);
Y=fc'*W; Z=fs'*W; total=sum(abs(Y).^2,2)+f.noise(:);
signal=zeros(U,1);
for k=1:U, signal(k)=abs(Y(k,k))^2; end
interference=total-signal; sinr=signal./interference;
rate=sum(log2(total./interference)); pattern=sum(abs(Z).^2,2);
pd=f.desired_pattern(:); energy=pd'*pd;
if isempty(iota), iota=(pattern'*pattern)/(pd'*pattern); end
residual=pattern-iota*pd; nmse=(residual'*residual)/(iota^2*energy);
utility=rate-f.rho*nmse;
metric=struct('utility',utility,'rate',rate,'nmse',nmse,'iota',iota,'sinr',sinr,'pattern',pattern);
gradient=[];
if ~needGradient, return; end
coefficient=repmat(1./total-1./interference,1,size(W,2));
for k=1:U, coefficient(k,k)=coefficient(k,k)+1/interference(k); end
gW=2*fc*(coefficient.*Y)/log(2)-4*f.rho*fs*(residual.*Z)/(iota^2*energy);
gd=zeros(size(df,3),1);
for d=1:size(df,3)
    dY=df(:,1:U,d)'*W; dZ=df(:,U+1:end,d)'*W;
    dt=2*real(sum(conj(Y).*dY,2)); ds=zeros(U,1);
    for k=1:U, ds(k)=2*real(conj(Y(k,k))*dY(k,k)); end
    dr=sum(dt./total-(dt-ds)./interference)/log(2);
    dp=2*real(sum(conj(Z).*dZ,2));
    gd(d)=dr-f.rho*2*residual'*dp/(iota^2*energy);
end
gradient=[real(gW(:));imag(gW(:));gd];
end

function [x,history] = risac_optimize(x0,f,rotations)
x=x0; M=size(f.bs_coordinates,1); U=numel(f.noise); count=M*(U+M); N=size(f.ris_coordinates,1);
center=x0(end-5:end); blocks={1:2*count,2*count+1:2*count+N}; steps=[0.15,0.35];
if rotations, blocks{3}=2*count+N+1:numel(x); steps(3)=0.15; end
metric=risac_evaluate(x,f,[],false); history=metric.utility;
for outer=1:f.outer_iterations
    metric=risac_evaluate(x,f,[],false); iota=metric.iota;
    for b=1:numel(blocks)
        block=blocks{b};
        for inner=1:f.inner_steps
            [metric,g]=risac_evaluate(x,f,iota,true);
            direction=g(block)/max(1,norm(g(block))); alpha=steps(b);
            for ls=1:28
                trial=x; trial(block)=trial(block)+alpha*direction;
                if block(1)==1
                    normW=norm(trial(1:2*count));
                    if normW>sqrt(f.power), trial(1:2*count)=trial(1:2*count)*sqrt(f.power)/normW; end
                elseif block(1)==2*count+N+1
                    trial(end-5:end)=max(center-f.rotation_half_width,min(center+f.rotation_half_width,trial(end-5:end)));
                end
                delta=trial-x; slope=g'*delta;
                candidate=risac_evaluate(trial,f,iota,false);
                if slope>=-1e-15 && candidate.utility>=metric.utility+1e-4*slope-1e-13
                    x=trial; break;
                end
                alpha=alpha/2;
            end
        end
    end
    metric=risac_evaluate(x,f,[],false); history(end+1)=metric.utility; %#ok<AGROW>
end
end

function summary = risac_summary(x,f)
metric=risac_evaluate(x,f,[],false); [W,phase,angles]=risac_unpack(x,f);
summary=struct('utility',metric.utility,'sum_rate',metric.rate,'nmse',metric.nmse,...
    'iota',metric.iota,'sinr',metric.sinr','beampattern',metric.pattern',...
    'w_re',real(W),'w_im',imag(W),'phases',phase','angles',angles');
end
