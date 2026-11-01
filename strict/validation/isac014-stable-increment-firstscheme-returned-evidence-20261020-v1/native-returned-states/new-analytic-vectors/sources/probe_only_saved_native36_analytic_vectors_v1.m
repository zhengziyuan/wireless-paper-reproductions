function summary=probe_only_saved_native36_analytic_vectors_v1(inputMAT,outputRoot,expectedMAT)
% New source-bound evaluation at already saved inputs, not historical memory.
assert(~isfolder(outputRoot)&&~isfile(outputRoot),'Never overwrite or repeat probe output');
[~,~,nativeEndian]=computer;assert(strcmp(nativeEndian,'L'),'Explicit little-endian binary64 transport required');
before=is_file_sha(inputMAT);assert(strcmp(before,expectedMAT),'Original closed MAT changed');
s=load(inputMAT,'scene','cfg','recording');assert(numel(s.recording.returns)==36);
assert(s.scene.rho==10&&numel(s.scene.noise)==2&&size(s.scene.bs_coordinates,1)==4&&size(s.scene.ris_coordinates,1)==36);
assert(numel(fieldnames(s.cfg))==28);c=s.scene;names=fieldnames(s.cfg);
for k=1:numel(names),assert(isequal(c.(names{k}),s.cfg.(names{k})));end
vectors=cell(36,1);counts=struct('update_w',0,'update_theta',0,'update_rotation',0);started=tic;
expectedBlocks={'W','RCG','PGA'};methods={'update_w','update_theta','update_rotation'};
for index=1:36
    row=s.recording.returns{index};kind=mod(index-1,3)+1;call=floor((index-1)/3)+1;
    assert(strcmp(row.block,expectedBlocks{kind})&&row.AO_iteration==call,'Actual native source order changed');
    assert(isequal(size(row.W),[4,6])&&isequal(size(row.theta),[36,1])&&isequal(size(row.r),[6,1]));
    assert(isscalar(row.fixed_iota)&&isfinite(row.fixed_iota)&&row.fixed_iota>0);
    [~,gw,gt,gr]=is_evaluate(row.W,row.theta,row.r,c,row.fixed_iota);
    if kind==1,g=gw;elseif kind==2,g=gt;else,g=gr;end
    assert(strcmp(class(g),'double')&&all(isfinite(g(:))),'Nonfinite/unsupported new native derivative');
    counts.(methods{kind})=counts.(methods{kind})+1;
    vectors{index}=struct('actual_return_index',index,'method',methods{kind},'call',call,'fixed_iota',row.fixed_iota,...
        'gradient',g,'native_gradient_size',size(g),'native_gradient_class',class(g),'native_isreal',isreal(g),...
        'component_real_then_imag_F_binary64_SHA256',is_component_sha(g),...
        'original_status',row.original_status,'original_W',row.W,'original_theta',row.theta,'original_r',row.r);
end
assert(counts.update_w==12&&counts.update_theta==12&&counts.update_rotation==12);
after=is_file_sha(inputMAT);assert(strcmp(before,after),'Original input interval changed');
mkdir(outputRoot);probe_metadata=struct('schema','new-native36-saved-state-analytic-vector-execution-v1',...
    'original_MAT_SHA256',before,'source_input_interval_closed',true,'native_returned_state_count',36,...
    'counts',counts,'final_ownstate_not_included',true,'historical_native_vectors_recovered',false,...
    'new_evaluate_calls',36,'optimizer_update_MC_RNG_or_MP_calls',0,'elapsed_seconds',toc(started));
save(fullfile(outputRoot,'actual-new-native36-analytic-vectors.mat'),'vectors','probe_metadata','-v7');
fid=fopen(fullfile(outputRoot,'actual-native36-probe-completion.json'),'w');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(probe_metadata));summary=probe_metadata;
end

function value=is_file_sha(path)
fid=fopen(path,'rb');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));bytes=fread(fid,Inf,'*uint8');
md=java.security.MessageDigest.getInstance('SHA-256');md.update(bytes);value=lower(reshape(dec2hex(typecast(md.digest(),'uint8'),2).',1,[]));
end

function value=is_component_sha(g)
bytes=[typecast(real(g(:)),'uint8');typecast(imag(g(:)),'uint8')];
md=java.security.MessageDigest.getInstance('SHA-256');md.update(bytes);value=lower(reshape(dec2hex(typecast(md.digest(),'uint8'),2).',1,[]));
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

