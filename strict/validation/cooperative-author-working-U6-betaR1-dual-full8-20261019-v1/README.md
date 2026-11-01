# Working author U6, beta_R=1: complete dual-language full8 evidence

This is one **working-source U6** physical-input variant. The author confirmed
that Fig. 4/5 actually use all six existing source-user positions in a direct
reply recorded on 2026-10-19. That clarification resolves the earlier user-count
question; it does not establish original-reference or full-paper PASS. Both
languages consume the same included eleven arrays derived from the saved
original native input. The final Fig. 4/5 paragraph on printed p.291 specifies
kappa_R=10dB; this working source uses beta_R=1 (kappa_R=0dB). No fitting bridges
that difference.

**Fig. 4/5 user-count clarification.** The author's direct answer was "6",
confirming use of all six existing author-source positions for these two
figures. Printed Table I still says U=2; this discrepancy is retained explicitly
and is not counted as an additional algebraic-paper error. Section VII on
printed p.290 still contains its one-LU/GT co-location and 2-degree-spacing
description. The clarification establishes the actual Fig. 4/5 count and use
of the supplied positions; it does not independently explain every printed
placement statement. No first-two-user truncation or new geometry was applied.
The normalized source INR versus the printed interference-axis unit in W,
author initializers, optimized-performance MC population and full reference
agreement remain unresolved. See
[the direct clarification](evidence/USER_FIG4_FIG5_U6_CLARIFICATION.json).

The fixed case is J3/U6/N16/M25/K1, 50W per satellite, normalized interference
limit0.01, and linear beta_N100/beta_R1/beta_G1000. The saved means/variances
already contain source gains, noise normalization and GEO power; do not apply
a second aperture/noise/GEO factor. Retained baseline geometry metadata is not
a substitute for the saved input factory.

## Real completions and retained failures

* First Python completed all eight optimizations and its original1000 channel-
  moment draws, then MAT export failed with actual exit1 because metadata keys
  exceeded63 characters. Its recording was lost. Both facts remain.
* Python recapture performed **new full8 optimization**, saved every returned
  state and reused the exact already-completed1000-draw moment return. It did
  not recover the lost first recording. Its actual exit0/source interval closed.
  Its evaluations/histories differ from the first run only in71 solve_seconds
  metadata leaves; this is not a statement that the complete JSON files match.
* Native MATLAB independently completed full8 and its own1000-draw population,
  then naturally exited0 with source and canonical-input closure.
* Both lanes contain8final states,67QT candidates and55phase endpoints.
  Independent MP80/MP100 checked these states/candidates,2direct preP7
  subproblems,55phase endpoints and8250complex gradient coordinates per lane.
  Signed relative stops, solver/primal/QT diagnostics, complete mu halving,
  strict Phi-star, MC-input binding and actual TS initial incumbents also closed.
  Native contains42recorded TS initial-incumbent calls.
* Native stops readerV1 failed at a host-cache boundary after stop checks.
  Host-onlyV2 admitted the separate savedMC input and exited0. Both are retained.

Each local1000-draw primitive stream was independently audited, including18000
link samples and36000second/fourth scalar values. The streams are **not public**.
Their completion/MP receipts, hashes, exact/empirical moments and input arrays
are public. This capsule alone therefore cannot repeat per-draw contraction
verification. These draws validate channel moments, not optimized-performance
MC, an author-recovered performance population, or confidence intervals.

## Inputs, full states, sources and readers

The canonical NPZ SHA256 is
ce39e03acac33fa0670264ee5f49cf95f2ea6bf96334ab09fb0445978cf4df8e.
The input folder contains all eleven arrays, both limits and exact MAT transport.

The compressed MATLAB state files include every final state, phase endpoint,
gradient, QT input/candidate and original diagnostic. A metadata-only MATLAB
transport checked native2987 and Python3425numeric/logical leaves before
projection and after writing: class, shape, real and imaginary bitpatterns are
identical. No phase alignment/normalization occurred. JSON projections preserve
every typed numeric value and float64 bitpattern while aliasing local paths.
Original-artifact digests identify source evidence; MANIFEST separately hashes
the actual public bytes. The projection's first empty-Java-digest host failure
was corrected without any scientific rerun and remains in local preparation.

The implementation folder contains byte-identical actual saved-input/recording
sources. Common theoretical providers already reside in this repository under
cooperative-corrected-Algorithm3 and are individually SHA-bound. No private PDF,
original ZIP, CVX/Manopt installation or primitive stream is bundled.

~~~console
python -B read_public_evidence_v1.py
python -B read_public_evidence_v1.py --state-inventory
~~~

