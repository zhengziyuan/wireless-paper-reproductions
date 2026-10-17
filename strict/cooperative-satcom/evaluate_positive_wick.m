function out = evaluate_positive_wick(data,phi,mode,p,smoothing,limit,W)
% Isolated original conditional-Gaussian component formulas; no optimizer/RNG.
% Stored phase radii retained. Positive Wick expansions, no variance subtraction.
[J,U,N]=size(data.d_mean); M=size(phi,2);
assert(isequal(size(phi),[U,M]) && all(isfinite(phi(:))));
% MAT integer scalar controls must enter continuous arithmetic as doubles.
smoothing=double(smoothing);
assert(max(abs(abs(phi(:))-1))<=1e-10,'Stored near-unit phase domain required');
assert(isequal([size(data.G_mean,1),size(data.G_mean,2),size(data.G_mean,3),size(data.G_mean,4)],[J,U,N,M]));
assert(size(data.gt_second,1)==J && size(data.gt_second,3)==N && size(data.gt_second,4)==N);
terms = moments(data,phi);
mean=terms.mean; C=terms.C; Q=terms.Q; A=terms.A; Cb=terms.Cb; Ev=terms.Ev;
if strcmp(mode,'ap')
    assert(isequal(size(W),[J,N,U]) && all(isfinite(W(:))));
    num=zeros(1,U); den=terms.offset; theta=zeros(U,M);
    dnall=zeros(U,M); ddall=zeros(U,M);
    for u=1:U
        for j=1:J
            m=reshape(mean(j,u,:),N,1);
            w=reshape(W(j,:,u),N,1); num(u)=num(u)+abs(m'*w)^2;
            for i=1:U
                w=reshape(W(j,:,i),N,1);
                if i==u, covariance=reshape(C(j,u,:,:),N,N); else, covariance=reshape(Q(j,u,:,:),N,N); end
                den(u)=den(u)+rdot(w,covariance*w);
            end
        end
        for coordinate=1:M
            r=reshape(data.r_mean(u,:),M,1);
            geoA=reshape(data.geo_G_mean(u,:),M,1).*reshape(phi(u,:),M,1);
            gm=data.geo_d_mean(u)+csum(geoA.*r);
            dg=1i*phi(u,coordinate)*data.geo_G_mean(u,coordinate)*r(coordinate);
            dn=0; dd=2*real(conj(gm)*dg);
            for j=1:J
                m=reshape(mean(j,u,:),N,1);
                d=1i*phi(u,coordinate)*reshape(data.G_mean(j,u,:,coordinate),N,1)*r(coordinate);
                w=reshape(W(j,:,u),N,1); a=m'*w; da=d'*w;
                dn=dn+2*real(conj(a)*da);
                for i=1:U
                    if i~=u
                        w=reshape(W(j,:,i),N,1);
                        dd=dd+2*real(conj(m'*w)*(d'*w));
                    end
                end
            end
            theta(u,coordinate)=(dn*den(u)-num(u)*dd)/den(u)^2;
            dnall(u,coordinate)=dn; ddall(u,coordinate)=dd;
        end
    end
    assert(all(isfinite(den)) && all(den>0));
    out=terms; out.criterion=num./den; out.sinr=num./den;
    out.numerator=num; out.denominator=den; out.weights=[]; out.weights_applicable=false;
    out.theta_gradient=theta; out.gradient=1i*phi.*theta;
    out.dnumerator=dnall; out.ddenominator=ddall; out.dsinr=theta;
    out.mode=mode; out.AP_individual_SINR_not_MR_softmin=true;
    return
end
assert(strcmp(mode,'mr_s') || strcmp(mode,'mr_tts'));
tts=strcmp(mode,'mr_tts'); K=numel(limit);
assert(isequal(size(p),[J,U]) && all(isfinite(p(:))) && all(p(:)>=0));
assert(isscalar(smoothing) && isfinite(smoothing) && smoothing>0 && K>=1);
if tts, power=terms.tts_power; else, power=zeros(J,U); end
signal=zeros(J,U); cross=zeros(J,U,U); own=zeros(J,U); leak=zeros(J,U,K);
gt=complex(zeros(J,K,N,N));
for j=1:J
    for k=1:K
        g=reshape(data.gt_second(j,k,:,:),N,N); gt(j,k,:,:)=reshape((g+g')/2,1,1,N,N);
    end
end
for j=1:J
    for u=1:U
        rv=data.r_var(u); m=reshape(mean(j,u,:),N,1); a=reshape(A(j,u,:,:),N,M); f=n2(a);
        if ~tts, power(j,u)=n2(m); end
        signal(j,u)=power(j,u)^2;
        if tts, own(j,u)=terms.tts_own(j,u); else, own(j,u)=rsum([rv*n2(a'*m),Ev(j,u)*n2(m)]); end
        for i=1:U
            if i==u, cross(j,u,i)=signal(j,u)+own(j,u); continue; end
            mi=reshape(mean(j,i,:),N,1); ai=reshape(A(j,i,:,:),N,M); rvi=data.r_var(i);
            value=rsum([rv*n2(a'*mi),Ev(j,u)*n2(mi),abs(m'*mi)^2]);
            if tts
                value=rsum([value,rvi*n2(ai'*m),Ev(j,i)*n2(m),rv*rvi*n2(a'*ai), ...
                    rv*Ev(j,i)*f,rvi*Ev(j,u)*n2(ai),N*Ev(j,u)*Ev(j,i)]);
            end
            cross(j,u,i)=value;
        end
        for k=1:K
            g=reshape(gt(j,k,:,:),N,N); value=rdot(m,g*m);
            if tts, value=value+rsum(real(diag(g*reshape(C(j,u,:,:),N,N)))); end
            leak(j,u,k)=value;
        end
    end
end
num=zeros(1,U); den=zeros(1,U);
for u=1:U
    num(u)=rsum(p(:,u).*signal(:,u)); parts=[terms.offset(u)];
    for j=1:J, parts(end+1)=p(j,u)*own(j,u); end %#ok<AGROW>
    for j=1:J
        for i=1:U, if i~=u, parts(end+1)=p(j,i)*cross(j,u,i); end, end %#ok<AGROW>
    end
    den(u)=rsum(parts);
end
assert(all(isfinite(den)) && all(den>0));
sinr=num./den; minimum=min(sinr); ex=exp(-(sinr-minimum)/smoothing); weights=ex/rsum(ex);
residual=zeros(1,K);
for k=1:K, residual(k)=rsum(p.*leak(:,:,k))-limit(k); end
value=minimum-smoothing*log(rsum(ex))-rsum(residual.^2);
theta=zeros(U,M); dnall=zeros(U,M,U); ddall=zeros(U,M,U); dsall=zeros(U,M,U); penalty=zeros(U,M);
for v=1:U
    for coordinate=1:M
        dns=cell(1,U); dds=cell(1,U); dls=cell(1,K);
        r=reshape(data.r_mean(v,:),M,1); geoA=reshape(data.geo_G_mean(v,:),M,1).*reshape(phi(v,:),M,1);
        gm=data.geo_d_mean(v)+csum(geoA.*r); dg=1i*phi(v,coordinate)*data.geo_G_mean(v,coordinate)*r(coordinate);
        dds{v}(end+1)=2*real(conj(gm)*dg);
        for j=1:J
            mv=reshape(mean(j,v,:),N,1); av=reshape(A(j,v,:,:),N,M);
            d=1i*phi(v,coordinate)*reshape(data.G_mean(j,v,:,coordinate),N,1)*r(coordinate);
            dp=2*rdot(mv,d); dns{v}(end+1)=p(j,v)*2*power(j,v)*dp;
            if tts
                ar=av*r;
                own_der=rsum([4*rdot(mv,reshape(Cb(j,v,:,:),N,N)*d),2*Ev(j,v)*dp, ...
                    4*(N+1)*data.G_var(j,v)*data.r_var(v)*(rdot(d,mv)+rdot(ar,d))]);
            else, own_der=2*rdot(d,reshape(C(j,v,:,:),N,N)*mv);
            end
            dds{v}(end+1)=p(j,v)*own_der;
            for u=1:U
                for i=1:U
                    if i==u, continue; end
                    m_u=reshape(mean(j,u,:),N,1); m_i=reshape(mean(j,i,:),N,1); c=m_u'*m_i; db=0;
                    if u==v
                        db=db+2*real(conj(c)*(d'*m_i));
                        if tts, db=db+2*rdot(d,reshape(C(j,i,:,:),N,N)*mv); end
                    end
                    if i==v
                        db=db+2*rdot(d,reshape(C(j,u,:,:),N,N)*mv)+2*real(conj(c)*(m_u'*d));
                    end
                    dds{u}(end+1)=p(j,i)*db;
                end
            end
            for k=1:K, dls{k}(end+1)=p(j,v)*2*rdot(d,reshape(gt(j,k,:,:),N,N)*mv); end
        end
        dn=zeros(1,U); dd=zeros(1,U); for u=1:U, dn(u)=rsum(dns{u}); dd(u)=rsum(dds{u}); end
        ds=(dn.*den-num.*dd)./(den.^2); ls=zeros(1,K); for k=1:K, ls(k)=rsum(dls{k}); end
        pen=2*rsum(residual.*ls); theta(v,coordinate)=rsum(weights.*ds)-pen;
        dnall(v,coordinate,:)=reshape(dn,1,1,U); ddall(v,coordinate,:)=reshape(dd,1,1,U);
        dsall(v,coordinate,:)=reshape(ds,1,1,U); penalty(v,coordinate)=pen;
    end
end
out=terms; out.criterion=value; out.gradient=1i*phi.*theta; out.theta_gradient=theta;
out.numerator=num; out.denominator=den; out.sinr=sinr; out.weights=weights; out.weights_applicable=true;
out.residual=residual; out.signal=signal; out.cross=cross; out.own_interference=own;
out.power=power; out.leakage=leak; out.dnumerator=dnall; out.ddenominator=ddall;
out.dsinr=dsall; out.penalty_theta=penalty; out.mode=mode;
out.AP_individual_SINR_not_MR_softmin=false;
end

function terms=moments(data,phi)
[J,U,N]=size(data.d_mean); M=size(phi,2);
mean=complex(zeros(J,U,N)); C=complex(zeros(J,U,N,N)); Q=C; A=complex(zeros(J,U,N,M)); Cb=C;
Ev=zeros(J,U); power=zeros(J,U); own=zeros(J,U); fourth=zeros(J,U); offset=zeros(1,U);
for j=1:J
    for u=1:U
        rv=data.r_var(u); dv=data.d_var(j,u); gv=data.G_var(j,u);
        assert(all(isfinite([rv,dv,gv])) && min([rv,dv,gv])>=0);
        a=reshape(data.G_mean(j,u,:,:),N,M).*phi(u,:); r=reshape(data.r_mean(u,:),M,1);
        mu=reshape(data.d_mean(j,u,:),N,1)+a*r;
        f=n2(a); r2=n2(r); m2=n2(mu); er2=r2+M*rv; er4=er2^2+M*rv^2+2*rv*r2;
        ev=dv+gv*er2; cb=(rv*a)*a'; covariance=cb+ev*eye(N);
        eb2=m2+rv*f; ev2=dv^2+2*dv*gv*er2+gv^2*er4;
        wick=n2(r*mu'+rv*a')+M*rv*m2+rv*r2*f+M*rv^2*f;
        t=a'*a+N*gv*eye(M);
        ownvar=rsum([rv^2*n2(t),2*rv*n2(a'*mu+N*gv*r),N*ev2,2*dv*eb2,2*gv*wick]);
        q=eb2+N*ev;
        A(j,u,:,:)=reshape(a,1,1,N,M); mean(j,u,:)=reshape(mu,1,1,N);
        Cb(j,u,:,:)=reshape(cb,1,1,N,N); C(j,u,:,:)=reshape(covariance,1,1,N,N);
        Q(j,u,:,:)=reshape(covariance+mu*mu',1,1,N,N);
        Ev(j,u)=ev; power(j,u)=q; own(j,u)=ownvar; fourth(j,u)=q^2+ownvar;
    end
end
for u=1:U
    r=reshape(data.r_mean(u,:),M,1); rv=data.r_var(u);
    ga=reshape(data.geo_G_mean(u,:),M,1).*reshape(phi(u,:),M,1);
    gm=data.geo_d_mean(u)+csum(ga.*r);
    offset(u)=rsum([1,data.geo_d_var(u),data.geo_G_var(u)*(n2(r)+M*rv),rv*n2(ga),abs(gm)^2]);
end
terms=struct('mean',mean,'C',C,'Q',Q,'A',A,'Cb',Cb,'Ev',Ev, ...
    'tts_power',power,'tts_own',own,'fourth',fourth,'offset',offset);
end

function value=n2(a), value=rsum(abs(a(:)).^2); end
function value=rdot(a,b), value=rsum(real(conj(a(:)).*b(:))); end
function value=csum(a), value=complex(rsum(real(a)),rsum(imag(a))); end
function value=rsum(a)
% Neumaier binary64 accumulation: precision control, same mathematical sum.
s=0; c=0; a=a(:);
for k=1:numel(a)
    x=a(k); t=s+x;
    if abs(s)>=abs(x), c=c+((s-t)+x); else, c=c+((x-t)+s); end
    s=t;
end
value=s+c;
end
