# Five native precision-before-one1000 components

The five retained numerical inputs (12,22,32,43,56) were actually executed in
native MATLAB. Each selected the first fixed scale (1) using precision gates
before any candidate evaluation, then executed exactly one original batch of
1000 randomizations. No candidate/reference curve selected a solver scale.
No later scale was exercised in these five protocol runs; they do not certify
the fallback branches. The earlier four-scale diagnostics remain separate.

The subsequent Python verifier did not resolve an SDP. It independently
rebuilt the original coefficients and checked the actually returned native
matrices at 80 decimal digits: true feasible primal, PSD dual witness,
unmodified 1e-5 feasible/raw primal-dual gaps, and the maximization equality
dual conversion `-native_CVX_dual/positive_scale`. This sign conversion is a
CVX convention/validator correction, not a paper model correction. A raw
maximization primal objective is not itself a certified upper bound.

Native receipts retain their originally false "independent recheck complete"
flags unchanged. The later independent receipts and aggregate supply the
separate actual recheck evidence; old bytes are not relabeled retrospectively.
All original 1000-candidate gate records and the saved best phase's original
surrogate replay pass. Every candidate matrix was not saved/recomputed, and
the prototype did not bind the entire selected backend MAT/MEX inventory.

These are five components, not complete AO/QT chains, a full1000 CDF bank,
production retry-policy certification, publisher/author-history recovery, or
published-curve agreement. All such flags remain false. Old failed samples
and old incorrect-sign receipts remain unchanged. The manifest binds the
actual raw matrix files and inputs without uploading private author sources.
