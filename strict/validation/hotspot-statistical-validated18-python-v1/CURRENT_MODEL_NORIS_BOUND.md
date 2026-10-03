# Qualified NoRIS current-model mismatch proof

Under the **current declared** full N16/J16/U6/K10 finite-Rician moment scene
at satellite Rician factor20dB, any beamformer with total power at most100W
has the source ratio-of-expected-powers NoRIS sum-rate at most
**5.44384144626725 bps/Hz**. The actual completed implementation gives
5.359550534711859. The supplied original EPS NoRIS point is
9.580010498687663. The latter cannot be obtained by improving an optimizer
under these *current* moments, even after dropping all NHU QoS constraints.

This is **not** a universal contradiction of the paper. The author's historical
receive gain, footprint coordinates and deterministic array responses are
unrecovered. The early per-feed ESA channel implies a nonuniform diagonal
NLoS covariance, while the later scalar-mu moment formula uses isotropic
covariance without a reported reduction condition. The current physically
declared correction is not literal recovery of that later formula.

## Complete algebra

The public matrices satisfy `l Q0 <= Q_u <= u Q0` for every HU, with
`l=0.9681625480122421`, `u=1.0328747149360558` and `0<l<=u<=2l`.
Also `lambda_max(Q0) <= 0.4117351574783424`.
For arbitrary original streams define `x_j=w_j^H Q0 w_j>=0` and
`S=sum_{j=1}^{16} x_j <=100 lambda_max(Q0)`.
Then `SINR_u <= u x_u/[1+l(S-x_u)]`, retaining every cochannel stream.

Merge any two HU energies `a,b>=0`, while keeping S and all other energies
fixed. Set `C=1+l(S-a-b)>0`. Cross-multiplication of the pair's two
`1+SINR` factors against the factor for the merged energy gives exactly

`RHS-LHS = u*a*b*[C*(2*l-u)+l^2*(a+b)] >=0`.

Thus merging cannot decrease this upper expression. Repeated merging places
all HU energy into one stream; unused NHU energy can only reduce the upper
expression. Consequently the sum rate is at most `log2(1+u S)`, and hence
at most `log2(1+u*100*lambda_max(Q0))`. NHU QoS was ignored only to enlarge
the feasible set, not changed in any simulation or optimizer.

## Matrix evidence and noise units

CURRENT_MODEL_NORIS_BOUND.json retains all six raw16x16 HU matrices and Q0,
the actual input/source hashes and independent80-digit matrix checks.
The executed source metric uses `real(w^H rawQ w)`, exactly equal to
`w^H H w` with `H=(rawQ+rawQ^H)/2`. Both matrix verifiers apply this
identity to every raw entry; no small antisymmetric rounding entry is dropped
with a tolerance. In the sandwich proof Q denotes this Hermitian H.
CURRENT_MODEL_NORIS_BOUND_EXACT_RATIONAL.json verifies positive Hermitian
LDL pivots for all13 matrices using exact fractions of every published
binary64 entry: six `Q_u-lQ0`, six `uQ0-Q_u`, and `lambda I-Q0`.
It separately verifies the merge identity in1000 exact rational cases.
No optimizer or reference-ordinate fitting is used in these checks.

The source channel-amplitude equation already divides satellite links by
`sqrt(k_B*T_R*B_W)`. Thus Q is noise normalized, the single receiver AWGN
variance in the SINR denominator is one, and W has units square-root watts.
The specified thermal parameters give physical noise
`6.497334194e-13 W`. Transforming both channels and noise back to watts
leaves the SINR unchanged. This proof concerns the approximate
ratio-of-expected-powers metric, **not** an exact `E[log2(1+SINR)]` bound.

To check the public exact witness with standard Python, run:

```text
python strict/audit_hotspot_no_ris_bound_certificate.py --input strict/validation/hotspot-statistical-validated18-python-v1/CURRENT_MODEL_NORIS_BOUND.json --output your-independent-bound-check.json
```

The separate no-ris-bound-manifest.json binds these added proof artifacts;
the original full243-start/54000-evaluation receipt retains its original
identity and is not upgraded into historical figure agreement. The original
reference artwork/manuscript and private filesystem paths are not published.
