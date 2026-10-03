# Metadata-only table route proposal (not enabled here)

A future `--artifact table --paper ... --table 1` route can return a read-only
plan plus the retained source-qualified parameter mapping. Executing that
route should run `audit_tables.py`, not a numerical optimizer or a simulation
that pretends to regenerate a parameter table. The existing figure-only CLI
does not provide such a table route yet.

Required fields: artifact kind, author-source label/version/hash, source line
anchors, exact normalized numeric values and units, canonical configuration
paths/hashes, explicit per-branch overrides, unresolved reference-pattern
qualifications, actual local source-read receipt hash, portable replay scope,
and `final_publisher_table_equivalence_verified=false`.

Negative gates: missing/changed canonical bytes, omitted parameter row, wrong
SI conversion, statistical/instantaneous branch swaps, changed constraints,
or an unsupported table ID must fail closed. Pattern-reference rows may not
acquire a false machine-scalar pass; the presence of a geometry interval may
not acquire an actual all-pair geometry certificate. Preparation/self-consistent
hashes alone must not be presented as fresh source-read evidence. Do not rename
or silently restore a caption from a guessed encoding: the actual UTF-8 source
captions already equal the inventoried captions.
