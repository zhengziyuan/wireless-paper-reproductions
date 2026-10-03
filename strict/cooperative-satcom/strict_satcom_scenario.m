function [data,powerLimit,interferenceLimit]=strict_satcom_scenario(config)
% Same configured physical finite-Rician model as Python. Unreported gains are
% tuning, not recovered original figure settings. See full_config.json.
p=config.reported; t=config.tuned_not_reported; J=p.J; U=p.U; N=p.N; K=p.K; M=p.M;
assert(N==prod(t.upa_shape) && J==numel(t.satellite_latitudes_deg),'No dimension fallback');
earth=t.earth_radius_m; lam=299792458/p.frequency_hz; noise=10^((p.noise_dbm-30)/10);
area=prod(p.subsurface_elements)*prod(p.element_size_m); risGain=4*pi*area/lam^2;
leoGain=10^(t.leo_element_gain_dbi/10); luGain=10^(t.lu_gain_dbi/10); geoGain=10^(t.geo_gain_dbi/10);
geo=location(0,p.geo_longitude_deg,earth+p.geo_height_m); gtpos=location(t.gt_latitude_deg,p.geo_longitude_deg,earth);
users=zeros(U,3); sats=zeros(J,3);
for u=1:U, users(u,:)=location(t.user_latitudes_deg(u),t.lu_longitudes_deg(u),earth); end
for j=1:J, sats(j,:)=location(t.satellite_latitudes_deg(j),p.geo_longitude_deg,earth+p.leo_height_m); end
data=struct('d_mean',complex(zeros(J,U,N)),'d_var',zeros(J,U), ...
    'G_mean',complex(zeros(J,U,N,M)),'G_var',zeros(J,U), ...
    'r_mean',complex(zeros(U,M)),'r_var',zeros(U,1),'gt_second',complex(zeros(J,K,N,N)), ...
    'geo_d_mean',complex(zeros(U,1)),'geo_d_var',zeros(U,1), ...
    'geo_G_mean',complex(zeros(U,M)),'geo_G_var',zeros(U,1));
mr=floor(sqrt(M)); while mod(M,mr)~=0, mr=mr-1; end
risShape=[mr,M/mr]; risSpacing=sqrt(area)/lam;
for u=1:U
    user=users(u,:); [east,north]=axes_vectors(t.user_latitudes_deg(u),t.lu_longitudes_deg(u)); ris=user+p.ris_lu_distance_m*east;
    rsteer=upa(user-ris,east,north,risShape,risSpacing);
    mur=(lam/(4*pi*norm(user-ris)))^2*risGain*luGain;
    [rm,rv]=factor(mur,p.kappa_ground_db,rsteer); data.r_mean(u,:)=rm.'; data.r_var(u)=rv;
    for j=1:J
        sat=sats(j,:); [se,sn]=axes_vectors(t.satellite_latitudes_deg(j),p.geo_longitude_deg);
        steer=upa(user-sat,se,sn,t.upa_shape,t.antenna_spacing_wavelengths);
        mul=(lam/(4*pi*norm(user-sat)))^2*leoGain*luGain/noise;
        [dm,dv]=factor(mul,p.kappa_leo_db,steer); data.d_mean(j,u,:)=dm; data.d_var(j,u)=dv;
        sr=upa(ris-sat,se,sn,t.upa_shape,t.antenna_spacing_wavelengths); rs=upa(sat-ris,east,north,risShape,risSpacing);
        mulr=(lam/(4*pi*norm(ris-sat)))^2*leoGain*risGain/noise;
        [gm,gv]=factor(mulr,p.kappa_leo_db,sr*rs'); data.G_mean(j,u,:,:)=gm; data.G_var(j,u)=gv;
    end
    geod=(lam/(4*pi*norm(user-geo)))^2*geoGain*luGain*p.geo_power_w/noise;
    [gm,gv]=factor(geod,p.kappa_geo_db,exp(-2i*pi*norm(user-geo)/lam)); data.geo_d_mean(u)=gm; data.geo_d_var(u)=gv;
    geor=(lam/(4*pi*norm(ris-geo)))^2*geoGain*risGain*p.geo_power_w/noise;
    [gm,gv]=factor(geor,p.kappa_geo_db,conj(upa(geo-ris,east,north,risShape,risSpacing)));
    data.geo_G_mean(u,:)=gm.'; data.geo_G_var(u)=gv;
end
for j=1:J
    sat=sats(j,:); [se,sn]=axes_vectors(t.satellite_latitudes_deg(j),p.geo_longitude_deg);
    steer=upa(gtpos-sat,se,sn,t.upa_shape,t.antenna_spacing_wavelengths);
    a=sat-gtpos; b=geo-gtpos; angle=acosd(max(-1,min(1,dot(a,b)/norm(a)/norm(b))));
    receiverGain=itu1428(angle,t.gt_diameter_m/lam);
    mugt=(lam/(4*pi*norm(a)))^2*leoGain*receiverGain/noise;
    [gm,gv]=factor(mugt,p.kappa_leo_db,steer); data.gt_second(j,1,:,:)=gm*gm'+gv*eye(N);
end
powerLimit=p.power_w*ones(J,1); interferenceLimit=10^(p.interference_to_noise_db/10)*ones(K,1);
end

function xyz=location(lat,lon,radius)
lat=deg2rad(lat); lon=deg2rad(lon); xyz=radius*[cos(lat)*cos(lon),cos(lat)*sin(lon),sin(lat)];
end
function [east,north]=axes_vectors(lat,lon)
lat=deg2rad(lat); lon=deg2rad(lon); east=[-sin(lon),cos(lon),0]; north=[-sin(lat)*cos(lon),-sin(lat)*sin(lon),cos(lat)];
end
function a=upa(direction,axis1,axis2,shape,spacing)
direction=direction/norm(direction); a=complex(zeros(prod(shape),1)); index=0;
for row=0:shape(1)-1
    for col=0:shape(2)-1
        index=index+1; a(index)=exp(2i*pi*spacing*(row*dot(direction,axis1)+col*dot(direction,axis2)));
    end
end
end
function [m,v]=factor(mu,kappaDb,steer)
k=10^(kappaDb/10); m=sqrt(mu*k/(1+k))*steer; v=mu/(1+k);
end

function gain=itu1428(angle,q)
% Full ITU-R S.1428-1 recommends1, including transition and back lobes.
assert(q>=20 && abs(angle)<=180,'Outside ITU pattern range'); angle=abs(angle);
if q<=100
    gmax=20*log10(q)+7.7; transition=95/q; g1=29-25*log10(transition); phim=20/q*sqrt(gmax-g1);
    if angle<phim, g=gmax-2.5e-3*(q*angle)^2;
    elseif angle<transition, g=g1;
    elseif angle<=33.1, g=29-25*log10(angle);
    elseif angle<=80, g=-9;
    elseif q<=25, g=-5;
    elseif angle<=120, g=-4;
    else, g=-9; end
else
    gmax=20*log10(q)+8.4; g1=-1+15*log10(q); phim=20/q*sqrt(gmax-g1); phir=15.85*q^(-0.6);
    if angle<phim, g=gmax-2.5e-3*(q*angle)^2;
    elseif angle<phir, g=g1;
    elseif angle<10, g=29-25*log10(angle);
    elseif angle<34.1, g=34-30*log10(angle);
    elseif angle<80, g=-12;
    elseif angle<120, g=-7;
    else, g=-12; end
end
gain=10^(g/10);
end
