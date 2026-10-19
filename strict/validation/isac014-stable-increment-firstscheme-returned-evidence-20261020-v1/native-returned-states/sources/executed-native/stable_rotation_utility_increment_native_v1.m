function [increment,detail]=stable_rotation_utility_increment_native_v1(W,theta,r0,r1,c,iota,p,fixedBase)
% Prepared arithmetic only: fixed-W/theta/iota original utility difference.
% p supplies the frozen native rotation,response,channel_base function handles.
% No optimizer, acceptance, threshold, floor, clipping, seed or stop lives here.
r0=r0(:);r1=r1(:);theta=theta(:);
if nargin<8 || isempty(fixedBase),fixedBase=p.channel_base(r0,c);end
[f0,df,boundary]=field_increment(theta,r0,r1,c,p,fixedBase);
K=numel(c.noise);Y0=f0(:,1:K)'*W;dY=df(:,1:K)'*W;
Z0=f0(:,K+1:end)'*W;dZ=df(:,K+1:end)'*W;
powers=abs(Y0).^2;dPowers=2*real(conj(Y0).*dY)+abs(dY).^2;
mask=true(size(powers));mask(sub2ind(size(mask),(1:K)',(1:K)'))=false;
S0=diag(powers(:,1:K));dS=diag(dPowers(:,1:K));
I0=c.noise(:)+sum(powers.*mask,2);dI=sum(dPowers.*mask,2);T0=S0+I0;
argument=(dS.*I0-S0.*dI)./(T0.*(I0+dI));
% MATLAB otherwise analytically continues log1p into complex values. Fail the
% real-domain arithmetic condition explicitly; do not floor/repair a trial.
assert(all(isfinite(I0+dI))&&all(I0+dI>0)&&isreal(argument)&&all(isfinite(argument))&&all(argument>-1),'Stable PGA real log domain is invalid; no repair.');
drate=sum(log1p(argument))/log(2);
p0=sum(abs(Z0).^2,2);dp=sum(2*real(conj(Z0).*dZ)+abs(dZ).^2,2);pd=c.desired_pattern(:);
dnmse=(dp'*(2*(p0-iota*pd)+dp))/(iota^2*(pd'*pd));
increment=drate-c.rho*dnmse;
assert(isreal(increment)&&isfinite(increment),'Stable PGA increment is nonfinite/nonreal; no repair.');
if nargout>1
    detail=struct('utility_increment',increment,'rate_increment',drate,'nmse_increment',dnmse,...
        'incumbent_field',f0,'field_increment',df,'minimum_trial_interference',min(I0+dI),...
        'minimum_rate_log1p_argument',min(argument),...
        'boundary',boundary);
end
end

function dQ=rotation_increment(r0,r1)
x=r0(1);y=r0(2);z=r0(3);cx=cos(x);sx=sin(x);cy=cos(y);sy=sin(y);cz=cos(z);sz=sin(z);
Rx=[1,0,0;0,cx,-sx;0,sx,cx];Ry=[cy,0,sy;0,1,0;-sy,0,cy];Rz=[cz,-sz,0;sz,cz,0;0,0,1];
half=(r1-r0)/2;middle=r0+half;dc=-2*sin(middle).*sin(half);ds=2*cos(middle).*sin(half);
dX=[0,0,0;0,dc(1),-ds(1);0,ds(1),dc(1)];
dY=[dc(2),0,ds(2);0,0,0;-ds(2),0,dc(2)];
dZ=[dc(3),-ds(3),0;ds(3),dc(3),0;0,0,0];
dQ=dX*Ry*Rz+(Rx+dX)*dY*Rz+(Rx+dX)*(Ry+dY)*dZ;
end

function [a0,da,stats]=response_increment(coords,center,u,r0,r1,c,p)
u=u(:);[a0,~]=p.response(coords,center,u,r0,c);[Q0,~]=p.rotation(r0);dQ=rotation_increment(r0,r1);
cosine0=Q0(:,3)'*u;dcosine=dQ(:,3)'*u;cosine1=cosine0+dcosine;
[Q1,~]=p.rotation(r1);cosine1Original=Q1(:,3)'*u;
fallback=cosine0<=0 || cosine1Original<=0 || cosine1<=0;
stats=[min(abs([cosine0,cosine1Original,cosine1])),double(fallback),double((cosine1Original>0)~=(cosine1>0))];
if fallback,[a1,~]=p.response(coords,center,u,r1,c);da=a1-a0;return;end
exponent=c.directivity_exponent/2;amp0=sqrt(c.maximum_gain)*cosine0^exponent;
damp=amp0*expm1(exponent*log1p(dcosine/cosine0));wave=2*pi/c.wavelength;
phase0=wave*((coords*Q0'+center(:)')*u);dphase=wave*(coords*dQ'*u);
phaseIncrement=-2*sin(dphase/2).^2+1i*sin(dphase);
da=exp(1i*phase0).*(damp+(amp0+damp).*phaseIncrement);
end

function [f0,df,stats]=field_increment(theta,r0,r1,c,p,base)
h=base{1};g=base{2};B=base{5};dh=zeros(size(h),'like',h);dg=zeros(size(g),'like',g);dB=zeros(size(B),'like',B);
cb=c.bs_coordinates;cr=c.ris_coordinates;ob=c.bs_center;orr=c.ris_center;K=numel(c.noise);ledger=zeros(0,3);
for u=1:K
    for path=1:size(c.bu_directions,2)
        [~,da,s]=response_increment(cb,ob,reshape(c.bu_directions(u,path,:),3,1),r0(1:3),r1(1:3),c,p);ledger(end+1,:)=s; %#ok<AGROW>
        dh(:,u)=dh(:,u)+(c.bu_gain_re(u,path)+1i*c.bu_gain_im(u,path))*da;
        [~,da,s]=response_increment(cr,orr,reshape(c.ru_directions(u,path,:),3,1),r0(4:6),r1(4:6),c,p);ledger(end+1,:)=s; %#ok<AGROW>
        dg(:,u)=dg(:,u)+(c.ru_gain_re(u,path)+1i*c.ru_gain_im(u,path))*da;
    end
end
for v=1:size(c.bt_directions,1)
    [~,dh(:,K+v),s]=response_increment(cb,ob,c.bt_directions(v,:),r0(1:3),r1(1:3),c,p);ledger(end+1,:)=s; %#ok<AGROW>
    [~,dg(:,K+v),s]=response_increment(cr,orr,c.rt_directions(v,:),r0(4:6),r1(4:6),c,p);ledger(end+1,:)=s; %#ok<AGROW>
end
for path=1:size(c.br_directions,1)
    [ab,dab,s]=response_increment(cb,ob,c.br_directions(path,:),r0(1:3),r1(1:3),c,p);ledger(end+1,:)=s; %#ok<AGROW>
    [ar,dar,s]=response_increment(cr,orr,c.rb_directions(path,:),r0(4:6),r1(4:6),c,p);ledger(end+1,:)=s; %#ok<AGROW>
    gain=c.br_gain_re(path)+1i*c.br_gain_im(path);dB=dB+gain*(dab*ar'+(ab+dab)*dar');
end
f0=h+B*(theta.*g);df=dh+dB*(theta.*g)+(B+dB)*(theta.*dg);
stats=struct('minimum_absolute_original_or_incremental_cosine',min(ledger(:,1)),...
    'literal_response_fallback_cases',sum(ledger(:,2)),'incremental_original_sign_disagreements',sum(ledger(:,3)),...
    'actual_response_calls',size(ledger,1));
end
