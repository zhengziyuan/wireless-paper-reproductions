function out=strict_satcom_capture(action,varargin)
% Numeric recording only. Never edits numerical inputs, solver results or RNG.
persistent active recording
out=[];
if strcmp(action,'begin')
    active=true; recording=struct('schema',1,'input',varargin{1},'final_states',{{}},'phase_endpoints',{{}},'QT_candidates',{{}});return;
end
if isempty(active) || ~active,return;end
switch action
    case 'final',recording.final_states{end+1}=varargin{1};
    case 'phase',recording.phase_endpoints{end+1}=varargin{1};
    case 'qt',recording.QT_candidates{end+1}=varargin{1};
    case 'save'
        path=varargin{1}; assert(~isfile(path),'Preserve previous state output');
        save(path,'recording','-v7');active=false;
        fid=fopen(path,'rb');assert(fid>=0);clean=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');clear clean;
        md=java.security.MessageDigest.getInstance('SHA-256');md.update(bytes);
        [~,name,ext]=fileparts(path);
        out=struct('filename',[name ext],'sha256',lower(reshape(dec2hex(typecast(md.digest(),'uint8'),2).',1,[])),...
            'final_scheme_states',numel(recording.final_states),'phase_endpoints',numel(recording.phase_endpoints),...
            'QT_candidates',numel(recording.QT_candidates),'new_numerical_operation',false);
        recording=[];
    otherwise,error('Unknown numeric recording action');
end
end
