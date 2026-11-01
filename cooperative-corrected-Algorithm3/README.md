# Cooperative corrected Algorithm 3: source and selected evidence

This source-only subpackage preserves the mathematical kernels and records a
specific correction to our implementation of the final IEEE Algorithm 3. It
also provides reviewed, experimental interfaces for explicit local inputs.
Existing selected numerical evidence and first use of these new interfaces
have separate status. [Evidence scope](EVIDENCE_SCOPE.md) records that boundary.

The paper is **Cooperative Multi-Satellite and Multi-RIS Beamforming: Enhancing
LEO SatCom and Mitigating LEO-GEO Intersystem Interference**,
[DOI 10.1109/JSAC.2024.3460068](https://doi.org/10.1109/JSAC.2024.3460068).
The reconciled IEEE source has 18 pages, pp. 279–296. Its source digest and the
existing 154-language-task registry boundary are recorded in
[paper scope](evidence/paper-scope-and-unit-boundary.json). This subpackage does
not modify the project's historical catalogue, root README or issue records.
The private supplied PDF, numerical banks and raw recordings are not bundled.

`python-saved/sources/` and `native/matlab/` contain the frozen numerical core.
`python-saved/portable_corrected_algorithm3_v2.py` and `native/adapter/` are
experimental host/input interfaces. [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json)
labels every runtime file and its inherited source digest. Native legacy base
runner/algorithm files marked as metadata dependencies are included for the
unchanged hash closure; they are not corrected entry points. The Python base
`algorithms.py`, `run.py` and `run_cooperative_v3_configured.py` also preserve
their historical bytes. Invoke the documented corrected wrappers; direct use
of these historical base runners does not install corrected Algorithm3.

Python saved-input inspection uses a fresh interpreter with assertions enabled:

```text
python -X utf8 -B python-saved/portable_corrected_algorithm3_v2.py validate --source-root python-saved/sources --data-dir <new-data-directory>
python -X utf8 -B python-saved/portable_corrected_algorithm3_v2.py inspect-saved --source-root python-saved/sources --data-dir <another-new-data-directory> --saved-result <source-bound-saved-case.json> --saved-result-sha256 <existing-receipt-hash>
```

The explicit numerical saved-input command is:

```text
python -X utf8 -B python-saved/portable_corrected_algorithm3_v2.py saved-two-ts --source-root python-saved/sources --data-dir <new-numerical-directory> --saved-result <source-bound-saved-case.json> --saved-result-sha256 <existing-receipt-hash> --execute
```

It executes two complete TS chains using their own saved NoRIS initial powers.
The other six chains and configured1000 moment result are explicit saved reuse.
This interface does not expose fresh full8. Its first true numerical execution
remains pending; the commands above were not run for this publication draft.

Fresh full8 has a separate experimental Python interface. It invokes the frozen
original full8 runner for one complete explicit configuration, including new
configured1000 moment draws. Its passive recorder preserves the original
scientific loops and records the two corrected preamble P7 updates. Only import
and exact configuration-byte IO were exercised; first true numerical use and
independent numerical acceptance remain pending.

The included [A configuration](examples/Fig13-A-full-configuration.json) is an
exact copy of the genuine complete historical A input. Its seeds, solver and
unreported caps are disclosed reconstruction choices. It is not an author
execution contract or a new adapter result.

```text
python -X utf8 -B python-full8/portable_corrected_fresh_full8_v1.py inspect-configuration --source-root python-full8/sources --data-dir <new-inspection-directory> --configuration examples/Fig13-A-full-configuration.json --configuration-sha256 0bac4efeba390b8b99fe80f31ae80c6eb6561100741b744a21ee5b314ce85971
python -X utf8 -B python-full8/portable_corrected_fresh_full8_v1.py full8-single-configuration --source-root python-full8/sources --data-dir <new-numerical-directory> --configuration examples/Fig13-A-full-configuration.json --configuration-sha256 0bac4efeba390b8b99fe80f31ae80c6eb6561100741b744a21ee5b314ce85971 --full --sweep base --execute
```

These commands are provided for review; no numerical command was run for this
publication. The fresh-full8 manifest changes historical origin metadata to
relative paths only; all18 source digests and scientific bytes are preserved.

Native preparation is Windows-only and does not start MATLAB by default:

The Windows process ownership interface was exercised with synthetic Python
children. Explicit paths do not establish a cross-platform process interface.

```text
python -X utf8 -B native/adapter/portable_native_host_v3.py --source-root native --data-dir <new-data-directory> --mode io-only
```

Future native modes are `io-only`, `full8`, `saved-two-TS`, and `reuse-A088`.
Execution additionally requires `--matlab-executable <installed-MATLAB>` and
`--execute`. `full8` requires `--configuration <complete-external-config>`;
the saved modes require `--saved-input-spec <pinned-case-spec>`.
`full8` and `saved-two-TS` also require `--cvx-root <installed-CVX>` and
`--cvx-preferences <explicit-configured-prefs>`. Preferences and temporary files
stay under the new data directory. The host does not install CVX, edit global
preferences, invoke cvx_setup/savepath or configure the network. Its new MATLAB
entry has not yet had an actual parser/codec/scientific execution.

Python requires NumPy, SciPy, CVXPY, CLARABEL and SCS. Native uses an existing
MATLAB/CVX/SDPT3 installation with the runtime identity recorded by the selected
run. These are external dependencies, not vendored binaries. No universal
dependency lock or cross-platform numerical equivalence is claimed.

Read [algorithm/source notes](ALGORITHMS_AND_SOURCE_NOTES.md) and
[budgets](BUDGETS_AND_CONFIGURATION.md) before selecting inputs. Four diagnosed
printed algebraic inconsistencies, the unresolved author W versus I/N plotting
convention, and our old Algorithm3 implementation omissions are separate items.
The declared numerical controls are reconstructed where the paper supplies no
executable budget; they retain their full configured values.

Selected Python A/B/C and native A/B evidence remains valid only within the
source/input scope recorded in [the small numerical summary](evidence/selected-numerical-evidence.json).
Original native A host exit1 remains1. Its independently optimized Python/native
solutions differ. Native B also retains its producer0/reference-wrapper1 distinction; same-state evaluator agreement does not require optimized
solutions to coincide. Full183, complete Fig12/Fig13 author agreement and the
six-paper goal remain unproved by this subpackage. Static inverses, imports,
fixtures, controller tests and host exit0 are not scientific acceptance.
