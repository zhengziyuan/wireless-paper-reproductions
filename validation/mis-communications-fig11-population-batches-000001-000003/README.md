# Figure 11 point 0: three population-repair batches

This evidence concerns eighteen **Python** replacement attempts for previously
failed continuation stages. Batch 1 covered MIS 2, SMS 1, MIS 3, MIS 4,
SMS 3 and MIS 5. Batch 2 covered MIS 6, SMS 4, MIS 7, SMS 6, MIS 8 and SMS 7;
batch 3 covered MIS 9, SMS 11, MIS 10, SMS 12, MIS 12 and SMS 13.
The prior SMS 2 replacement already had saved artifacts and was deferred, not
rerun or counted as a new pass. Each attempt started from the saved input to
its first failed stage, retained the original 4,000-iteration stage cap, and
used an experimental floating-point phase-retraction mapping. These are
separate attempts, not the original author's trajectories.

The eighteen complete `events/*.jsonl.gz` files are lossless gzip copies of
the original event streams, verified byte-for-byte after decompression. They
include saved numerical state and are not just plots or derived scores.
`evidence.json` reports each original failure, its recorded replacement-stage
stops, and a sanitized per-run guard terminal. Process identifiers, local file
paths and machine-specific timing identities are not published. The original
local event files, historical failures, complete guard records and checkpoints
remain preserved. The selected public guard fields are recorded observations,
not a hard file-system quota.

From the repository root, run:

```text
python -B tools/mis-communications-population-batch-v1/verify_public_batch1.py validation/mis-communications-fig11-population-batches-000001-000003
```

This standard-library verifier checks the event hash chains, recorded original
failure boundaries, logged iteration limits, per-stage reported projected KKT
stops and consistency with the extracted result and guard terminal. It checks
the reported values and records; it does **not** independently recompute the
gradient or KKT residual. A valid event chain alone does not authenticate the
historical producer or all original inputs.

The original numerical failure histories and reused earlier stages have not
been independently authenticated here. Independent physical feasibility,
convergence for the entire population, full 6,000-start ranking, MATLAB/Python
agreement and agreement with the published figure remain unresolved. No one
of these eighteen attempts is admitted to the final ranking by this evidence, and
this is not a complete reproduction or a scientific acceptance of the paper.
