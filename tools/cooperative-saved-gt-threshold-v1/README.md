# Saved cooperative GEO threshold inspection

`check_saved_threshold.py CAPSULE` reads the canonical NPZ and each lane's
saved result JSON; it recomputes the producer's absolute-tolerance aggregate
flag and separately compares each stored GEO-interference scalar to its saved
limit. The values come from the previously saved evaluations, not a new
beamformer or channel reconstruction. The source check uses one absolute
`solver_objective_tolerance` for both satellite power differences and the
normalized GEO-interference difference. A positive stored-scalar excess does
not by itself establish strict physical infeasibility or a paper error: the
evaluation's floating-point error has not been bounded.

This is one saved U6/K1 point, not full-figure, original-reference, convergence,
or dual-language acceptance. It writes no result or copies.
