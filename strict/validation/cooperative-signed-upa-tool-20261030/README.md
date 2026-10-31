# Oriented UPA response prototype

`signed_upa.response` maps a fixed boresight, first transverse axis and ray
direction to unit-modulus spatial phases. The second axis is chosen once per
array as either `cross(boresight, first_axis)` or its negative; it must not be
selected separately for each user. The default negative phase and
column-fastest ordering match the supplied initializer's conjugate-transposed
row construction. No path loss, time-of-flight phase or channel conjugation is
included. Callers must preserve their own transmit/receive and outer-product
conventions. A ray along either normal returns all ones, without computing an
undefined azimuth. Invalid zero directions or inconsistent axes are rejected.

Run `python -B verify.py` with NumPy. The only scientific data read are the
previously saved canonical U6 NPZ in the adjacent validation directory; no
inputs or results are changed and no figures, optimization or new channel
realizations are generated. The check compares the two actually saved direct
satellite 2/user 2 and satellite 2/user 6 responses against both globally
oriented axes and the supplied initializer's folded expression, then tests
small synthetic boundary cases. The saved propagation phase and gain are
removed by normalization to the first entry.

This is a prototype and a diagnostic, **not a complete physical repair or
scientific acceptance**. The source also constructs satellite-to-RIS,
RIS-from-satellite, satellite-to-GEO-user, RIS-from-GEO and RIS-to-user
responses; all relevant links and their phase, propagation, receiver and
matrix-conjugation conventions require consistent explicit review and
application before a new input variant can be validated. The RIS-to-user
source additionally omits normalization of the projected direction; in the
present supplied geometry its intended direction is at boresight, so the
general off-boresight effect is not evidence of a large error in that case.
The final paper's displayed angular formula does not independently choose the
ECEF second-axis orientation or establish what was used for its figures.
Keep the original inputs, results and failures intact; a new oriented variant
and full published-budget MATLAB/Python results remain future work.

## Candidate six-factor generation

`links_v1.generate` takes explicit positions, frames, wavelength, physical
spacings and shapes, then returns candidate factors in memory only. It does not
copy or write the canonical NPZ, inject the factors into it, generate fading,
set large-scale gains, or run the optimizer. The table maps each source
initializer factor to the ray vector from the array, its fixed frame and the
source's subsequent channel expression. `a` is a column with negative spatial
phase; `*` below is complex conjugation and `H` is conjugate transpose.

| Factor (INIT lines) | Array frame | Ray vector | Source LOS use |
|---|---|---|---|
| `a_N_R` (105–118) | LEO j | RIS u − LEO j | `H_NR = a_N_R a_M_S^H` |
| `a_M_S` (128–140) | RIS u | LEO j − RIS u | same outer product |
| `a_N_U` (150–163) | LEO j | user u − LEO j | `H_NN = a_N_U` |
| `a_M_U` (172–185) | RIS u | user u − RIS u | `H_RU = a_M_U` |
| `a_N_K` (194–207) | LEO j | GEO user k − LEO j | `H_NG = a_N_K` |
| `a_M_G` (228–241) | RIS u | GEO satellite − RIS u | `H_GR = a_M_G^H` |

The source sets satellite frames at lines 33–48 and RIS frames at 81–95.
Its row steering has a positive phase and is conjugate-transposed. Where the
row contains `exp(-i 2π distance/wavelength)`, the resulting column therefore
contains `exp(+i 2π distance/wavelength)`; `a_M_S` has no propagation term.
The extra conjugate transpose in the outer product and `H_GR` is retained.
This faithfully describes the supplied code's algebra, without asserting that
its propagation convention or RIS receive/transmit orientation is uniquely
mandated by the paper. Source line 79 sets `d_M = 1`, although its nearby
comment says 0.01 m; the verification explicitly uses the executable value
1 m and the canonical data agree for the checks below. Source lines 477–479
also set `mu_RU=0`; the previously saved U6 variant has nonzero RIS-user mean.
This prototype does not choose or change that gain.

