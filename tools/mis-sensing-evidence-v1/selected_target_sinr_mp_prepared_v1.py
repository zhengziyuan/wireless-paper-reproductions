"""Prepared independent high-precision target SINR checker, no execution on import.

This library is not admitted for the saved scientific input. A future separately
reviewed and guarded host must bind sources, input, precision, environment and
bounded outputs. It never performs optimization or draws random samples.

The finite saved phase components, placement and dimension inputs are treated as
exact binary64 numbers. Trigonometric response and reference conversion are
recomputed at arbitrary precision; this is not an interval error certificate or
historical MATLAB equivalence. Normalization is the explicitly assumed inverse-W,
raw-PRI, effective gain-one convention, not a confirmed paper reference unit.
"""
import math
import mpmath as mp


def binary64(v):
    v = float(v)
    if not math.isfinite(v):
        raise ValueError('nonfinite binary64 input')
    n, d = v.as_integer_ratio()
    return mp.mpf(n) / d


def target_sinrs(*, ms1, ms2, phi, theta, selections, azimuth_deg,
                 elevation_deg, spacing, incidence, echo_db, power_dbm, dps):
    """Re-evaluate selected placements with finite full-array sums at dps.

    This generic function accepts synthetic dimensions for testing. Users must
    separately bind it to the intended scenario and the saved precision inputs.
    selections are zero-based overlapping rectangular MS2 placement indices.
    """
    if type(dps) is not int or not 30 <= dps <= 120:
        raise ValueError('dps must be an integer between 30 and 120')
    mr, mc = ms1; nr, nc = ms2
    if any(type(x) is not int or x <= 0 for x in (mr, mc, nr, nc)) or nr > mr or nc > mc:
        raise ValueError('invalid array dimensions')
    if len(phi) != mr*mc or len(theta) != nr*nc:
        raise ValueError('phase dimensions differ')
    k = len(selections)
    if k == 0 or len(azimuth_deg) != k or len(elevation_deg) != k or len(incidence) != 2:
        raise ValueError('target dimensions differ')
    ucount = (mr-nr+1)*(mc-nc+1)
    if any(type(u) is not int or not 0 <= u < ucount for u in selections):
        raise ValueError('invalid placement')
    if any(len(x) != 2 for x in phi) or any(len(x) != 2 for x in theta):
        raise ValueError('phase must contain real/imaginary pairs')
    with mp.workdps(dps):
        p = [mp.mpc(binary64(a), binary64(b)) for a,b in phi]
        t = [mp.mpc(binary64(a), binary64(b)) for a,b in theta]
        inc = [binary64(x) for x in incidence]
        spacing = binary64(spacing)
        if spacing <= 0:
            raise ValueError('spacing must be positive')
        scale = 2*mp.pi*spacing
        coeff = mp.power(10, binary64(echo_db)/10)
        power = mp.power(10, (binary64(power_dbm)-30)/10)
        noise = 1/power
        coords = [(r,c) for r in range(mr) for c in range(mc)]
        fields = []
        for az,el in zip(azimuth_deg,elevation_deg):
            az = binary64(az)*mp.pi/180
            el = binary64(el)*mp.pi/180
            dx,dy = mp.sin(el)*mp.cos(az),mp.sin(el)*mp.sin(az)
            fields.append([mp.exp(mp.j*scale*((dx+inc[0])*r+(dy+inc[1])*c))
                           for r,c in coords])
        echoes = []
        for u in selections:
            r0,c0 = divmod(u,mc-nc+1)
            selection = {(r0+i)*mc+c0+j:i*nc+j for i in range(nr) for j in range(nc)}
            row=[]
            for field in fields:
                q = mp.fsum(field[i]*p[i]*(t[selection[i]] if i in selection else 1)
                            for i in range(mr*mc))
                row.append(coeff*abs(q)**4)
            echoes.append(row)
        answer=[]
        for target,row in enumerate(echoes):
            denom=noise+mp.fsum(row[j] for j in range(k) if j!=target)
            if not mp.isfinite(denom) or denom<=0:
                raise ValueError('invalid interference plus noise')
            value=row[target]/denom
            if not mp.isfinite(value) or value < 0:
                raise ValueError('invalid SINR')
            answer.append(mp.nstr(value,n=dps-5))
        return answer
