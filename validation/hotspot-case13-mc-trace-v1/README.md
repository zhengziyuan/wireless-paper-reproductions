# Case 13: saved Monte Carlo trace metadata

This is an audit of retained records from one statistical case (U=1, satellite
Rician factor 20 dB), not a new simulation or reproduction of the paper. The
bounded scan walked the previously indexed interval with held identities for
the required old chunks. File identity does not authenticate historical bytes,
and separate locked reads do not prove an atomic snapshot of the original run.

The retained aggregate records 8,002 events: one MC begin and end, 1,000 draw
records, 1,000 each of geometry begin, satellite-to-RIS, ground, and geometry
end, and 3,000 scheme evaluations. The recorded draw IDs and scheme coverage
were complete within the scanned interval. All recorded rate scalars and the
three MC-end arrays agreed bit for bit with the three previously published
1,000-element sample vectors; no negative recorded rate, MC boundary position
mismatch or draw-group order mismatch was reported. These checks do not verify
the complete order of every event type within each draw. The scanner read
56,608,228 logical bytes while seeking
past unneeded data; this is not a physical-disk I/O count.

For every saved draw, the recorded direct-NHU matrix in the geometry-end event
matched the matrix in each of the three evaluation records. All 999 adjacent
recorded direct-NHU matrices differed. In-memory serialized RNG comparisons
reported a changed before/after pair for all 1,000 geometry records, with no
adjacent chain mismatch. Raw RNG states and channel matrices are not included.
These observations do **not** establish statistical independence, full-channel
pairing across schemes, authorship or correspondence to the original figure.
The previously identified paper-default parameter mismatch remains unresolved.

The child ended naturally with code zero, the actual termination was observed,
and the guard's peak accounted output was 18,652 bytes. Polling is not a hard
filesystem quota. `recorded-audit.json` and `child-summary.json` are exact
copies of the retained small result records; `guard-summary.json` removes local
process identity. The scan worker at
`tools/hotspot-case13-mc-trace-v1/prepared_mc_trace_scan.py` was bound by the
single-run manifest. It is disabled outside a separately admitted guard. Its
synthetic test checks fabricated aggregation inputs only and does not rerun
the original trace.

`verify_saved_summary.py` checks internal consistency of the three small
records, without opening the historical trace. It cannot independently verify
the historical scanner's arithmetic or its source provenance. From a complete
checkout, run:

```text
python -I -S -B validation/hotspot-case13-mc-trace-v1/verify_saved_summary.py
python -I -S -B tools/hotspot-case13-mc-trace-v1/test_synthetic.py
```

Neither command tests the solver, physical feasibility, MATLAB/Python agreement,
statistical independence, figure agreement, or completion of any paper.
