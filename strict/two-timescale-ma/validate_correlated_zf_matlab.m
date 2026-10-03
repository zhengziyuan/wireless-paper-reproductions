function result=validate_correlated_zf_matlab(outputPath,jobPath,configPath)
% Paired original N/M model and all1000 exported draws, not a full figure.
config=jsondecode(fileread(configPath));job=jsondecode(fileread(jobPath));N=job.N;M=job.M;
assert(config.nlos_realizations_per_geometry==1000&&size(job.nlos_re,1)==1000,'All1000 original draws required');
c=config;c.wavelength=1;c.power=job.power;c.noise=ones(M,1)*1e-11;c.rician=ones(M,1)*job.kappa;
c.beta=1e-4*job.geometry.distances_m(:).^(-2.8);theta=job.geometry.elevation(:);phi=job.geometry.azimuth(:);c.directions=[cos(theta).*sin(phi),sin(theta)];
factor=config.antenna_factorization.(matlab.lang.makeValidName(num2str(N)));nr=factor(1);nc=factor(2);t=zeros(N,2);index=1;
for x=((0:nr-1)-(nr-1)/2)/2,for y=((0:nc-1)-(nc-1)/2)/2,t(index,:)=[x y];index=index+1;end,end
if isfield(job,'initial_positions'),t=job.initial_positions;end
nlos=job.nlos_re+1i*job.nlos_im;bound=correlated_zf_jensen_bound(t,c,nlos);
distance=sqrt(sum((reshape(t,N,1,2)-reshape(t,1,N,2)).^2,3));S=besselj(0,2*pi*distance);[V,D]=eig(S,'vector');assert(all(real(D)>0));root=(V.*sqrt(real(D)).')*V';
kap=c.rician(:).';mu=exp(2i*pi*t*c.directions.').*sqrt(kap./(kap+1));inverseSamples=zeros(1000,M);rates=zeros(1000,1);schurError=0;
for sample=1:1000
X=mu+(root*reshape(nlos(sample,:,:),N,M))./sqrt(kap+1);inverse=(X'*X)\eye(M);inverseSamples(sample,:)=real(diag(inverse)).';
for user=1:M,[Q,~]=qr(X(:,[1:user-1,user+1:M]));z=Q(:,M:end)'*X(:,user);schurError=max(schurError,abs(real(inverse(user,user))-1/real(z'*z)));end
H=X.*sqrt(c.beta(:).');Z=H/(H'*H);W=Z./vecnorm(Z,2,1)*sqrt(c.power/M);gain=abs(H'*W).^2;signal=diag(gain);rates(sample)=sum(log2(1+signal./(sum(gain,2)-signal+c.noise(:))));
end
checks=struct('full1000_used',true,'Schur_identity_all5000_pass',schurError<1e-8,'source_row_covariance_unchanged',true,'no_Wishart_surrogate',true);assert(checks.Schur_identity_all5000_pass);
result=struct('paper_id','two-timescale-ma','mode','full1000_draw_original_model_identity_not_full_figure','N',N,'M',M,'positions',t,'outer_ensemble_count',1000,...
    'conditional_exact_Jensen_evaluator',bound,'actual_correlated_ZF',struct('sample_sum_rates',rates,'mean_sum_rate',mean(rates)),...
    'direct_MC_inverse_diagonal_mean',mean(inverseSamples,1),'direct_MC_inverse_diagonal_standard_error',std(inverseSamples,0,1)/sqrt(1000),...
    'maximum_Schur_identity_error_over_all1000_draws_and_users',schurError,'checks',checks,'printed_Eq74_closed_form_recovered',false,'original_figure_reproduction_certified',false);
folder=fileparts(outputPath);if ~isempty(folder)&&~isfolder(folder),mkdir(folder);end
fid=fopen(outputPath,'w','n','UTF-8');assert(fid>=0);cleaner=onCleanup(@()fclose(fid));fprintf(fid,'%s',jsonencode(result,'PrettyPrint',true));
end
