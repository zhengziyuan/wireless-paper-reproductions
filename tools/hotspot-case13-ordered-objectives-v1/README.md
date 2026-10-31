# Case 13: ordered saved-point hotspot rates

This read-only check uses the previously published, small
`../hotspot-case13-hu-evidence-v1/q_rate_projection.json` as its only input.
For each of eight saved events it takes the hotspot SINR (first of 16 entries),
computes `log1p(SINR) / log(2)` in binary64, and compares it to the saved
hotspot rate. The first event's saved rate is stored in the projection's
`first_hu_sum_rate`; the other seven are stored with their events.

In the recorded execution the maximum absolute difference was approximately
1.78e-15. All three consecutive *saved-point* rate differences are positive
for each of the two starts. See `recorded_saved_objectives.json` for ordinals,
values and differences. The SINR and saved rates originate from the same
historical run; this is an independent arithmetic calculation on those fields,
not an independent run or channel reconstruction.

The calculation does not authenticate the historical producer or establish an
atomic source snapshot. Ordering by event ordinal does not establish that all
intermediate iterations were retained. It does not prove convergence, physical
feasibility, agreement with the original paper, or completion of this scenario.

From the repository root, run with Python 3:

```text
python -I -S -B tools/hotspot-case13-ordered-objectives-v1/verify_saved_objectives.py
```

The script only reads the stated projection and writes JSON to standard
output. Binary64 logarithm results can vary slightly with the host math library.
