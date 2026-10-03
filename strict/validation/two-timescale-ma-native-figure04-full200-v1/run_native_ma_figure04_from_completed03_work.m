function receipt=run_native_ma_figure04_from_completed03_work(bankFolder,sourceFolder,outputFolder,mode)
% WORK recording/evaluation-only derivation. Original ZF positions are not optimized again.
assert(any(strcmp(mode,{'preflight-first-case','full200'})));
assert(~isfolder(outputFolder),'Use a fresh identity, never overwrite old evidence.');
mkdir(outputFolder);
configPath=fullfile(bankFolder,'run_config.json');config=jsondecode(fileread(configPath));
manifestPath=fullfile(bankFolder,'manifest.json');manifest=jsondecode(fileread(manifestPath));
planPath=fullfile(bankFolder,'plan.json');plan=jsondecode(fileread(planPath));
identityPath=fullfile(sourceFolder,'execution-identity.json');identity=jsondecode(fileread(identityPath));
assert(plan.figure==3&&numel(plan.cases)==2&&manifest.expected_jobs==200);
assert(config.geometry_realizations==100&&config.nlos_realizations_per_geometry==1000);
assert(identity.expected_jobs==200&&identity.all_result_identities_pass&&identity.source_unchanged_during_run&&identity.runtime_dependency_identity_unchanged);
[sourceFingerprint,runtimeIdentity]=strict_ma_full_v2_implementation_fingerprint(configPath);
assert(strcmp(sourceFingerprint,identity.implementation_fingerprint));
assert(numel(identity.records)==200&&numel(manifest.files)==200);
inputBindings=cell(200,1);
for j=1:200
    entry=manifest.files(j);[~,stem]=fileparts(entry.filename);
    jobPath=fullfile(bankFolder,'jobs',entry.filename);rawPath=fullfile(sourceFolder,[stem,'-matlab.json']);
    recorded=identity.records(j);
    assert(strcmp(recorded.input_filename,entry.filename)&&recorded.input_identity_pass&&recorded.result_input_identity_pass&&recorded.implementation_identity_pass);
    assert(strcmp(recorded.input_fingerprint,entry.input_fingerprint)&&strcmp(recorded.result_filename,[stem,'-matlab.json']));
    assert(strcmp(recorded.result_sha256,file_sha(rawPath)));
    assert(strcmp(entry.input_fingerprint,input_fingerprint(configPath,jobPath)));
    inputBindings{j}=struct('input',entry.filename,'input_sha256',file_sha(jobPath),'source_result',recorded.result_filename,'source_result_sha256',recorded.result_sha256);
end
ownPath=[mfilename('fullpath'),'.m'];ownBefore=file_sha(ownPath);
binding=struct('scope','WORK_native_MATLAB_Fig4_from_all200_actual_source_ZF_trajectories_NOT_Python_metrics',...
    'source_implementation_fingerprint',sourceFingerprint,'actual_source_runtime_identity',runtimeIdentity,...
    'source_configuration_sha256',file_sha(configPath),'source_manifest_sha256',file_sha(manifestPath),...
    'source_plan_sha256',file_sha(planPath),'source_execution_identity_sha256',file_sha(identityPath),...
    'derivation_entry_sha256',ownBefore,'required_source200_bindings',{inputBindings},...
    'actual_matlab_version',version,'actual_blas',version('-blas'),'actual_lapack',version('-lapack'),...
    'all_runtime_binary_hashes_available',false,'position_optimization_rerun',false,'mode',mode);
