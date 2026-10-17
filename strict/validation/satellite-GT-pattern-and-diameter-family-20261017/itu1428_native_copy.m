function gain=itu1428_native_copy(angle,q)
% Full ITU-R S.1428-1 recommends1, including transition and back lobes.
assert(q>=20 && abs(angle)<=180,'Outside ITU pattern range'); angle=abs(angle);
if q<=100
    gmax=20*log10(q)+7.7; transition=95/q; g1=29-25*log10(transition); phim=20/q*sqrt(gmax-g1);
    if angle<phim, g=gmax-2.5e-3*(q*angle)^2;
    elseif angle<transition, g=g1;
    elseif angle<=33.1, g=29-25*log10(angle);
    elseif angle<=80, g=-9;
    elseif q<=25, g=-5;
    elseif angle<=120, g=-4;
    else, g=-9; end
else
    gmax=20*log10(q)+8.4; g1=-1+15*log10(q); phim=20/q*sqrt(gmax-g1); phir=15.85*q^(-0.6);
    if angle<phim, g=gmax-2.5e-3*(q*angle)^2;
    elseif angle<phir, g=g1;
    elseif angle<10, g=29-25*log10(angle);
    elseif angle<34.1, g=34-30*log10(angle);
    elseif angle<80, g=-12;
    elseif angle<120, g=-7;
    else, g=-12; end
end
gain=10^(g/10);
end
