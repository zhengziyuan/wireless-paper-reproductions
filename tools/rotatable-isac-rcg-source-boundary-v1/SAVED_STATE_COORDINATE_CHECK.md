# Saved ISAC state: phase-coordinate check

`check_saved_phase_coordinates.py --job JOB.json --result RESULT.json` holds
the saved beamformer, rotation and iota fixed, re-evaluates the current model,
and compares every analytic phase-coordinate derivative to a centered angular
finite difference. It reads the specified files only and does not optimize or
write a result. The default coordinate increment is `1e-5` radians.

For the saved `case-000-mc-004` Python result, scheme `Rot-BS & Fix-RIS`,
all 36 phase coordinates agree within the script's disclosed numerical
tolerance; the maximum absolute component difference is approximately
`4.36e-7`. The finite-difference and analytic projected-gradient squared norms
are approximately `13.660153968` and `13.660153775`. The saved record reports
outer, inner and full convergence as false and a maximum-iteration stop.

The compact `saved_case_000_mc_004_projection.json` contains the selected
state, its required original job parameters and the reported stopping fields;
it is explicitly a projection, not the complete historical result. Both
read-only scripts can use this file for `--job` and `--result`. Its retained
fields were compared with the unchanged original files; that comparison does
not authenticate the historical runtime.

This is a check of a single state against the **current** code, not proof of
the source actually loaded by the historic run. Saved flags are not an
independent convergence proof. Finite differences are not interval bounds;
no MATLAB, physical, original-reference or full-figure gate is established.
