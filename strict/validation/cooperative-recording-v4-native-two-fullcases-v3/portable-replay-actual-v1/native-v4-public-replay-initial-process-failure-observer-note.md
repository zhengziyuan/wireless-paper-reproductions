# Initial public-path replay process failure (observer note)

This note records a tool-observed process failure, not a manufactured numerical
failure receipt. The first actual sequential public-path M30/N48 replay command
returned Windows process exit code `-1073740022`, with no stdout and no completed
independent audit/binding JSON. A separate read-only file inspection confirmed
that neither intended output receipt existed at that point.

The raw machine stderr/stdout was not saved as a standalone transcript. The
cause is **unclassified**; absence of a completed receipt does not prove which
internal operation executed. It is not evidence of a failed scientific model,
matrix, gradient or QT constraint, and is not marked as a successful audit.

The subsequent unchanged-source import diagnostics successfully loaded the
existing NumPy/core/oracle route. An actual serial retry from the same public
data then completed M30 successfully (tool session 84418, exit 0), with a new
real independent audit and portable-source binding receipt. N48 was run
separately afterwards. No numerical formula, source output, threshold, saved
state, sample count or original manifest was changed to obtain the retry.

Later actual receipts, if present and independently verified, establish only
their own successful runs; they do not overwrite or retroactively certify this
failed first process launch. No new MATLAB optimizer or RNG run was launched by
the public-path Python retry.