The Python MAT transport also encodes two long metadata field names and109
original None values. The actual reversible codebook is included.
Use the additional --decode-python-metadata reader option or
load_decoded_python_recording() for safe MAT+codebook restoration. It verifies
every non-marker numeric leaf's dtype, shape and F-order bits. This route never
unpickles any payload. The known empty solver_options struct is restored to its dictionary using the exact included source JSON; this changes no numeric leaf. All109None and both long names originate in the old
physical_input_variant metadata that the short fresh-run configuration replaces;
the actual short configuration has no None, long or unsafe MAT field names.
The byte-identical fresh entry therefore stays unchanged. No failed fresh
numerical reproduction was observed or claimed during this path review.

The inventory option needs NumPy/SciPy. load_saved_recording(lane) exposes the
full arrays for independent inspection. The reader checks files/structure;
it does not execute physics/MP, optimize or draw RNG.

Optional fresh full-budget reproduction plans can be written with:

~~~console
python -B prepare_fresh_reproduction_plans_v1.py --repository-root /path/to/wireless-paper-reproductions --work-dir /fresh/output
~~~

Supply cvx-root/cvx-prefs and optionally matlab arguments to prepare native
commands too. This preparer only writes plans. A fresh rerun is new scientific
computation, not reading saved evidence. The portable path preparer was syntax
checked; no new numerical run is claimed for it. The scientific sources are
unchanged actual providers. The short runtime JSON preserves reported/tuned/
sweeps/multi_vs_single controls and avoids long metadata keys; the exact full
original JSON is separately included by its original SHA.
Required runtime dependencies include NumPy/SciPy, CVXPY/CLARABEL, mpmath and
MATLAB with the configured CVX2.2.2/SDPT3. Manopt is not the current RGD provider.

## Unfitted final evaluations

| Method | MATLAB minimum SINR | Python recapture minimum SINR |
| --- | ---: | ---: |
| AP-NoRIS | 0.5218798275103679 | 0.5218798316552461 |
| AP-AO | 0.9666600067799986 | 0.9666619018634686 |
| MR-S-NoRIS | 0.5038070144780132 | 0.5038069917479810 |
| MR-S-PA | 0.9176582157099327 | 0.9176586112342997 |
| MR-S-TS | 0.9004166391312404 | 0.9004102282435166 |
| MR-TTS-NoRIS | 0.5112738858606146 | 0.5112737992070915 |
| MR-TTS-PA | 0.9248461429056697 | 0.9248466445393738 |
| MR-TTS-TS | 0.9068806839802633 | 0.9068676876268831 |

Maximum relative minimum-SINR gap is1.43310358915379e-5. These are separately
optimized outcomes, not proof of equal optimizer solutions or reference match.

## Scientific limits and distinct source discrepancies

Controls remain QT/AO200, RMO100000, relative1e-4, gradient1e-6, mu1 to.001
by halving,50smoothing repeats and original primal/QT gates. These complete
reconstruction controls are not recovered author Manopt defaults or performance
MC budgets. Algorithm3 includes the full preP9+oneP7, fresh auxiliaries,
fixed updatedp_INIT, strict improvement and disclosed undefined-Phi-star fallback.

The working source differs in initialization, first-block order, Manopt[]
starting points, fixed iterations and stored surrogate statistics. Its MR cost
uses hinge-square penalties; finalEq36/current use the full residual square.
That difference alone is not a paper error. At one actual saved MR-S P9 state,
positive GT residual makes both penalties equal; author/current criteria differ
by -1.6653345369377348e-16 minus2.15545368248954e-21i. One scalar agreement
does not certify every component or explain a reference-performance gap.

Earlier literal native/Python physical comparison remains not-all-strict-pass:
120/130numeric comparisons passed and10complex component fields differed due
to large-ToF binary64 operation order. Selecting native canonical input for
both languages does not rewrite that result; storage-class-only issues were
explained separately.

The four diagnosed printed algebraic inconsistencies remain Eq12/Eq30d/Eq11c/
Eq45c, not an official erratum. The newly supplied working TTS cost has a
different direct-only fourth-moment discrepancy: N=s=v=1 gives6 versus exact7
and printedEq45c's5. This is **not a fifth new printed-paper error**.
See the included source notes and working-vs-final diagnosis.

Original author seed, Manopt version/default point, performanceMC population,
and mapping of the working source to other final figures remain unknown.
The Fig. 4/5 six-user/source-position mapping is clarified above. This beta_R=1
capsule does not claim validation of the final-kappa10 variant, original-reference
agreement or full-paper completion. All original numerical/MP receipts retain
their historical scope; no scientific run was repeated for this clarification.
