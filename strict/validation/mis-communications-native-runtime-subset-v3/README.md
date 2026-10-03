# Native communication: portable runtime-only reconstruction v3

This supplement reconstructs the exact 17 source/data files needed by the native
numerical runtime and component fixtures from existing public repository files.
Their bytes are a selected subset of the actual 42-file source-origin manifest
SHA `1a643626b2ebde224c160dcf9191ceb99b56338fe189f43d0656437ed8cefd23`.
The 21 old ignored outputs, original plot-vector reference and routing README
are **not published here**. This is not the complete 42-file snapshot and must
not be passed off as a successful run of its old all42 provenance verifier.
`source_map.json` is taken byte-exactly from the existing repository instead of
duplicating its routing strings. No original manuscript/figure file is copied.

From the repository root, create a fresh local directory:

```text
python strict/validation/mis-communications-native-runtime-subset-v3/reconstruct_runtime_subset_v3.py --repo . --output fresh-native-runtime/mis-communications
```

The reconstruction checks every selected SHA before/after and refuses an existing
target. Its generated `recording-source-freeze.json` explicitly describes this
runtime subset, never the complete42 origin. Those generated metadata JSON files
do not enter the unchanged native `implementation_digest`: all top-level .m/.py
and `source_map.json` inputs remain byte-identical to the actual native runtime.

For fresh recorded-state physical/provenance rechecks (not optimizer reruns):

```text
python strict/validation/mis-communications-native-runtime-subset-v3/audit_runtime_subset_saved_endpoints_v3.py --runtime-source fresh-native-runtime/mis-communications --record-folder strict/validation/mis-communications-native-fig7-preflight-v2/records --scheme MIS --start 1 --output fresh-MIS-runtime-subset-audit.json
python strict/validation/mis-communications-native-runtime-subset-v3/audit_runtime_subset_saved_endpoints_v3.py --runtime-source fresh-native-runtime/mis-communications --record-folder strict/validation/mis-communications-native-fig7-preflight-v2/records --scheme SMS --start 1 --output fresh-SMS-runtime-subset-audit.json
```

This v3 adapter verifies all selected callable/data bytes and entire saved settings,
then calls the unchanged independent Decimal60 physical auditor. It does not
rewrite the old actual42/v2 provenance receipts. Only the actual fixed two cases
(34 own-mu endpoints) are supplied, not an all12000 or historical-figure result.

The unchanged native recording engine/observer/entry are runnable from the fresh
runtime directory. The external `run_native_runtime_subset_v3` checks source
identity and opens that original entry; use one MATLAB computational thread.
For a fixed complete MIS1 start, set `figureName='recording-preflight:fig7:MIS:1'`;
for all6000 MIS+6000 SMS set `figureName='fig7'`. Both retain the original frozen
reconstruction controls (4000 RCG/1e-6/halving), dimensions and explicit1x2
geometry correction. The subset source identity does not certify a new native
execution; the fresh source-only entry has not been used to claim an all12000
result. All failures and missing observations must remain visible.

The existing actual42/full native bank and two-case preflight proofs stay immutable.
