# Case 13: recorded saved-matrix Hermitian-part checks

One guarded run examined **15 shared NHU second-moment matrices** \(\Psi\)
and **eight saved HU second-moment event matrices** \(Q\) from two starts of
case 13 (\(U=1\), \(\beta=20\) dB). The eight Q events include a repeated
saved matrix reference; they are not eight distinct independent inputs. The
exact retained records are in `recorded-matrix-checks.jsonl`.

For each stored binary64 matrix \(A\), the executed program interpreted its
binary entries exactly as rationals and applied a rational complex Schur/LDL
calculation to \(H=(A+A^H)/2\). All 23 records report 16 positive pivots,
which establishes positive definiteness of each **stored Hermitian part** if
the retained inputs and recorded computation are taken as given. The largest
recorded absolute real and imaginary components of \(A-A^H\) were respectively
\(1/72057594037927936\) and \(1/2305843009213693952\). All 15 stored
\(\Psi\) matrices have exactly zero recorded residual; all eight saved \(Q\)
events have nonzero residuals, so those stored \(Q\) matrices are not exactly
Hermitian. This is not a claim that the physical channel or its exact
mathematical moment is non-Hermitian.

The execution finished naturally with return code zero, 23 matrix records and
a complete terminal record. The guard recorded no error and reported resource
limits satisfied; polling is not a hard filesystem quota. The input projections
have the same historical source as earlier case 13 evidence. Their historical
producer, atomic original snapshot, numerical integration error, physical
units and original-paper consistency remain unverified. These checks are
necessary matrix properties for the saved values; they do not establish full
physical feasibility, optimizer convergence, MATLAB agreement, figure matches,
or reproduction of this paper.

`verify_recorded_checks.py` reads only the included records and checks their
identities, reported pivot statuses and exact residual encodings. It does **not**
rerun or independently verify the matrix arithmetic. The exact computation
source used in the guarded task is `tools/hotspot-case13-psd-exact-v1/prepared_exact_psd.py`;
its real-data entry remains disabled unless a separate, reviewed guard admits it.
The saved inputs were already published as
`tools/hotspot-case13-evidence-v1/ao_projection.json` and
`tools/hotspot-case13-hu-evidence-v1/q_rate_projection.json`.

From the repository root, run the record-only inspection with:

```text
python -I -S -B validation/hotspot-case13-saved-matrix-hermitian-v1/verify_recorded_checks.py
```
