function [value,error]=correlated_zf_inverse_moment(mu,C,relativeTolerance)
% Exact E[1/(z'*z)], z~CN(mu,C), not a replacement Wishart covariance.
if nargin<3,relativeTolerance=1e-9;end
mu=mu(:);r=numel(mu);assert(r>=2&&isequal(size(C),[r r]),'N>M projected dimension required');
assert(all(isfinite(mu))&&all(isfinite(C),'all')&&max(abs(C-C'),[],'all')<1e-11,'Finite Hermitian covariance required');
[V,D]=eig(C,'vector');assert(all(real(D)>0),'No covariance ridge is permitted');
d=real(D);a=abs(V'*mu).^2;scale=sum(d)+sum(a);lambda=d/scale;weights=a/scale;
f=@(x)kernel(x,lambda,weights,scale,r);
% Deterministic partition of the SAME Laplace integral. Working accuracy is
% tightened after independently verified endpoint-resolution failures; the
% declared acceptance gate, projected covariance and channel model stay fixed.
workingTolerance=min(1e-12,relativeTolerance/100);
[value,error]=quadgk(f,0,1,'Waypoints',[.25 .5 .75 .9 .99],...
    'RelTol',workingTolerance,'AbsTol',workingTolerance/scale,'MaxIntervalCount',500);
assert(isfinite(value)&&value>0&&error<=10*relativeTolerance*max(value,1/scale),'Quadrature accuracy failed');
end
function out=kernel(t,lambda,weights,scale,r)
originalSize=size(t);t=t(:).';out=zeros(size(t));inside=t<1;u=t(inside)./(1-t(inside));den=1+lambda.*u;
out(inside)=exp(-sum(log(den),1)-sum(u.*weights./den,1)-2*log1p(-t(inside))-log(scale));
if r==2,out(~inside)=exp(-sum(log(lambda))-sum(weights./lambda))/scale;end
out=reshape(out,originalSize);
end
