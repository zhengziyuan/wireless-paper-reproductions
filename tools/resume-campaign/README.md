# Resume saved full scenarios

`recover_missing_bank.py` runs only missing Python MA/ISAC jobs from an existing
complete immutable input bank. All original points, 100 realizations per point,
schemes and solver budgets remain in that bank. MA also retains all 1000 NLoS
draws per geometry. Existing converged and failed results are retained at their
original paths; new results and logs go into a fresh external data directory.

```powershell
& tools/local-runtime/activate.ps1
python -B tools/resume-campaign/recover_missing_bank.py `
  --paper rotatable-isac --bank E:/saved-full-isac-bank `
  --output-dir E:/paper-reproduction-data/isac-missing-jobs --workers 1
```

The command records all original manifest slots, including known failures. It
checks input fingerprints and the current strict result/convergence schema
before describing a saved job as reusable. Those checks do not replace an
independent physical, dual-language or reference-curve audit. Missing-job
recovery cannot repair a known algorithmic convergence failure; such failures
stay visible for a separate, source-supported diagnosis.

Each new subprocess runs the original full scenario entry and writes separate
stdout/stderr. No timeouts, reduced populations, alternative solvers or modified
settings are introduced. Admission defers work if target free space falls below
16 GiB, and source changes block subsequent launches. Host failures and missing
outputs remain failures. A fresh directory is required so that earlier attempts
are never overwritten.
