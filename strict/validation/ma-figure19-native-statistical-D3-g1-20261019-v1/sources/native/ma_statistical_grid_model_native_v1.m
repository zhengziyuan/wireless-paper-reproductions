function model=ma_statistical_grid_model_native_v1(c,N,D,mode)
% Native frozen binary64 phasors -> exact rational statistical Eq13/Eq39.
% No instantaneous channel samples, beamforming optimizer or Python winner.
assert(any(strcmp(mode,{'MRT','ZF'}))&&N>numel(c.beta),'MAExact:Scope','MRT/ZF with N>M required.');
assert(isscalar(D)&&D>=2&&D==fix(D),'MAExact:Grid','Integral grid axis required.');
x=linspace(c.region_lower(1),c.region_upper(1),D);y=linspace(c.region_lower(2),c.region_upper(2),D);
grid=zeros(D^2,2);k=1;for a=x,for b=y,grid(k,:)=[a,b];k=k+1;end,end
P=size(grid,1);M=numel(c.beta);Q=@(v)ma_rat_v1(double(v));Z=@(a,b)ma_exact_complex_v1('make',a,b);
model=struct('mode',mode,'N',N,'M',M,'D',D,'grid',grid,'count',P,'pairs',nchoosek(1:M,2),...
    'directions',[1,0;1,1;0,1;-1,1;-1,0;-1,-1;0,-1;1,-1]);
model.pair_id=zeros(M);for p=1:size(model.pairs,1),u=model.pairs(p,1);v=model.pairs(p,2);model.pair_id(u,v)=p;model.pair_id(v,u)=p;end
points=cell(P,2);for p=1:P,for d=1:2,points{p,d}=Q(grid(p,d));end,end
spacing=Q(c.minimum_distance)^2;compatible=false(P);
for p=1:P,for q=1:P,compatible(p,q)=(points{p,1}-points{q,1})^2+(points{p,2}-points{q,2})^2>=spacing;end,end
model.compatible=compatible;
beta=cell(1,M);kap=beta;noise=beta;for u=1:M,beta{u}=Q(c.beta(u));kap{u}=Q(c.rician(u));noise{u}=Q(c.noise(u));end
power=Q(c.power);model.base=cell(1,M);model.numerator=cell(1,M);model.eta=cell(1,M);model.coefficient=cell(M);
model.terms=cell(size(model.pairs,1),P);model.diagonal=cell(P,M);
primitive=struct('grid',grid,'beta',c.beta,'rician',c.rician,'noise',c.noise,'power',c.power,...
    'directions',c.directions,'wavelength',c.wavelength,'minimum_distance',c.minimum_distance,...
    'region_lower',c.region_lower,'region_upper',c.region_upper,'mode',mode,'N',N,'D',D,...
    'actual_exact_squared_spacing_compatibility',compatible);
if strcmp(mode,'MRT')
    sumBeta=Q(0);for u=1:M,sumBeta=sumBeta+beta{u};end
    for u=1:M
        model.numerator{u}=beta{u}^2*(Q(N*N)+Q(N)*(Q(2)*kap{u}+Q(1))/(kap{u}+Q(1))^2);
        model.base{u}=noise{u}*Q(N)*sumBeta/power;
        for v=1:M
            if u==v,continue;end
            model.coefficient{u,v}=beta{u}*beta{v}*kap{u}*kap{v}/((kap{u}+Q(1))*(kap{v}+Q(1)));
            model.base{u}=model.base{u}+beta{u}*beta{v}*Q(N)*(kap{u}+kap{v}+Q(1))/((kap{u}+Q(1))*(kap{v}+Q(1)));
        end
    end
    primitive.pair_phasors=complex(zeros(P,size(model.pairs,1)));wave=2*pi/c.wavelength;
    for pair=1:size(model.pairs,1)
        u=model.pairs(pair,1);v=model.pairs(pair,2);phasor=exp(1i*wave*(grid*(c.directions(u,:)-c.directions(v,:))'));
        primitive.pair_phasors(:,pair)=phasor;
        for point=1:P,model.terms{pair,point}=Z(Q(real(phasor(point))),Q(imag(phasor(point))));end
    end
else
    h=exp(2i*pi/c.wavelength*(grid*c.directions'));scale=sqrt(c.rician(:)./(c.rician(:)+1));
    primitive.LOS_phasors=h;primitive.binary64_sqrt_scale=scale;weighted=cell(P,M);
    % Match the declared Fraction(h.real)*Fraction(scale) convention exactly;
    % no binary64 weighted-product rounding is hidden in the rational model.
    for p=1:P,for u=1:M,weighted{p,u}=Z(Q(real(h(p,u)))*Q(scale(u)),Q(imag(h(p,u)))*Q(scale(u)));end,end
    for u=1:M
        model.base{u}=Q(1)/(kap{u}+Q(1));model.eta{u}=power*beta{u}*Q(N-M)/(Q(M)*noise{u});
        for p=1:P,model.diagonal{p,u}=ma_exact_complex_v1('norm2',weighted{p,u})/Q(N);end
    end
    for pair=1:size(model.pairs,1)
        u=model.pairs(pair,1);v=model.pairs(pair,2);
        for p=1:P
            z=ma_exact_complex_v1('mul',ma_exact_complex_v1('conj',weighted{p,u}),weighted{p,v});model.terms{pair,p}=Z(z.r/Q(N),z.i/Q(N));
        end
    end
end
model.projections=cell(size(model.pairs,1),8);model.projection_order=cell(size(model.pairs,1),8);
for pair=1:size(model.pairs,1)
    for direction=1:8
        values=cell(1,P);d=model.directions(direction,:);
        for p=1:P,z=model.terms{pair,p};values{p}=Q(d(1))*z.r+Q(d(2))*z.i;end
        model.projections{pair,direction}=values;model.projection_order{pair,direction}=sort_exact(values,false);
    end
end
model.diagonal_descending=cell(1,M);
if strcmp(mode,'ZF'),for u=1:M,model.diagonal_descending{u}=sort_exact(model.diagonal(:,u)',true);end,end
model.primitive_floating_input=primitive;
model.objective_scope='Exact rational product(1+statisticalSINR) of native frozen binary64 primitives. Not an exact symbolic trigonometric channel or historical author BF protocol.';
end

function order=sort_exact(values,descending)
order=1:numel(values);
for i=2:numel(order)
    point=order(i);j=i-1;
    while j>=1
        move=values{order(j)}>values{point};if descending,move=values{order(j)}<values{point};end
        if ~move,break;end
        order(j+1)=order(j);j=j-1;
    end
    order(j+1)=point;
end
end
