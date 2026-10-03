function out=strict_satcom_recording_v4_work(action,varargin)
% WORK recording side channel only: no science, solver, gradient, or RNG call.
% Not installed, not a complete-bank or historical-reproduction certificate.
persistent trace
switch action
    case 'reset'
        trace=struct('original_case_input',varargin{1},'phase',{{}},'QT',{{}});
        out=[];
    case 'phase_final'
        trace.phase{end+1}=varargin{1};out=[];
    case 'phase_context'
        context=varargin{1};names=fieldnames(context);
        for k=1:numel(names),trace.phase{end}.(names{k})=context.(names{k});end
        out=[];
    case 'QT_start'
        entry=varargin{1};entry.complete_original_return=false;
        trace.QT{end+1}=entry;out=[];
    case 'QT'
        entry=varargin{1};entry.complete_original_return=true;
        trace.QT{end}=entry;out=[];
    case 'get'
        out=trace;
    case 'hashes'
        paths=varargin{1};out=struct('name',{},'sha256',{});
        for k=1:numel(paths)
            path=paths{k};assert(~isempty(path)&&exist(path,'file')==2);
            [~,name,extension]=fileparts(path);fid=fopen(path,'rb');assert(fid>=0);
            cleanup=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');clear cleanup
            md=java.security.MessageDigest.getInstance('SHA-256');md.update(bytes);
            digest=typecast(md.digest(),'uint8');
            out(end+1)=struct('name',[name,extension],'sha256',lower(reshape(dec2hex(digest,2).',1,[]))); %#ok<AGROW>
        end
    otherwise
        error('Unknown recording-only action');
end
end
