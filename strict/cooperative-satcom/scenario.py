"""Reproducible physical finite-Rician scenarios, author-model version labelled.

Unreported receive/element gains and antenna-pattern details are explicit tuning
in full_config.json. This generator does not claim recovered original scenarios.
"""
import numpy as np


def location(lat,lon,radius):
    lat,lon=np.deg2rad([lat,lon]); return radius*np.array([np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)])


def axes(lat,lon):
    lat,lon=np.deg2rad([lat,lon]); return np.array([-np.sin(lon),np.cos(lon),0]),np.array([-np.sin(lat)*np.cos(lon),-np.sin(lat)*np.sin(lon),np.cos(lat)])


def upa(direction,axis1,axis2,shape,spacing_wavelengths):
    direction=direction/np.linalg.norm(direction); nr,nc=shape
    row,col=np.meshgrid(np.arange(nr),np.arange(nc),indexing='ij')
    return np.exp(2j*np.pi*spacing_wavelengths*(row.ravel()*np.dot(direction,axis1)+col.ravel()*np.dot(direction,axis2)))


def factor(mu,kappa_db,steering):
    k=10**(kappa_db/10); return np.sqrt(mu*k/(1+k))*steering,mu/(1+k)


def gt_pattern(angle_deg,cfg,wavelength):
    """ITU-R S.1428-1 recommends1, referenced by S.1503 FSS receive pattern.

    Full main/transition/side/back lobes, not the S.465 envelope substitute.
    Diameter is an explicit unreported numeric choice; pattern shape is ITU's.
    """
    q=cfg['gt_diameter_m']/wavelength; angle=abs(float(angle_deg))
    if not 20<=q or angle>180: raise ValueError('Outside ITU S.1428-1 validity range')
    gmax=20*np.log10(q)+(7.7 if q<=100 else 8.4)
    if q<=100:
        transition=95/q; g1=29-25*np.log10(transition)
        phim=20/q*np.sqrt(gmax-g1)
        if angle<phim: gain=gmax-2.5e-3*(q*angle)**2
        elif angle<transition: gain=g1
        elif angle<=33.1: gain=29-25*np.log10(angle)
        elif angle<=80: gain=-9
        elif q<=25: gain=-5
        elif angle<=120: gain=-4
        else: gain=-9
    else:
        g1=-1+15*np.log10(q); phim=20/q*np.sqrt(gmax-g1); phir=15.85*q**(-0.6)
        if angle<phim: gain=gmax-2.5e-3*(q*angle)**2
        elif angle<phir: gain=g1
        elif angle<10: gain=29-25*np.log10(angle)
        elif angle<34.1: gain=34-30*np.log10(angle)
        elif angle<80: gain=-12
        elif angle<120: gain=-7
        else: gain=-12
    return 10**(gain/10)


