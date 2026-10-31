# MIS Fig. 11, point 0, start 2679: one failed-stage replacement

This folder records one local Python floating-point variant attempt. It is not
a complete figure, population ranking, physical validation, MATLAB comparison,
or original-reference reproduction. No result here certifies the six-paper goal.

The saved historical start contains 20 successive penalty-stage stopping
records. Its first 19 report `gradient_tolerance` and projected KKT residuals
at most `1e-6`; the 20th, at μ = 0.0014781951904296875, reports a phi block
line-search failure after 3 iterations. `historical_stage_stops.json` is a
descriptive extraction of those records. The 19 prior states, their history,
and the failed 20th-stage input came from the existing local saved start and
its endpoint tape; their original producer, input provenance, and historical
execution were not independently authenticated. The old failed attempt and
saved data were retained locally. No later historical stage was reused.

The new independent attempt starts from the saved input of the failed stage,
uses the existing configured 4000-iteration cap afresh, and uses an experimental
floating-point phase-retraction variant. It is not a continuation using the
3997 iterations left in the previous attempt. The current attempt recorded
three iteration events and stopped with `gradient_tolerance` at projected KKT
residual 7.121917930555965e-7. Its ordinary gradient norm is much larger and
must not be confused with this projected residual. The recorded projected KKT
value has not been independently recomputed from the physics.

`events.jsonl` and `result.json` are the complete unmodified event chain and
result for this short attempt, including numerical optimizer states. Their
embedded digests bind the event sequence to an internal context; they do not
authenticate the historical inputs or independently prove execution. The
sanitized guard terminal omits machine-specific process identifiers and retains
the actual result and resource observations. Its polling was not a hard file
system quota. The guard reported a natural exit, no automatic restart, and no
scientific acceptance. Selecting this start as a priority does not remove any
other start from the population; final ranking is not yet eligible.

Run `python verify_evidence.py` from this directory to check the retained event
digest chain, stopping records, and disclosure flags. This is an evidence
consistency check, not a rerun or independent mathematical verification.
