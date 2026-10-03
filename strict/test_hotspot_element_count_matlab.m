function result=test_hotspot_element_count_matlab(fixturePath,outputPath)
% Shared full dimension seven-count identities, not full optimization banks.
f=load(fixturePath);errors=zeros(7,1);fixed=true;rician=true;
for k=1:numel(f.counts)
    a=strict_hotspot_element_count(f.reference,f.counts(k));b=f.expected{k};
    names={'direct','cascade','nhu','phi0','nhu_target'};
    for j=1:numel(names),x=a.(names{j});y=b.(names{j});errors(k)=max(errors(k),max(abs(x(:)-y(:)))/max(1,max(abs(y(:)))));end
    names=fieldnames(a.mean_inputs);
    for j=1:numel(names),x=a.mean_inputs.(names{j});y=b.mean_inputs.(names{j});errors(k)=max(errors(k),max(abs(x(:)-y(:)))/max(1,max(abs(y(:)))));end
    fixed=fixed&&isequal(a.geometry,f.reference.geometry)&&isequal(a.direct,f.reference.direct)&&isequal(a.nhu,f.reference.nhu)&&isequal(a.phi0,f.reference.phi0);
    names={'matrix','ground'};
    for j=1:2,m=[names{j},'_mean'];v=[names{j},'_variance'];x=abs(a.mean_inputs.(m)).^2./a.mean_inputs.(v);y=abs(f.reference.mean_inputs.(m)).^2./f.reference.mean_inputs.(v);rician=rician&&max(abs(x(:)-y(:)))<1e-11;end
end
result=struct('scope','full_dimension_seven_count_gain_component_NOT7000_optimization_runs', ...
    'counts',f.counts,'maximum_relative_python_matlab_error',max(errors),'centers_direct_NHU_phase_fixed',fixed, ...
    'finite_Rician_factors_unchanged',rician,'all_passed',max(errors)<1e-12&&fixed&&rician,'full_reproduction_pass',false);
folder=fileparts(outputPath);if ~isfolder(folder),mkdir(folder);end
fid=fopen(outputPath,'w');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(result));assert(result.all_passed);
end
