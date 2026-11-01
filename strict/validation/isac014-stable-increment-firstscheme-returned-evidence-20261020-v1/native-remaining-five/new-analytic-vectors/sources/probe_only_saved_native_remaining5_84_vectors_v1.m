function summary=probe_only_saved_native_remaining5_84_vectors_v1(planPath,outputRoot,expectedPlanSHA)
% New original-source evaluation, never recovery of historical memory vectors.
assert(~isfolder(outputRoot)&&~isfile(outputRoot),'Never repeat or overwrite probe');
[~,~,nativeEndian]=computer;assert(strcmp(nativeEndian,'L'),'Little-endian binary64 transport required');
assert(strcmp(is_file_sha(planPath),expectedPlanSHA),'Plan bytes differ');plan=jsondecode(fileread(planPath));
assert(plan.expected_returned_states==84&&plan.expected_components_per_precision==1596);
assert(strcmp(strrep(outputRoot,'\','/'),strrep(plan.fresh_output_directory,'\','/')),'Wrong new output');
before=is_watch(plan.watch_files);original=jsondecode(fileread(plan.original_scene));cfg=jsondecode(fileread(plan.configuration));
assert(numel(fieldnames(cfg))==28);vectors=cell(84,1);globalIndex=0;components=0;counts=struct('update_w',0,'update_theta',0,'update_rotation',0);started=tic;
names={'Rot-BS & Fix-RIS','Fix-BS & Rot-RIS','Fix-BS & Fix-RIS','Rot-BS & No-RIS','Fix-BS & No-RIS'};
flags=[1,0,1;0,1,1;0,0,1;1,0,0;0,0,0];
for schemeIndex=1:5
    item=plan.schemes(schemeIndex);ordinal=schemeIndex+1;assert(item.ordinal==ordinal&&strcmp(item.scheme_name,names{schemeIndex}));
    assert(strcmp(is_file_sha(item.input_MAT),item.input_MAT_SHA256));s=load(item.input_MAT,'scene','cfg','recording');
    assert(isequal(s.cfg,cfg)&&numel(s.recording.returns)==item.returned_states);
    expectedScene=original;if ~flags(schemeIndex,3),expectedScene.br_gain_re(:)=0;expectedScene.br_gain_im(:)=0;end
    assert(isequal(s.scene,expectedScene)&&isequal(s.recording.source_inputs.scene,s.scene));
    assert(isequal(s.recording.source_inputs.original_scene,original)&&isequal(s.recording.source_inputs.configuration,cfg));
    assert(s.recording.source_inputs.scheme_ordinal==ordinal&&strcmp(s.recording.source_inputs.scheme,names{schemeIndex}));
    assert(s.recording.extra_objective_gradient_RNG_calls==0&&logical(s.recording.initial_state.with_RIS)==logical(flags(schemeIndex,3)));
    c=s.scene;width=[ones(3,1)*pi/2*flags(schemeIndex,1);ones(3,1)*pi/2*flags(schemeIndex,2)];
    if isfield(c,'rotation_half_width'),width=width*c.rotation_half_width/(pi/2);end
    if isfield(c,'rotation_bs_half_width'),width(1:3)=c.rotation_bs_half_width*flags(schemeIndex,1);end
    if isfield(c,'rotation_ris_half_width'),width(4:6)=c.rotation_ris_half_width*flags(schemeIndex,2);end
    lower=s.recording.initial_state.lower;upper=s.recording.initial_state.upper;
    assert(isequal(lower,-width)&&isequal(upper,width)&&isequal(size(lower),[6,1])&&isequal(size(upper),[6,1]));
    blocks={'W','RCG','PGA'};methods={'update_w','update_theta','update_rotation'};
    if ~flags(schemeIndex,3),blocks={'W','PGA'};methods={'update_w','update_rotation'};end
    assert(item.returned_states==item.AO_blocks*numel(blocks));
    for localIndex=1:item.returned_states
        row=s.recording.returns{localIndex};kind=mod(localIndex-1,numel(blocks))+1;call=floor((localIndex-1)/numel(blocks))+1;
        assert(strcmp(row.block,blocks{kind})&&row.AO_iteration==call,'Wrong actual own-block index');
        assert(strcmp(class(row.W),'double')&&strcmp(class(row.theta),'double')&&strcmp(class(row.r),'double'));
        assert(isequal(size(row.W),[4,6])&&isequal(size(row.theta),[36,1])&&isequal(size(row.r),[6,1]));
        assert(all(isfinite(row.W(:)))&&all(isfinite(row.theta(:)))&&all(isfinite(row.r(:))));
        assert(isscalar(row.fixed_iota)&&isfinite(row.fixed_iota)&&row.fixed_iota>0);
        [metric,gw,gt,gr]=is_evaluate(row.W,row.theta,row.r,c,row.fixed_iota);
        method=methods{kind};if strcmp(method,'update_w'),g=gw;elseif strcmp(method,'update_theta'),g=gt;else,g=gr;end
        assert(strcmp(class(g),'double')&&all(isfinite(g(:))));
        globalIndex=globalIndex+1;components=components+numel(g);counts.(method)=counts.(method)+1;
        vectors{globalIndex}=struct('global_index',globalIndex,'scheme_ordinal',ordinal,'scheme_name',names{schemeIndex},'scheme_flags',flags(schemeIndex,:),...
            'actual_local_return_index',localIndex,'method',method,'call',call,'fixed_iota',row.fixed_iota,...
            'actual_native_metric',metric,'metric_utility_component_SHA256',is_component_sha(metric.utility),'metric_iota_component_SHA256',is_component_sha(metric.iota),...
            'gradient',g,'native_gradient_size',size(g),'native_gradient_class',class(g),'native_isreal',isreal(g),...
            'component_real_then_imag_F_binary64_SHA256',is_component_sha(g),...
            'original_W',row.W,'original_theta',row.theta,'original_r',row.r,'original_lower',lower,'original_upper',upper,...
            'original_W_component_SHA256',is_component_sha(row.W),'original_theta_component_SHA256',is_component_sha(row.theta),...
            'original_r_component_SHA256',is_component_sha(row.r),'fixed_iota_component_SHA256',is_component_sha(row.fixed_iota),...
            'lower_component_SHA256',is_component_sha(lower),'upper_component_SHA256',is_component_sha(upper));
    end
end
assert(globalIndex==84&&components==1596&&counts.update_w==34&&counts.update_theta==16&&counts.update_rotation==34);
after=is_watch(plan.watch_files);assert(isequal(before,after),'Watched source/input bytes changed');mkdir(outputRoot);
probe_metadata=struct('schema','actual-new-native-remaining5-84-own-block-analytic-vectors-v1','plan_SHA256',expectedPlanSHA,...
    'source_before',{before},'source_after',{after},'source_input_interval_closed',true,'native_returned_state_count',84,...
    'component_count_per_precision',1596,'counts',counts,'excluded_old_firstscheme',true,'five_final_states_not_included',true,...
    'historical_native_vectors_recovered',false,'new_evaluate_calls',84,'optimizer_update_MC_RNG_or_MP_calls',0,'elapsed_seconds',toc(started));
save(fullfile(outputRoot,'actual-new-native84-analytic-vectors.mat'),'vectors','probe_metadata','-v7');
fid=fopen(fullfile(outputRoot,'actual-native84-probe-completion.json'),'w');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(probe_metadata));summary=probe_metadata;
end

function rows=is_watch(pins)
rows=cell(numel(pins),1);for k=1:numel(pins),h=is_file_sha(pins(k).path);assert(strcmp(h,pins(k).SHA256),'Frozen source/input changed');rows{k}=struct('path',pins(k).path,'SHA256',h);end
end

function value=is_file_sha(path)
fid=fopen(path,'rb');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');md=java.security.MessageDigest.getInstance('SHA-256');md.update(bytes);value=lower(reshape(dec2hex(typecast(md.digest(),'uint8'),2).',1,[]));
end

