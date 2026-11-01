"""Audit a signed-direction ambiguity in the saved author-derived input.

This reads the existing canonical NPZ only; it runs no optimization and writes
no outputs. Coordinates and array spacing are transcribed from the author's
INIT_S_AO_beta_N_100_SCSI_u2_k1_j2.m, lines 22--24, 30--31, and 52--57.
"""
from pathlib import Path

import numpy as np


INPUT = (Path(__file__).resolve().parent.parent /
         "cooperative-author-U6-final-ground10-dual-full8-20261019-v1" /
         "inputs" / "canonical-eleven-arrays-and-limits.npz")


def ecef(latitude, longitude, radius):
    latitude, longitude = np.deg2rad([latitude, longitude])
    return radius * np.array([np.cos(latitude) * np.cos(longitude),
                              np.cos(latitude) * np.sin(longitude),
                              np.sin(latitude)])


with np.load(INPUT, allow_pickle=False) as data:
    direct = data["d_mean"]

# Satellite 2, users 2 and 6: a pair on opposite sides of the boresight.
satellite = ecef(0.0, 100.0, 6928e3)
boresight = -satellite / np.linalg.norm(satellite)
axis_x = ((satellite[2] * boresight[2] + satellite[1] * boresight[1]) /
          boresight[0] + satellite[0])
first_axis = satellite - np.array([axis_x, 0.0, 0.0])
first_axis /= np.linalg.norm(first_axis)
second_axis = np.cross(boresight, first_axis)

projections, observed, folded, oriented = [], [], [], []
for user_index, latitude in [(1, -2.0), (5, 2.0)]:
    direction = ecef(latitude, 100.0, 6378e3) - satellite
    direction /= np.linalg.norm(direction)
    signed = float(direction @ second_axis)
    response = direct[1, user_index]
    projections.append(signed)
    observed.append(response / response[0])
    # The author's row construction uses d/lambda=10 and a conjugate
    # transpose. acos plus sin folds the second direction component.
    folded.append(np.exp(-20j * np.pi * abs(signed)))
    oriented.append(np.exp(-20j * np.pi * signed))

assert projections[0] < 0 < projections[1]
assert np.isclose(projections[0], -projections[1], atol=1e-12)
assert np.max(np.abs(observed[0] - observed[1])) < 1e-10
assert np.allclose([observed[0][1], observed[1][1]], folded, atol=1e-10)
assert abs(oriented[0] - oriented[1]) > 1.9

print("second-axis projections:", *projections)
print("maximum difference between saved normalized steering vectors:",
      float(np.max(np.abs(observed[0] - observed[1]))))
print("separation between oriented adjacent-element ratios:",
      float(abs(oriented[0] - oriented[1])))
print("PASS: saved author input folds the two geometrically distinct directions")
