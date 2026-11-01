function out=ma_exact_complex_v1(action,varargin)
% Independent exact complex rational arithmetic; no LAPACK or MC.
switch action
    case 'make',out=struct('r',ma_rat_v1(varargin{1}),'i',ma_rat_v1(varargin{2}));
    case 'add',a=varargin{1};b=varargin{2};out=make(a.r+b.r,a.i+b.i);
    case 'sub',a=varargin{1};b=varargin{2};out=make(a.r-b.r,a.i-b.i);
    case 'conj',a=varargin{1};out=make(a.r,-a.i);
    case 'mul',a=varargin{1};b=varargin{2};out=make(a.r*b.r-a.i*b.i,a.r*b.i+a.i*b.r);
    case 'div'
        a=varargin{1};b=varargin{2};den=b.r^2+b.i^2;assert(den>0,'MAExact:Pivot','Zero exact complex pivot.');out=make((a.r*b.r+a.i*b.i)/den,(a.i*b.r-a.r*b.i)/den);
    case 'norm2',a=varargin{1};out=a.r^2+a.i^2;
    case 'inverse_diagonal'
        matrix=varargin{1};m=size(matrix,1);a=cell(m,2*m);
        for i=1:m,for j=1:m,a{i,j}=matrix{i,j};a{i,m+j}=make(double(i==j),0);end,end
        for k=1:m
            % Positive definite covariance: no approximate pivoting needed.
            pivot=a{k,k};assert(pivot.i==0&&pivot.r>0,'MAExact:SPD','Leading exact SPD pivot must be positive real.');
            for j=1:2*m,a{k,j}=ma_exact_complex_v1('div',a{k,j},pivot);end
            for i=1:m
                if i==k,continue;end
                factor=a{i,k};for j=1:2*m,a{i,j}=ma_exact_complex_v1('sub',a{i,j},ma_exact_complex_v1('mul',factor,a{k,j}));end
            end
        end
        out=cell(1,m);for i=1:m,v=a{i,m+i};assert(v.i==0&&v.r>0,'MAExact:SPD','Positive exact inverse diagonal required.');out{i}=v.r;end
    otherwise,error('MAExact:Action','Unknown exact complex action.');
end
end

function z=make(r,i),z=struct('r',ma_rat_v1(r),'i',ma_rat_v1(i));end
