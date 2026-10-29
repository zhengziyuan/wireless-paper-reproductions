# Hotspot V11 call-only numerical source binding

This independent helper replaces the tracing behavior of the original V10
source binder. It preserves V10's numerical module selector, whole-file SHA
check before first code binding, compilation with the actual code filename,
recursive immutable-code comparison, absolute filename/code cache, and
rejection of selected numerical code with an unbound path or dynamic filename.
It neither edits nor launches the frozen V10 consumer.

Whole-file compilation uses `dont_inherit=True`. Only the compiled source's
own `__future__` declarations take effect; the binder's future flags cannot
leak into the provider. The test's extraction of the original V10 class uses
the same explicit compilation setting, matching V10's original module context.

The change is specific: every successful trace callback returns `None`.
CPython continues to invoke the global hook on nested Python calls, including
numerical calls below an unselected parent, while no local line, return or
exception tracing function is installed on those frames. This removes those
local callback events. A controlled end-to-end speedup is not established.

## API

Load `call_only_numeric_source_guard.py` by its path, then use:

```python
guard = CallOnlyNumericSourceGuard(before, selected_numeric_paths, canonical)
with guard.armed():
    result = existing_frozen_computation()
binding_diagnostics = guard.report()
```

`before` maps resolved POSIX-format source paths to SHA256 values;
`selected_numeric_paths` is the complete allowed numerical source set. Supply
the original, separately pinned `canonical_code_fields` module as `canonical`
(the existing V10 loader is `epoch.load_canonical()`). No alternate digest
scheme or new numerical dependency is included here. The caller must validate
the complete source/runtime epoch before entry and its interval after exit.

Keep the original numerical module names when loading providers. Changing a
provider's module name so that it evades the selector invalidates the intended
scope. As in V10, the prefix rule is `name.startswith('mpmath')`, and the exact
remaining module names are declared in `NUMERIC_MODULE_NAMES`.

The context requires a fresh current thread with no global trace hook or
caller-local trace functions. It rejects nested/reused scopes, cleans up its
own hook on normal and exceptional exit, detects a caught binding failure and
detects removal or replacement of its hook at normal exit. A replacement hook
is not silently deleted. This is not a security boundary against arbitrary
code changing tracing during the scope. Other threads, native code, function
defaults, closure values, globals and loaded DLL identities are outside this
immutable-code check, as they were outside V10's code-content claim.

## Actual small regression scope

The companion test uses the original V10 class and `code_descendants` extracted
as unchanged AST definitions. Its controlled namespace supplies the same
standard-library dependencies and the original canonical helper. It does not
execute V10 imports, manifest validation, main, mpmath or a scientific model.
Small arithmetic fixtures check binary64 result bits, numerical call order,
canonical code sets, cache behavior, drift/dynamic/path rejection, and trace
entry/exit boundaries. It also records that V10 receives local line/return
events while V11 receives call events only.

Run with an existing Python interpreter, `-B`, no `-O`, and explicit E-drive
temporary/output paths:

```text
python -B -X utf8 test_call_only_numeric_source_guard.py
  --v10-entry <original-frozen-V10-entry.py>
  --canonical-helper <original-pinned-canonical_code_fields.py>
  --work-dir <fresh-E-test-temporary-directory>
  --result <fresh-E-small-result.json>
```

The test refuses to overwrite a result. All created fixtures are small and are
removed when each test ends. No dependency installation is required.

These small regressions establish source-binding behavior on the stated
fixtures. They do not by themselves verify physical fields, the full event
stream, convergence, author references, or any paper's reproduction. The
original interrupted partial output and failed outcomes remain historical
evidence. No checkpoint/resume implementation is included.

The first 17-test receipt is retained as historical evidence. Its arithmetic
fixture was compiled within a module declaring future annotations, so it did
not catch future-flag inheritance. A subsequent actual geometry comparison
failed at code binding before producing a geometry result. The corrected
19-test run additionally imports two source files through actual importlib
loading: one without future annotations and one with its own declaration.
Both are checked against the original V10 class and V11, including code flags,
binary64 result bits and canonical verified-code sets. This correction does
not itself establish a successful real geometry comparison.

## Actual full-size fixed-geometry comparison

The separate `compare_full18_geometry.py` run subsequently completed all 18
saved native configurations, retaining N=16, J=16, M=25, U=1..6 and satellite
Rician factors 0/10/20 dB. Each configuration uses MP80 and MP100 and both
existing deterministic constructor lanes. The unchanged frozen geometry and
formula sources execute once under each binder for every combination.

All 72 pairs have exactly equal complete output MP mantissa/exponent words,
matrix dimensions and remaining fields. The run exited 0 in 75.641 seconds;
its primary evidence is 21,500 bytes. Every actual selected numerical call
was source-bound and executed source files were checked unchanged afterward.
The two runs record 7,428,858 and 7,427,810 selected calls respectively;
their canonical code sets are not identical for every pair. The test does
not assert identical internal call histories across sequential evaluations.
The controlled small-fixture tests separately establish call-sequence parity.

Recorded kernel times total 41.033 seconds for V10 and 30.675 seconds for V11.
These are one ordered run with possible cache effects, not a randomized
performance benchmark or a prediction for complete science execution.

The evidence in `evidence/` retains the failed first comparison, the corrected
19-test receipt, all 72 paired results, the bounded execution receipt and a
scope summary. The failure came from host compiler-flag inheritance and is
not an original-paper numerical failure. No older failure was overwritten.

This proves compatibility of this binder change on the stated deterministic
geometry component. It does not certify random channel draws, finite-CN
projector quadrature, optimizers, convergence, the 1,478,707-event audit,
MATLAB/Python end-to-end agreement, author references, or a complete figure.
The frozen consumer is still unchanged and this helper is not yet integrated
into a restartable full-event consumer. Re-running the component script needs
the retained frozen manifest, original sources, canonical helper and saved
native case configurations at its declared local paths; they are not recreated
or silently substituted by this package.
