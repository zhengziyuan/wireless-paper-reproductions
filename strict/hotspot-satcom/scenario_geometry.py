"""Same full finite-Rician scenario with source-compliant declared HU geometry.

Historical author coordinates are not recovered. All pairwise HU distances
are checked against the original 10..20m range; radius10m is not curve fitted.
"""
import numpy as np
from scipy.special import jv


def esa_power_pattern(nu):
    nu=np.asarray(nu); result=np.ones_like(nu,float); nonzero=abs(nu)>1e-8; x=nu[nonzero]
    result[nonzero]=(jv(1,x)/(2*x)+36*jv(3,x)/x**3)**2
    return result


def cluster_positions(U, radius=10.0):
    if int(U)!=U or not 1<=U<=6:
        raise ValueError('Original HU-count contract requires integer U1..6')
    if U==1:
        return np.zeros((1,2))
    angles=np.arange(U)*2*np.pi/U
    positions=np.column_stack((radius*np.cos(angles),radius*np.sin(angles)))
    distances=np.linalg.norm(positions[:,None,:]-positions[None,:,:],axis=2)[np.triu_indices(U,1)]
    if np.min(distances)<10-1e-12 or np.max(distances)>20+1e-12:
        raise ValueError('All original HU pair distances must remain in10..20m')
    return positions


def sample_scenario(config,rng):
    p=config['reported']; t=config['tuned_not_reported']; N,J,U,K,M=(p[k] for k in ('N','J','U','K','M'))
    if N!=16 or J!=16 or U+K!=J: raise ValueError('Original 16-feed/16-user dimensions required')
    cn=lambda shape:(rng.standard_normal(shape)+1j*rng.standard_normal(shape))/np.sqrt(2)
    lam=299792458/p['frequency_hz']; noise=1.380649e-23*p['temperature_k']*p['bandwidth_hz']; H=p['leo_height_m']
    centers=np.array([[x,y] for x in (-1.5,-0.5,0.5,1.5) for y in (-1.5,-0.5,0.5,1.5)])*t['feed_center_spacing_m']
    hu_pos=cluster_positions(U,t['hu_cluster_radius_m'])
    # U is a paper sweep, so K=16-U, not a computational downsize.
    feed_order=sorted(range(N),key=lambda n:float(np.linalg.norm(centers[n])))
    nhu_pos=centers[feed_order[-K:]]; ris_pos=np.array([p['ris_hu_distance_m'],0.])
    gain=10**(p['satellite_gain_dbi']/10); receive=10**(t['ground_receive_gain_dbi']/10)
    area=np.prod(p['subsurface_elements'])*np.prod(p['element_size_m']); ris_gain=4*np.pi*area/lam**2
    def sat_mean_variance(pos,receiver_gain):
        pos=np.atleast_2d(pos); distance=np.sqrt(H**2+np.sum(pos**2,axis=1))
        theta=np.arctan(np.linalg.norm(centers[None,:,:]-pos[:,None,:],axis=2)/H)
        nu=np.pi*p['antenna_diameter_m']/lam*np.sin(theta)
        amplitude=np.sqrt(esa_power_pattern(nu)*gain*receiver_gain)*(lam/(4*np.pi*distance[:,None]))/np.sqrt(noise)
        k=10**(p['kappa_satellite_db']/10)
        mean=amplitude*np.sqrt(k/(1+k))*np.exp(-2j*np.pi*distance[:,None]/lam)
        variance=amplitude**2/(1+k)
        return mean,variance
    dm,dv=sat_mean_variance(hu_pos,receive); nm,nv=sat_mean_variance(nhu_pos,receive)
    direct=dm+np.sqrt(dv)*cn((U,N)); nhu=nm+np.sqrt(nv)*cn((K,N))
    gm,gv=sat_mean_variance(ris_pos,ris_gain)
    # One satellite-to-RIS channel is shared by every HU.
    mr=int(np.sqrt(M))
    while M%mr: mr-=1
    mc=M//mr; coords=np.array([[a,b] for a in range(mr) for b in range(mc)])*np.sqrt(area)
    coords-=np.mean(coords,axis=0)
    Gmean=np.tile(gm,(M,1)); Gvar=np.tile(gv,(M,1)); G=Gmean+np.sqrt(Gvar)*cn((M,N))
    cascade=np.zeros((U,M,N),complex); rm=np.zeros((U,M),complex); rv=np.zeros((U,M))
    kg=10**(p['kappa_ground_db']/10)
    for u in range(U):
        direction=hu_pos[u]-ris_pos; distance=np.linalg.norm(direction)
        # Original numerical paragraph fixes equal large-scale RIS-to-HU
        # attenuation at d_RU=400m for every subpanel/user. Actual position
        # offsets remain in the propagation phase, not the path-loss gain.
        amplitude=lam/(4*np.pi*p['ris_hu_distance_m'])*np.sqrt(ris_gain*receive)
        phase=np.exp(-2j*np.pi*(distance+coords@direction/distance)/lam)
        rm[u]=amplitude*np.sqrt(kg/(1+kg))*phase; rv[u]=amplitude**2/(1+kg)
        r=rm[u]+np.sqrt(rv[u])*cn((M,)); cascade[u]=r[:,None]*G
    phi=np.exp(2j*np.pi*rng.uniform(size=M))
    return {'direct':direct,'cascade':cascade,'nhu':nhu,'phi0':phi,'noise':1.0,
            'power':p['power_w'],'nhu_target':np.full(K,10**(p['nhu_sinr_db']/10)),
            'mean_inputs':{'direct_mean':dm,'direct_variance':dv,'matrix_mean':Gmean,'matrix_variance':Gvar,'ground_mean':rm,'ground_variance':rv,
                           'nhu_mean':nm,'nhu_variance':nv},
            'geometry':{'hu_xy_m':hu_pos,'nhu_xy_m':nhu_pos,'ris_xy_m':ris_pos,
                        'common_ground_pathloss_distance_m':p['ris_hu_distance_m']}}
