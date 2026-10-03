function result=test_correlated_zf_matlab(outputPath)
% Analytic component checks, not an original MC paper figure.
centralError=0;quadratureError=0;
for r=[2 3 4 6],[value,error]=correlated_zf_inverse_moment(zeros(r,1),.7*eye(r));centralError=max(centralError,abs(value-1/(.7*(r-1))));quadratureError=max(quadratureError,error);end
mu=[.3+.2i;-.5+.1i];C=[.7 .1i;-.1i .4];Q=[1 1i;1i 1]/sqrt(2);
base=correlated_zf_inverse_moment(mu,C);rotated=correlated_zf_inverse_moment(Q*mu,Q*C*Q');scaled=correlated_zf_inverse_moment(3*mu,9*C);
indices=1:30;H=reshape(cos(indices.^2*.73)+1i*sin(indices.^2*1.17),6,5);assert(rank(H)==5,'Deterministic test fixture must have full column rank');G=H'*H;inverse=G\eye(5);schurError=0;
for user=1:5,[q,~]=qr(H(:,[1:user-1,user+1:5]));projection=q(:,5:end)'*H(:,user);schurError=max(schurError,abs(real(inverse(user,user))-1/real(projection'*projection)));end
checks=struct('central_iid_Wishart_limit_error',centralError,'unitary_invariance_error',abs(base-rotated),'scale_invariance_error',abs(base/9-scaled),'full_N6_M5_Schur_identity_error',schurError,'maximum_quadrature_error',quadratureError);
assert(centralError<1e-9&&abs(base-rotated)<1e-10&&abs(base/9-scaled)<1e-10&&schurError<1e-8,'Analytic inverse moment checks failed');
result=struct('scope','exact_original_correlated_channel_Jensen_identity_tests_not_paper_figure','checks',checks,'all_passed',true,'printed_Eq74_closed_form_recovered',false);
if nargin>0,folder=fileparts(outputPath);if ~isempty(folder)&&~isfolder(folder),mkdir(folder);end;fid=fopen(outputPath,'w','n','UTF-8');assert(fid>=0);cleaner=onCleanup(@()fclose(fid));fprintf(fid,'%s',jsonencode(result,'PrettyPrint',true));end
end
