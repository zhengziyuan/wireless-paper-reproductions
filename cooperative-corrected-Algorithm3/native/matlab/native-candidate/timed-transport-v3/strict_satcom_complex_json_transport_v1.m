function out=strict_satcom_complex_json_transport_v1(action,value)
% Pure complex-only JSON transport; no mutation of the original result.
% Real/imag numeric fields remain inspectable. IEEE hex sidecars preserve
% complex component bits, including signed zero, class and nonfinite values.
switch action
    case 'encode',out=encode_value(value);
    case 'decode',out=decode_value(value);
    otherwise,error('Unknown complex JSON transport action');
end
end

function out=encode_value(value)
if isnumeric(value)&&~isreal(value)
    assert(any(strcmp(class(value),{'double','single'})),'Unsupported complex numeric class');
    out=struct('codex_complex_transport','matlab_complex_json_v1','class',class(value), ...
        'shape',size(value),'real',real(value),'imag',imag(value), ...
        'real_ieee_hex',{cellstr(num2hex(real(value(:))))}, ...
        'imag_ieee_hex',{cellstr(num2hex(imag(value(:))))});
elseif isstruct(value)
    assert(~(isscalar(value)&&isfield(value,'codex_complex_transport')),'Reserved complex transport tag collision');
    out=value;names=fieldnames(value);
    for index=1:numel(value),for field=1:numel(names),out(index).(names{field})=encode_value(value(index).(names{field}));end,end
elseif iscell(value)
    out=cell(size(value));for index=1:numel(value),out{index}=encode_value(value{index});end
else
    out=value;
end
end

function out=decode_value(value)
if isstruct(value)&&isscalar(value)&&isfield(value,'codex_complex_transport')
    assert(strcmp(value.codex_complex_transport,'matlab_complex_json_v1'),'Unknown complex transport tag');
    assert(all(isfield(value,{'class','shape','real','imag','real_ieee_hex','imag_ieee_hex'})),'Incomplete complex transport');
    className=char(value.class);assert(any(strcmp(className,{'double','single'})),'Unsupported complex transport class');
    shape=double(value.shape(:).');assert(numel(shape)>=2&&all(isfinite(shape))&&all(shape>=0)&&all(shape==fix(shape)),'Invalid complex shape');
    re=decode_component(value.real_ieee_hex,className);im=decode_component(value.imag_ieee_hex,className);
    assert(numel(re)==prod(shape)&&numel(im)==prod(shape),'Complex transport size mismatch');
    out=reshape(complex(re,im),shape);
elseif isstruct(value)
    out=value;names=fieldnames(value);
    for index=1:numel(value),for field=1:numel(names),out(index).(names{field})=decode_value(value(index).(names{field}));end,end
elseif iscell(value)
    out=cell(size(value));for index=1:numel(value),out{index}=decode_value(value{index});end
else
    out=value;
end
end

function out=decode_component(hexValues,className)
if isempty(hexValues),out=zeros(0,1,className);return;end
hexRows=char(hexValues);width=16;if strcmp(className,'single'),width=8;end
assert(size(hexRows,2)==width&&all(ismember(lower(hexRows(:)),'0123456789abcdef')),'Invalid IEEE component hex');
if strcmp(className,'single')
    out=typecast(uint32(hex2dec(hexRows)),'single');
else
    high=uint64(hex2dec(hexRows(:,1:8)));low=uint64(hex2dec(hexRows(:,9:16)));
    out=typecast(bitor(bitshift(high,32),low),'double');
end
out=out(:);
end
