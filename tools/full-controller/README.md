# Full-paper command controller — source-only review candidate

This small directory can be placed at `tools/full-controller/` in the repository
after ROOT review. It does not modify any existing `strict/` source. By default
it only reads metadata and prints a plan; it does not create a numerical bank or
launch Python scientific code or MATLAB.

From the repository root, the portable future commands are:

```text
python -B tools/full-controller/run_all_full.py --output-dir new-full-campaign --plan-output new-plan.json
python -B tools/full-controller/run_all_full.py --output-dir new-full-campaign --matlab "C:/Program Files/MATLAB/R2025b/bin/matlab.exe" --execute
```

Choose a **new** output directory and a new plan filename. Use `--repo` if the
tool is not installed inside the repository. `--python` chooses the actual
scientific Python executable; `--workers 1/2/3` only controls existing CLI CPU
parallelism. There are no paper/language subsets, preview, component, shortened
population, altered configuration, selected-winner, reference-fit, or automatic
failure-retry options.

## Exact scope

The six author-source inventories contain 85 figures. The original metadata
maps classify 73 numerical figures: communications7–11; sensing2–16;
ISAC2–17; MA3–20; cooperative2–11; hotspot2–10. Twelve conceptual/hardware
figures remain explicitly inventoried, not passed off as simulations. There
are two source-qualified parameter tables. Both language slots are retained:
75 artifacts ×2 =150 tasks. Every original subpanel, caption, map, full setting,
grid, count, budget, and scientific-branch warning is stored without alteration
in the plan's `artifacts[].strict_specification`.

The controller invokes the actual `strict/reproduce.py` CLI once per supported
task. It does not regenerate physical/model formulas or implement a new solver.
Each numerical figure uses the current default canonical full configuration.
In particular:

- Sensing5/6 reuse the same language's actual Fig3 result and require the Fig3
  command to have completed with its declared output. A missing/failed Fig3
  dependency is a blocked task, not a new6000-start bank or success.
- MA14/16 retain the explicitly corrected original-model Schur/Laplace/Jensen
  evaluation, not recovered printed undefined equations74/75 or historical
  author curves. All300 trajectories/every saved original position remain the
  underlying route. MA19/20 use their separate full-axis configurations and
  declared fixed-MC ordered-candidate protocol; their very large exhaustive
  searches are not shortened or claimed to have completed here.
- Hotspot9 calls the central entry's genuine scalar element-count wrapper.
  Effective counts are4000:4000:28000,1000 channels each,total7000, with fixed
  N=J16/U6/K10/M25/beta12. The retained legacy configuration's five shape pairs
  are **not** this effective grid. Unreported fixed subpanel centers and other
  declared controls do not become recovered author geometry.
- Hotspot10 retains the full18 corrected vector-QT original finite-Rician
  branch and uniform all-scheme start policy; printed invalid scalar SOC and
  historical state/curve recovery remain false. Reported AO20/AO100 budget
  endpoints are not promoted to stationarity.

## Known current interface blockers

The plan has four blocked tasks under the current reviewed sources:

1. MATLAB parameter table1 for each satellite paper: `execute_table` explicitly
   supports only Python stdlib source/config metadata replay. No MATLAB
   simulation is substituted, and the table's unverified external pattern rows
   and publisher equivalence remain unverified.
2. Sensing MATLAB15/16: the unchanged `ris_baselines` return in
   `mis_sensing_strict_engine.m`868–881 omits `target_start_banks`. The unchanged
   strict renderer's `mis_population_evidence.py` requires every original
   target's full6000 summaries. This is a known transport/evidence interface
   gap, not an assertion that the algorithm did not compute those starts.
   The command is retained but not launched as a complete-render route until
   the interface is repaired separately.

Other full commands can still fail from solver/cap/unknown parameter or
dependency issues. Runnable means the current CLI exists, **not** a guarantee
of convergence, source-curve closeness, native independent validation, or
completion within a practical runtime. Current pre-existing banks/receipts are
never used as automatic task success or silently skipped.

## Native host adapter

The original central `run_matlab` constructs `[executable,'-batch',expression]`.
On Windows a private `run` binding in a clone with the **identical original
complete code object**, defaults, closure, and remaining globals adds only
`-wait` to that command. Original MATLAB expression bytes, function, paths,
arguments, populations and solver are unchanged. The production adapter never
replaces global stdlib `subprocess.run` or edits the strict source. On other
platforms the command is unchanged. [MathWorks' Windows startup documentation](https://www.mathworks.com/help/matlab/ref/matlabwindows.html)
states that `-wait` is needed to capture the exit code and wait for MATLAB to
terminate.

The adapter records each actual waited command PID, argv, start/end, exit or
exception, executable byte identity before/after, and resource admission.
It uses hidden host launches on Windows and inherited stdout/stderr captured
in the controller's binary logs. It does **not** invent the actual numerical
backend PID or certify a native scientific result from a launcher return.
Before native work, fresh free physical RAM must be known and at least3GiB and
free target-volume disk at least16GiB. Insufficient/unknown resource admission
is deferred with no native launch, not success, deletion, or a reduced scene.

## Failures and meaning of completion

Tasks run sequentially and continue after a failed/blocked/deferred/unknown
task. A host failure while creating a task directory or its start/final receipt
is retained in the campaign failure ledger and does not drop later task slots.
Unavailable after-run metadata is recorded as unknown and forces a nonzero
aggregate, not success. Each has immutable start/dispatch/completion JSON where
the host permits their creation, actual exit (or null
when unavailable), binary stdout/stderr, and hashes of declared result files.
The final150-task command inventory exits nonzero if any command, dependency,
output-presence, interface, admission or metadata before/after check fails.
No existing outputs are overwritten by this controller; a fresh campaign
directory is required. Stderr and partial scientific outputs are retained.

`exit_zero_outputs_present_scientific_unverified` means only the actual command
returned zero and the literal declared output locations exist. Directory
existence is not proof that all native job files are complete. The controller
does not decode banks or verify physical states, gradients, RNG, all solver
stops, all scientific runtime code, publisher figures, or original-curve
agreement. These flags always remain false. The strict renderer's own checks
remain active; neither a component receipt nor a preview is a full task.

## Source-only preparation evidence

`test_controller.py` exercises standard-library metadata and non-scientific
toy/mocked process controls. It does not launch a paper scenario/native job,
decode a numerical bank, or create a scientific output. `prepare_review.py`
records the actual tests, exact source SHA, whole original reproduce byte
before/after and its position-bearing AST, exact150-slot plan metadata, and
the original complete `run_matlab` code-object preservation control.

One developmental STD attempt failed before tests because Windows path keys
used backslashes; the tool output is retained in the conversation. The final
unfrozen development source now uses portable `as_posix()` metadata keys. This
was a controller metadata defect, not a scientific execution or paper error.
No scientific task, native parser, model import, bank or run was performed in
this preparation.
