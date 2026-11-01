# Rotatable ISAC: author-version beampattern expansion and zero-scale boundary

This note concerns the title-matched [arXiv v2 HTML author version](https://arxiv.org/html/2512.20987v2), not a publisher-final equation check. It is an algebraic source audit, not a simulation or a claim that any numerical figure has been reproduced.

Let `u = t_a^BT`, `v = B diag(theta) t_a^RT`, and `Q = W W^H`. Equation (14) defines the sensing field as `sqrt(G_B) u + sqrt(G_R) v`. Direct expansion of its quadratic form in (18b) gives

```text
G_B u^H Q u + 2 sqrt(G_B G_R) Re(u^H Q v) + G_R v^H Q v.
```

The arXiv v2 displayed (19) instead omits `G_B` from the first term and uses `sqrt(G_B G_R)` on the last term. Its cross term has the expected factor. These expressions are not generally equal; `exact_counterexamples.py` gives both a one-element rational example and a two-element complex example with positive gains. In the latter, the products are evaluated with the conjugate transposes in (14) and (18b), giving 26 for the field power and 16 for the displayed expansion. The primary computation in `strict/rotatable-isac/core.py` forms the composite field and then its power, instead of evaluating the displayed expansion as written. This observation alone does not establish historical author code, figure values, or correctness of all implementation components.

There is also a boundary in the author's practical scale update: the text after (23) suggests a positive additive epsilon in the denominator but gives no numerical epsilon. If the transmit pattern is zero and the desired template is nonzero, equation (22) equals 1 for every positive scale `iota`; the exact objective is therefore well-defined on that positive-scale domain. However, the update returns `iota = 0` for a zero pattern, and substituting that particular scale into (22) produces `0/0`. A positive-scale fallback or domain restriction is needed to obtain an admissible scale from the update at that point; the suggested positive epsilon alone does not provide one. For zero overlap but positive pattern and desired energies, a supplied positive epsilon produces a finite positive scale and finite NMSE, but is a practical selection rather than the unattained exact finite minimizer. The selected numerical epsilon and its provenance must be disclosed rather than presented as an author setting.

The repository already contains disabled, prepared scale-policy candidates and a MATLAB helper; they are not yet integrated as verified production implementations. No original solver, existing result or figure was altered by this note. The publisher-final version, full physical correctness, convergence and original-reference agreement remain unverified.

Run the self-contained exact-arithmetic checks with `python tools/isac-author-v19-error-evidence-v1/exact_counterexamples.py`.
