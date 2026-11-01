# Final IEEE statistical-CSI QoS counterexample

The final 17-page IEEE version of DOI
[10.1109/TWC.2023.3309957](https://doi.org/10.1109/TWC.2023.3309957)
prints (32b), (33b), and (36d) together with the definitions of its augmented
vectors and matrix on printed page 3656. `counterexample.py` gives a concrete
real scalar instance of those printed expressions where the original QoS is
satisfied but (36d) is not. The instance uses N=1, two streams (one HU and one
NHU), beta=Gamma=mu=sigma^2=1, equal unit LoS components, the HU beam 0, the
NHU beam 2, and power budget 4. It uses exact rational arithmetic, treating the
printed equation literally; no optimizer or Monte Carlo simulation runs.

The example also evaluates a diagnostic with the same printed augmented
definitions but with the RHS norm unsquared. That alone does not recover the
original QoS in this example. In particular, the printed imaginary coefficient
does not subtract a squared term under a norm. This is an independently derived
mathematical counterexample, not an official publisher erratum or evidence of
the parameter values or algorithm used for the original figures.

The repository's full-rank QT correction and the separate ESA-weighted versus
scalar-isotropic model-scope issue are documented in
`strict/hotspot-satcom/STATISTICAL_ERRATUM.md`. The counterexample does not prove
convergence, feasibility of any stored design, agreement with the historical
figures, or completion of the full paper reproduction.

Run `python -B counterexample.py`.