function value=is_component_sha(g)
realBytes=typecast(real(g(:)),'uint8');imagBytes=typecast(imag(g(:)),'uint8');bytes=[realBytes(:);imagBytes(:)];md=java.security.MessageDigest.getInstance('SHA-256');md.update(bytes);value=lower(reshape(dec2hex(typecast(md.digest(),'uint8'),2).',1,[]));
end

function [R,dR]=is_rotation(r)
x=r(1);y=r(2);z=r(3);cx=cos(x);sx=sin(x);cy=cos(y);sy=sin(y);cz=cos(z);sz=sin(z);
rx=[1,0,0;0,cx,-sx;0,sx,cx];ry=[cy,0,sy;0,1,0;-sy,0,cy];rz=[cz,-sz,0;sz,cz,0;0,0,1];
dx=[0,0,0;0,-sx,-cx;0,cx,-sx];dy=[-sy,0,cy;0,0,0;-cy,0,-sy];dz=[-sz,-cz,0;cz,-sz,0;0,0,0];
R=rx*ry*rz;dR={dx*ry*rz,rx*dy*rz,rx*ry*dz};
end

function [a,da]=is_response(coords,center,u,r,c)
[R,dR]=is_rotation(r);u=u(:);cosine=R(:,3)'*u;wave=2*pi/c.wavelength;
t=exp(1i*wave*((coords*R'+center(:)')*u));
if cosine<=0,a=zeros(size(t));da=zeros(numel(t),3);return;end
b=c.directivity_exponent;amp=sqrt(c.maximum_gain)*cosine^(b/2);a=amp*t;da=zeros(numel(t),3);
for d=1:3
    damp=sqrt(c.maximum_gain)*(b/2)*cosine^(b/2-1)*(dR{d}(:,3)'*u);
    dphase=wave*(coords*dR{d}'*u);da(:,d)=t.*(damp+1i*amp*dphase);
end
end

function base=is_channel_base(r,c)
cb=c.bs_coordinates;cr=c.ris_coordinates;M=size(cb,1);N=size(cr,1);K=numel(c.noise);A=size(c.bt_directions,1);links=K+A;
h=zeros(M,links);g=zeros(N,links);dh=zeros(M,links,6);dg=zeros(N,links,6);
for k=1:K
    for p=1:size(c.bu_directions,2)
        [a,da]=is_response(cb,c.bs_center,reshape(c.bu_directions(k,p,:),3,1),r(1:3),c);
        gain=c.bu_gain_re(k,p)+1i*c.bu_gain_im(k,p);h(:,k)=h(:,k)+gain*a;dh(:,k,1:3)=dh(:,k,1:3)+reshape(gain*da,M,1,3);
        [a,da]=is_response(cr,c.ris_center,reshape(c.ru_directions(k,p,:),3,1),r(4:6),c);
        gain=c.ru_gain_re(k,p)+1i*c.ru_gain_im(k,p);g(:,k)=g(:,k)+gain*a;dg(:,k,4:6)=dg(:,k,4:6)+reshape(gain*da,N,1,3);
    end
end
for a=1:A
    [h(:,K+a),der]=is_response(cb,c.bs_center,c.bt_directions(a,:),r(1:3),c);dh(:,K+a,1:3)=reshape(der,M,1,3);
    [g(:,K+a),der]=is_response(cr,c.ris_center,c.rt_directions(a,:),r(4:6),c);dg(:,K+a,4:6)=reshape(der,N,1,3);
end
B=zeros(M,N);dB=zeros(M,N,6);
for p=1:size(c.br_directions,1)
    [ab,dab]=is_response(cb,c.bs_center,c.br_directions(p,:),r(1:3),c);
    [ar,dar]=is_response(cr,c.ris_center,c.rb_directions(p,:),r(4:6),c);
    gain=c.br_gain_re(p)+1i*c.br_gain_im(p);B=B+gain*ab*ar';
    for d=1:3,dB(:,:,d)=dB(:,:,d)+gain*dab(:,d)*ar';dB(:,:,d+3)=dB(:,:,d+3)+gain*ab*dar(:,d)';end
end
base={h,g,dh,dg,B,dB};
end

function [f,jac,B,g]=is_channels(theta,r,c,fixedRotationBase)
if nargin<4 || isempty(fixedRotationBase),fixedRotationBase=is_channel_base(r,c);end
h=fixedRotationBase{1};g=fixedRotationBase{2};dh=fixedRotationBase{3};dg=fixedRotationBase{4};B=fixedRotationBase{5};dB=fixedRotationBase{6};
[M,links]=size(h);f=h+B*(theta.*g);jac=zeros(M,links,6);
for d=1:6,jac(:,:,d)=dh(:,:,d)+dB(:,:,d)*(theta.*g)+B*(theta.*dg(:,:,d));end
end

function [metric,gw,gt,gr]=is_evaluate(W,theta,r,c,iota,fixedChannelBundle,fixedRotationBase)
% Full bundle: fixed-theta W block; base: fixed-r RIS block. No stale reuse.
if nargin<6 || isempty(fixedChannelBundle)
    if nargin<7,[f,jac,B,g]=is_channels(theta,r,c);else,[f,jac,B,g]=is_channels(theta,r,c,fixedRotationBase);end
else,f=fixedChannelBundle{1};jac=fixedChannelBundle{2};B=fixedChannelBundle{3};g=fixedChannelBundle{4};end
K=numel(c.noise);fc=f(:,1:K);fs=f(:,K+1:end);Y=fc'*W;Z=fs'*W;
powers=abs(Y).^2;mask=true(size(powers));mask(sub2ind(size(mask),(1:K)',(1:K)'))=false;
signal=abs(diag(Y(:,1:K))).^2;interference=c.noise(:)+sum(powers.*mask,2);total=signal+interference;
rate=sum(log1p(signal./interference))/log(2);p=sum(abs(Z).^2,2);pd=c.desired_pattern(:);energy=pd'*pd;
if nargin<5 || isempty(iota)
    overlap=pd'*p;if overlap<=c.iota_denominator_epsilon,error('Exact iota* undefined at zero overlap.');end
    iota=(p'*p)/overlap;
end
D=iota^2*energy;residual=p-iota*pd;nmse=(residual'*residual)/D;
metric=struct('utility',rate-c.rho*nmse,'rate',rate,'nmse',nmse,'iota',iota,'pattern',p','sinr',(signal./interference)');
if nargout<2,return;end
coefficient=repmat(-signal./(total.*interference),1,size(W,2));
for k=1:K,coefficient(k,k)=1/total(k);end
gw=2*fc*(coefficient.*Y)/log(2)-4*c.rho*fs*(residual.*Z)/D;
bw=B'*W;gt=zeros(numel(theta),1);
for k=1:K,gt=gt+2*conj(g(:,k)).*(bw*(coefficient(k,:).*conj(Y(k,:))).')/log(2);end
for a=1:numel(pd),gt=gt-4*c.rho*residual(a)/D*conj(g(:,K+a)).*(bw*conj(Z(a,:)).');end
gr=zeros(6,1);
for d=1:6
    dY=jac(:,1:K,d)'*W;dZ=jac(:,K+1:end,d)'*W;
    derivatives=2*real(conj(Y).*dY);ds=real(diag(derivatives(:,1:K)));dinterference=sum(derivatives.*mask,2);
    dr=sum(ds./total-signal./(total.*interference).*dinterference)/log(2);dp=2*real(sum(conj(Z).*dZ,2));gr(d)=dr-2*c.rho*residual'*dp/D;
end
end

