function result=strict_satcom_model_test(configPath,outputPath)
% Full geometry analytical gradient and finite-Rician tests, no convex/full MC run.
config=jsondecode(fileread(configPath)); [data,pl,il]=strict_satcom_scenario(config);
[U,M]=size(data.r_mean); phi=ones(U,1)*exp(1i*(0.2+0.01*(0:M-1))); errors=[]; apErrors=[];
for tts=[false,true]
    c=strict_satcom_models('mr_components',data,phi,tts); p=ones(size(c.power)); scale=1;
    for j=1:size(p,1), scale=min(scale,pl(j)/sum(c.power(j,:))); end
    for k=1:size(c.leak,3), total=sum(sum(c.leak(:,:,k))); if total>0, scale=min(scale,il(k)/total); end, end
    p=p*scale*0.95; [~,g]=strict_satcom_models('mr_phase',data,phi,p,1,il,tts);
    indexes=[1,1;2,floor(M/2)+1];
    for a=1:size(indexes,1)
        u=indexes(a,1); m=indexes(a,2); plus=phi; minus=phi; plus(u,m)=plus(u,m)*exp(1i*1e-6); minus(u,m)=minus(u,m)*exp(-1i*1e-6);
        fp=strict_satcom_models('mr_phase',data,plus,p,1,il,tts); fm=strict_satcom_models('mr_phase',data,minus,p,1,il,tts);
        numeric=(fp-fm)/2e-6; analytic=real(conj(1i*phi(u,m))*g(u,m)); errors(end+1)=abs(analytic-numeric)/max(1,abs(numeric)); %#ok<AGROW>
    end
end
[mu,~,~,~,~]=strict_satcom_models('moments',data,phi); W=permute(mu,[1,3,2]).*0.0001;
[~,g]=strict_satcom_models('ap_phase',data,phi,W);
for a=1:size(indexes,1)
    u=indexes(a,1); m=indexes(a,2); plus=phi; minus=phi; plus(u,m)=plus(u,m)*exp(1i*1e-6); minus(u,m)=minus(u,m)*exp(-1i*1e-6);
    fp=strict_satcom_models('ap_phase',data,plus,W); fm=strict_satcom_models('ap_phase',data,minus,W);
    numeric=(fp(u)-fm(u))/2e-6; analytic=real(conj(1i*phi(u,m))*g(u,m)); apErrors(end+1)=abs(analytic-numeric)/max(1,abs(numeric)); %#ok<AGROW>
end
result=struct('paper_id','cooperative-satcom','scope','full_dimension_geometry_analytic_gradient_test_NOT_full_reproduction', ...
    'metrics',struct('mr_gradient_relative_error',max(errors),'ap_gradient_relative_error',max(apErrors)), ...
    'checks',struct('mr_gradient_pass',max(errors)<1e-6,'ap_gradient_pass',max(apErrors)<1e-6, ...
    'finite_nlos_pass',all(data.d_var(:)>0) && all(data.G_var(:)>0) && all(data.r_var(:)>0)), ...
    'full_reproduction_pass',false);
if nargin>=2
    folder=fileparts(outputPath); if ~isempty(folder) && ~exist(folder,'dir'), mkdir(folder); end
    fid=fopen(outputPath,'w'); assert(fid>=0); clean=onCleanup(@()fclose(fid)); fprintf(fid,'%s\n',jsonencode(result));
end
end
