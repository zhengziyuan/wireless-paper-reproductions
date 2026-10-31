"""Independent high-precision fixed-double moment/phase formulas, no optimizer.

Cartesian binary floats are imported exactly. A saved phase coordinate moves
along phi*exp(i*theta), retaining its stored radius. Thus covariance A*A^H is
constant under the angular derivative even when |binary phi|-1 is nonzero.
This is finite-precision MP, NOT interval/analytic-channel certification.
"""
import mpmath as mp
import numpy as np


def real(value):
    n,d=float(value).as_integer_ratio();return mp.mpf(n)/d
def scalar(value):
    return mp.mpc(real(np.real(value)),real(np.imag(value))) if np.iscomplexobj(value) else real(value)
def vector(a):return [scalar(z) for z in np.asarray(a).reshape(-1)]
def matrix(a):return [[scalar(z) for z in row] for row in np.asarray(a)]
def dot(a,b):return mp.fsum(mp.conj(x)*y for x,y in zip(a,b))
def mv(a,b):return [mp.fsum(x*y for x,y in zip(row,b)) for row in a]
def norm2(a):return mp.re(dot(a,a))
def quad(a,b):return mp.re(dot(a,mv(b,a)))
def tr(a):return mp.fsum(mp.re(a[n][n]) for n in range(len(a)))
def outer_add(c,a):return [[c[i][j]+a[i]*mp.conj(a[j]) for j in range(len(a))] for i in range(len(a))]
def mat_hpart(a):return [[(a[i][j]+mp.conj(a[j][i]))/2 for j in range(len(a))] for i in range(len(a))]
def trace_product(a,b):return mp.re(mp.fsum(a[i][j]*b[j][i] for i in range(len(a)) for j in range(len(a))))


