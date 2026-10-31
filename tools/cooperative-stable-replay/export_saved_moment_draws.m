function export_saved_moment_draws(repo,resultPath,outDir)
% Exact declared1000-draw native moment stream; no optimizer or new designs.
assert(~isfolder(outDir) && ~isfile(outDir),'Preserve prior replay output');
original=jsondecode(fileread(resultPath));[folder,~,~]=fileparts(resultPath);
statePath=fullfile(folder,original.state_recording.filename);
assert(strcmp(hashfile(statePath),original.state_recording.sha256),'Original saved states differ');
runner=fullfile(repo,'strict','cooperative-satcom','run_strict_cooperative_v3.m');runnerSHA=hashfile(runner);
assert(strcmp(runnerSHA,original.executed_source_hashes.run_strict_cooperative_v3_m.sha256),'Original moment-stream source differs');
saved=load(statePath,'recording');input=saved.recording.input;data=input.data;
t=input.configuration.tuned_not_reported;count=t.monte_carlo_realizations;assert(count==1000);
[J,U,N]=size(data.d_mean);M=size(data.r_mean,2);rng(double(t.seed),'twister');
mkdir(outDir);payload=fullfile(outDir,'declared-moment-stream.bin');fid=fopen(payload,'wb','ieee-le');assert(fid>=0);clean=onCleanup(@()fclose(fid));
powers=zeros(J,U);fourths=zeros(J,U);
for realization=1:count
    for u=1:U
        r=data.r_mean(u,:).'+sqrt(data.r_var(u))*cn([M,1]);emit_complex(fid,r);
        for j=1:J
            G=reshape(data.G_mean(j,u,:,:),N,M)+sqrt(data.G_var(j,u))*cn([N,M]);
            d=reshape(data.d_mean(j,u,:),N,1)+sqrt(data.d_var(j,u))*cn([N,1]);
            h=d+G*r;p=sum(abs(h).^2);powers(j,u)=powers(j,u)+p;fourths(j,u)=fourths(j,u)+p^2;
            emit_complex(fid,G);emit_complex(fid,d);fwrite(fid,[p;p^2],'double');
        end
    end
end
clear clean;
if iscell(original.results),point=original.results{1};else,point=original.results(1);end
assert(strcmp(runnerSHA,hashfile(runner)) && strcmp(hashfile(statePath),original.state_recording.sha256),'Original source/input changed during replay');
meta=struct('scope','Replayed original fixed phi=ones channel-moment stream; not optimized performance draws or recovered historical buffers',...
    'count',count,'seed',double(t.seed),'J',J,'U',U,'N',N,'M',M,'payload','declared-moment-stream.bin',...
    'payload_sha256',hashfile(payload),'source_result_sha256',hashfile(resultPath),'state_sha256',hashfile(statePath),'original_runner_sha256',hashfile(runner),...
    'layout','little-endian float64; realization,user: r real/imag; satellite: G real/imag(column-major),d real/imag,p,p^2',...
    'native_empirical_second_moment',powers/count,'native_empirical_fourth_moment',fourths/count,...
    'original_MC_metrics',point.monte_carlo,'count_provenance','Configured1000-draw validation, not a count reported in the supplied numerical paragraph',...
    'exporter_sha256',hashfile([mfilename('fullpath') '.m']),'new_optimization',false);
out=fopen(fullfile(outDir,'index.json'),'w','n','UTF-8');assert(out>=0);guard=onCleanup(@()fclose(out));fwrite(out,jsonencode(meta),'char');clear guard;
fprintf('Replayed all%d original moment draws at J%d/U%d/N%d/M%d.\n',count,J,U,N,M);
end

function emit_complex(fid,x),fwrite(fid,real(x),'double');fwrite(fid,imag(x),'double');end
function z=cn(shape),z=(randn(shape)+1i*randn(shape))/sqrt(2);end
function out=hashfile(path)
fid=fopen(path,'rb');assert(fid>=0);clean=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');clear clean;
md=java.security.MessageDigest.getInstance('SHA-256');md.update(bytes);out=lower(reshape(dec2hex(typecast(md.digest(),'uint8'),2).',1,[]));
end
