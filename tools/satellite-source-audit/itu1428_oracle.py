"""Independent scalar transcription of ITU-R S.1428-1, recommends1 pp2-3.

Angles are degrees; gains are absolute dBi. No production evaluator is used.
The printed small-q gap at exactly33.1deg and boresight's open endpoint remain
explicit conventions. Algebraic thresholds are probed on both strict sides.
"""
import mpmath as mp


def binary(value):
    numerator, denominator = float(value).as_integer_ratio()
    return mp.mpf(numerator)/denominator


def parameters(q):
    if q < 20 or not mp.isfinite(q):
        raise ValueError('S.1428-1 requires finite D/lambda>=20')
    peak = 20*mp.log10(q) + mp.mpf('7.7' if q <= 100 else '8.4')
    plateau_end = 95/q if q <= 100 else mp.mpf('15.85')*q**mp.mpf('-.6')
    plateau = 29-25*mp.log10(95/q) if q <= 100 else -1+15*mp.log10(q)
    main_end = 20/q*mp.sqrt(peak-plateau)
    return peak, plateau, main_end, plateau_end


def db(q, angle, conventions=False):
    angle = abs(angle)
    if not mp.isfinite(angle) or angle > 180:
        raise ValueError('S.1428-1 angular range is +/-180deg')
    peak, plateau, main_end, plateau_end = parameters(q)
    if angle == 0 and not conventions:
        raise ValueError('Printed main-lobe domain excludes zero; use declared continuous peak convention')
    if q <= 25 and angle == mp.mpf('33.1') and not conventions:
        raise ValueError('Printed small-q clauses leave exactly33.1deg uncovered')
    if angle < main_end:
        return peak-mp.mpf('.0025')*(q*angle)**2
    if angle < plateau_end:
        return plateau
    if q <= 100:
        if angle <= mp.mpf('33.1'):
            return 29-25*mp.log10(angle)
        if angle <= 80:
            return mp.mpf(-9)
        if q <= 25:
            return mp.mpf(-5)
        return mp.mpf(-4 if angle <= 120 else -9)
    if angle < 10:
        return 29-25*mp.log10(angle)
    if angle < mp.mpf('34.1'):
        return 34-30*mp.log10(angle)
    if angle < 80:
        return mp.mpf(-12)
    return mp.mpf(-7 if angle < 120 else -12)


def linear(q, angle, conventions=False):
    return mp.power(10, db(q, angle, conventions)/10)


def stable_meridional_angle(radius, height, latitude_degrees):
    """Off-axis angle at an equatorial GT pointing at an equatorial GEO.

    The LEO shares the GEO longitude. atan2 avoids the cancellation of acos at
    exact boresight. This is an independent geometry identity for the admitted
    original configuration, not a general replacement of the scenario factory.
    """
    latitude = abs(latitude_degrees)*mp.pi/180
    rho = radius+height
    return mp.atan2(rho*mp.sin(latitude), rho*mp.cos(latitude)-radius)*180/mp.pi


def diameter_family_gain_floor(angle):
    """A lower gain valid for all standard-covered q>=20 at these GT angles.

    At boresight, the smallest peak is q20. Between10 and33.1deg, q<=100 is
    already beyond95/q<=4.75, while q>100 is beyond15.85*q^(-.6)<1.001.
    Both ranges are therefore diameter-independent side lobes. Taking their
    smaller gain per satellite is a relaxation, even if its independently
    selected q regimes cannot share one physical diameter.
    """
    if angle == 0:
        return linear(mp.mpf(20), angle, conventions=True), 'minimum_peak_at_q20'
    if not 10 < angle < mp.mpf('33.1'):
        raise ValueError('This analytic family floor is restricted to actual admitted boresight/side-lobe angles')
    small = 29-25*mp.log10(angle)
    large = 34-30*mp.log10(angle)
    return mp.power(10, min(small, large)/10), 'minimum_of_two_diameter_independent_side_lobes'
