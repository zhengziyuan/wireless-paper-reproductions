function result=corrected_zf_position_matlab(t,c,nlos)
% Independent full1000 exact-original-model evidence, no position optimizer.
N=size(t,1);M=numel(c.beta);assert(N>M&&isequal(size(t),[N 2])&&all(isfinite(t),'all'));
assert(c.nlos_realizations_per_geometry==1000&&isequal(size(nlos),[1000 N M]),'All1000 exported draws required');
distance=sqrt(sum((reshape(t,N,1,2)-reshape(t,1,N,2)).^2,3))+eye(N)*1e9;
assert(min(distance,[],'all')>=c.minimum_distance-c.verification_tolerance);
assert(all(t>=c.region_lower(:).'-c.verification_tolerance,'all')&&all(t<=c.region_upper(:).'+c.verification_tolerance,'all'));
iid=evaluate_model(false);correlated=evaluate_model(true);
kap=c.rician(:);hbar=exp(2i*pi/c.wavelength*(t*c.directions.'));
omega=diag(1./(kap+1));a=sqrt(kap./(kap+1));sigma=omega+(hbar'*hbar).*(a*a.')/N;
eta=c.power*c.beta(:)*(N-M)./(M*c.noise(:));ratio=1./real(diag(sigma\eye(M)));design=sum(log2(1+eta.*ratio));
result=struct('positions',t,'nlos_samples',1000,'models',struct('iid',iid,'correlated',correlated),...
    'original_iid_Algorithm2_statistical_design_objective',design,...
    'iid_design_objective_is_source_noncentral_Wishart_approximation_not_exact_inverse_moment',true,...
    'trajectory_position_reoptimized',false,'original_covariance_or_power_model_changed',false,...
    'printed_Eq74_75_recovered',false,'original_curve_closeness_verified',false);
    function out=evaluate_model(useCorrelation)
        if useCorrelation
            ds=sqrt(sum((reshape(t,N,1,2)-reshape(t,1,N,2)).^2,3));S=besselj(0,2*pi/c.wavelength*ds);model='Eq68_spatially_correlated';
        else,S=eye(N);model='Eq1_4_iid';end
        [V,D]=eig(S,'vector');assert(all(real(D)>0),'No covariance ridge or clipping');root=(V.*sqrt(real(D)).')*V';
        k=c.rician(:).';mu=exp(2i*pi/c.wavelength*(t*c.directions.')).*sqrt(k./(k+1));
        diagonal=zeros(1000,M);rates=zeros(1000,1);powers=zeros(1000,1);leakage=zeros(1000,1);schurError=0;rateError=0;
        aa=c.power*c.beta(:).'./(M*c.noise(:).');
        for sample=1:1000
            X=mu+(root*reshape(nlos(sample,:,:),N,M))./sqrt(k+1);inverse=(X'*X)\eye(M);diagonal(sample,:)=real(diag(inverse)).';
            assert(all(isfinite(diagonal(sample,:)))&&all(diagonal(sample,:)>0));
            for user=1:M
                [Q,~]=qr(X(:,[1:user-1,user+1:M]));projected=Q(:,M:end)'*X(:,user);s=1/real(projected'*projected);
                error=abs(s-diagonal(sample,user));schurError=max(schurError,error);assert(error<=1e-10+1e-8*abs(diagonal(sample,user)));
            end
            H=X.*sqrt(c.beta(:).');Z=H/(H'*H);W=Z./vecnorm(Z,2,1)*sqrt(c.power/M);
            HW=H'*W;gain=abs(HW).^2;signal=diag(gain);rates(sample)=sum(log2(1+signal./(sum(gain,2)-signal+c.noise(:))));
            identity=sum(log2(1+aa./diagonal(sample,:)));error=abs(identity-rates(sample));rateError=max(rateError,error);assert(error<=1e-9+1e-9*abs(rates(sample)));
            powers(sample)=sum(abs(W).^2,'all');leakage(sample)=max(abs(HW-diag(diag(HW))),[],'all');
        end
        bound=correlated_zf_jensen_bound(t,c,nlos,useCorrelation);moment=bound.mean_inverse_normalized_Gram_diagonal;
        derivative=aa./(log(2)*moment.*(moment+aa));quadError=sum(derivative.*bound.mean_quadrature_error_estimate_per_user);
        deltaSE=std(bound.conditional_inverse_moment_samples*derivative(:),0,1)/sqrt(1000);
        actual=struct('sample_sum_rates',rates,'mean_sum_rate',mean(rates),'powers',powers,'off_diagonal_amplitude',leakage);
        out=struct('channel_model',model,'actual_full1000_MC',actual,'MC_standard_error_within_geometry',std(rates)/sqrt(1000),...
            'exact_original_model_Jensen',bound,'MC_minus_population_Jensen_plugin',mean(rates)-bound.sum_rate,...
            'population_Jensen_rate_quadrature_error_estimate_first_order',quadError,...
            'population_Jensen_rate_outer_MC_standard_error_delta_method',deltaSE,...
            'direct_MC_inverse_diagonal_samples',diagonal,'direct_MC_inverse_diagonal_mean',mean(diagonal,1),...
            'direct_MC_inverse_diagonal_standard_error',std(diagonal,0,1)/sqrt(1000),...
            'maximum_Schur_identity_absolute_error',schurError,'maximum_ZF_beamformer_inverse_Gram_rate_identity_error',rateError,...
            'minimum_original_covariance_eigenvalue',min(real(D)),'all1000_times_M_Schur_identities_pass',true,...
            'all1000_ZF_beamformer_rate_identities_pass',true,'quadrature_error_is_reported_estimate_not_interval_certificate',true,...
            'rate_error_delta_method_is_not_a_confidence_interval',true,'finite_ensemble_bound_guaranteed',false);
    end
end
