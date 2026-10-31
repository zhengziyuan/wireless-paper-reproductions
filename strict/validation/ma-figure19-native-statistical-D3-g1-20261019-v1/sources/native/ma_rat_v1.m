classdef ma_rat_v1
    % Exact rational scalar backed by java.math.BigInteger, no Symbolic.
    % Binary64 primitives enter exactly. No double is used for comparisons.
    properties (SetAccess=private)
        n
        d
    end
    methods
        function q=ma_rat_v1(a,b)
            if nargin==0,a=0;end
            if nargin==1&&isa(a,'ma_rat_v1'),q=a;return;end
            if nargin<2
                if ischar(a),n=javaObject('java.math.BigInteger',a);d=ma_rat_v1.bi(1);
                elseif isa(a,'java.math.BigInteger'),n=a;d=ma_rat_v1.bi(1);
                else
                    assert(isa(a,'double')&&isscalar(a)&&isreal(a)&&isfinite(a),'MAExact:Primitive','Finite binary64 scalar required.');
                    bits=typecast(a,'uint64');exponent=double(bitand(bitshift(bits,-52),uint64(2047)));mantissa=bitand(bits,uint64(4503599627370495));
                    if exponent==0,power=-1074;else,mantissa=mantissa+uint64(4503599627370496);power=exponent-1075;end
                    n=javaObject('java.math.BigInteger',sprintf('%u',mantissa));d=ma_rat_v1.bi(1);
                    if bitget(bits,64),n=n.negate();end
                    if power>=0,n=n.shiftLeft(int32(power));else,d=d.shiftLeft(int32(-power));end
                end
            else
                if ischar(a),n=javaObject('java.math.BigInteger',a);else,n=a;end
                if ischar(b),d=javaObject('java.math.BigInteger',b);else,d=b;end
                assert(isa(n,'java.math.BigInteger')&&isa(d,'java.math.BigInteger'),'MAExact:Integer','Exact integer numerator/denominator required.');
            end
            assert(d.signum()~=0,'MAExact:ZeroDenominator','Zero exact denominator.');
            if d.signum()<0,n=n.negate();d=d.negate();end
            divisor=n.abs().gcd(d);q.n=n.divide(divisor);q.d=d.divide(divisor);
        end
        function c=plus(a,b)
            a=ma_rat_v1(a);b=ma_rat_v1(b);c=ma_rat_v1(a.n.multiply(b.d).add(b.n.multiply(a.d)),a.d.multiply(b.d));
        end
        function c=minus(a,b),c=ma_rat_v1(a)+(-ma_rat_v1(b));end
        function c=uminus(a),c=ma_rat_v1(a.n.negate(),a.d);end
        function c=mtimes(a,b)
            a=ma_rat_v1(a);b=ma_rat_v1(b);c=ma_rat_v1(a.n.multiply(b.n),a.d.multiply(b.d));
        end
        function c=mrdivide(a,b)
            a=ma_rat_v1(a);b=ma_rat_v1(b);assert(b.n.signum()~=0,'MAExact:ZeroDenominator','Division by exact zero.');c=ma_rat_v1(a.n.multiply(b.d),a.d.multiply(b.n));
        end
        function c=mpower(a,k)
            assert(isa(k,'double')&&isscalar(k)&&k==fix(k)&&k>=0&&k<=16,'MAExact:Power','Only small nonnegative integral powers are used.');c=ma_rat_v1(a.n.pow(int32(k)),a.d.pow(int32(k)));
        end
        function y=lt(a,b),y=ma_rat_v1.compare(a,b)<0;end
        function y=le(a,b),y=ma_rat_v1.compare(a,b)<=0;end
        function y=gt(a,b),y=ma_rat_v1.compare(a,b)>0;end
        function y=ge(a,b),y=ma_rat_v1.compare(a,b)>=0;end
        function y=eq(a,b),y=ma_rat_v1.compare(a,b)==0;end
        function y=ne(a,b),y=ma_rat_v1.compare(a,b)~=0;end
        function c=abs(a),c=ma_rat_v1(a.n.abs(),a.d);end
        function p=pack(a),p=struct('numerator',char(a.n.toString()),'denominator',char(a.d.toString()));end
        function x=display_log2(a)
            assert(a.n.signum()>0,'MAExact:Display','Positive ratio required.');x=ma_rat_v1.log2bi(a.n)-ma_rat_v1.log2bi(a.d);
        end
        function c=sqrt_upper(a)
            % Rational ceiling at2^-64, following the exact Schur bound.
            assert(a>=0,'MAExact:Sqrt','Nonnegative exact value required.');scale=ma_rat_v1.bi(1).shiftLeft(int32(64));
            numerator=a.n.multiply(scale).multiply(scale);scaled=numerator.divide(a.d);
            if numerator.remainder(a.d).signum()~=0,scaled=scaled.add(ma_rat_v1.bi(1));end
            root=ma_rat_v1.isqrt(scaled);if root.multiply(root).compareTo(scaled)<0,root=root.add(ma_rat_v1.bi(1));end
            c=ma_rat_v1(root,scale);assert(c*c>=a,'MAExact:Sqrt','Integer square-root upper proof failed.');
        end
    end
    methods (Static)
        function z=bi(x),z=javaObject('java.math.BigInteger',sprintf('%.0f',x));end
        function q=unpack(p),q=ma_rat_v1(p.numerator,p.denominator);end
        function v=compare(a,b)
            a=ma_rat_v1(a);b=ma_rat_v1(b);v=a.n.multiply(b.d).compareTo(b.n.multiply(a.d));
        end
        function root=isqrt(value)
            assert(value.signum()>=0,'MAExact:Sqrt','Nonnegative integer required.');
            if value.signum()==0,root=value;return;end
            root=ma_rat_v1.bi(1).shiftLeft(int32(ceil(double(value.bitLength())/2)));
            while true
                next=root.add(value.divide(root)).shiftRight(int32(1));
                if next.compareTo(root)>=0,return;end
                root=next;
            end
        end
        function x=log2bi(value)
            bits=double(value.bitLength());shift=max(0,bits-53);top=value.shiftRight(int32(shift));x=log2(str2double(char(top.toString())))+shift;
        end
    end
end