class FixedContext:
    def __init__(self,data,phi,power,mu,limit,tts):
        self.J,self.U,self.N=data['d_mean'].shape;self.M=phi.shape[1];self.K=len(limit)
        self.phi=[vector(row) for row in phi];self.p=[vector(row) for row in power]
        self.mu=real(mu);self.limit=vector(limit);self.tts=bool(tts)
        if self.mu<=0:raise ValueError("Positive original smoothing required")
        self.d=[[vector(data['d_mean'][j,u]) for u in range(self.U)] for j in range(self.J)]
        self.G=[[matrix(data['G_mean'][j,u]) for u in range(self.U)] for j in range(self.J)]
        self.r=[vector(row) for row in data['r_mean']];self.rv=vector(data['r_var'])
        self.dv=[vector(row) for row in data['d_var']];self.Gv=[vector(row) for row in data['G_var']]
        self.gt=[[matrix(data['gt_second'][j,k]) for k in range(self.K)] for j in range(self.J)]
        self.gt_h=[[mat_hpart(a) for a in row] for row in self.gt]
        self.gt_hermitian_residual=max(abs(a[i][k]-mp.conj(a[k][i])) for row in self.gt for a in row for i in range(self.N) for k in range(self.N))
        self.mean=[];self.C=[];self.Cb=[];self.er2=[];self.er4=[];self.afro=[];self.trCb=[]
        for j in range(self.J):
            mrow=[];crow=[];brow=[];e2row=[];e4row=[];arow=[];trow=[]
            for u in range(self.U):
                A=[[self.G[j][u][i][m]*self.phi[u][m] for m in range(self.M)] for i in range(self.N)]
                Ar=mv(A,self.r[u]);mean=[a+b for a,b in zip(self.d[j][u],Ar)]
                rv=self.rv[u];cb=[[rv*mp.fsum(A[a][m]*mp.conj(A[b][m]) for m in range(self.M)) for b in range(self.N)] for a in range(self.N)]
                er2=norm2(self.r[u])+self.M*rv
                er4=er2**2+self.M*rv**2+2*rv*norm2(self.r[u])
                var=self.dv[j][u]+self.Gv[j][u]*er2
                c=[[cb[a][b]+(var if a==b else 0) for b in range(self.N)] for a in range(self.N)]
                mrow.append(mean);crow.append(c);brow.append(cb);e2row.append(er2);e4row.append(er4)
                arow.append(mp.fsum(norm2(row) for row in A));trow.append(tr(cb))
            self.mean.append(mrow);self.C.append(crow);self.Cb.append(brow)
            self.er2.append(e2row);self.er4.append(e4row);self.afro.append(arow);self.trCb.append(trow)
        self.geo_d=vector(data['geo_d_mean']);self.geo_G=[vector(row) for row in data['geo_G_mean']]
        self.geo_mean=[self.geo_d[u]+mp.fsum(self.geo_G[u][m]*self.phi[u][m]*self.r[u][m] for m in range(self.M)) for u in range(self.U)]
        self.geo_constant=[]
        for u in range(self.U):
            avar=self.rv[u]*mp.fsum(abs(self.geo_G[u][m]*self.phi[u][m])**2 for m in range(self.M))
            er2=norm2(self.r[u])+self.M*self.rv[u]
            self.geo_constant.append(1+real(data['geo_d_var'][u])+real(data['geo_G_var'][u])*er2+avar)
        self.traceCC=[[[trace_product(self.C[j][u],self.C[j][i]) for i in range(self.U)] for u in range(self.U)] for j in range(self.J)]

    def fourth(self,j,u,mean):
        rv=self.rv[u];eb2=norm2(mean)+self.trCb[j][u]
        eb4=eb2**2+trace_product(self.Cb[j][u],self.Cb[j][u])+2*quad(mean,self.Cb[j][u])
        ar=[a-b for a,b in zip(mean,self.d[j][u])]
        er2b2=self.er2[j][u]*eb2+rv**2*self.afro[j][u]+2*rv*mp.re(dot(ar,mean))
        evb2=self.dv[j][u]*eb2+self.Gv[j][u]*er2b2
        ev2=self.dv[j][u]**2+2*self.dv[j][u]*self.Gv[j][u]*self.er2[j][u]+self.Gv[j][u]**2*self.er4[j][u]
        return eb4+2*(self.N+1)*evb2+self.N*(self.N+1)*ev2

    def objective(self,means=None,geomean=None,details=False):
        means=self.mean if means is None else means;geomean=self.geo_mean if geomean is None else geomean
        power=[[norm2(means[j][u])+(tr(self.C[j][u]) if self.tts else 0) for u in range(self.U)] for j in range(self.J)]
        numerator=[mp.fsum(self.p[j][u]*power[j][u]**2 for j in range(self.J)) for u in range(self.U)]
        offset=[self.geo_constant[u]+abs(geomean[u])**2 for u in range(self.U)]
        cross=[[[mp.mpf(0) for _ in range(self.U)] for _ in range(self.U)] for _ in range(self.J)]
        for j in range(self.J):
            for u in range(self.U):
                for i in range(self.U):
                    if self.tts:
                        cross[j][u][i]=self.fourth(j,u,means[j][u]) if u==i else self.traceCC[j][u][i]+quad(means[j][i],self.C[j][u])+quad(means[j][u],self.C[j][i])+abs(dot(means[j][u],means[j][i]))**2
                    else:cross[j][u][i]=quad(means[j][i],self.C[j][u])+abs(dot(means[j][u],means[j][i]))**2
        denominator=[offset[u]+mp.fsum(self.p[j][i]*cross[j][u][i] for j in range(self.J) for i in range(self.U))-numerator[u] for u in range(self.U)]
        if min(denominator)<=0:raise ValueError("Original positive SINR denominator not met")
        sinr=[a/b for a,b in zip(numerator,denominator)];minimum=min(sinr)
        ex=[mp.exp(-(x-minimum)/self.mu) for x in sinr];weights=[x/mp.fsum(ex) for x in ex]
        leak=[mp.fsum(self.p[j][u]*(quad(means[j][u],self.gt_h[j][k])+(trace_product(self.gt_h[j][k],self.C[j][u]) if self.tts else 0)) for j in range(self.J) for u in range(self.U)) for k in range(self.K)]
        residual=[a-b for a,b in zip(leak,self.limit)]
        value=minimum-self.mu*mp.log(mp.fsum(ex))-mp.fsum(x*x for x in residual)
        return (value,numerator,denominator,sinr,weights,residual,power) if details else value

    def objective_rotation(self,user,coordinate,delta):
        # Exact rank-one angular update of the SAME full physical objective;
        # |phi| is constant, so all conditional-Gaussian covariance terms stay.
        factor=mp.exp(1j*delta)-1
        means=[[list(z) for z in row] for row in self.mean]
        for j in range(self.J):
            direction=[self.G[j][user][i][coordinate]*self.phi[user][coordinate]*self.r[user][coordinate] for i in range(self.N)]
            means[j][user]=[a+factor*b for a,b in zip(means[j][user],direction)]
        geo=list(self.geo_mean);geo[user]+=factor*self.geo_G[user][coordinate]*self.phi[user][coordinate]*self.r[user][coordinate]
        return self.objective(means,geo)

    def gradient(self,finite_difference=False):
        value,num,den,sinr,weights,residual,power=self.objective(details=True)
        Q=[[outer_add(self.C[j][u],self.mean[j][u]) for u in range(self.U)] for j in range(self.J)]
        Qmu=[[[mv(Q[j][u],self.mean[j][i]) for i in range(self.U)] for u in range(self.U)] for j in range(self.J)]
        GTmu=[[[mv(self.gt_h[j][k],self.mean[j][u]) for k in range(self.K)] for u in range(self.U)] for j in range(self.J)]
        CBmu=[[mv(self.Cb[j][u],self.mean[j][u]) for u in range(self.U)] for j in range(self.J)]
        theta=[];gradient=[];fd=[];all_ds=[];all_penalty=[];h=mp.mpf('1e-20')
        for v in range(self.U):
            row=[];grow=[];fdrow=[];dsrow=[];penaltyrow=[]
            for m in range(self.M):
                dn=[mp.mpf(0) for _ in range(self.U)];dd=[mp.mpf(0) for _ in range(self.U)];dl=[mp.mpf(0) for _ in range(self.K)]
                dd[v]=2*mp.re(mp.conj(self.geo_mean[v])*1j*self.phi[v][m]*self.geo_G[v][m]*self.r[v][m])
                for j in range(self.J):
                    d=[1j*self.phi[v][m]*self.G[j][v][i][m]*self.r[v][m] for i in range(self.N)]
                    qdot=2*mp.re(dot(self.mean[j][v],d));dn[v]+=self.p[j][v]*2*power[j][v]*qdot
                    eb2=norm2(self.mean[j][v])+self.trCb[j][v]
                    deb4=2*eb2*qdot+4*mp.re(dot(CBmu[j][v],d))
                    ar=[a-b for a,b in zip(self.mean[j][v],self.d[j][v])]
                    der2b2=self.er2[j][v]*qdot+2*self.rv[v]*mp.re(dot(d,self.mean[j][v])+dot(ar,d))
                    df=deb4+2*(self.N+1)*(self.dv[j][v]*qdot+self.Gv[j][v]*der2b2)
                    for u in range(self.U):
                        for i in range(self.U):
                            db=mp.mpf(0)
                            if self.tts:
                                if u==i:db=df if u==v else 0
                                else:
                                    if u==v:db+=2*mp.re(dot(Qmu[j][i][v],d))
                                    if i==v:db+=2*mp.re(dot(Qmu[j][u][v],d))
                            else:
                                if i==v:db+=2*mp.re(dot(d,Qmu[j][u][v]))
                                if u==v:db+=2*mp.re(mp.conj(dot(self.mean[j][v],self.mean[j][i]))*dot(d,self.mean[j][i]))
                            dd[u]+=self.p[j][i]*db
                    for k in range(self.K):dl[k]+=self.p[j][v]*2*mp.re(dot(GTmu[j][v][k],d))
                dd=[a-b for a,b in zip(dd,dn)]
                ds=[(dn[u]*den[u]-num[u]*dd[u])/den[u]**2 for u in range(self.U)]
                component=mp.fsum(w*x for w,x in zip(weights,ds))-2*mp.fsum(a*b for a,b in zip(residual,dl))
                row.append(component);grow.append(1j*self.phi[v][m]*component)
                dsrow.append(ds);penaltyrow.append(2*mp.fsum(a*b for a,b in zip(residual,dl)))
                if finite_difference:fdrow.append((self.objective_rotation(v,m,h)-self.objective_rotation(v,m,-h))/(2*h))
            theta.append(row);gradient.append(grow)
            all_ds.append(dsrow);all_penalty.append(penaltyrow)
            if finite_difference:fd.append(fdrow)
        return {"criterion":value,"theta_gradient":theta,"complex_gradient":gradient,
                "norm":mp.sqrt(mp.fsum(abs(z)**2 for row in gradient for z in row)),
                "numerator":num,"denominator":den,"sinr":sinr,"softmin_weights":weights,
                "SINR_coordinate_derivatives":all_ds,"penalty_theta_gradient":all_penalty,
                "residual":residual,"GT_Hermitian_residual":self.gt_hermitian_residual,
                "finite_difference_step":h if finite_difference else None,"finite_difference":fd}
