# MATLAB output and continuation status

The existing MATLAB entry points in this directory contain output writes that
may replace existing files. The full-bank functions may also create a complete
job/output population. They are not currently admitted under this project's
storage policy. Do not run them until a task-specific, independently reviewed
space guard and non-overwriting continuation are available.

The affected full-bank entry points include `run_full_ma_figure.m` and the
`_v2`, `_v3` and `_v4` variants, and
`run_corrected_ma_figure_matlab.m`. Single-job/evaluation writers include
`run_strict_two_timescale_ma.m`, its `_full_v2`, `_full_v3` and `_full_v4`
variants, `evaluate_correlated_zf_matlab.m`,
`validate_corrected_zf_position_matlab.m`, and
`validate_correlated_zf_matlab.m`. `test_correlated_zf_matlab.m` also writes
when supplied an output path. This list describes inspected source only; it is
not a complete inventory of every dependency or MATLAB runtime write.

Existing original and versioned source files are deliberately left unchanged:
source identities for some saved runs include these files. Preserving those
identities does **not** make a legacy writer safe to execute. New protection
must use a versioned, independently reviewed route that preserves historical
inputs, results, failures and checkpoints. The MATLAB runtime, temporary files
and guard's output scope must also satisfy the current storage policy.

No MATLAB code was executed for this notice. It does not establish that any
paper, figure, scientific result, or language comparison has passed.
