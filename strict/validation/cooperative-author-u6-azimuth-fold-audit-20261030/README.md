# Signed azimuth in the supplied cooperative-satellite initializer

The user-supplied author archive `test_varsigma_316.zip` contains the
initializer `test_varsigma_316/INIT_S_AO_beta_N_100_SCSI_u2_k1_j2.m`, which
sets a satellite-indexed boresight and first transverse axis once (lines
33–48), outside the loop over users. It computes `AOD_SU_azi` using
`acos` (line 153) and subsequently uses its sine in the second array-coordinate
phase (lines 157–160). No per-user satellite-array rotation is specified in
this loop. That construction
folds the sign of the second direction cosine. The canonical saved U6 input
actually contains this folding; it is not merely a hypothetical edge case.

The supplied final paper, DOI 10.1109/JSAC.2024.3460068, on printed p. 282
(PDF page 4) describes the UPA response and includes the
second term `n_c sin(azimuth) sin(elevation)`. This observation concerns the
fixed physical array assumed in that model; it does not establish the sign
convention used in any unavailable original figure-generation run.

`audit.py` uses the author's fixed satellite and user coordinates, boresight,
first transverse axis, wavelength and array spacing to check satellite 2 and
users 2 and 6. Their signed second-axis projections are respectively
−0.3728847017 and +0.3728847017, but their saved normalized `d_mean`
steering vectors are identical. Their oriented adjacent-element phase ratios
would differ in the complex plane by 1.9823614214. The test also checks that
the saved ratios agree with the folded source formula. Reversing the second
axis for the entire satellite merely swaps the signs and cannot make these
two opposite projections have the same oriented response.

Run the audit with Python and NumPy; it reads the existing canonical NPZ and
writes no files. It is a deterministic source/input check, not an optimizer,
feasibility, convergence, or original-figure agreement test. The corrected
physical orientation requires an explicitly chosen fixed array coordinate
system and should be constructed as a separate input variant. Other array
links using the same azimuth construction need their own checks. Existing
source-faithful results and failed runs remain evidence for their original
inputs; the audit does not justify relabeling or replacing them. This is an
issue in the supplied initializer, not by itself proof of a printed-paper
algebraic error or of the settings used for the published figures.