write_json(fullfile(outputFolder,'actual-execution-start-binding.json'),binding);
if strcmp(mode,'full200'),required=200;else,required=1;end
records=cell(required,1);began=tic;
for j=1:required
    entry=manifest.files(j);[~,stem]=fileparts(entry.filename);
    job=jsondecode(fileread(fullfile(bankFolder,'jobs',entry.filename)));
    raw=jsondecode(fileread(fullfile(sourceFolder,[stem,'-matlab.json'])));
    assert(job.figure==3&&job.N==6&&job.M==5&&any(job.kappa==[6,100]));
    assert(strcmp(raw.input_fingerprint,entry.input_fingerprint)&&strcmp(raw.implementation_fingerprint,sourceFingerprint));
    assert(raw.checks.zf_converged&&raw.checks.zf_nominal_design_spacing_feasible&&raw.checks.zf_nominal_design_box_feasible);
    history=raw.history.zf;assert(history.converged&&strcmp(history.termination,'fractional_increase'));
    objectives=history.objective(:);acceptedCount=numel(objectives);
    assert(acceptedCount>=2&&(objectives(end)-objectives(end-1))/abs(objectives(end-1))<config.fractional_increase_threshold);
    assert(size(history.positions,1)==acceptedCount&&size(history.positions,2)==6&&size(history.positions,3)==2);
    nlos=job.nlos_re+1i*job.nlos_im;assert(isequal(size(nlos),[1000,6,5]));
    [c,~]=ma_scenario(config,job.N,job.M,job.kappa,job.power,job.A,job.geometry);
    sampleSumRates=zeros(acceptedCount,1000);meanRates=zeros(acceptedCount,1);powerErrors=zeros(acceptedCount,1);offDiagonal=zeros(acceptedCount,1);
    for k=1:acceptedCount
        t=reshape(history.positions(k,:,:),6,2);
        distance=sqrt(sum((reshape(t,6,1,2)-reshape(t,1,6,2)).^2,3))+eye(6)*1e9;
        assert(min(distance,[],'all')>=c.minimum_distance-c.verification_tolerance);
        assert(all(t>=c.region_lower(:).'-c.verification_tolerance,'all')&&all(t<=c.region_upper(:).'+c.verification_tolerance,'all'));
        values=ma_instantaneous(t,c,nlos,'ZF',false);
        assert(numel(values.sample_sum_rates)==1000&&all(isfinite(values.sample_sum_rates)));
        sampleSumRates(k,:)=values.sample_sum_rates;meanRates(k)=values.mean_sum_rate;
        powerErrors(k)=max(abs(values.powers-c.power));offDiagonal(k)=max(values.off_diagonal_amplitude);
        assert(powerErrors(k)<=1e-10*max(1,c.power));
    end
    terminal=raw.metrics.schemes.MA_ZF.sample_sum_rates(:).';
    assert(numel(terminal)==1000);terminalDifference=max(abs(terminal-sampleSumRates(end,:)));
    assert(terminalDifference<=1e-10,'Original native final-state sample replay changed.');
    matrixPath=fullfile(outputFolder,[stem,'-native-zf-all1000-histories.mat']);
    save(matrixPath,'sampleSumRates','meanRates','powerErrors','offDiagonal','-v7');
    rec=struct('source_figure',3,'figure',4,'mode','actual_native_full1000_ZF_evaluation_at_every_original_accepted_position',...
        'source_input',entry.filename,'source_input_fingerprint',entry.input_fingerprint,...
        'source_raw_result_sha256',inputBindings{j}.source_result_sha256,'case_index',entry.case_index,...
        'realization',entry.realization,'kappa',job.kappa,'accepted_ZF_positions',acceptedCount,...
        'N',6,'M',5,'nlos_per_position',1000,'actual_full1000_MC_history',meanRates,...
        'original_statistical_objective_history',objectives,'raw_all1000_samples_file', [stem,'-native-zf-all1000-histories.mat'],...
        'raw_all1000_samples_sha256',file_sha(matrixPath),'maximum_terminal_native_sample_difference',terminalDifference,...
        'maximum_power_absolute_error',max(powerErrors),'maximum_ZF_off_diagonal_amplitude',max(offDiagonal),...
        'original_positions_reoptimized',false,'source_stop_and_domains_checked',true,...
        'historical_original_reference_agreement_verified',false);
    write_json(fullfile(outputFolder,[stem,'-native-figure04.json']),rec);records{j}=rec;
    write_json(fullfile(outputFolder,'execution-progress.json'),struct('required_jobs',required,'completed_jobs',j,'full_original_jobs',200,'scope',mode,'elapsed_seconds',toc(began),'full200_certificate',false));
    fprintf('Native Fig4 evaluation %d/%d with %d actual positions x1000 draws\n',j,required,acceptedCount);
end
sourceAfter=strict_ma_full_v2_implementation_fingerprint(configPath);assert(strcmp(sourceFingerprint,sourceAfter)&&strcmp(ownBefore,file_sha(ownPath)));
for j=1:200
    item=inputBindings{j};assert(strcmp(item.input_sha256,file_sha(fullfile(bankFolder,'jobs',item.input))));
    assert(strcmp(item.source_result_sha256,file_sha(fullfile(sourceFolder,item.source_result))));
end
receipt=struct('scope','actual_native_Fig4_full_draw_evaluation_of_original_Fig3_ZF_trajectories',...
    'required_source_jobs',200,'actual_evaluated_jobs',required,'nlos_per_position',1000,...
    'all_required_source200_bytes_unchanged',true,'derivation_source_before_after_unchanged',true,...
    'all_actual_evaluated_original_positions_and_native1000_arrays_saved',true,...
    'native_full200_history_evaluation_complete',required==200,'source_start_binding_sha256',file_sha(fullfile(outputFolder,'actual-execution-start-binding.json')),...
    'elapsed_seconds',toc(began),'records',{records},'original_reference_agreement_verified',false,'full_reproduction_pass',false);
write_json(fullfile(outputFolder,'actual-completion-receipt.json'),receipt);
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
function value=file_sha(path)
fid=fopen(path,'rb');assert(fid>=0);cleaner=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');d=java.security.MessageDigest.getInstance('SHA-256');d.update(bytes);value=lower(reshape(dec2hex(typecast(d.digest(),'uint8'),2).',1,[]));
end
function value=input_fingerprint(configPath,jobPath)
d=java.security.MessageDigest.getInstance('SHA-256');d.update(uint8('strict-v1'));d.update(uint8(0));
for path={configPath,jobPath}
    fid=fopen(path{1},'rb');assert(fid>=0);bytes=fread(fid,Inf,'*uint8');fclose(fid);d.update(bytes);if strcmp(path{1},configPath),d.update(uint8(0));end
end
value=lower(reshape(dec2hex(typecast(d.digest(),'uint8'),2).',1,[]));
end
function write_json(path,value)
fid=fopen(path,'w','n','UTF-8');assert(fid>=0);cleaner=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(value));
end
