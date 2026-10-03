function [c,nlos,t]=corrected_zf_context_matlab(job,config)
% Reconstruct original dimensional model; exported draws are never resampled.
assert(config.geometry_realizations==100&&config.nlos_realizations_per_geometry==1000);
N=job.N;M=job.M;c=config;c.wavelength=1;c.minimum_distance=.5;c.power=job.power;c.noise=ones(M,1)*1e-11;c.rician=ones(M,1)*job.kappa;
factor=config.antenna_factorization.(matlab.lang.makeValidName(num2str(N)));nr=factor(1);nc=factor(2);
c.region_lower=[-nr*job.A/2;-nc*job.A/2];c.region_upper=[nr*job.A/2;nc*job.A/2];
c.beta=1e-4*job.geometry.distances_m(:).^(-2.8);theta=job.geometry.elevation(:);phi=job.geometry.azimuth(:);c.directions=[cos(theta).*sin(phi),sin(theta)];
t=zeros(N,2);index=1;for x=((0:nr-1)-(nr-1)/2)/2,for y=((0:nc-1)-(nc-1)/2)/2,t(index,:)=[x y];index=index+1;end,end
if isfield(job,'initial_positions'),t=job.initial_positions;end
if isfield(job,'region_lower'),c.region_lower=job.region_lower;c.region_upper=job.region_upper;end
nlos=job.nlos_re+1i*job.nlos_im;assert(isequal(size(nlos),[1000 N M]));
end
