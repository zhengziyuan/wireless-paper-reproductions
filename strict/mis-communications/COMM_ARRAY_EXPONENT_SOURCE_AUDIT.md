# Array-response and SNR source audit

This audit concerns the supplied R2 manuscript, not an official publisher
erratum. Its TeX SHA256 is
`6e27fb9fd2ba0decc9d7bcfc54bcb73612553f91f6df923ab502e7d561058cb0`.
The source equations, actual saved graphics, and current reconstruction are
different evidence objects. None is silently substituted for another.

## Explicit manuscript inconsistencies

1. The BS response in equation (3) uses `2*pi*d_BS/lambda` in its first
   nonconstant entry, but `2*pi*(2*pi*d_BS/lambda)` in its final entry. A
   uniformly spaced array cannot use these different wave numbers in the same
   response. The user response also contains that extra `2*pi`. The consistent
   physical array-response factor is `2*pi*d/lambda`, as already used in the
   MIS response. The original manuscript is retained; the correction is
   explicitly labelled rather than used to claim literal printed equivalence.
2. The user-channel response is required to have M entries by
   `h_k^T * diag(theta_bar) * diag(phi) * G`, with `G` of size M-by-L.
   Its printed final indices instead use `L_r,L_c`, the BS dimensions.
   MIS indices `M_r,M_c` are required for that product. The frequency-only
   diagnostic below does **not** pretend to resolve this second printed issue.
3. The phase-vector definition writes `exp(phi_m)` and `exp(theta_n)` for
   real phases in `[0,2*pi]`. That conflicts with the subsequently imposed
   unit-modulus constraints. The consistent transmission phase is
   `exp(1j*phase)`; real exponential magnitudes are not phase shifts.
4. The first SNR line multiplies by `1/sigma_k^2` twice, while the next line
   and the definition of `iota_k` use it once. With the stated MRT beamformer,
   the received model gives `Pmax*||H_k||^2/sigma_k^2`, hence
   `Pmax*L*|c_k^T*(theta_bar*phi)|^2/sigma_k^2` in the stated rank-one LoS
   model. The second noise factor is inconsistent with that derivation.

These are source-level mathematical/editorial conflicts. They are not a
claim about an unverified final-publisher PDF or permission to fit reference
ordinates, change the aperture, or replace the paper's optimizer.

## Complete Figure 8 necessary-model diagnostic

For the fixed 2-by-2 half-wavelength array at elevation 45 degrees, every
beampattern is in the real span of the constant and the sine/cosine pairs
associated with the four array differences `(1,0),(0,1),(1,1),(1,-1)`.
This follows by expanding all sixteen ordered terms of the squared complex
field. It holds independently of the unknown phase choices.

The diagnostic uses all four curves and all 360 original FIG samples,
including their original grids and linear-SNR units. It also checks the
complete current Python and MATLAB curves. Geometry-only projection matrices
are evaluated at 100 and 160 decimal digits; the source, selected runtime,
closed inputs, and full crossprecision checks remain unchanged. No fitted
coefficients, projected reproduction curves, recovered author phases or
reference-selected winner are output.

For the original FIG curves, the 160-digit maximum necessary residuals are:

| Array-response interpretation | Curve 1 | Curve 2 | Curve 3 | Curve 4 |
| --- | ---: | ---: | ---: | ---: |
| Single `2*pi`, unit-radius centred space | 1.8320e-17 | 1.9464e-17 | 5.1259e-17 | 6.1301e-17 |
| Extra printed `2*pi`, same geometry, unit-radius centred space | 0.0602312 | 0.0513971 | 0.0931046 | 0.0787695 |
| Extra printed `2*pi`, same geometry, free constant/unknown fixed radii | 0.0237716 | 0.0258526 | 0.0831122 | 0.0771688 |

The single-factor result is compatible with this **necessary** condition;
it does not prove that one common physical MIS phase/shift state realizes all
curves. In particular, it rejects the earlier inference that the original
plot must be structurally impossible merely because the current selected
state has a different summed pattern.

The extra-factor results provide a numerically stable conflict under the
specified geometry and units, supporting the source typo diagnosis. These
are finite-precision necessary residuals, not outward-rounded interval
infeasibility certificates. Unknown historical phases, initialization and
the printed L-versus-M ambiguity remain separate issues. The current
reconstruction's original-curve agreement remains false.

Closed diagnostics, with actual owned exit 0, no exception and unchanged
selected bytes:

- Single-factor diagnostic completion SHA256:
  `26058cbf1d170a5c937a8a301755c6c0155910332899083bf37085f12516302b`.
- Extra-factor diagnostic completion SHA256:
  `e994a818c6eab14a64f48862f87b8799d13a281c7aed122f2c9826d58a473df2`.

Both cover 12 complete lanes and six full crossprecision comparisons. These
diagnostics supplement, and do not replace, the complete optimizer banks,
independent physical checks, or the unfitted original-reference comparison.
