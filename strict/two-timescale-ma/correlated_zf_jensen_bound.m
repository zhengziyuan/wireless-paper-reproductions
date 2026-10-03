function result=correlated_zf_jensen_bound(t,c,nlos,spatialCorrelation)
% Exact Eq35/37 conditional inverse moment under the ORIGINAL row-correlated
% Eq68 channel. Full exported outer ensemble, no surrogate Wishart covariance.
if nargin<4,spatialCorrelation=true;end
N=size(t,1);M=numel(c.beta);count=size(nlos,1);
assert(N>M&&isequal(size(nlos),[count N M])&&count>0,'Full N>M ensemble required');
if isfield(c,'nlos_realizations_per_geometry'),assert(count==c.nlos_realizations_per_geometry,'Do not shorten configured ensemble');end
distance=sqrt(sum((reshape(t,N,1,2)-reshape(t,1,N,2)).^2,3));S=besselj(0,2*pi/c.wavelength*distance);
if ~spatialCorrelation,S=eye(N);end
[V,D]=eig(S,'vector');assert(all(real(D)>0),'No covariance ridge permitted');root=(V.*sqrt(real(D)).')*V';
kap=c.rician(:).';meanChannel=exp(2i*pi/c.wavelength*(t*c.directions.')).*sqrt(kap./(kap+1));conditional=zeros(count,M);errors=zeros(count,M);
for sample=1:count
U=reshape(nlos(sample,:,:),N,M);normalized=meanChannel+(root*U)./sqrt(kap+1);
for user=1:M
others=normalized(:,[1:user-1,user+1:M]);[Q,~]=qr(others);basis=Q(:,M:end);
mu=basis'*meanChannel(:,user);C=basis'*S*basis/(kap(user)+1);
[conditional(sample,user),errors(sample,user)]=correlated_zf_inverse_moment(mu,C);
end
end
moment=mean(conditional,1);rates=log2(1+c.power*c.beta(:).'./(M*c.noise(:).'.*moment));
sourceModel='Eq68_exact_row_covariance;Eq35_37_original_Jensen_bound_before_invalid_Eq71_Wishart_step';
if ~spatialCorrelation,sourceModel='Eq1_4_exact_iid_covariance;Eq35_37_Jensen_inverse_moment_without_noncentral_Wishart_approximation';end
result=struct('sum_rate',sum(rates),'per_user_rates',rates,'mean_inverse_normalized_Gram_diagonal',moment,'conditional_inverse_moment_samples',conditional,'inverse_moment_standard_error',std(conditional,0,1)/sqrt(count),'maximum_quadrature_error',max(errors,[],'all'),'conditional_quadrature_error_samples',errors,'mean_quadrature_error_estimate_per_user',mean(errors,1),'spatial_correlation',logical(spatialCorrelation),'outer_expectation_samples',count,'projected_complex_dimension',N-M+1,'method','exact_Schur_complement_conditional_Gaussian_Laplace_moment_then_full_exported_outer_ensemble','source_model',sourceModel,'modified_channel_or_Wishart_approximation',false,'printed_Eq74_closed_form_recovered',false,'original_curve_closeness_verified',false);
result.quadrature_controls=struct('version','segmented_same_Laplace_integral_v3','normalized_interval',[0 1],...
    'waypoints',[.25 .5 .75 .9 .99],'working_relative_tolerance',1e-12,...
    'working_absolute_tolerance','1e-12/(sum_covariance_eigenvalues_plus_mean_energy)',...
    'declared_accuracy_gate_relative_tolerance',1e-9,'subinterval_limit',500,...
    'reported_error_is_not_an_interval_certificate',true);
end
