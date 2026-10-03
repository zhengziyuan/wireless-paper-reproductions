# Source-distance correction and evidence boundary

The author numerical paragraph and Table3-1 require distances between hotspot
users to be between 10m and 20m, while keeping equal RIS-to-HU large-scale
attenuation at 400m. Exact historical user/feed coordinates are not supplied.
This is a scenario contract, not a convergence or curve-fitting criterion.

## Confirmed reconstruction error

The earlier independent generator used a 15m-radius regular polygon at each
U>1, with U1 at the center. It produced distances above 20m for every U2..6:
for example U2 has 30m, U3 has 25.9808m, and opposite U4/U6 users have 30m.
The U6 nearest-neighbor distance of 15m did **not** establish the all-pair
source condition. This was an implementation error, not an author-paper
erratum. Completed old statistical18 receipts and seven old instantaneous
MC checkpoints remain preserved with their true executed-source identity;
their internal algorithm gates do not certify this original scenario.

## Declared compliant geometry

`scenario_geometry.py` and `strict_hotspot_geometry.m` use the same original
full finite-Rician channel equations, sample dimensions and random draws,
but declare a fixed 10m-radius regular polygon for U2..6 and U1 at the center.
The generators check every pair, not only neighbors. The exact pair ranges are:

| HU count | Minimum pair distance (m) | Maximum pair distance (m) |
| --- | ---: | ---: |
| 1 | not applicable | not applicable |
| 2 | 20 | 20 |
| 3 | 17.320508 | 17.320508 |
| 4 | 14.142136 | 20 |
| 5 | 11.755705 | 19.021130 |
| 6 | 10 | 20 |

The source does not require U-sweep coordinates to be nested. This explicitly
declared polygon is not claimed as the author's historical placement.
Changing U retains J=N=16 and K=16-U. Feed-center placement, common 400m
RIS-to-HU power gain, RIS center, all covariances, the shared satellite-RIS
channel, transmit power, QoS, algorithm, iteration budgets and stop tests
are otherwise unchanged. User offsets affect the actual propagation phases
and satellite distances, as in the original channel model.

`verify_geometry.py` independently checks all six source-distance cases,
unchanged NHU/shared-G means and variances/ground variances/phase initializer,
and HU permutation invariance of exact second moments, statistical phase
criterion, analytical gradient and rate. It rejects the old 15m geometry.
`strict_hotspot_geometry_test.m` independently regenerates the deterministic
full-model fields from a shared generated numeric fixture; the MATLAB
configuration scalars are doubles, not integer-typed arithmetic operands.
These are component tests, not optimized paper curves.

## Genuine model fingerprints, not an explanation by curve fitting

The old regular polygon causes every even-U design to have two users on the
RIS-cluster-center line. Their ground far-field steering vectors are equal
up to a scalar phase; this remains true at radius10. The new declared geometry
has direct LoS row correlations at least 0.99999898666, so near-rank-one
direct channels and stationary local designs are plausible. The independent
HU permutation test excludes the checked index-order errors but does not
prove a global optimum or that the original author used these coordinates.

The old statistical18 bank has a large independently measured discrepancy
from the original54 EPS ordinates and must not be described as close. In
particular U1 is unchanged by this distance correction, so a U1 Rician trend
disagreement cannot be attributed to the radius correction alone. Unreported
feed centers, receive gains, LoS phase references, numerical initialization,
original printed versus explicitly corrected QoS, and publisher-version
equation conformance remain distinct uncertainties. Reference ordinates are
never passed into the optimizer. A matching-looking plot cannot resolve them.

## New source-bound entries and actual results

The distance-only single-start statistical entry is `run_statistical_geometry.py`
with immutable `statistical_geometry_config.json`; its MATLAB counterpart is
`run_strict_hotspot_statistical_geometry`. Its fresh18-point bank completed
all cases but retained U6/beta0 two-stage non-convergence at20000, so it is not
a successful full-bank certificate. The separate uniform-ensemble entry is
`run_statistical_validated.py` with `statistical_validated_config.json` and
MATLAB `run_strict_hotspot_statistical_validated`. It runs every declared0..U
start for every scheme; the disclosed100000 safety cap follows an independently
verified identical-stage39910-iteration stop. No phase threshold changes.
The new instantaneous entry is
`run_instantaneous_geometry.py` with `instantaneous_geometry_config.json`;
its MATLAB counterpart is `run_strict_hotspot_instantaneous_geometry`.
Each binds the actual new geometry, numerical algorithm modules, runner and
configuration before/after execution. Old checkpoints cannot be resumed into
the new branch. `--full-case` is one complete physical optimization, not a
1000-realization instantaneous figure bank.

A representative U4/satellite-Rician20 statistical case actually completed
all three original-model designs, their original stopping tests, four gates
and 1000 independent finite-Rician moment draws in 39.2679s. A representative
instantaneous N16/J16/U6/K10/M25 case actually completed original QT/SDP and
all1000 rounding candidates, AO/two-stage/NoRIS/RandRIS and all four gates in
144.2004s. These are complete cases only. The distinct new statistical18 and
instantaneous1000-realization CDF batches were started. The single-start
statistical bank completed with its one genuine capped phase retained; the
new ensemble bank must separately execute every required start. No partial batch,
source-compatible local solution or component fixture is a final-publisher
or historical-curve certificate. `full_reproduction_pass` remains false.
