function result=strict_satcom_increment_test(fixturePath,outputPath)
% Exact original AP/MR algebra on a shared full-dimensional Python fixture.
f=load(fixturePath);U=size(f.old,1);M=size(f.old,2);count=size(f.new,1);ap=zeros(count,U);ms=zeros(count,1);mt=ms;ae=zeros(count,1);se=ae;te=ae;
[ap0,~]=strict_satcom_models('ap_phase',f.data,f.old,f.W);
[s0,~]=strict_satcom_models('mr_phase',f.data,f.old,f.p_stat,f.smoothing,f.limit,false);
[t0,~]=strict_satcom_models('mr_phase',f.data,f.old,f.p_tts,f.smoothing,f.limit,true);
for k=1:count
    new=reshape(f.new(k,:,:),U,M);ap(k,:)=strict_satcom_increments('ap',f.data,f.old,new,f.W).';
    ms(k)=strict_satcom_increments('mr',f.data,f.old,new,f.p_stat,f.smoothing,f.limit,false);
    mt(k)=strict_satcom_increments('mr',f.data,f.old,new,f.p_tts,f.smoothing,f.limit,true);
    [av,~]=strict_satcom_models('ap_phase',f.data,new,f.W);ae(k)=max(abs(ap(k,:).'-(av-ap0)));
    [v,~]=strict_satcom_models('mr_phase',f.data,new,f.p_stat,f.smoothing,f.limit,false);se(k)=abs(ms(k)-(v-s0));
    [v,~]=strict_satcom_models('mr_phase',f.data,new,f.p_tts,f.smoothing,f.limit,true);te(k)=abs(mt(k)-(v-t0));
end
zero=max(abs([strict_satcom_increments('ap',f.data,f.old,f.old,f.W); ...
    strict_satcom_increments('mr',f.data,f.old,f.old,f.p_stat,f.smoothing,f.limit,false); ...
    strict_satcom_increments('mr',f.data,f.old,f.old,f.p_tts,f.smoothing,f.limit,true)]));
checks=struct('AP_python_matlab_max_error',max(abs(ap-f.AP_increment),[],'all'), ...
    'MR_S_python_matlab_max_error',max(abs(ms-f.MR_S_increment(:))), ...
    'MR_TTS_python_matlab_max_error',max(abs(mt-f.MR_TTS_increment(:))), ...
    'AP_direct_difference_max_error',max(ae),'MR_S_direct_difference_max_error',max(se), ...
    'MR_TTS_direct_difference_max_error',max(te),'zero_step_identity_error',zero);
allpass=all(structfun(@(v)v<1e-11,checks))&&zero==0;
result=struct('scope','full_dimension_exact_original_objective_increment_component_NOT_paper_reproduction', ...
    'dimensions',struct('J',3,'U',2,'N',16,'M',25,'K',1),'checks',checks,'all_passed',allpass,'full_reproduction_pass',false);
if nargin>1,folder=fileparts(outputPath);if ~exist(folder,'dir'),mkdir(folder);end,fid=fopen(outputPath,'w');assert(fid>=0);clean=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(result));end
assert(allpass,'Exact original AP/MR objective increment identity/parity failed');
end
