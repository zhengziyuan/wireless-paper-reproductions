# Statistical NHU interference: source index and physical model

The final IEEE paper [DOI: 10.1109/TWC.2023.3309957](https://doi.org/10.1109/TWC.2023.3309957)
defines simultaneous transmission to all streams `J` and uses all interfering
streams in the non-hotspot user's instantaneous SINR (printed p. 3651, Eq. 4a).
Its statistical formulation (printed p. 3656, Eq. 32b) instead sums only over
non-hotspot users `K`. The paper does not state cancellation of hotspot signals
or their silence at that point. Hence, under its earlier transmission model,
the K-only statistical denominator omits the hotspot beams.

`compare_index_scope.py` provides an exact scalar counterexample, with one
hotspot stream and one non-hotspot stream: the printed K-only ratio equals 1
and satisfies a 3/4 threshold, whereas including the hotspot stream gives 1/2
and fails it. The second moment, noise and both beams have unit power and the
total power limit is 2. No optimizer, historical figure, or measured channel
is used. This comparison is an independent mathematical observation, not a
claim about the numerical code or settings actually used by the authors.

For each user, the additional interference is
`sum_{u in U} w_u^H Psi_k w_u >= 0`. It vanishes exactly when all hotspot
beams belong to the nullspace of `Psi_k`. With positive path gain and finite
Rician factor, the isotropic term of the paper's Eq. (33b) makes `Psi_k`
positive definite, so the extra interference vanishes only when all hotspot
beams are zero.

The repository's full-interference ratio and additional QoS auxiliaries are
an explicit physical-model correction, not a literal reproduction of the
K-only printed constraint or proof of the authors' historical optimizer.
Both ratios are ratios of expected signal and interference powers, and should
not be presented as an exact expectation of instantaneous SINR. Original and
corrected scopes require separate reporting and reference validation.

The published numerical discussion for Fig. 2 reports AO comparisons at 20
and 100 iterations and an example fractional-increase threshold of `1e-4`.
Those reported settings must not be replaced by a reduced demonstration. A
historical Monte Carlo population count was not established by this targeted
comparison; any chosen count must be disclosed rather than attributed to the
paper without evidence.

Run `python -B compare_index_scope.py`.
