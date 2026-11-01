# Case 13: recorded stop and history fields

The accompanying gzip contains the **lossless 28-event output** of one
bounded, identity-locked extraction from an existing case 13 trajectory. The
reader did not re-run optimization, Monte Carlo trials, or channel generation.
The event types are four `QT_loop_end`, ten `phase_end`, eight
`AO_iteration`, and six `execute_final`. The retained event contexts and
typed fields distinguish NoRIS, TwoStage, and the two AO starts.

The child exited naturally with return code zero. It read 100,146 bytes of
indexed fields; the public compressed stream is 12,501 bytes. The guard's
peak accounted output was 143,503 bytes; its polling is not a hard filesystem
quota. The sanitized `receipt.json` omits local paths and process identities.
The original guard and run artifacts remain separate from this public copy.

These are recorded fields, not a proof that every relevant iteration, stopping
condition or published scenario has been captured. The trajectory's historical
content and producer were not authenticated, and identity-locked field reads do
not establish an atomic snapshot of each complete event. An optimizer stop flag
alone is not proof of convergence, physical feasibility, MATLAB agreement,
published-figure agreement, or full reproduction.

To inspect the UTF-8 JSON lines without modifying the archive, for example:

```text
python -I -S -B -c "import gzip,sys; sys.stdout.write(gzip.open(sys.argv[1], 'rt', encoding='utf-8').read())" validation/hotspot-case13-saved-stop-history-v1/recorded-stop-history.jsonl.gz
```

All numerical histories and stop fields remain observational data; a separate
review must establish whether they satisfy the applicable algorithmic gates.
