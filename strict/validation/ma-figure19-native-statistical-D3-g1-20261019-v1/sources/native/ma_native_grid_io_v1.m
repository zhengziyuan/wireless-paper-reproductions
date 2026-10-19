function varargout=ma_native_grid_io_v1(action,varargin)
% Pure typed IO/identity host. No objective, optimizer, sampling or RNG call.
switch action
    case 'sha_file'
        varargout{1}=bytes_sha(read_bytes(varargin{1}));
    case 'sha_value'
        md=java.security.MessageDigest.getInstance('SHA-256');feed_value(md,varargin{1});varargout{1}=digest_text(md);
    case 'bind'
        folder=varargin{1};binding=varargin{2};if ~isfolder(folder),mkdir(folder);end
        path=fullfile(folder,'binding.mat');
        if isfile(path),old=load(path,'payload');assert_same(old.payload,binding,'Case/source/input binding differs');
        else,items=dir(folder);items=items(~ismember({items.name},{'.','..'}));assert(isempty(items),'MAHost:Unbound','Cannot adopt nonempty unbound work directory.');atomic_mat(path,binding);end
    case 'load'
        item=load(varargin{1},'payload');varargout{1}=item.payload;
    case 'mat'
        atomic_mat(varargin{1},varargin{2});
    case 'json'
        atomic_bytes(varargin{1},unicode2native([jsonencode(varargin{2}),newline],'UTF-8'));
    case 'same'
        varargout{1}=same(varargin{1},varargin{2});
    case 'assert_same'
        assert_same(varargin{1},varargin{2},varargin{3});
    case 'append_frame'
        path=varargin{1};payload=varargin{2};tmp=[path,'.frame-pending.mat'];
        if isfile(tmp),error('MAHost:UncertainFrame','Existing pending MAT frame is retained; no automatic invocation.');end
        save(tmp,'payload','-v7');sync_file(tmp);bytes=read_bytes(tmp);sha=bytes_sha(bytes);
        fid=fopen(path,'ab','ieee-le');assert(fid>=0,'MAHost:IO','Cannot append typed return tape.');clean=onCleanup(@()fclose(fid));
        assert(fwrite(fid,uint64(numel(bytes)),'uint64')==1,'MAHost:IO','Short frame length write.');
        assert(fwrite(fid,uint8(sha),'uint8')==64,'MAHost:IO','Short frame digest write.');
        assert(fwrite(fid,bytes,'uint8')==numel(bytes),'MAHost:IO','Short frame body write.');offset=ftell(fid);clear clean;sync_file(path);delete(tmp);varargout{1}=offset;
    case 'read_frame'
        path=varargin{1};offset=varargin{2};fid=fopen(path,'rb','ieee-le');assert(fid>=0,'MAHost:IO','Cannot read own typed tape.');clean=onCleanup(@()fclose(fid));
        assert(fseek(fid,offset,'bof')==0,'MAHost:IO','Cannot seek own typed tape.');
        length=fread(fid,1,'*uint64');sha=fread(fid,64,'*uint8');
        assert(numel(length)==1&&numel(sha)==64&&length<=uint64(256*1024^2),'MAHost:UncertainFrame','Partial or oversized typed frame; retained without retry.');
        bytes=fread(fid,double(length),'*uint8');next=ftell(fid);assert(numel(bytes)==double(length)&&strcmp(bytes_sha(bytes),char(sha')),'MAHost:UncertainFrame','Partial/corrupt typed return frame; no retry.');clear clean;
        tmp=[path,'.read-frame.mat'];atomic_bytes(tmp,bytes);item=load(tmp,'payload');delete(tmp);varargout{1}=item.payload;varargout{2}=next;
    case 'cleanup_exact_pending_frame'
        tmp=[varargin{1},'.frame-pending.mat'];
        if isfile(tmp),item=load(tmp,'payload');assert_same(item.payload,varargin{2},'Pending typed frame differs from complete durable return');delete(tmp);end
    case 'adopt_return'
        path=varargin{1};value=varargin{2};binding=varargin{3};
        if isfile(path),old=load(path,'payload');assert_same(old.payload,value,'Existing actual return differs in exact typed leaves/IEEE bits');
        else,atomic_mat(path,value);end
        stamp=struct('case_binding',binding,'actual_typed_return',path,'actual_typed_return_SHA256',bytes_sha(read_bytes(path)),'exact_typed_leaves',true);
        stampPath=[path,'.binding.mat'];if isfile(stampPath),old=load(stampPath,'payload');assert_same(old.payload,stamp,'Actual return binding differs');else,atomic_mat(stampPath,stamp);end
        varargout{1}=stamp;
    case 'failure'
        err=varargin{1};varargout{1}=struct('identifier',err.identifier,'message',err.message,'stack',{err.stack});
    otherwise
        error('MAHost:UnknownAction','Unknown pure host action.');
end
end

function assert_same(a,b,message)
assert(same(a,b),'MAHost:Identity','%s',message);
end

function yes=same(a,b)
if ~strcmp(class(a),class(b))||~isequal(size(a),size(b)),yes=false;return;end
if isnumeric(a)||islogical(a)
    yes=isreal(a)==isreal(b)&&isequal(raw_numeric(real(a)),raw_numeric(real(b)));
    if yes&&~isreal(a),yes=isequal(raw_numeric(imag(a)),raw_numeric(imag(b)));end
elseif ischar(a),yes=isequal(uint16(a),uint16(b));
elseif iscell(a),yes=true;for i=1:numel(a),if ~same(a{i},b{i}),yes=false;return;end,end
elseif isstruct(a)
    names=fieldnames(a);yes=isequal(names,fieldnames(b));if ~yes,return;end
    for i=1:numel(a),for j=1:numel(names),if ~same(a(i).(names{j}),b(i).(names{j})),yes=false;return;end,end,end
else,error('MAHost:UnsupportedLeaf','Unsupported typed host leaf class %s.',class(a));end
end

function feed_value(md,value)
feed(md,uint8(class(value)));feed(md,typecast(uint64(size(value)),'uint8'));feed(md,uint8(isreal(value)));
if isnumeric(value)||islogical(value)
    feed(md,raw_numeric(real(value)));if ~isreal(value),feed(md,raw_numeric(imag(value)));end
elseif ischar(value),feed(md,typecast(uint16(value(:)),'uint8'));
elseif iscell(value),for i=1:numel(value),feed_value(md,value{i});end
elseif isstruct(value)
    names=fieldnames(value);for j=1:numel(names),feed(md,unicode2native(names{j},'UTF-8'));end
    for i=1:numel(value),for j=1:numel(names),feed_value(md,value(i).(names{j}));end,end
else,error('MAHost:UnsupportedLeaf','Unsupported digest leaf class %s.',class(value));end
end

function bytes=raw_numeric(value)
if islogical(value),bytes=uint8(value(:));elseif isempty(value),bytes=uint8([]);else,bytes=typecast(value(:),'uint8');end
end

function feed(md,bytes)
bytes=uint8(bytes(:));md.update(typecast(uint64(numel(bytes)),'uint8'));if ~isempty(bytes),md.update(bytes);end
end

function value=bytes_sha(bytes)
md=java.security.MessageDigest.getInstance('SHA-256');if ~isempty(bytes),md.update(uint8(bytes(:)));end;value=digest_text(md);
end

function value=digest_text(md)
raw=typecast(md.digest(),'uint8');value=lower(reshape(dec2hex(raw,2).',1,[]));
end

function bytes=read_bytes(path)
fid=fopen(path,'rb');assert(fid>=0,'MAHost:IO','Cannot read required file: %s',path);clean=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8'); %#ok<NASGU>
end

function atomic_mat(path,payload)
tmp=[path,'.pending.mat'];save(tmp,'payload','-v7');sync_file(tmp);replace_atomic(tmp,path);
end

function atomic_bytes(path,bytes)
tmp=[path,'.pending'];fid=fopen(tmp,'wb');assert(fid>=0,'MAHost:IO','Cannot create pending host output.');clean=onCleanup(@()fclose(fid));assert(fwrite(fid,uint8(bytes),'uint8')==numel(bytes),'MAHost:IO','Short pending write.');clear clean;sync_file(tmp);replace_atomic(tmp,path);
end

function sync_file(path)
raf=javaObject('java.io.RandomAccessFile',path,'rw');clean=onCleanup(@()raf.close());fd=raf.getFD();fd.sync(); %#ok<NASGU>
end

function replace_atomic(source,destination)
src=javaObject('java.io.File',source);dst=javaObject('java.io.File',destination);
options=javaArray('java.nio.file.CopyOption',2);
options(1)=javaMethod('valueOf','java.nio.file.StandardCopyOption','REPLACE_EXISTING');
options(2)=javaMethod('valueOf','java.nio.file.StandardCopyOption','ATOMIC_MOVE');
javaMethod('move','java.nio.file.Files',src.toPath(),dst.toPath(),options);
% An unsupported atomic rename is a retained host failure, never a science retry.
end
