# Immutable progress I/O wrapper; no numerical change

The actual v1 full audit returned after checking 31 cases / 5,368 positions /
5,368,000 rates with zero numerical failures. It had saved case 32's evidence,
then Windows WinError 5 denied the atomic replacement of its progress file even
after its twelve I/O retries. This is retained as an I/O interruption, not a
case 32 physical failure or a completed 200-case audit. The original v1 entry,
before-freeze, per-position files and progress remain unchanged.

This v2 wrapper imports the frozen v1 evaluator SHA256
`f014e63f98539482b5f788f81d1ab7c72c8ac61db7cfd77b284d06d9858f6139`.
All channel, QR, SVD, design, residual, source/input identity, threshold,
population and loop functions are exactly that entry. Only `atomic` is
rebound: each progress update is a fresh immutable `...-NNN.json`, not a
replacement of the OneDrive-locked prior file. Other evidence names are also
required to be fresh. At most 60 I/O-only retries of at most 0.5 seconds handle
sharing contention; no numerical solve or gate is retried. A missing final
completion receipt remains an incomplete audit.

The wrapper and this explanation are added to the before/after source freeze.
The new audit is a fresh full 200-case execution in a new output directory; it
does not reuse the interrupted v1 numerical outputs, change any native/Python
bank or numerical source, or relabel the interrupted old run as a numerical
pass. One worker and one BLAS thread remain. The full count is computed from
all actual native records and independently checked against source trajectories.
