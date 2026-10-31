"""SOURCE ONLY complete deterministic geometry and finite-CN Pk formulas.

Caller supplies a separately bound MP80/100 context and the frozen independent
formula module F. No imports of NumPy/MP/production model, RNG or optimizers.
The two explicit constructor lanes are separate diagnostics; no native input or
stop is changed. Individual Pk is a fixed-input independent reference, not an
unavailable native Pk record or a rigorous quadrature error certificate.
"""


def need(value,message):
    if value is not True:raise ValueError(message)


def deterministic_geometry(mp,F,config,lane):
    need(lane in ('full_physical_MP_pi','literal_binary64_constants_point'),'Separate full constructor diagnostic lane')
    need(mp.dps in (80,100),'Full original independent precisions')
    p=config['reported'];t=config['tuned_not_reported']
    N,J,U,K,M=[p[key] for key in ('N','J','U','K','M')]
    need(N==16 and J==16 and M==25 and type(U) is int and 1<=U<=6 and K==16-U,'Full original deterministic model only')
    num=lambda value:F.number(mp,value)
    pi=mp.pi if lane=='full_physical_MP_pi' else num(3.141592653589793)
    kb=mp.mpf('1.380649e-23') if lane=='full_physical_MP_pi' else num(1.380649e-23)
    lam=num(299792458)/num(p['frequency_hz']);thermal=kb*num(p['temperature_k'])*num(p['bandwidth_hz'])
    H=num(p['leo_height_m']);spacing=num(t['feed_center_spacing_m'])
    centers=[(num(x)*spacing,num(y)*spacing) for x in (-1.5,-.5,.5,1.5) for y in (-1.5,-.5,.5,1.5)]
    if U==1:hu=[(mp.mpf(0),mp.mpf(0))]
    else:
        radius=num(t['hu_cluster_radius_m']);hu=[(radius*mp.cos(j*2*pi/U),radius*mp.sin(j*2*pi/U)) for j in range(U)]
    order=sorted(range(16),key=lambda j:(mp.sqrt(centers[j][0]**2+centers[j][1]**2),j))
    nhu=[centers[j] for j in order[-K:]];ris=(num(p['ris_hu_distance_m']),mp.mpf(0))
    gain=mp.power(10,num(p['satellite_gain_dbi'])/10);receive=mp.power(10,num(t['ground_receive_gain_dbi'])/10)
    area=mp.fprod(num(v) for v in p['subsurface_elements'])*mp.fprod(num(v) for v in p['element_size_m'])
    ris_gain=4*pi*area/lam**2
    def satellite(positions,receiver):
        mean=mp.matrix(len(positions),16);variance=mp.matrix(len(positions),16)
        rician=mp.power(10,num(p['kappa_satellite_db'])/10)
        for row,pos in enumerate(positions):
            distance=mp.sqrt(H**2+pos[0]**2+pos[1]**2)
            propagation=mp.exp(-2*mp.j*pi*distance/lam)
            for col,center in enumerate(centers):
                theta=mp.atan(mp.sqrt((center[0]-pos[0])**2+(center[1]-pos[1])**2)/H)
                nu=pi*num(p['antenna_diameter_m'])/lam*mp.sin(theta)
                pattern=mp.mpf(1)
                if abs(nu)>num(1e-8):pattern=(mp.besselj(1,nu)/(2*nu)+36*mp.besselj(3,nu)/nu**3)**2
                amplitude=mp.sqrt(pattern*gain*receiver)*lam/(4*pi*distance)/mp.sqrt(thermal)
                mean[row,col]=amplitude*mp.sqrt(rician/(1+rician))*propagation
                variance[row,col]=amplitude**2/(1+rician)
        return mean,variance
    dm,dv=satellite(hu,receive);nm,nv=satellite(nhu,receive);gm,gv=satellite([ris],ris_gain)
    Gmean=F.filled_matrix(mp,25,16,lambda m,n:gm[0,n]);Gvar=F.filled_matrix(mp,25,16,lambda m,n:gv[0,n])
    # Original M25 implies a5x5 grid. All original25 positions retained.
    mr=5;mc=5;root_area=mp.sqrt(area)
    coords=[(num(a)*root_area,num(b)*root_area) for a in range(mr) for b in range(mc)]
    mean_coord=[mp.fsum(point[j] for point in coords)/25 for j in range(2)]
    coords=[(point[0]-mean_coord[0],point[1]-mean_coord[1]) for point in coords]
    rm=mp.matrix(U,25);rv=mp.matrix(U,25);kg=mp.power(10,num(p['kappa_ground_db'])/10)
    amplitude=lam/(4*pi*num(p['ris_hu_distance_m']))*mp.sqrt(ris_gain*receive)
    for u,position in enumerate(hu):
        direction=(position[0]-ris[0],position[1]-ris[1]);distance=mp.sqrt(direction[0]**2+direction[1]**2)
        need(distance>0,'Original nonzero HU/RIS geometry')
        for m,point in enumerate(coords):
            phase=mp.exp(-2*mp.j*pi*(distance+(point[0]*direction[0]+point[1]*direction[1])/distance)/lam)
            rm[u,m]=amplitude*mp.sqrt(kg/(1+kg))*phase
            rv[u,m]=amplitude**2/(1+kg)
    return dict(mean_inputs=dict(direct_mean=dm,direct_variance=dv,matrix_mean=Gmean,matrix_variance=Gvar,
                    ground_mean=rm,ground_variance=rv,nhu_mean=nm,nhu_variance=nv),
                physical_thermal_noise_W=thermal,normalized_source_noise=mp.mpf(1),power=num(p['power_w']),
                nhu_target=[mp.power(10,num(p['nhu_sinr_db'])/10)]*K,
                hu_xy_m=hu,nhu_xy_m=nhu,ris_xy_m=ris,common_ground_pathloss_distance=num(p['ris_hu_distance_m']),
                constructor_lane=lane,all_deterministic_original_dimensions=(16,16,U,K,25),
                actual_random_channels_or_phi_generated=False,rigorous_forward_or_quadrature_certificate=False)


