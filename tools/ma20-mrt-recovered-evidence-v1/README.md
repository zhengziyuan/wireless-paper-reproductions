# MA Fig. 20 D3/g0: saved MRT theoretical AO, with interrupted first segment

This is **one reconstructed geometry and one mode**, not a full figure or
paper reproduction. The saved input uses N=6, M=5, kappa=100, P=1 W, A=2,
and the D=3 point. The exposed box and spacing constraints are those stored in
the Fig. 20 job. The full 1000-draw NLoS bank is **not** included here and
was not consumed by this theoretical AO trajectory.

The first bounded worker was interrupted by a guard directory-enumeration
failure: the guard reported `FileNotFoundError` when inspecting
`inflight.json`. This is consistent with the worker removing the transient
marker after committing a coordinate; the exact timing and cause were not
independently observed. Its failure receipt is preserved. Its
151 complete frames were validated; the next worker held the original epoch
lease, checked the failure and prefix, retained the first claim, created one
new claim and continued at the next uncommitted coordinate. The first worker's
return code of zero is **not** a natural-exit claim. The old Job close is
inferred from the guard implementation and failure terminal; no closed-Job
member count was directly observed. The second guard recorded a natural exit.
Polling was not a filesystem quota.

The replay checks all 151 + 83 saved coordinate frames, chained ordering,
the source objective and the source's acceptance and stopping tests without
calling the coordinate solver again. It separately evaluates the MRT Eq. 13
expression at each saved before/after state and checks all 235 saved geometry
states. On this environment:

* The initial and final theoretical objective values were approximately
  9.574574275552322 and 16.012476592191426 bit/s/Hz.
* The first configured fractional-increase stop was sweep 39: the last
  fractional increment was about 2.7620e-5 against the 5e-5 threshold.
* The independent objective comparison differed by at most 3.56e-15; the
  smallest saved antenna spacing was 0.5 wavelengths, with zero observed box
  violation. The stated comparison tolerance in the reader is 1e-9.
* No saved coordinate update had a negative objective difference in the
  replayed binary64 values. These checks are not a global-optimality proof or
  a mathematical convergence theorem.

The compact gzip bundle retains the two exact frame streams, theoretical
geometry/configuration, starts, checkpoint, successor claim, and redacted
terminal facts. It excludes the random channel bank and local paths. The
sample-bank file was read and held in each execution interval, but its byte
identity across the interrupted intervals and the historical producer's input
identity were not authenticated. MATLAB independent AO, full sample-rate
evaluation, author-reference agreement, and the full figure remain unverified.

A previously saved Fig. 5 MRT trajectory on the currently compared input has
the same 40 sweep positions and objectives, and a 1000-sample rate result is
available as a **conditional donor**. The boxes differ and the coordinate
certificates are not identical; the donor's historical input/source identity
has not been freshly authenticated. The Fig. 5 data is not duplicated here and
is not claimed as a Fig. 20 physical or dual-language pass. Existing MATLAB
1000-sample results concern a different grid-winning layout, not this AO final
layout.

With Python and NumPy installed, run from the repository root:

```text
python tools/ma20-mrt-recovered-evidence-v1/replay_bundle.py --bundle tools/ma20-mrt-recovered-evidence-v1/recorded_ao_bundle.json.gz --repo .
```

The script uses the repository's current `strict/two-timescale-ma/core.py` and
`run.py` to re-evaluate saved source values and an independently written
Eq. 13 expression for comparison. It consumes no random samples and performs
no solver call. Replay success does not authenticate the historical runtime,
prove the coordinate certificates mathematically, run MATLAB, validate the
unpublished author inputs, or establish agreement with the paper figures.
