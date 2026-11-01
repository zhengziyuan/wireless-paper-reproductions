function export_saved_native_mc(repo,bank,output)
% Export the exact declared saved-run RNG stream. No optimization/new bank.
package=fullfile(repo,'strict','hotspot-satcom');addpath(package);
manifest=jsondecode(fileread(fullfile(bank,'execution-progress.json')));
assert(manifest.completed_cases==18&&manifest.expected_cases==18);
records=manifest.records;if ~iscell(records),records=num2cell(records);end
assert(numel(records)==18&&~isfolder(output));mkdir(output);index={};
for j=1:18
    row=records{j};cfgPath=fullfile(bank,row.configuration_filename);rawPath=fullfile(bank,row.result_filename);
    cfg=jsondecode(fileread(cfgPath));raw=jsondecode(fileread(rawPath));hashes=strict_hotspot_validated_hashes(cfgPath);
    assert(isequal(hashes,raw.executed_source_hashes),'Changed producer source/configuration');
    U=cfg.reported.U;K=cfg.reported.K;M=cfg.reported.M;N=cfg.reported.N;
    assert(U==row.U&&K==16-U&&N==16&&M==25&&cfg.reported.J==16);
    assert(cfg.tuned_not_reported.monte_carlo_realizations==1000);
    assert(~raw.full_reproduction_pass&&raw.source_unchanged_during_run&&~raw.reference_ordinates_used);
    filename=sprintf('case-%02d-channels.f64le',j);path=fullfile(output,filename);
    fid=fopen(path,'w','ieee-le');assert(fid>=0);clean=onCleanup(@()fclose(fid));
    % Exact producer reset immediately before its original1000 paired draws.
    rng(cfg.tuned_not_reported.seed+271828+U,'twister');
    count=U*N+U*M*N+K*N;
    for draw=1:1000
        f=strict_hotspot_geometry(cfg);
        values=[f.direct(:);f.cascade(:);f.nhu(:)];assert(numel(values)==count);
        assert(fwrite(fid,[real(values);imag(values)],'double')==2*count);
    end
    clear clean;
    info=dir(path);assert(info.bytes==1000*2*count*8);
    assert(isequal(hashes,strict_hotspot_validated_hashes(cfgPath)),'Sources changed during RNG replay');
    index{end+1}=struct('U',U,'beta_db',row.kappa_satellite_db,'file',filename,...
        'draws',1000,'complex_values_per_draw',count,'dtype','float64_little_endian',...
        'packing','per_draw_all_real_then_all_imag;direct_then_cascade_then_nhu;MATLAB_column_major',...
        'direct_shape',[U,N],'cascade_shape',[U,M,N],'nhu_shape',[K,N],...
        'bytes',info.bytes,'sha256',sha(path),'result_filename',row.result_filename,...
        'result_sha256',sha(rawPath),'configuration_sha256',sha(cfgPath),'source_hashes',hashes); %#ok<AGROW>
    write(fullfile(output,'partial-index.json'),struct('cases_completed',j,'cases',{index}));
    fprintf('Replayed full1000 saved native draws U=%d beta=%g\n',U,row.kappa_satellite_db);
end
write(fullfile(output,'index.json'),struct('scope','all18_full1000_declared_native_RNG_stream_replay_no_optimization',...
    'cases',{index},'required_draws',18000,'required_selected_design_evaluations',54000,...
    'optimizers_called',0,'full_reproduction_pass',false,'matlab_version',version));
end
function value=sha(path)
fid=fopen(path,'rb');assert(fid>=0);clean=onCleanup(@()fclose(fid));md=java.security.MessageDigest.getInstance('SHA-256');
while ~feof(fid),md.update(fread(fid,8*1024*1024,'*uint8'));end
value=lower(reshape(dec2hex(typecast(md.digest(),'uint8'),2).',1,[]));
end
function write(path,value)
fid=fopen(path,'w','n','UTF-8');assert(fid>=0);clean=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(value));
end
