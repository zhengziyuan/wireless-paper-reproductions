"""Small read-only checks; no optimization, no modification of inputs."""
from pathlib import Path

import numpy as np
from signed_upa import response


def ecef(latitude, longitude, radius):
    lat, lon = np.deg2rad([latitude, longitude])
    return radius * np.array([np.cos(lat) * np.cos(lon),
                              np.cos(lat) * np.sin(lon), np.sin(lat)])


canonical = (Path(__file__).resolve().parent.parent /
             "cooperative-author-U6-final-ground10-dual-full8-20261019-v1" /
             "inputs" / "canonical-eleven-arrays-and-limits.npz")
with np.load(canonical, allow_pickle=False) as data:
    saved = data["d_mean"]

sat = ecef(0, 100, 6928e3)
b = -sat / np.linalg.norm(sat)
axis_x = (sat[2] * b[2] + sat[1] * b[1]) / b[0] + sat[0]
a = sat - np.array([axis_x, 0, 0])
a /= np.linalg.norm(a)
second = np.cross(b, a)
measurements = []
for index, lat in [(1, -2.0), (5, 2.0)]:
    d = ecef(lat, 100, 6378e3) - sat
    d /= np.linalg.norm(d)
    actual = saved[1, index] / saved[1, index, 0]
    signed = response(b, a, d, 4, 4, 10)
    reverse = response(b, a, d, 4, 4, 10, handedness=-1)
    p, q = a @ d, second @ d
    # This reproduces the source fold independently of the proposed response.
    source = np.exp(-20j * np.pi * (np.arange(4)[:, None] * p +
                                    np.arange(4)[None, :] * abs(q))).reshape(-1)
    measurements.append((q, np.max(np.abs(actual - signed)),
                         np.max(np.abs(actual - reverse)),
                         np.max(np.abs(actual - source))))
q0, q1 = measurements[0][0], measurements[1][0]
assert q0 < 0 < q1 and np.isclose(q0, -q1, atol=1e-12)
assert measurements[0][1] > 1.9 and measurements[1][1] < 1e-10
assert measurements[0][2] < 1e-10 and measurements[1][2] > 1.9
assert max(x[3] for x in measurements) < 1e-10

# Degenerate azimuth at both array normals is well defined in projection form.
for normal in ([0, 0, 1], [0, 0, -1]):
    np.testing.assert_allclose(response([0, 0, 1], [1, 0, 0], normal, 3, 2, .5),
                               np.ones(6), atol=1e-14)
# Exact first-axis plane, sign, ordering, and conjugation checks.
expected = np.exp(-2j * np.pi * .5 * .6 * np.repeat(np.arange(3), 2))
np.testing.assert_allclose(response([0, 0, 1], [1, 0, 0], [.6, 0, .8], 3, 2, .5), expected)
positive = response([0, 0, 1], [1, 0, 0], [.6, 0, .8], 3, 2, .5, phase_sign=1)
np.testing.assert_allclose(positive, np.conj(expected))
for args in [([0, 0, 0], [1, 0, 0], [0, 0, 1]),
             ([0, 0, 1], [0, 0, 1], [0, 0, 1]),
             ([0, 0, 1], [1, 0, 0], [0, 0, 0])]:
    try:
        response(*args, 2, 2, .5)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid frame or direction was accepted")

for user, (q, err, reverse, folded) in zip((2, 6), measurements):
    print(f"user {user}: second projection {q:.12g}; "
          f"fixed-basis error {err:.12g}; reversed-basis error {reverse:.12g}; "
          f"source-fold error {folded:.12g}")
print("PASS: actual saved two-user comparison and synthetic boundary checks")