`python -B verify_links_v1.py` checks the six factors on the initializer's
finite six-user geometry and small synthetic examples. For satellite 2 and
user/RIS 2 it compares normalized saved `d_mean`, `G_mean`, `r_mean` and
`geo_G_mean` against both the fixed-oriented candidate and independently
reconstructed source-fold expression; only the latter is asserted to agree.
For the chosen frame orientation, maximum differences from the saved arrays
are respectively 1.98236, 1.98662, 0 and 0.03842, and source-fold differences
are below 1e-10. These are elementwise differences, not changes in achievable
rate or evidence of published-figure agreement. The `gt_second` covariance
cannot be rebuilt merely by changing this deterministic LOS prototype: its
large-scale gain, Rician model and source mapping must be reviewed separately.
The numerical comparisons above cover one satellite/RIS/user index and
normalized LOS arrays; the absolute propagation phase and every other index
were not independently compared. For example, the saved satellite 2 / user 3
response differs from an ideal boresight response by about 2.64e-6 after
normalization, so even near-boresight reconstruction needs care. For a general
off-boresight RIS-to-user ray, this candidate's direct signed projections also
do not reproduce the initializer's unnormalized-projection formula; the single
boresight example does not establish general equivalence.

The second-axis handedness is an explicit candidate fixed per array family,
not a recovered historical physical orientation. Array handedness, the 1 m
versus 0.01 m source discrepancy, publication versus initializer parameters,
path/common-phase treatment and the `mu_RU` override require adjudication
before full channels or figures are claimed corrected. Scalar GEO links do not
use these UPA factors and are not changed. MATLAB implementation, independent
dual-language checks, physical feasibility, full-budget convergence and
reference-figure comparisons remain open.

## Conditional GEO-interference second moment

`gt_second_v1.candidate_gt_second` constructs an **in-memory candidate** from
the actual saved `gt_second` and `d_mean`, and a caller-supplied oriented
`a_N_K`. The caller must provide the user and GEO-user coordinates, an explicit
co-location mapping, and the Rician factor. The function checks co-location,
unit-magnitude LOS vectors, Hermitian symmetry, positive semidefiniteness and
the source model `Q = mu/(1+beta) * (I + beta * a * a^H)`. It then applies
the diagonal unitary transformation `Q_new = D Q D^H`, where `D` maps the
saved LOS direction to the candidate. This preserves the existing gain,
isotropic scatter contribution, diagonal and eigenvalues; the common LOS
propagation phase cancels in `Q`. It makes no random draws and changes neither
the stored input nor any result. It rejects incompatible geometry or source
moments rather than silently adapting them.

`python -B verify_gt_second_v1.py` checks the actual saved U6/K1 input with
user 3 co-located with GEO user 1 and `beta_N=100`, for both global satellite
second-axis handedness choices. The positions are reconstructed from the
author's geometry; the saved NPZ does not itself bind those coordinates.
The co-location conclusion is conditional on that geometry. The maximum relative saved-model residual was
`7.9e-16`; the minimum eigenvalue before and after was `5.43513e-6`, and the
largest relative entrywise covariance change was `0.926125` for both choices.
An independent rank-one reconstruction agrees with the transformed result.
These checks concern only this stored input and conditional construction; the
handedness has not been recovered from a physical measurement, the other
channel components are not assembled here, and no corrected optimization,
MATLAB implementation or original-figure agreement is established.

## Conditional full distribution moments

`candidate_moments_v1.construct` assembles the four directional mean arrays
and the matching GEO second moment in memory. It retains each saved link's
first complex coefficient, copies the saved variances and limits, and checks
that co-located GEO and direct-link LOS directions agree. It also checks every
saved link against a reconstruction of the source's folded directions. The
actual U6/K1 test uses author-reconstructed coordinates, which are not bound by
the NPZ; it observes near-boresight residuals up to `2.65e-6` for direct and
`1.50e-5` for RIS-user directions. Its explicitly chosen thresholds apply only
to that reconstruction and are not paper-accuracy criteria.

`python -B verify_candidate_moments_v1.py` exercises all four global
satellite/RIS handedness combinations, preserves the saved inputs, and rejects
invalid geometry, inconsistent co-located directions, wrong dimensions and
negative variances. These are candidate distribution moments, not generated
channel samples, optimized beams, MATLAB validation, or figure reproduction.
The historic physical handedness remains unknown.