def make_scenario(config):
    p=config['reported']; t=config['tuned_not_reported']; J,U,N,K,M=(p[k] for k in ('J','U','N','K','M'))
    if N!=np.prod(t['upa_shape']) or J!=len(t['satellite_latitudes_deg']): raise ValueError('Full dimensions/config geometry mismatch')
    if U!=len(t['user_latitudes_deg']): raise ValueError('No implicit user-count reduction')
    earth=t['earth_radius_m']; lam=299792458/p['frequency_hz']; noise=10**((p['noise_dbm']-30)/10)
    subsurface_area=np.prod(p['subsurface_elements'])*np.prod(p['element_size_m'])
    ris_gain=4*np.pi*subsurface_area/lam**2
    leo_gain=10**(t['leo_element_gain_dbi']/10); lu_gain=10**(t['lu_gain_dbi']/10); geo_gain=10**(t['geo_gain_dbi']/10)
    geo=location(0,p['geo_longitude_deg'],earth+p['geo_height_m'])
    users=[location(t['user_latitudes_deg'][u],t['lu_longitudes_deg'][u],earth) for u in range(U)]
    sats=[location(lat,p['geo_longitude_deg'],earth+p['leo_height_m']) for lat in t['satellite_latitudes_deg']]
    gtpos=location(t['gt_latitude_deg'],p['geo_longitude_deg'],earth)
    data={'d_mean':np.zeros((J,U,N),complex),'d_var':np.zeros((J,U)),
          'G_mean':np.zeros((J,U,N,M),complex),'G_var':np.zeros((J,U)),
          'r_mean':np.zeros((U,M),complex),'r_var':np.zeros(U),
          'gt_second':np.zeros((J,K,N,N),complex),
          'geo_d_mean':np.zeros(U,complex),'geo_d_var':np.zeros(U),
          'geo_G_mean':np.zeros((U,M),complex),'geo_G_var':np.zeros(U)}
    mr=int(np.floor(np.sqrt(M)))
    while M%mr: mr-=1
    ris_shape=(mr,M//mr); ris_spacing=np.sqrt(subsurface_area)/lam
    for u,user in enumerate(users):
        east,north=axes(t['user_latitudes_deg'][u],t['lu_longitudes_deg'][u]); ris=user+p['ris_lu_distance_m']*east
        rsteer=upa(user-ris,east,north,ris_shape,ris_spacing)
        mur=(lam/(4*np.pi*np.linalg.norm(user-ris)))**2*ris_gain*lu_gain
        data['r_mean'][u],data['r_var'][u]=factor(mur,p['kappa_ground_db'],rsteer)
        for j,sat in enumerate(sats):
            se,sn=axes(t['satellite_latitudes_deg'][j],p['geo_longitude_deg'])
            steer=upa(user-sat,se,sn,t['upa_shape'],t['antenna_spacing_wavelengths'])
            mul=(lam/(4*np.pi*np.linalg.norm(user-sat)))**2*leo_gain*lu_gain/noise
            data['d_mean'][j,u],data['d_var'][j,u]=factor(mul,p['kappa_leo_db'],steer)
            sr=upa(ris-sat,se,sn,t['upa_shape'],t['antenna_spacing_wavelengths'])
            rs=upa(sat-ris,east,north,ris_shape,ris_spacing)
            mulr=(lam/(4*np.pi*np.linalg.norm(ris-sat)))**2*leo_gain*ris_gain/noise
            data['G_mean'][j,u],data['G_var'][j,u]=factor(mulr,p['kappa_leo_db'],np.outer(sr,np.conj(rs)))
        geod=(lam/(4*np.pi*np.linalg.norm(user-geo)))**2*geo_gain*lu_gain*p['geo_power_w']/noise
        data['geo_d_mean'][u],data['geo_d_var'][u]=factor(geod,p['kappa_geo_db'],np.exp(-2j*np.pi*np.linalg.norm(user-geo)/lam))
        geor=(lam/(4*np.pi*np.linalg.norm(ris-geo)))**2*geo_gain*ris_gain*p['geo_power_w']/noise
        data['geo_G_mean'][u],data['geo_G_var'][u]=factor(geor,p['kappa_geo_db'],np.conj(upa(geo-ris,east,north,ris_shape,ris_spacing)))
    for j,sat in enumerate(sats):
        se,sn=axes(t['satellite_latitudes_deg'][j],p['geo_longitude_deg'])
        steer=upa(gtpos-sat,se,sn,t['upa_shape'],t['antenna_spacing_wavelengths'])
        a=sat-gtpos; b=geo-gtpos; angle=np.rad2deg(np.arccos(np.clip(np.dot(a,b)/np.linalg.norm(a)/np.linalg.norm(b),-1,1)))
        receiver_gain=gt_pattern(angle,t,lam)
        mugt=(lam/(4*np.pi*np.linalg.norm(a)))**2*leo_gain*receiver_gain/noise
        gm,gv=factor(mugt,p['kappa_leo_db'],steer)
        data['gt_second'][j,0]=np.outer(gm,np.conj(gm))+gv*np.eye(N)
    return data,np.full(J,p['power_w']),np.full(K,10**(p['interference_to_noise_db']/10))
