function report=run_one_native_theory_bounded_case_v1(jobPath,configPath,work,admissionPath,nodeBudget)
% Prepared single native theory search. No production starts without admission.
% A complete winner's optional final1000 is a separate explicit bridge action.
a=jsondecode(fileread(admissionPath));
assert(isscalar(nodeBudget)&&isfinite(nodeBudget)&&nodeBudget>0&&nodeBudget==fix(nodeBudget),'MAExact:Work','Finite positive resumable work chunk required.');
assert(a.root_admitted_unique_native_statistical_theory_search&&a.user_selected_statistical_target,'MAExact:Admission','Explicit single native statistical-target admission required.');
assert(strcmp(ma_native_grid_io_v1('sha_file',a.prepared_plan_path),a.prepared_plan_SHA256),'MAExact:Plan','Reviewed native statistical plan differs.');
assert(strcmp(a.job_path,jobPath)&&strcmp(a.configuration_path,configPath)&&strcmp(a.output_directory,work),'MAExact:Admission','Exact single-case paths required.');
assert(strcmp(ma_native_grid_io_v1('sha_file',jobPath),a.job_SHA256)&&strcmp(ma_native_grid_io_v1('sha_file',configPath),a.configuration_SHA256),'MAExact:Input','Shared native inputs differ.');
for i=1:numel(a.source_pins)
    p=a.source_pins(i);assert(strcmp(ma_native_grid_io_v1('sha_file',p.path),p.SHA256),'MAExact:Source','Native exact search source changed.');
    [~,name,extension]=fileparts(p.path);if strcmp(extension,'.m'),assert(strcmpi(strrep(which(name),'\','/'),strrep(p.path,'\','/')),'MAExact:LoadedProvider','Loaded native provider differs from pinned source.');end
end
job=jsondecode(fileread(jobPath));config=jsondecode(fileread(configPath));
assert(strcmp(ma_native_grid_io_v1('sha_file',a.original_bank_configuration_path),a.original_bank_configuration_SHA256)&&strcmp(ma_native_grid_io_v1('sha_file',a.original_manifest_path),a.original_manifest_SHA256),'MAExact:Bank','Original bank metadata changed.');
manifest=jsondecode(fileread(a.original_manifest_path));[~,filename,extension]=fileparts(jobPath);
matches=find(strcmp({manifest.files.filename},[filename,extension]));assert(numel(matches)==1,'MAExact:Bank','One original bank slot required.');entry=manifest.files(matches);
assert(entry.case_index==job.point-3&&entry.realization==job.realization&&strcmp(entry.input_fingerprint,a.original_shared_bank_input_fingerprint),'MAExact:Input','Original shared-bank slot identity differs.');
assert(strcmp(original_fingerprint(a.original_bank_configuration_path,jobPath),entry.input_fingerprint),'MAExact:Input','Original input/config bytes differ from bank fingerprint.');
assert(any(job.figure==[19,20])&&job.kappa==100&&job.power==1,'MAExact:Scope','Only original Fig19/20 geometry controls.');
if job.figure==19,N=4;M=3;axis=3:18;else,N=6;M=5;axis=3:12;end
assert(job.N==N&&job.M==M&&any(job.brute_force_D==axis)&&job.point==job.brute_force_D,'MAExact:Scope','Original dimensions and full original grid point required.');
assert(config.user_selected_statistical_reconstruction.user_selected_lower_computation_and_storage&&strcmp(config.brute_force_objective,'paper_statistical_design_objective')&&any(config.configuration_scope.allowed_figures==job.figure)&&isequal(config.sweeps.brute_force_points_per_axis(:),axis(:)),'MAExact:Target','Complete figure-specific user-selected statistical target configuration required.');
assert(config.nlos_realizations_per_geometry==1000&&strcmp(config.user_selected_statistical_reconstruction.immutable_original_config_SHA256,a.original_bank_configuration_SHA256),'MAExact:Input','Original1000 population/config provenance differs.');
assert(any(strcmp(a.mode,{'MRT','ZF'})),'MAExact:Scope','One explicit statistical MRT or ZF target required.');
context=ma_theory_native_original_bridge_v1('context',config,job);
model=ma_statistical_grid_model_native_v1(context.c,N,job.brute_force_D,a.mode);
binding=struct('job_SHA256',a.job_SHA256,'configuration_SHA256',a.configuration_SHA256,'source_pins',{a.source_pins},...
    'original_manifest_SHA256',a.original_manifest_SHA256,'original_shared_bank_input_fingerprint',entry.input_fingerprint,...
    'figure',job.figure,'realization',job.realization,'target','user_selected_statistical_objective_not_historical_MC',...
    'MATLAB_version',version,'BLAS',version('-blas'));
report=ma_statistical_bounded_DFS_native_v1(model,work,binding,nodeBudget);
report.final1000_MC_not_run_here=true;
end

function value=original_fingerprint(configPath,jobPath)
md=java.security.MessageDigest.getInstance('SHA-256');md.update(uint8([double('strict-v1'),0]));
paths={configPath,jobPath};for index=1:2
    path=paths(index);
    fid=fopen(path{1},'rb');assert(fid>=0,'MAExact:Input','Cannot read exact original input bytes.');clean=onCleanup(@()fclose(fid));bytes=fread(fid,inf,'*uint8');clear clean;md.update(bytes);if index==1,md.update(uint8(0));end
end
raw=typecast(md.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end
