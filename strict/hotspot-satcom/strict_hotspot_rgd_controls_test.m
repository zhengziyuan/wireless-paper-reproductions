function result=strict_hotspot_rgd_controls_test(fixturePath,outputPath)
% All original dimensions and full-rank stochastic moments; no paper curve test.
f=load(fixturePath);c=zeros(size(f.new,1),1);r=c;differenceC=c;differenceR=c;
[c0,~]=strict_hotspot_statistical('criterion_gradient',f.x,f.old,f.P);
[r0,~]=strict_hotspot_statistical('rate_gradient',f.x,f.old,f.W,f.noise);
for k=1:size(f.new,1)
    c(k)=strict_hotspot_rgd_controls('criterion_increment',f.x,f.old,f.new(k,:),f.P);
    r(k)=strict_hotspot_rgd_controls('rate_increment',f.x,f.old,f.new(k,:),f.W,f.noise);
    [v,~]=strict_hotspot_statistical('criterion_gradient',f.x,f.new(k,:),f.P);differenceC(k)=v-c0;
    [v,~]=strict_hotspot_statistical('rate_gradient',f.x,f.new(k,:),f.W,f.noise);differenceR(k)=v-r0;
end
identity=max(abs([strict_hotspot_rgd_controls('criterion_increment',f.x,f.old,f.old,f.P), ...
    strict_hotspot_rgd_controls('rate_increment',f.x,f.old,f.old,f.W,f.noise)]));
checks=struct('criterion_python_matlab_max_error',max(abs(c-f.criterion_increment(:))), ...
    'rate_python_matlab_max_error',max(abs(r-f.rate_increment(:))), ...
    'criterion_direct_difference_max_error',max(abs(c-differenceC)), ...
    'rate_direct_difference_max_error',max(abs(r-differenceR)), ...
    'zero_step_identity_error',identity);
allpass=all(structfun(@(x)x<1e-11,checks))&&identity==0;
result=struct('scope','synthetic_full_rank_full_dimension_exact_increment_component_NOT_paper_reproduction', ...
    'dimensions',struct('N',16,'U',6,'K',10,'M',25),'checks',checks,'all_passed',allpass,'full_reproduction_pass',false);
if nargin>1,folder=fileparts(outputPath);if ~exist(folder,'dir'),mkdir(folder);end,fid=fopen(outputPath,'w');assert(fid>=0);clean=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(result));end
assert(allpass,'Exact original objective increment identity/parity failed');
end
