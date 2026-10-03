function varargout=strict_satcom_models(action,varargin)
% Author/thesis model, exact finite-Rician moments and analytic circle derivatives.
switch action
    case 'moments', [varargout{1:nargout}]=channel_moments(varargin{:});
    case 'mr_components', [varargout{1:nargout}]=mr_components(varargin{:});
    case 'mr_phase', [varargout{1:nargout}]=mr_phase(varargin{:});
    case 'ap_phase', [varargout{1:nargout}]=ap_phase(varargin{:});
    case 'mr_phase_reference', [varargout{1:nargout}]=mr_phase_reference(varargin{:});
    case 'ap_phase_reference', [varargout{1:nargout}]=ap_phase_reference(varargin{:});
    otherwise, error('Unknown model action');
end
end

function [mu,C,Q,fourth,offset]=channel_moments(data,phi,noRis)
if nargin<3, noRis=false; end
[J,U,N]=size(data.d_mean); M=size(data.r_mean,2); mu=complex(zeros(J,U,N)); C=complex(zeros(J,U,N,N)); Q=C;
fourth=zeros(J,U); offset=ones(U,1);
for u=1:U
    for j=1:J
        G=reshape(data.G_mean(j,u,:,:),N,M); Gvar=data.G_var(j,u);
        if noRis, G=0*G; Gvar=0; end
        q=strict_satcom_core('moments',reshape(data.d_mean(j,u,:),N,1),data.d_var(j,u), ...
            G,Gvar,data.r_mean(u,:),data.r_var(u),phi(u,:));
        mu(j,u,:)=q.mean; C(j,u,:,:)=q.covariance; Q(j,u,:,:)=q.second; fourth(j,u)=q.norm_fourth;
    end
    G=data.geo_G_mean(u,:); Gvar=data.geo_G_var(u); if noRis, G=G*0; Gvar=0; end
    g=strict_satcom_core('moments',data.geo_d_mean(u),data.geo_d_var(u),G,Gvar,data.r_mean(u,:),data.r_var(u),phi(u,:));
    offset(u)=offset(u)+real(g.second(1,1));
end
end

