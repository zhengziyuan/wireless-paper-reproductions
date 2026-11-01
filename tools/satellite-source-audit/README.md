# Physical-source checks using actual scalar controls and saved states

The [GT pattern and diameter-family packet](../../strict/validation/satellite-GT-pattern-and-diameter-family-20261017/README.md)
retains actual native/Python scalar inputs, outputs, frozen source bytes and
complete independent MP80/MP100 reports. `itu1428_oracle.py` is an independent
official-formula transcription. It keeps the printed endpoint gap and boresight
convention explicit.

`prepare_pattern_controls.py` creates a fresh scalar-control directory from an
unchanged original configuration. The copied native function has an exact
name-only inverse. `run_native_pattern_controls.m` records only scalar gains,
guards the selected implementation/inputs and makes no optimizer or RNG calls.
`audit_pattern_controls.py` reads the actual values and checks every admitted
probe with the independent oracle.

`audit_diameter_family_bound.py` consumes the full real M18 final-state packet
and all18 exact original configurations. It reuses independently verified MP
matrix quotients, applies the analytic gain-floor relaxation for all standard
diameters, and compares all54 NoRIS reference ordinates per language.
`replay_evidence.py` verifies every public payload before running both readers.
These checks narrow the missing-input diagnosis; they do not identify the
author's hidden gains, change a production scenario or certify source curves.
