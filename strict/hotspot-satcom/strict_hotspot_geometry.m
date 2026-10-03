function f=strict_hotspot_geometry(config)
% Source-compliant declared10m HU geometry; all original finite-Rician terms.
% This declares numerical coordinates, not recovered historical author geometry.
% Seed the caller once; shared cross-language fixtures are used for parity tests.
p=config.reported; t=config.tuned_not_reported; N=p.N; J=p.J; U=p.U; K=p.K; M=p.M;
assert(N==16 && J==16 && U+K==J,'Original 16-feed/16-user count required');
lam=299792458/p.frequency_hz; noise=1.380649e-23*p.temperature_k*p.bandwidth_hz; H=p.leo_height_m;
centers=zeros(N,2); index=0;
for x=[-1.5,-0.5,0.5,1.5], for y=[-1.5,-0.5,0.5,1.5], index=index+1; centers(index,:)=[x,y]*t.feed_center_spacing_m; end, end
assert(U>=1&&U<=6&&U==round(U),'Original HU count1..6');
if U==1, huPos=zeros(1,2); else, angles=(0:U-1).'*2*pi/U; radius=t.hu_cluster_radius_m; huPos=[radius*cos(angles),radius*sin(angles)];
    distances=[];for a=1:U,for b=a+1:U,distances(end+1)=norm(huPos(a,:)-huPos(b,:));end,end %#ok<AGROW>
    assert(min(distances)>=10-1e-12&&max(distances)<=20+1e-12,'Every original HU pair distance must be10..20m');
end
% Stable tie order equals Python sorting by radius then original feed index.
[~,order]=sortrows([sqrt(sum(centers.^2,2)),(1:N).'],[1,2]); nhuPos=centers(order(end-K+1:end),:);
risPos=[p.ris_hu_distance_m,0]; gain=10^(p.satellite_gain_dbi/10); receive=10^(t.ground_receive_gain_dbi/10);
area=prod(p.subsurface_elements)*prod(p.element_size_m); risGain=4*pi*area/lam^2;
[dm,dv]=sat_moments(huPos,receive,centers,H,lam,noise,p.antenna_diameter_m,gain,p.kappa_satellite_db);
[nm,nv]=sat_moments(nhuPos,receive,centers,H,lam,noise,p.antenna_diameter_m,gain,p.kappa_satellite_db);
direct=dm+sqrt(dv).*cn([U,N]); nhu=nm+sqrt(nv).*cn([K,N]);
[gm,gv]=sat_moments(risPos,risGain,centers,H,lam,noise,p.antenna_diameter_m,gain,p.kappa_satellite_db);
mr=floor(sqrt(M)); while mod(M,mr)~=0, mr=mr-1; end
mc=M/mr; coords=zeros(M,2); index=0;
for a=0:mr-1, for b=0:mc-1, index=index+1; coords(index,:)=[a,b]*sqrt(area); end, end
coords=coords-mean(coords,1); Gmean=repmat(gm,M,1); Gvar=repmat(gv,M,1); G=Gmean+sqrt(Gvar).*cn([M,N]);
R=complex(zeros(U,M,N)); rm=complex(zeros(U,M)); rv=zeros(U,M); kg=10^(p.kappa_ground_db/10);
for u=1:U
    direction=huPos(u,:)-risPos; distance=norm(direction);
    % Original numerical paragraph fixes equal 400m path loss for all HUs;
    % retain their actual geometry only in the propagation phase.
    amplitude=lam/(4*pi*p.ris_hu_distance_m)*sqrt(risGain*receive);
    phase=exp(-2i*pi*(distance+coords*direction.'/distance)/lam);
    rm(u,:)=amplitude*sqrt(kg/(1+kg))*phase.'; rv(u,:)=amplitude^2/(1+kg);
    r=rm(u,:).'+sqrt(rv(u,:)).'.*cn([M,1]); R(u,:,:)=r.*G;
end
phi=exp(2i*pi*rand(1,M));
means=struct('direct_mean',dm,'direct_variance',dv,'matrix_mean',Gmean,'matrix_variance',Gvar, ...
    'ground_mean',rm,'ground_variance',rv,'nhu_mean',nm,'nhu_variance',nv);
f=struct('direct',direct,'cascade',R,'nhu',nhu,'phi0',phi,'noise',1,'power',p.power_w, ...
    'nhu_target',10^(p.nhu_sinr_db/10)*ones(K,1),'mean_inputs',means, ...
    'geometry',struct('hu_xy_m',huPos,'nhu_xy_m',nhuPos,'ris_xy_m',risPos,'common_ground_pathloss_distance_m',p.ris_hu_distance_m));
end

function [mu,variance]=sat_moments(pos,receiver,centers,H,lam,noise,diameter,gain,kappaDb)
P=size(pos,1); N=size(centers,1); distance=sqrt(H^2+sum(pos.^2,2)); amplitude=zeros(P,N);
for p=1:P
    theta=atan(sqrt(sum((centers-pos(p,:)).^2,2))/H); nu=pi*diameter/lam*sin(theta);
    pattern=ones(N,1); mask=abs(nu)>1e-8; x=nu(mask);
    pattern(mask)=(besselj(1,x)./(2*x)+36*besselj(3,x)./x.^3).^2;
    amplitude(p,:)=sqrt(pattern*gain*receiver).'*lam/(4*pi*distance(p))/sqrt(noise);
end
k=10^(kappaDb/10); mu=amplitude*sqrt(k/(1+k)).*exp(-2i*pi*distance/lam); variance=amplitude.^2/(1+k);
end
function x=cn(shape)
x=(randn(shape)+1i*randn(shape))/sqrt(2);
end
