function value=strict_satcom_increments(action,varargin)
% Exact original AP/MR stable objective differences; no altered phase objective.
switch action
    case 'ap',value=ap_increment(varargin{:});
    case 'mr',value=mr_increment(varargin{:});
    otherwise,error('Unknown original objective increment');
end
end

function y=square_increment(x,dx)
y=2*real(conj(x).*dx)+abs(dx).^2;
end

function y=quadratic_increment(x,dx,Q)
y=2*real(x'*Q*dx)+real(dx'*Q*dx);
end

function [dm,doo]=mean_changes(data,old,new)
[J,U,N]=size(data.d_mean);M=size(old,2);dm=complex(zeros(J,U,N));doo=zeros(U,1);
for u=1:U
    for j=1:J,G=reshape(data.G_mean(j,u,:,:),N,M);dm(j,u,:)=G*(data.r_mean(u,:).'.*(new(u,:).'-old(u,:).'));end
    geo=data.geo_d_mean(u)+sum(data.geo_G_mean(u,:).*old(u,:).*data.r_mean(u,:));
    dgeo=sum(data.geo_G_mean(u,:).*(new(u,:)-old(u,:)).*data.r_mean(u,:));doo(u)=square_increment(geo,dgeo);
end
end

function value=ap_increment(data,old,new,W)
[means,C,~,~,offset]=strict_satcom_models('moments',data,old);[dm,doo]=mean_changes(data,old,new);
[J,U,N]=size(means);numerator=zeros(U,1);den=offset;dn=zeros(U,1);dd=doo;
for u=1:U
    for j=1:J
        m=reshape(means(j,u,:),N,1);d=reshape(dm(j,u,:),N,1);wj=reshape(W(j,:,:),N,U);projected=m'*wj;change=square_increment(projected,d'*wj);
        numerator(u)=numerator(u)+abs(projected(u))^2;dn(u)=dn(u)+change(u);cu=reshape(C(j,u,:,:),N,N);
        den(u)=den(u)+sum(real(sum(conj(wj).*(cu*wj),1)))+sum(abs(projected).^2)-abs(projected(u))^2;
        dd(u)=dd(u)+sum(change)-change(u);
    end
end
value=(dn.*den-numerator.*dd)./(den.*(den+dd));
end

function value=mr_increment(data,old,new,p,smoothing,limit,tts)
c=strict_satcom_models('mr_components',data,old,tts);[~,C]=strict_satcom_models('moments',data,old);[dm,doo]=mean_changes(data,old,new);
[J,U,N]=size(c.mean);M=size(old,2);K=size(c.leak,3);dQ=complex(zeros(size(c.second)));ds=zeros(size(c.signal));db=zeros(size(c.cross));dl=zeros(size(c.leak));
for j=1:J
    df=zeros(U,1);
    for u=1:U
        m=reshape(c.mean(j,u,:),N,1);d=reshape(dm(j,u,:),N,1);dp=sum(square_increment(m,d));dQ(j,u,:,:)=m*d'+d*m'+d*d';ds(j,u)=2*c.power(j,u)*dp+dp^2;
        if tts
            G=reshape(data.G_mean(j,u,:,:),N,M);r=data.r_mean(u,:).';rv=data.r_var(u);Cb=rv*(G*G');er2=real(r'*r)+M*rv;eb2=real(m'*m)+real(trace(Cb));
            deb4=2*eb2*dp+dp^2+2*quadratic_increment(m,d,Cb);ar=m-reshape(data.d_mean(j,u,:),N,1);
            der2b2=er2*dp+2*rv*real(ar'*d+d'*m+d'*d);
            df(u)=deb4+2*(N+1)*(data.d_var(j,u)*dp+data.G_var(j,u)*der2b2);
        end
        for k=1:K,dl(j,u,k)=quadratic_increment(m,d,reshape(data.gt_second(j,k,:,:),N,N));end
    end
    for u=1:U
        for i=1:U
            if tts
                if i==u,db(j,u,i)=df(u);else
                    qu=reshape(c.second(j,u,:,:),N,N);qi=reshape(c.second(j,i,:,:),N,N);dqu=reshape(dQ(j,u,:,:),N,N);dqi=reshape(dQ(j,i,:,:),N,N);
                    db(j,u,i)=real(trace(dqu*qi+qu*dqi+dqu*dqi));
                end
            else
                m=reshape(c.mean(j,u,:),N,1);mi=reshape(c.mean(j,i,:),N,1);d=reshape(dm(j,u,:),N,1);di=reshape(dm(j,i,:),N,1);
                a=m'*mi;da=m'*di+d'*mi+d'*di;db(j,u,i)=square_increment(a,da)+quadratic_increment(mi,di,reshape(C(j,u,:,:),N,N));
            end
        end
    end
end
num=sum(p.*c.signal,1).';den=c.offset;dn=sum(p.*ds,1).';dd=doo;
for u=1:U,den(u)=den(u)+sum(sum(p.*reshape(c.cross(:,u,:),J,U)))-num(u);dd(u)=dd(u)+sum(sum(p.*reshape(db(:,u,:),J,U)))-dn(u);end
dsn=(dn.*den-num.*dd)./(den.*(den+dd));snr=num./den;centered=-(snr-min(snr))/smoothing;
logweights=centered-log(sum(exp(centered)));weights=exp(logweights);t=-dsn/smoothing;
if max(abs(t))<50,soft=-smoothing*log1p(weights.'*expm1(t));else,z=logweights+t;maximum=max(z);soft=-smoothing*(maximum+log(sum(exp(z-maximum))));end
res=zeros(K,1);dleak=res;for k=1:K,res(k)=sum(sum(p.*c.leak(:,:,k)))-limit(k);dleak(k)=sum(sum(p.*dl(:,:,k)));end
value=soft-sum(2*res.*dleak+dleak.^2);
end
