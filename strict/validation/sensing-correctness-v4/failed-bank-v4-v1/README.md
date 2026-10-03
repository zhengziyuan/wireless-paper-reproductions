# Historical incomplete sensing bank: actual v4 failure evidence

This is an immutable **failed-bank** record, not a completed Figure 3 result.
The original full task requested 6000 starts, each retaining 30 outer updates
and the published 4000-inner-iteration budget. The executor exited with an
uncaught numeric tangent-cone projection exception, before finishing the bank.

- The last progress file records 376 completed jobs: 340 certified and 36
  capped/unverified. Its original bytes and SHA are retained in the snapshot.
- Independently observed saved files are 379 jobs: 343 certified and the same
  36 capped/unverified. Starts 378–380 finished while already in flight.
- The unique missing index in the saved 1–380 prefix is start 377 (1-based).
  A fresh original-v4 cold run with unchanged eta0/lambda0/seed and source bytes
  reproduced the same exception at outer 1, inner iteration 138 (zero-based).
- The snapshot binds every saved compressed result and the complete original
  source/configuration snapshot. File hashes are **archive-observation** hashes,
  not retroactively invented hashes at worker completion.
- The original terminal exit is parent-observed tool evidence, not an archived
  stdout file. The fresh cold exception has its own actual capture and SHA.

The finite sorted-threshold/Fraction numerical fix computes the **same
Euclidean cone projection**. A passing fixed component/cold start cannot erase
the original 36 capped results, prove all 6000 starts, or certify the article's
figure/normalization. A distinct source version and new complete population
must be run before any new full-bank statement.
