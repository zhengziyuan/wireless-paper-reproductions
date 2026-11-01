function out=strict_satcom_power24_mc_capture_v1(action,varargin)
% Passive physical primitive/vector IO. Never invokes RNG, moments or optimizers.
persistent T;
out=[];
switch action
    case 'configure'
        assert(isempty(T),'One prospective original MC stream per fresh process');
        T=struct('outputPath',varargin{1},'opened',false,'closed',false);
    case 'begin'
        assert(~isempty(T)&&~T.opened,'One original MC begin');
        data=varargin{1};phi=varargin{2};count=varargin{3};seed=varargin{4};rngBefore=varargin{5};
        assert(count==1000,'All original1000 actual draws required');
        [J,U,N]=size(data.d_mean);M=size(data.r_mean,2);assert(isequal(size(phi),[U,M]));
        [~,~,endian]=computer;assert(endian=='L','Explicit little-endian physical stream');
        T.directory=[T.outputPath '.actual-online-MC1000'];assert(~isfolder(T.directory)&&~isfile(T.directory));mkdir(T.directory);
        T.J=J;T.U=U;T.N=N;T.M=M;T.count=count;T.seed=seed;T.rngBefore=rngBefore;
        T.fid=fopen(fullfile(T.directory,'actual-primitive-vector-stream.bin'),'wb','ieee-le');assert(T.fid>=0);
        T.md=java.security.MessageDigest.getInstance('SHA-256');T.bytes=0;T.rRows=0;T.leaves=0;T.draws=0;
        T.opened=true;T.closed=false;T.user=0;T.satellite=0;
        inputPath=fullfile(T.directory,'actual-moment-input.mat');save(inputPath,'data','phi','count','seed','rngBefore','-v7');
        fresh_json(fullfile(T.directory,'actual-moment-start.json'),struct('count',count,'J',J,'U',U,'N',N,'M',M,'seed',seed,'RNG_before',rngBefore,'input_mat','actual-moment-input.mat','input_mat_SHA256',hashfile(inputPath),'tape_is_actual_original_calls_not_regeneration',true,'first_true_use_independent_math_pending',true));
    case 'r'
        realization=varargin{1};u=varargin{2};r=varargin{3};
        assert(T.opened&&~T.closed&&realization==floor(T.rRows/T.U)+1&&u==mod(T.rRows,T.U)+1);
        assert(isequal(size(r),[T.M,1]));
        if u>1,assert(T.satellite==T.J);end
        T.user=u;T.satellite=0;T=emit_complex(T,r);T.rRows=T.rRows+1;
    case 'leaf'
        realization=varargin{1};u=varargin{2};j=varargin{3};G=varargin{4};d=varargin{5};h=varargin{6};p=varargin{7};pSquared=varargin{8};
        assert(T.opened&&~T.closed&&realization==floor(T.leaves/(T.U*T.J))+1&&u==T.user&&j==T.satellite+1);
        assert(isequal(size(G),[T.N,T.M])&&isequal(size(d),[T.N,1])&&isequal(size(h),[T.N,1]));
        T=emit_complex(T,G);T=emit_complex(T,d);T=emit_complex(T,h);T=emit_real(T,[p;pSquared]);
        T.satellite=j;T.leaves=T.leaves+1;
        if u==T.U&&j==T.J,T.draws=T.draws+1;end
    case 'finish'
        powers=varargin{1};fourths=varargin{2};exact2=varargin{3};exact4=varargin{4};mc=varargin{5};rngAfter=varargin{6};
        assert(T.draws==1000&&T.rRows==1000*T.U&&T.leaves==1000*T.U*T.J&&mc.count==1000);
        expected=1000*(T.U*2*T.M+T.U*T.J*(2*(T.N*T.M+2*T.N)+2))*8;
        assert(T.bytes==expected,'All actual physical primitive/vector/power bytes');
        assert(fclose(T.fid)==0);T.closed=true;
        raw=typecast(T.md.digest(),'uint8');digest=lower(reshape(dec2hex(raw,2).',1,[]));
        meta=struct('schema','actual-online-original1000-physical-primitive-vector-tape-native-v1','count',1000,'completed_draws',T.draws,'physical_r_rows',T.rRows,'physical_G_d_h_rows',T.leaves,'J',T.J,'U',T.U,'N',T.N,'M',T.M,'seed',T.seed,'stream','actual-primitive-vector-stream.bin','stream_bytes',T.bytes,'stream_SHA256',digest,'layout','little-endian float64; draw,user:r(real,imag); satellite:G(real,imag,column-major),d(real,imag),h(real,imag),original_p,observer_same_expression_p^2','RNG_before',T.rngBefore,'RNG_after',rngAfter,'empirical_second',powers/1000,'empirical_fourth',fourths/1000,'exact_second',exact2,'exact_fourth',exact4,'original_monte_carlo_return',mc,'actual_new_observer_RNG_calls',0,'actual_original_moment_draws',1000,'optimized_performance_MC',false,'scientific_physical_dual_reference_PASS',false,'full_vectors_and_inputs_saved_but_independent_first_use_pending',true);
        fresh_json(fullfile(T.directory,'actual-moment-tape-complete.json'),meta);out=meta;
    case 'abort_if_open'
        if ~isempty(T)&&T.opened&&~T.closed
            fclose(T.fid);T.closed=true;raw=typecast(T.md.digest(),'uint8');digest=lower(reshape(dec2hex(raw,2).',1,[]));
            fresh_json(fullfile(T.directory,'actual-moment-tape-partial.json'),struct('complete',false,'completed_sample_returns',T.draws,'physical_r_rows',T.rRows,'physical_G_d_h_rows',T.leaves,'stream_bytes',T.bytes,'stream_SHA256',digest,'original_failed_or_partial_output_retained',true,'independent_PASS',false));
        end
    otherwise
        error('Unknown passive MC capture action');
end
end
function T=emit_complex(T,x)
T=emit_real(T,real(x));T=emit_real(T,imag(x));
end
function T=emit_real(T,x)
assert(isa(x,'double'));n=fwrite(T.fid,x,'double');assert(n==numel(x));
raw=typecast(x(:),'uint8');T.md.update(raw);T.bytes=T.bytes+numel(raw);
end
function fresh_json(path,value)
assert(~isfile(path));fid=fopen(path,'w','n','UTF-8');assert(fid>=0);clean=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(value));
end
function digest=hashfile(path)
fid=fopen(path,'rb');assert(fid>=0);clean=onCleanup(@()fclose(fid));raw=fread(fid,Inf,'*uint8');clear clean;
md=java.security.MessageDigest.getInstance('SHA-256');md.update(raw);bytes=typecast(md.digest(),'uint8');digest=lower(reshape(dec2hex(bytes,2).',1,[]));
end