function [dm,dQ,dfourth,doffset]=direction(data,phi,mu,u,m)
[J,U,N]=size(mu); M=size(phi,2); dm=complex(zeros(size(mu))); dQ=complex(zeros(J,U,N,N)); dfourth=zeros(J,U);
for j=1:J
    G=reshape(data.G_mean(j,u,:,:),N,M); r=data.r_mean(u,:).'; rv=data.r_var(u);
    mean=reshape(mu(j,u,:),N,1); d=1i*phi(u,m)*G(:,m)*r(m); dm(j,u,:)=d;
    dQ(j,u,:,:)=d*mean'+mean*d'; Cb=rv*(G*G'); er2=real(r'*r)+M*rv;
    eb2=real(mean'*mean)+real(trace(Cb)); deb2=2*real(mean'*d);
    deb4=2*eb2*deb2+4*real(mean'*Cb*d); ar=mean-reshape(data.d_mean(j,u,:),N,1);
    der2b2=er2*deb2+2*rv*real(d'*mean+ar'*d);
    devb2=data.d_var(j,u)*deb2+data.G_var(j,u)*der2b2;
    dfourth(j,u)=deb4+2*(N+1)*devb2;
end
geoMean=data.geo_d_mean(u)+sum(data.geo_G_mean(u,:).*phi(u,:).*data.r_mean(u,:));
dgeo=1i*phi(u,m)*data.geo_G_mean(u,m)*data.r_mean(u,m);
doffset=zeros(U,1); doffset(u)=2*real(conj(geoMean)*dgeo);
end

function coef=mr_components(data,phi,tts,noRis)
if nargin<4, noRis=false; end
[mu,C,Q,fourth,offset]=channel_moments(data,phi,noRis);
if tts, [s,b,p,l]=strict_satcom_core('tts_mr_coefficients',Q,fourth,data.gt_second);
else, [s,b,p,l]=strict_satcom_core('statistical_mr_coefficients',mu,Q,data.gt_second); end
coef=struct('signal',s,'cross',b,'power',p,'leak',l,'offset',offset,'mean',mu,'second',Q,'fourth',fourth);
end

function [value,g]=mr_phase_reference(data,phi,p,smoothing,limit,tts)
coef=mr_components(data,phi,tts); mu=coef.mean; Q=coef.second; power=coef.power; l=coef.leak;
[J,U,N]=size(mu); M=size(phi,2); K=size(l,3);
numerator=sum(p.*coef.signal,1).'; den=coef.offset;
for u=1:U, den(u)=den(u)+sum(sum(p.*reshape(coef.cross(:,u,:),J,U)))-numerator(u); end
snr=numerator./den; minimum=min(snr); ex=exp(-(snr-minimum)/smoothing); weights=ex/sum(ex);
leakage=zeros(K,1); for k=1:K, leakage(k)=sum(sum(p.*l(:,:,k))); end
residual=leakage-limit(:); value=minimum-smoothing*log(sum(ex))-sum(residual.^2); gt=zeros(U,M);
for v=1:U
    for m=1:M
        [dm,dQ,df,doo]=direction(data,phi,mu,v,m); ds=zeros(J,U); db=zeros(J,U,U); dl=zeros(size(l));
        for j=1:J
            for u=1:U
                qu=reshape(Q(j,u,:,:),N,N); dqu=reshape(dQ(j,u,:,:),N,N);
                muu=reshape(mu(j,u,:),N,1); dmu=reshape(dm(j,u,:),N,1);
                if tts
                    dp=real(trace(dqu)); ds(j,u)=2*power(j,u)*dp;
                    for i=1:U
                        if i==u, db(j,u,i)=df(j,u);
                        else, db(j,u,i)=real(trace(dqu*reshape(Q(j,i,:,:),N,N)+qu*reshape(dQ(j,i,:,:),N,N))); end
                    end
                    for k=1:K, dl(j,u,k)=real(trace(reshape(data.gt_second(j,k,:,:),N,N)*dqu)); end
                else
                    dp=2*real(muu'*dmu); ds(j,u)=2*power(j,u)*dp;
                    for i=1:U
                        mi=reshape(mu(j,i,:),N,1); di=reshape(dm(j,i,:),N,1);
                        db(j,u,i)=2*real(di'*qu*mi)+real(mi'*dqu*mi);
                    end
                    for k=1:K, dl(j,u,k)=2*real(dmu'*reshape(data.gt_second(j,k,:,:),N,N)*muu); end
                end
            end
        end
        dn=sum(p.*ds,1).'; dd=doo;
        for u=1:U, dd(u)=dd(u)+sum(sum(p.*reshape(db(:,u,:),J,U)))-dn(u); end
        dsnr=(dn.*den-numerator.*dd)./den.^2; dleak=zeros(K,1);
        for k=1:K, dleak(k)=sum(sum(p.*dl(:,:,k))); end
        gt(v,m)=weights.'*dsnr-2*residual.'*dleak;
    end
end
g=1i*phi.*gt;
end

function [snr,g]=ap_phase_reference(data,phi,W)
[mu,C,Q,~,offset]=channel_moments(data,phi); [J,U,N]=size(mu); M=size(phi,2);
numerator=zeros(U,1); den=offset;
for u=1:U
    for j=1:J
        m=reshape(mu(j,u,:),N,1); numerator(u)=numerator(u)+abs(m'*reshape(W(j,:,u),N,1))^2;
        for i=1:U
            if i==u, qi=reshape(C(j,u,:,:),N,N); else, qi=reshape(Q(j,u,:,:),N,N); end
            w=reshape(W(j,:,i),N,1); den(u)=den(u)+real(w'*qi*w);
        end
    end
end
snr=numerator./den; gt=zeros(U,M);
for u=1:U
    for m=1:M
        [dm,dQ,~,doo]=direction(data,phi,mu,u,m); dn=0; dd=doo(u);
        for j=1:J
            mean=reshape(mu(j,u,:),N,1); d=reshape(dm(j,u,:),N,1); w=reshape(W(j,:,u),N,1);
            a=mean'*w; da=d'*w; dn=dn+2*real(conj(a)*da);
            for i=1:U
                if i~=u, w=reshape(W(j,:,i),N,1); dd=dd+real(w'*reshape(dQ(j,u,:,:),N,N)*w); end
            end
        end
        gt(u,m)=(dn*den(u)-numerator(u)*dd)/den(u)^2;
    end
end
g=1i*phi.*gt;
end

function [value,g]=mr_phase(data,phi,p,smoothing,limit,tts)
% Exact all-coordinate contraction. The scalar-coordinate oracle remains above.
coef=mr_components(data,phi,tts);means=coef.mean;Q=coef.second;power=coef.power;l=coef.leak;
[J,U,N]=size(means);M=size(phi,2);K=size(l,3);numerator=sum(p.*coef.signal,1).';den=coef.offset;
for u=1:U,den(u)=den(u)+sum(sum(p.*reshape(coef.cross(:,u,:),J,U)))-numerator(u);end
snr=numerator./den;minimum=min(snr);ex=exp(-(snr-minimum)/smoothing);weights=ex/sum(ex);
leak=zeros(K,1);for k=1:K,leak(k)=sum(sum(p.*l(:,:,k)));end
residual=leak-limit(:);value=minimum-smoothing*log(sum(ex))-sum(residual.^2);theta=zeros(U,M);
for v=1:U
    dn=zeros(U,M);dd=zeros(U,M);dleak=zeros(K,M);
    geo=data.geo_d_mean(v)+sum(data.geo_G_mean(v,:).*phi(v,:).*data.r_mean(v,:));
    dd(v,:)=2*real(conj(geo)*1i*phi(v,:).*data.geo_G_mean(v,:).*data.r_mean(v,:));
    for j=1:J
        G=reshape(data.G_mean(j,v,:,:),N,M);r=data.r_mean(v,:).';rv=data.r_var(v);mv=reshape(means(j,v,:),N,1);
        D=G.*(1i*phi(v,:).*r.');dp=2*real(mv'*D);dn(v,:)=dn(v,:)+p(j,v)*2*power(j,v)*dp;
        if tts
            Cb=rv*(G*G');er2=real(r'*r)+M*rv;eb2=real(mv'*mv)+real(trace(Cb));deb4=2*eb2*dp+4*real(mv'*Cb*D);
            ar=mv-reshape(data.d_mean(j,v,:),N,1);der2b2=er2*dp+2*rv*real((D'*mv).'+ar'*D);
            df=deb4+2*(N+1)*(data.d_var(j,v)*dp+data.G_var(j,v)*der2b2);
        end
        for u=1:U
            for i=1:U
                db=zeros(1,M);
                if tts
                    if u==i,if u==v,db=df;end
                    else
                        if u==v,db=db+2*real(mv'*reshape(Q(j,i,:,:),N,N)*D);end
                        if i==v,db=db+2*real(mv'*reshape(Q(j,u,:,:),N,N)*D);end
                    end
                else
                    if i==v,db=db+2*real((D'*reshape(Q(j,u,:,:),N,N)*mv).');end
                    if u==v,mi=reshape(means(j,i,:),N,1);a=mv'*mi;db=db+2*real(conj(a)*(D'*mi).');end
                end
                dd(u,:)=dd(u,:)+p(j,i)*db;
            end
        end
        for k=1:K,dleak(k,:)=dleak(k,:)+p(j,v)*2*real(mv'*reshape(data.gt_second(j,k,:,:),N,N)*D);end
    end
    dd=dd-dn;dsnr=(dn.*den-numerator.*dd)./den.^2;theta(v,:)=weights.'*dsnr-2*residual.'*dleak;
end
g=1i*phi.*theta;
end

function [snr,g]=ap_phase(data,phi,W)
[means,C,Q,~,offset]=channel_moments(data,phi);[J,U,N]=size(means);M=size(phi,2);
numerator=zeros(U,1);den=offset;theta=zeros(U,M);
for u=1:U
    dn=zeros(1,M);geo=data.geo_d_mean(u)+sum(data.geo_G_mean(u,:).*phi(u,:).*data.r_mean(u,:));
    dd=2*real(conj(geo)*1i*phi(u,:).*data.geo_G_mean(u,:).*data.r_mean(u,:));
    for j=1:J
        mean=reshape(means(j,u,:),N,1);wj=reshape(W(j,:,:),N,U);received=mean'*wj;
        D=reshape(data.G_mean(j,u,:,:),N,M).*(1i*phi(u,:).*data.r_mean(u,:));derivative=D'*wj;
        increments=2*real(conj(received).*derivative);numerator(u)=numerator(u)+abs(received(u))^2;dn=dn+increments(:,u).';
        for i=1:U
            if i==u,qi=reshape(C(j,u,:,:),N,N);else,qi=reshape(Q(j,u,:,:),N,N);end
            den(u)=den(u)+real(wj(:,i)'*qi*wj(:,i));
        end
        dd=dd+sum(increments,2).'-increments(:,u).';
    end
    theta(u,:)=(dn*den(u)-numerator(u)*dd)/den(u)^2;
end
snr=numerator./den;g=1i*phi.*theta;
end
