"""Independent arbitrary-precision original physical ISAC scalar objective.

No production core calls. Binary64 inputs are promoted exactly to mp numbers;
all rotations, gains, steering/path sums, powers and utility are then evaluated
at the selected precision. Fixed iota is required for an inner-block audit.
"""
import mpmath as mp

def exact(v):
    if isinstance(v,(complex,mp.mpc)):
        return mp.mpc(mp.mpf(v.real),mp.mpf(v.imag))
    return mp.mpf(v)

def frame(r):
    x,y,z=[exact(v) for v in r]
    cx,sx,cy,sy,cz,sz=mp.cos(x),mp.sin(x),mp.cos(y),mp.sin(y),mp.cos(z),mp.sin(z)
    return mp.matrix([[1,0,0],[0,cx,-sx],[0,sx,cx]])*mp.matrix([[cy,0,sy],[0,1,0],[-sy,0,cy]])*mp.matrix([[cz,-sz,0],[sz,cz,0],[0,0,1]])

def field_parts(r,c):
    qb,qr=frame(r[:3]),frame(r[3:])
    cb,cr=c['bs_coordinates'],c['ris_coordinates'];m,n=len(cb),len(cr)
    k,a=len(c['noise']),len(c['desired_pattern'])
    wave=2*mp.pi/exact(c['wavelength'])
    gain0=mp.sqrt(exact(c['maximum_gain']));exponent=exact(c['directivity_exponent'])/2
    def response(coordinate,center,direction,q):
        u=mp.matrix([exact(v) for v in direction])
        cosine=sum(q[d,2]*u[d] for d in range(3))
        if cosine<=0:return mp.mpc(0)
        xyz=q*mp.matrix([exact(v) for v in coordinate])+mp.matrix([exact(v) for v in center])
        return gain0*cosine**exponent*mp.exp(1j*wave*sum(xyz[d]*u[d] for d in range(3)))
    H,G=mp.matrix(m,k+a),mp.matrix(n,k+a)
    for user in range(k):
        for ray,direction in enumerate(c['bu_directions'][user]):
            gain=mp.mpc(exact(c['bu_gain_re'][user][ray]),exact(c['bu_gain_im'][user][ray]))
            for antenna in range(m):H[antenna,user]+=gain*response(cb[antenna],c['bs_center'],direction,qb)
        for ray,direction in enumerate(c['ru_directions'][user]):
            gain=mp.mpc(exact(c['ru_gain_re'][user][ray]),exact(c['ru_gain_im'][user][ray]))
            for element in range(n):G[element,user]+=gain*response(cr[element],c['ris_center'],direction,qr)
    for target in range(a):
        for antenna in range(m):H[antenna,k+target]=response(cb[antenna],c['bs_center'],c['bt_directions'][target],qb)
        for element in range(n):G[element,k+target]=response(cr[element],c['ris_center'],c['rt_directions'][target],qr)
    B=mp.matrix(m,n)
    for ray in range(len(c['br_directions'])):
        gain=mp.mpc(exact(c['br_gain_re'][ray]),exact(c['br_gain_im'][ray]))
        ab=[response(coordinate,c['bs_center'],c['br_directions'][ray],qb) for coordinate in cb]
        ar=[response(coordinate,c['ris_center'],c['rb_directions'][ray],qr) for coordinate in cr]
        for antenna in range(m):
            for element in range(n):B[antenna,element]+=gain*ab[antenna]*mp.conj(ar[element])
    return H,G,B

def utility(w,theta,r,c,iota,parts=None):
    H,G,B=field_parts(r,c) if parts is None else parts
    m,n=len(c['bs_coordinates']),len(c['ris_coordinates']);k=len(c['noise']);a=len(c['desired_pattern'])
    F=mp.matrix(H)
    for antenna in range(m):
        for link in range(k+a):
            F[antenna,link]+=sum(B[antenna,element]*exact(theta[element])*G[element,link] for element in range(n))
    def amplitude(link,stream):
        return sum(mp.conj(F[antenna,link])*exact(complex(w[antenna,stream])) for antenna in range(m))
    rate=mp.mpf(0);pattern=[]
    for user in range(k):
        gains=[abs(amplitude(user,stream))**2 for stream in range(w.shape[1])]
        interference=sum(value for stream,value in enumerate(gains) if stream!=user)+exact(c['noise'][user])
        rate+=mp.log(1+gains[user]/interference)/mp.log(2)
    for target in range(a):pattern.append(sum(abs(amplitude(k+target,stream))**2 for stream in range(w.shape[1])))
    iota=exact(iota);desired=[exact(v) for v in c['desired_pattern']]
    nmse=sum((p-iota*d)**2 for p,d in zip(pattern,desired))/(iota*iota*sum(d*d for d in desired))
    return rate-exact(c['rho'])*nmse
