# One ISAC004 zero-overlap diagnostic, saved-state evidence

The original **Rot-BS & No-RIS** diagnostic retained its failure. Its process exited 0 because the requested failure operands were completely captured. This does not establish optimizer, whole-case, curve or paper acceptance.

At the captured fourth outer attempt, evaluation call 3395, the 66-bin pattern has 35 nonzero entries. Its two desired bins (zero-based indices 40 and 57) are exactly zero. Independent calculations at 80 and 100 decimal digits give BS boresight cosines of approximately −0.4797982850 and −0.0153180390: both directions are in the back hemisphere. The frozen response returns zero there, and the NoRIS bridge is zero. This is neither cancellation nor a false alarm caused by a positive epsilon.

The [paper, arXiv v2](https://arxiv.org/html/2512.20987v2#S2.SS4) defines NMSE in Eq. (22) and gives the exact Eq. (23) minimizer **only when d = pdᵀp > 0**. Eq. (23) itself is not identified as erroneous. The immediately following paragraph explicitly gives the practical safeguard **iota = c/(d + epsilon)**, with c = ||p||² and a small positive epsilon; its numerical value is not reported. The strict implementation used here raises at d ≤ 10⁻¹⁴ and does not implement that practical branch.

Here c = 190.746509016214… > 0 and d = 0. For finite iota > 0 and e = ||pd||², NMSE = 1 + c/(e·iota²) > 1. Its infimum 1 is approached only as iota tends to infinity. This differs from the all-zero-pattern case. A practical epsilon update is not the exact minimizer; the exact-minimizer argument for monotonicity does not automatically establish the same claim for the safeguarded update. No epsilon fitting, execution of the practical branch or tolerance change is included.

`evidence/` contains the original 90,054-byte NPZ, the necessary NoRIS scene, captured metadata, the actual saved-math report and the source clarification. Paths in JSON metadata are projected; numeric leaf types and IEEE bits are preserved. `source-reference/` contains the byte-exact physical prefix of the frozen original core.

To independently replay **only the saved mathematics**, install NumPy and mpmath and run from this directory:

```text
python replay_saved_MP80_MP100.py --output-dir /path/to/new-empty-output
```

The reader covers all saved 4 × 66 sensing coefficients, six beam columns and 66 pattern values at 80 and 100 decimal digits, plus independent high-precision Euler/cosine branch signs. It generates no samples or channels and runs no optimizer. It does not verify the missing earlier rotation iterates, the entire trajectory, the other 499 cases, original curves or paper acceptance. The original failure remains unchanged. See `actual-portable-replay.json` for the executed portable-reader result; the receipt is separate from the pre-execution manifest to avoid a circular file identity.
