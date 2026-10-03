function result=strict_hotspot_geometry_test(fixturePath,outputPath)
% Independently regenerate deterministic moments at every original HU count.
f=load(fixturePath);records=cell(1,numel(f.cases));keys={'direct_mean','direct_variance','matrix_mean','matrix_variance','ground_mean','ground_variance','nhu_mean','nhu_variance'};
for k=1:numel(f.cases)
    c=f.cases{k};rng(c.config.tuned_not_reported.seed,'twister');actual=strict_hotspot_geometry(c.config);U=c.config.reported.U;pos=actual.geometry.hu_xy_m;dist=[];
    for a=1:U,for b=a+1:U,dist(end+1)=norm(pos(a,:)-pos(b,:));end,end %#ok<AGROW>
    modelError=0;details=struct();
    for n=1:numel(keys),name=keys{n};expected=c.mean_inputs.(name);value=actual.mean_inputs.(name);err=max(abs(value(:)-expected(:)))/max(1,max(abs(expected(:))));details.(name)=err;modelError=max(modelError,err);end
    geometryError=max(abs(pos(:)-c.geometry.hu_xy_m(:)));distancePass=U==1||(min(dist)>=10-1e-12&&max(dist)<=20+1e-12);
    records{k}=struct('U',U,'all_pair_distances_m',dist,'source_distance_contract_pass',distancePass, ...
        'geometry_error',geometryError,'moment_relative_errors',details,'maximum_model_error',modelError, ...
        'all_passed',distancePass&&geometryError<1e-12&&modelError<1e-7);
end
result=struct('scope','independent_all6_HU_geometry_and_deterministic_full_model_component_NOT_full_figures', ...
    'cases',{records},'all_passed',all(cellfun(@(c)c.all_passed,records)),'historical_author_coordinates_recovered',false,'full_reproduction_pass',false);
if nargin>1,folder=fileparts(outputPath);if ~exist(folder,'dir'),mkdir(folder);end,fid=fopen(outputPath,'w');assert(fid>=0);clean=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(result));end
assert(result.all_passed,'Independent source-compliant geometry/model fixture check failed');
end
