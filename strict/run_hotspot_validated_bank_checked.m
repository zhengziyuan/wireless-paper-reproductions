function result=run_hotspot_validated_bank_checked(configPath,bankFolder)
% Independent MATLAB full18 execution; each full-size case is durable.
% The original numerical engines are not edited or replaced by this wrapper.
% All declared starts are required; a surviving start never hides a failure.
base=fileparts(mfilename('fullpath'));package=fullfile(base,'hotspot-satcom');addpath(package);
config=jsondecode(fileread(configPath));assert(config.tuned_not_reported.monte_carlo_realizations==1000);
assert(config.reported.N==16&&config.reported.J==16&&config.reported.M==25);
assert(config.tuned_not_reported.gradient_tolerance==1e-6);
if ~isfolder(bankFolder),mkdir(bankFolder);end
before=strict_hotspot_validated_hashes(configPath);runtimeBefore=runtime_identity();
binding=struct('paper_id','hotspot-satcom','engine','matlab','configuration_sha256',file_hash(configPath), ...
    'wrapper_sha256',file_hash(mfilename('fullpath')),'sources',before, ...
    'selected_runtime_dependencies',runtimeBefore,'expected_cases',18,'expected_starts',243, ...
    'monte_carlo_draws_per_selected_design',1000,'original_figure_reproduction_certified',false);
startPath=fullfile(bankFolder,'execution-start-identity.json');
if isfile(startPath)
    old=jsondecode(fileread(startPath));assert(isequal(old,jsondecode(jsonencode(binding))), ...
        'Execution binding changed: use a fresh bank directory; old results must be retained');
else
    assert(isempty(dir(fullfile(bankFolder,'case-*-matlab.json'))),'Unbound old results cannot acquire a post-hoc certificate');
    write_json(startPath,binding);
end
cases=cell(18,1);records=cell(18,1);index=0;clock=tic;
for beta=[0,10,20]
    for U=1:6
        index=index+1;scene=config;scene.reported.U=U;scene.reported.K=16-U;
        scene.reported.kappa_satellite_db=beta;
        scene.reported.kappa_ground_db=20;scene.reported.nhu_statistical_sinr_db=-3;
        configName=sprintf('case-%02d-config.json',index);resultName=sprintf('case-%02d-matlab.json',index);
        scenePath=fullfile(bankFolder,configName);resultPath=fullfile(bankFolder,resultName);
        if isfile(scenePath)
            assert(isequal(jsondecode(fileread(scenePath)),jsondecode(jsonencode(scene))),'Case configuration changed');
        else,write_json(scenePath,scene);end
        caseSources=strict_hotspot_validated_hashes(scenePath);
        if isfile(resultPath)
            raw=jsondecode(fileread(resultPath));
            assert(raw.source_unchanged_during_run&&isequal(raw.executed_source_hashes,caseSources), ...
                'Saved case was not executed under the unchanged current scientific sources');
        else
            raw=run_strict_hotspot_statistical_validated(scenePath,resultPath,'full-case');
        end
        assert(raw.source_unchanged_during_run&&isequal(raw.executed_source_hashes,caseSources));
        assert(isequal(before,strict_hotspot_validated_hashes(configPath)),'Sources changed during full bank');
        assert(isequal(runtimeBefore,runtime_identity()),'Selected MATLAB/CVX dependencies changed during full bank');
        assert(numel(raw.cases)==1);c=raw.cases(1);if iscell(c),c=c{1};end
        assert(c.U==U&&c.kappa_satellite_db==beta&&strcmp(c.status,'executed'));
        names={'NoRIS','TwoStage','AO'};starts=0;
        for k=1:3
            r=c.schemes.(names{k}).all_start_records;assert(numel(r)==U+1);starts=starts+numel(r);
        end
        cases{index}=c;records{index}=struct('U',U,'kappa_satellite_db',beta, ...
            'configuration_filename',configName,'configuration_sha256',file_hash(scenePath), ...
            'result_filename',resultName,'result_sha256',file_hash(resultPath), ...
            'executed_starts',starts,'checks',c.checks);
        progress=struct('binding',binding,'completed_cases',index,'expected_cases',18, ...
            'records',{records(1:index)},'elapsed_seconds_this_invocation',toc(clock), ...
            'failed_cases_are_retained',true,'full_reproduction_pass',false);
        write_json(fullfile(bankFolder,'execution-progress.json'),progress);
        fprintf('MATLAB full statistical bank case %d/18 U=%d beta=%g convergence=%d\n',index,U,beta,c.checks.convergence_pass);
    end
end
gates={'physical_constraint_pass','convergence_pass','solver_primal_pass','qt_sdr_bound_pass'};checks=struct();
for k=1:numel(gates),checks.(gates{k})=all(cellfun(@(c)c.checks.(gates{k}),cases));end
result=struct('paper_id','hotspot-satcom','engine','matlab','scope','full','configuration',config, ...
    'source_settings',struct('ground_rician_db',20,'nhu_average_sinr_db',-3),'cases',{cases}, ...
    'checks',checks,'binding',binding,'records',{records},'expected_cases',18,'expected_starts',243, ...
    'all_declared_starts_required_for_certification',true,'reference_ordinates_used',false, ...
    'geometry_contract',config.geometry_contract,'source_unchanged_during_run',isequal(before,strict_hotspot_validated_hashes(configPath)), ...
    'selected_runtime_dependency_identity_unchanged',isequal(runtimeBefore,runtime_identity()), ...
    'historical_author_coordinates_recovered',false,'all_original_source_constraints_verified',false, ...
    'publisher_version_and_original_curve_agreement_verified',false,'full_reproduction_pass',false, ...
    'elapsed_seconds_this_invocation',toc(clock));
write_json(fullfile(bankFolder,'full18-matlab.json'),result);
end

function result=runtime_identity()
names={'cvx_begin','cvx_end','cvx_solver','cvx_precision','sqlp','sdpt3','mexschur','mexqops'};
items=cell(numel(names),1);
for k=1:numel(names)
    path=which(names{k});digest='';if ~isempty(path)&&isfile(path),digest=file_hash(path);end
    items{k}=struct('function',names{k},'resolved_path',path,'sha256',digest);
end
result=struct('matlab_version',version,'architecture',computer('arch'),'selected_dependencies',{items});
end
function value=file_hash(path)
if ~isfile(path)&&isfile([path,'.m']),path=[path,'.m'];end
fid=fopen(path,'rb');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');
digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(bytes);
raw=typecast(digest.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end
function write_json(path,value)
temporary=[path,'.tmp-',char(java.util.UUID.randomUUID())];fid=fopen(temporary,'w','n','UTF-8');assert(fid>=0);
cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(value));clear cleanup;
[okay,message]=movefile(temporary,path,'f');assert(okay,message);
end
