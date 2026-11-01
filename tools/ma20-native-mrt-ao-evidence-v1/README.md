# MA Fig. 20 D=3, geometry 0: native MRT AO trajectory

This is a **single-scenario, single-mode** record of an independent MATLAB
MRT theoretical AO search. The saved job uses six movable antennas, five
users, Rician factor 100, 1 W and the indicated Fig. 20 region. Eight bounded
MATLAB segments wrote **234 coordinate updates** over **39 sweeps**, using
the configured maximum of 10,000 sweeps and the `certified_exact_2d` original
coordinate subproblem. The first segment began at the original fixed-array
positions; each following segment resumed at the last committed coordinate.
All eight guard terminals reported natural exit. The monitors sampled disk
use; they were **not hard filesystem quotas**.

The retained original native stopping expression first triggered at sweep 39:
the saved relative sweep increase was approximately `2.7620228815828897e-5`,
below the configured `5e-5`. None of the 39 saved sweep changes was negative;
this matters because the native expression would also stop on a negative
change. The final saved theoretical objective was approximately
`16.01247659219142`. This is a finite-run stopping observation, not a proof of
global optimality or an interval-certified convergence theorem.

`recorded_native_events.json.gz` contains all eight complete native event
streams, their summaries, the de-identified guard terminals, and the theory
configuration/geometry. It does **not** contain the 1000 NLoS sample bank. The
independently saved Python trajectory is the adjacent
[`ma20-mrt-recovered-evidence-v1`](../ma20-mrt-recovered-evidence-v1/) bundle;
it is referenced rather than copied here.

The verifier checks event continuity and the exact native stopping predicate,
then compares all saved native coordinates and before/after objectives against
the 234 Python updates. It also evaluates the current Python Eq. 13 expression
at each saved native input and output without calling a coordinate solver.
Observed maxima were `2.387e-15` in coordinate, `2.487e-14` in objective
between languages, and `7.106e-15` against that current formula. The minimum
saved spacing was `0.5` and the minimum region margin was about `1.04345812`.
The saved per-coordinate source certificate bounds and surrogate acceptance
are also checked. These are floating-point checks, not interval certificates.

With Python and NumPy installed, from the repository root run:

```text
python tools/ma20-native-mrt-ao-evidence-v1/verify_native_evidence.py --bundle tools/ma20-native-mrt-ao-evidence-v1/recorded_native_events.json.gz --repo .
python -m unittest discover -s tools/ma20-native-mrt-ao-evidence-v1 -p "test_*.py"
```

The MATLAB search and Python replay used a shared saved scenario. Historical
producer identity and the full dependency environment were not reauthenticated;
file-path edge checks were not a permanent lock on parent directories. The
record does not authenticate the historical NLoS bank across runs. An earlier
single-layout, 1000-sample MATLAB/Python evaluation is reported separately in
[`ma20-mrt-native-final1000-evidence-v1`](../ma20-mrt-native-final1000-evidence-v1/);
that evaluation is not a new search. This record does not establish ZF, the
other scenarios, all figures, independent original-reference agreement, or a
full-paper pass.

This folder records and rechecks the trajectory; it does **not** contain the
executed MATLAB helper or execution driver. The repository's `full_v4` MATLAB
implementation has the same numerical component bodies, but its stopping
handling for negative changes or a zero previous objective differs from the
executed helper. In this recorded trajectory no sweep change was negative and
no preceding sweep objective was zero. A separately reviewed source package is
needed to replay the native execution itself.
