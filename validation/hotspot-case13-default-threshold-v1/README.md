# Case 13: saved-state checks against a 3 dB reference threshold

This is a **conditional examination of one retained case**, not a new solve or
a claim that the author's historical implementation, channels, geometry or
figure have been recovered. The saved case is U=1 and satellite Rician factor
20 dB. The paper's Section VI gives a global 3 dB default; Fig. 10's caption
and Section VI.G do not state an override, but unpublished author settings
are unavailable. Existing case-13 evidence reports a saved NHU target near
-3 dB; here we ask what can be proved about these same saved states if the
3 dB default is applied. They were not reoptimized for 3 dB.

For each of the three selected states, the guard-bound computation checked the
15 saved NHU channels in exact rational arithmetic. It tested both the saved
Psi matrices and an independently evaluated expression built from the saved
NHU means and variances. They share a historical source and are not independent
experiments. For each, it compared the desired power to `1.99` times the
interference-plus-noise denominator. The integer inequality
`199^10 < 1000*100^10` establishes `1.99 < 10^(3/10)`, so every strict
below-1.99 witness is also below the 3 dB power-ratio threshold.

| Saved scheme | Full-J interference: proved below 1.99 | K-only interference: proved below 1.99 |
| --- | ---: | ---: |
| NoRIS | 15 of 15 | 12 of 15 |
| TwoStage | 15 of 15 | 12 of 15 |
| AO | 15 of 15 | 12 of 15 |

Both saved-Psi and saved-moment expressions gave these counts. The three
remaining K-only flags per scheme are **inconclusive**: a false witness does
not mean the SINR reaches 1.99 or 3 dB. The two denominator conventions are
reported separately because the printed K-only formulation and the earlier
full-J signal equation are not identical; see
`strict/hotspot-satcom/STATISTICAL_ERRATUM.md`. This check does not decide
whether the publisher's Fig. 10 used either exact convention or this channel
model, and it does not establish the cause of any reference-figure gap. The
K-only denominator here uses the **saved current-implementation covariance**;
it is not a full reconstruction of the paper's printed Eq. (33b) model.

The three source states are the already published compact projections in
`validation/hotspot-case13-selected-physical-v1/`; the original 45 recorded
Boolean witnesses and terminal record are in `recorded-threshold.jsonl`.
`verify_saved_threshold.py` independently recomputes both denominator
conventions from the saved binary64 values with standard-library rational
arithmetic and compares all 180 booleans. It reuses primitive complex and
moment calculations from `tools/hotspot-case13-selected-independent-v1/`.
It does not read the historical trajectory, generate channels, optimize,
change a saved result, or prove historical producer identity. Held reads of
the selected projection did not establish an atomic historical event. A
non-Hermitian saved Psi, negative quadratic power, invalid identity or
incomplete recorded stream fails the verifier; it is not replaced with a pass.

The retained guard observation finished naturally, with the child exit
observed and no guard error; its sanitized receipt omits local process identity.
The guard's peak accounted output was 11,662 bytes. Polling was not a hard
filesystem quota. These results alone do not prove physical feasibility,
convergence, MATLAB/Python agreement, original-reference agreement or full
reproduction.

From a complete checkout, Python's standard library suffices:

```text
python -I -S -B validation/hotspot-case13-default-threshold-v1/verify_saved_threshold.py
python -I -S -B validation/hotspot-case13-default-threshold-v1/test_verify_synthetic.py
```
