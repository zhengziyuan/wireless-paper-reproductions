function out=ma_statistical_value_bound_native_v1(action,model,indices,remaining)
% Exact product objective and conservative projection/Schur/Gershgorin bound.
Q=@(x)ma_rat_v1(double(x));pairs=size(model.pairs,1);sums=cell(1,pairs);
for pair=1:pairs
    z=ma_exact_complex_v1('make',0,0);for point=indices,z=ma_exact_complex_v1('add',z,model.terms{pair,point});end;sums{pair}=z;
end
if strcmp(action,'value')
    assert(numel(indices)==model.N,'MAExact:Leaf','Complete geometry required.');product=Q(1);
    if strcmp(model.mode,'MRT')
        for u=1:model.M
            den=model.base{u};for v=1:model.M,if v~=u,den=den+model.coefficient{u,v}*ma_exact_complex_v1('norm2',sums{model.pair_id(u,v)});end,end
            assert(den>0,'MAExact:Denominator','Positive exact MRT denominator required.');product=product+Q(0);product=product*(Q(1)+model.numerator{u}/den);
        end
    else
        sigma=cell(model.M);for u=1:model.M
            diagonal=model.base{u};for p=indices,diagonal=diagonal+model.diagonal{p,u};end
            sigma{u,u}=ma_exact_complex_v1('make',diagonal,0);
            for v=u+1:model.M,z=sums{model.pair_id(u,v)};sigma{u,v}=z;sigma{v,u}=ma_exact_complex_v1('conj',z);end
        end
        inverse=ma_exact_complex_v1('inverse_diagonal',sigma);
        for u=1:model.M,product=product*(Q(1)+model.eta{u}/inverse{u});end
    end
    out=product;return;
end
assert(strcmp(action,'upper'),'MAExact:Action','Only exact value/upper supported.');
r=model.N-numel(indices);assert(numel(remaining)>=r&&r>0,'MAExact:Frontier','Valid incomplete frontier required.');
eligible=false(1,model.count);eligible(remaining)=true;lower=cell(1,pairs);upper=lower;
for pair=1:pairs
    low=Q(0);
    for direction=1:8
        d=model.directions(direction,:);projection=Q(d(1))*sums{pair}.r+Q(d(2))*sums{pair}.i;
        order=model.projection_order{pair,direction};chosen=order(eligible(order));chosen=chosen(1:r);values=model.projections{pair,direction};
        for point=chosen,projection=projection+values{point};end
        if projection>0,candidate=projection^2/Q(sum(d.^2));if candidate>low,low=candidate;end,end
    end
    lower{pair}=low;
    if strcmp(model.mode,'ZF')
        rectangle=Q(0);
        for coordinate=[1,3] % positive real and positive imaginary projections
            values=model.projections{pair,coordinate};order=model.projection_order{pair,coordinate};chosen=order(eligible(order));
            if coordinate==1,a=sums{pair}.r;else,a=sums{pair}.i;end
            lo=a;hi=a;for k=1:r,lo=lo+values{chosen(k)};hi=hi+values{chosen(end-k+1)};end
            maximum=lo^2;if hi^2>maximum,maximum=hi^2;end;rectangle=rectangle+maximum;
        end
        upper{pair}=sqrt_upper(rectangle);
    end
end
product=Q(1);
if strcmp(model.mode,'MRT')
    for u=1:model.M
        den=model.base{u};for v=1:model.M,if v~=u,den=den+model.coefficient{u,v}*lower{model.pair_id(u,v)};end,end
        product=product*(Q(1)+model.numerator{u}/den);
    end
else
    diagonals=cell(1,model.M);
    for u=1:model.M
        d=model.base{u};for p=indices,d=d+model.diagonal{p,u};end
        order=model.diagonal_descending{u};chosen=order(eligible(order));for k=1:r,d=d+model.diagonal{chosen(k),u};end;diagonals{u}=d;
    end
    for u=1:model.M
        other=setdiff(1:model.M,u);trace=Q(0);gersh=[];offLower=Q(0);
        for v=other
            trace=trace+diagonals{v};row=diagonals{v};offLower=offLower+lower{model.pair_id(u,v)};
            for w=other,if w~=v,row=row+upper{model.pair_id(v,w)};end,end
            if isempty(gersh)||row>gersh,gersh=row;end
        end
        eigenUpper=trace;if gersh<trace,eigenUpper=gersh;end
        assert(eigenUpper>0,'MAExact:Schur','Positive covariance upper bound required.');schur=diagonals{u}-offLower/eigenUpper;
        if schur<0,schur=Q(0);end % Safe completion-free relaxation, no numeric tolerance.
        product=product*(Q(1)+model.eta{u}*schur);
    end
end
out=product;
end