def single_projector(mp,mean,variance):
    """All16x16 fixed literal finite-CN normalized projector, frozen V6 formula.

    This copies the original mathematical per-NHU integrand/operation order.
    Caller separately verifies both precision outcomes; no tolerance is fitted.
    """
    need(mp.dps in (80,100) and len(mean)==len(variance)==16,'Full original literal NHU/kernel precision')
    N=16;scale=mp.fsum(abs(mean[n])**2+variance[n] for n in range(N))
    need(scale>0,'Nonzero complete original finite-CN channel')
    m=[mp.conj(mean[n])/mp.sqrt(scale) for n in range(N)]
    v=[variance[n]/scale for n in range(N)]
    need(all(a>0 for a in v),'No LoS-only replacement or erased finite variance')
    P=mp.matrix(N,N)
    for i in range(N):
        for j in range(i,N):
            def integrand(s):
                if s==1:return mp.mpf(0)
                t=s/(1-s);iv=[1/(1+t*a) for a in v]
                lap=mp.exp(-mp.fsum(mp.log1p(t*a) for a in v)
                    -t*mp.fsum(abs(m[n])**2*iv[n] for n in range(N)))
                entry=m[i]*mp.conj(m[j])*iv[i]*iv[j]
                if i==j:entry+=v[i]*iv[i]
                return lap*entry/(1-s)**2
            P[i,j]=mp.quad(integrand,[0,mp.mpf('0.5'),mp.mpf('0.9'),mp.mpf('0.99'),1])
            P[j,i]=mp.conj(P[i,j])
    return P


def complete_projector_square(mp,projectors):
    """Full ordered original K10..15 composite; no native cache injection."""
    need(mp.dps in (80,100) and 10<=len(projectors)<=15 and all(p.rows==p.cols==16 for p in projectors),
         'Whole original finite-CN NHU population')
    square=mp.eye(16)
    for p in projectors:square-=p
    for k in range(len(projectors)):
        for j in range(len(projectors)):
            if k!=j:square+=projectors[k]*projectors[j]
    return (square+square.H)/2
