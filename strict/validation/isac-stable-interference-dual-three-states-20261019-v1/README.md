# Explicit-interference arithmetic candidate: three saved ISAC states

This is a narrowly tested arithmetic candidate for the rotatable-ISAC reproduction. It preserves the mathematical self-excluded interference sum instead of subtracting the desired power from a much larger total. The utility derivatives use the equivalent stable coefficients and explicit interference derivatives. The W-QT auxiliary uses the same explicit sum. Channel formulas, solver updates, budgets, stopping inequalities and safeguards are preserved in the candidate sources.

The package contains exactly two terminal states from original case149 and one from case159. It is not a rerun of their optimized trajectories. Original failed/convergence outcomes remain in `data/three-saved-states.json` and `results/historical-scoped-results.json`. The old Armijo failure in case145 and the failed QCQP in another scheme of case159 are not solved by this evidence.

Actual finite verification found that both candidate languages pass the stored physical fields, all W/RIS/rotation derivative components, explicit interference auxiliaries and final QT q/p at these three states against the same independent MP80 and MP100 references. There are198 complex-or-real derivative components per precision, corresponding to378 real degrees of freedom. The largest MP80/MP100 difference was about1.82e-58. Native evaluation used a separate MATLAB R2025b batch; its process exited0. The original Python expanded run exited1.

The expanded extra check remains **false**. Some unchanged sensing intermediates `lip` and `ga` differ from full-physics MP values by more than an added absolute1e-5 check. Python maxima were1.66067e-5 for case149 lip, and0.0226290/0.0114278 for case159 lip/ga. Native maxima were3.10770e-5 and0.0248187/0.0129163. These arrays have magnitudes up to about4.72e8,3.74e11 and1.23e10. The1e-5 threshold was borrowed for this new coverage from the existing derivative component comparison bound: it is **not** a recovered original lip/ga acceptance standard. Relative errors are diagnostic only; they do not replace the failed absolute checks. The failures do not by themselves establish an original algorithm error or the cause of the case159 non-positive-definite Q.

## Portable finite checks

The default checks actual stored native vectors against the existing references. It records the historical Python outcome without pretending that the original Python derivative vectors were serialized. It requires only Python's standard library. Choose a fresh output directory outside this package:

```console
python check_three_saved_states.py --mode recorded-only --output-dir ../three-state-recorded-check
```

To also evaluate the isolated Python candidate on these same three saved states, install NumPy in your existing environment and use:

```console
python check_three_saved_states.py --mode evaluate-python --output-dir ../three-state-python-check
```

No optimizer, initializer, sampler, Monte Carlo run or new MP reference is called. The entry evaluates only these existing inputs and reports the physical/derivative/changed-QT checks separately from the extra-intermediate checks. **Exit1 is expected while the expanded gate is false**; exit0 is not used to hide that gate. The portable entry has actually checked the three existing states using both Python fixed-state evaluation and the already stored actual native MAT, with source/input bytes closed before and after. It returned1: physical/derivative/changed-QT checks passed, while the extra-intermediate gate remained false. See `results/actual-portable-first-use.json`. No new optimizer or MP reference was run. A separate hidden MATLAB R2025b batch has now actually executed the public relative entry with exactly these three existing inputs. It naturally exited0; the existing checker then checked its fresh MAT against the same stored MP80/100 references and naturally exited1, retaining the extra-intermediate failure. Sources and input bytes closed unchanged before and after, and the fresh MAT inputs match the three fixture states exactly. No Python mathematical audit was repeated for this native first use. See `results/actual-public-relative-native-first-use.json`. MATLAB process0 is not expanded scientific-gate success.

For an optional fresh native fixed-state evaluation, run from this package root using an installed MATLAB. The supplied primary MATLAB file is the exact source used in the actual fixed-state batch. Give an output MAT outside the package:

```matlab
addpath('sources/matlab');
run_native_three_state_candidate_v1('data/exact-three-saved-state-inputs.mat','../fresh-native-three-states.mat','data/scenario-149.json','data/scenario-159.json');
```

Then check that saved native output using SciPy (and NumPy for the Python evaluation):

```console
python check_three_saved_states.py --mode evaluate-python --native-mat ../fresh-native-three-states.mat --output-dir ../three-state-fresh-native-check
```

The MATLAB entry contains preserved historical local functions, but calls only fixed-state evaluation and the coefficient prefix before the eigensolver. It never initializes or optimizes. These MATLAB/Python candidate sources are isolated candidates, not an installation into the production runner.

## Evidence and limits

`data/MP80-MP100-references.json` preserves the already computed independent reference numbers and bounds. Full channels were evaluated independently; W/RIS derivatives are analytic, while the six rotation components use the existing MP central difference at1e-20. The publication preparation did not recalculate these references. The Python original run did not serialize its complete derivative vectors; its actual error records are retained, and `--mode evaluate-python` can reproduce candidate derivatives directly from the saved state inputs. Native complete actual derivative and coefficient vectors are included.

The public MAT contains only the three W/theta/rotation/iota inputs. The two small scenario JSON files provide their complete fixed physical/control configuration. The large per-case RAW files, trajectories and private paths are omitted. Omission from this compact package does not imply those local files are unavailable.

Same-state physical agreement is distinct from equality of separately optimized trajectories. This package does not establish full convergence, original-reference figure agreement, complete dual-language optimized-output agreement, a case145/159 optimizer fix, or whole-paper success. Original budgets present in the source/configuration were not executed anew.

`manifest.json` binds every public file except itself. Local `.gitattributes` preserves exact bytes. `source-provenance.json` records the exact executed source/input copies and explicit projections without local drive paths.
