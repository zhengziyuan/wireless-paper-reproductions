function export_saved_native_contexts(repo,bank,output)
% Replay the saved 18-case model constructor only. No optimizer is called.
package=fullfile(repo,'strict','hotspot-satcom');addpath(package);
manifest=jsondecode(fileread(fullfile(bank,'execution-progress.json')));
assert(manifest.completed_cases==18&&manifest.expected_cases==18);
records=cells(manifest.records);assert(numel(records)==18);
assert(~isfolder(output),'Preserve earlier exports; choose a fresh directory');mkdir(output);
index={};seen=zeros(18,2);
for j=1:18
    row=records{j};cfgPath=fullfile(bank,row.configuration_filename);rawPath=fullfile(bank,row.result_filename);
    config=jsondecode(fileread(cfgPath));raw=jsondecode(fileread(rawPath));
    hashes=strict_hotspot_validated_hashes(cfgPath);
    assert(isequal(hashes,raw.executed_source_hashes),'Saved producer/current MATLAB sources differ');
    assert(raw.source_unchanged_during_run&&~raw.full_reproduction_pass&&~raw.reference_ordinates_used);
    assert(config.reported.N==16&&config.reported.J==16&&config.reported.M==25);
    assert(config.reported.U==row.U&&config.reported.K==16-row.U&&config.reported.kappa_satellite_db==row.kappa_satellite_db);
    assert(config.tuned_not_reported.monte_carlo_realizations==1000);
    rng(config.tuned_not_reported.seed,'twister');f=strict_hotspot_geometry(config);
    names=fieldnames(f.mean_inputs);inputs=struct();
    for k=1:numel(names),inputs.(names{k})=encode(f.mean_inputs.(names{k}));end
    name=sprintf('case-%02d-context.json',j);
    context=struct('U',row.U,'beta_db',row.kappa_satellite_db,'mean_inputs',inputs,...
        'noise',f.noise,'power',f.power,'phi0',encode(f.phi0),'geometry',f.geometry,...
        'source_hashes',hashes,'result_filename',row.result_filename,...
        'result_sha256',sha(rawPath),'configuration_sha256',sha(cfgPath),...
        'scope','deterministic_replay_of_saved_native_constructor_no_optimization',...
        'matlab_version',version,'full_reproduction_pass',false);
    assert(isequal(hashes,strict_hotspot_validated_hashes(cfgPath)),'Sources changed during constructor replay');
    write(fullfile(output,name),context);seen(j,:)=[row.U,row.kappa_satellite_db];
    index{end+1}=struct('U',row.U,'beta_db',row.kappa_satellite_db,'context_file',name,...
        'result_filename',row.result_filename,'result_sha256',context.result_sha256); %#ok<AGROW>
    fprintf('Exported saved native context U=%d beta=%g\n',row.U,row.kappa_satellite_db);
end
assert(isequal(sortrows(seen),sortrows([repmat((1:6)',3,1),repelem([0;10;20],6)])));
write(fullfile(output,'index.json'),struct('scope','all18_saved_native_model_context_replay',...
    'cases',{index},'optimizers_executed',0,'all_producer_source_bindings_match',true,...
    'full_reproduction_pass',false));
end
function out=cells(value),if iscell(value),out=value;else,out=num2cell(value);end,end
function out=encode(value)
out=struct('shape',size(value),'real',reshape(real(value),1,[]),'imag',reshape(imag(value),1,[]),'order','F');
end
function value=sha(path)
fid=fopen(path,'rb');assert(fid>=0);clean=onCleanup(@()fclose(fid));b=fread(fid,Inf,'*uint8');
md=java.security.MessageDigest.getInstance('SHA-256');md.update(b);
value=lower(reshape(dec2hex(typecast(md.digest(),'uint8'),2).',1,[]));
end
function write(path,value)
fid=fopen(path,'w','n','UTF-8');assert(fid>=0);clean=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(value));
end
