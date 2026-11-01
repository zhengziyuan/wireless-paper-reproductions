# Fig. 20 grid-spacing diagnostic (current environment)

For the configured Fig. 20 grid, the diagnostic's **batched floating-point norm and exact-rational spacing decisions matched on all 30,024 unordered point pairs across D = 3 through 12**. The saved [result](spacing-result.json) is the actual worker output, reformatted only; it includes all ten per-axis counts and mismatch lists.

For each D, the grid contains D² points generated using NumPy `linspace`, with x in [-1.6, 1.6] and y in [-1.6, 2.4]. The nominal minimum separation is 0.5. The current Python search rejects a pair when `numpy.linalg.norm(p - q) < 0.5`; the prototype treats each frozen binary64 coordinate and the binary64 threshold as exact rationals, accepting when the exact squared distance is at least the squared threshold. These are comparisons of the generated binary64 grid, not exact decimal coordinates.

| D | Points | Unordered pairs | Differing decisions |
|---:|---:|---:|---:|
| 3 | 9 | 36 | 0 |
| 4 | 16 | 120 | 0 |
| 5 | 25 | 300 | 0 |
| 6 | 36 | 630 | 0 |
| 7 | 49 | 1,176 | 0 |
| 8 | 64 | 2,016 | 0 |
| 9 | 81 | 3,240 | 0 |
| 10 | 100 | 4,950 | 0 |
| 11 | 121 | 7,260 | 0 |
| 12 | 144 | 10,296 | 0 |

The diagnostic used NumPy 2.5.3 and the [prepared comparison code](../ma-statistical-bnb-stream-v1/spacing_contract_prepared_v1.py). The current exhaustive source is [here](../../strict/two-timescale-ma/brute_force.py). The actual task guard reported a natural exit, zero return code, intact output structure, and a passing monitored resource envelope; this report is not an independent numerical recomputation, and polling is not a hard filesystem quota.

The original search computes norms over arrays of 1–5 prior selected points for this N = 6 scenario; the diagnostic batches 1–143 prior grid points. Each norm reduces the two coordinate components of one row. A separate [synthetic check](synthetic_norm_context.py) of 715 pair/context combinations, including values adjacent to 0.5, found bitwise-identical norms in the bound NumPy version; it did not exhaust all possible contexts. Historical producer and numerical environment, author search criterion, objective values, winner selection, physical feasibility, MATLAB agreement and full-paper reproduction remain unverified by this diagnostic. No optimizer or sample bank was run here, and the result does not itself constitute scientific acceptance.
