function out=ma_theory_native_original_bridge_v1(action,config,job,varargin)
% Original native physical context; optional final1000 is explicit and separate.
[c,t]=ma_scenario(config,job.N,job.M,job.kappa,job.power,job.A,job.geometry);
if isfield(job,'initial_positions'),t=job.initial_positions;end
if isfield(job,'region_lower'),c.region_lower=job.region_lower(:);c.region_upper=job.region_upper(:);end
if strcmp(action,'context')
    out=struct('c',c,'original_initial_positions',t);return;
end
assert(strcmp(action,'final1000'),'MAExact:Bridge','Only native context or explicit post-search final1000 supported.');
positions=varargin{1};mode=varargin{2};nlos=job.nlos_re+1i*job.nlos_im;
assert(size(nlos,1)==1000&&config.nlos_realizations_per_geometry==1000,'MAExact:Population','Only full original1000 final performance evaluation.');
out=ma_instantaneous(positions,c,nlos,mode,false);
end

function [c,t]=ma_scenario(config,N,M,kappa,power,A,geometry)
c=config;field=matlab.lang.makeValidName(num2str(N));if ~isfield(config.antenna_factorization,field),error('Explicit factorization needed.');end
factor=config.antenna_factorization.(field);nr=factor(1);nc=factor(2);
c.wavelength=1;c.minimum_distance=0.5;c.power=power;c.noise=ones(M,1)*1e-11;c.region_lower=[-nr*A/2;-nc*A/2];c.region_upper=-c.region_lower;c.rician=ones(M,1)*kappa;
theta=geometry.elevation(:);phi=geometry.azimuth(:);c.directions=[cos(theta).*sin(phi),sin(theta)];c.beta=1e-4*geometry.distances_m(:).^(-2.8);
x=((0:nr-1)-(nr-1)/2)/2;y=((0:nc-1)-(nc-1)/2)/2;t=zeros(N,2);index=1;
for a=x,for b=y,t(index,:)=[a,b];index=index+1;end,end
end

function H=ma_los(t,c)
H=exp(2i*pi/c.wavelength*(t*c.directions'));
end

function S=ma_covariance(t,c)
distance=sqrt(sum((reshape(t,size(t,1),1,2)-reshape(t,1,size(t,1),2)).^2,3));S=besselj(0,2*pi*distance/c.wavelength);
end

function out=ma_instantaneous(t,c,nlos,mode,correlated)
if nargin<5,correlated=false;end
Hbar=ma_los(t,c);[N,M]=size(Hbar);sampleCount=size(nlos,1);rates=zeros(1,sampleCount);powers=rates;leakage=rates;
root=eye(N);if correlated,S=ma_covariance(t,c);[V,L]=eig((S+S')/2);lambda=real(diag(L));if min(lambda)<-c.verification_tolerance,error('Bessel covariance not PSD.');end;root=V*diag(sqrt(max(lambda,0)))*V';end
for index=1:sampleCount
    sample=root*reshape(nlos(index,:,:),N,M);H=Hbar.*sqrt(c.beta(:).*c.rician(:)./(c.rician(:)+1))'+sample.*sqrt(c.beta(:)./(c.rician(:)+1))';
    if strcmp(mode,'MRT'),W=H*sqrt(c.power/sum(abs(H(:)).^2));else,V=H/(H'*H);W=V./vecnorm(V,2,1)*sqrt(c.power/M);end
    gain=abs(H'*W).^2;signal=diag(gain);rates(index)=sum(log2(1+signal./(sum(gain,2)-signal+c.noise(:))));powers(index)=sum(abs(W(:)).^2);
    hw=H'*W;off=hw-diag(diag(hw));leakage(index)=max(abs(off(:)));
end
out=struct('sample_sum_rates',rates,'mean_sum_rate',mean(rates),'powers',powers,'off_diagonal_amplitude',leakage);
end

