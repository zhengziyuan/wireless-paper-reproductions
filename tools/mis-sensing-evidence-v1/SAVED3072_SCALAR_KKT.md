# Saved sensing scalar fields: start 3072

`verify_saved_3072_scalar_kkt.py --saved-state STATE.json` checks the saved
q and multiplier fields using exact rational arithmetic over their binary64
values. For this saved state the eta-direction residual is approximately
3.96e-7, the largest positive q is 1.11e-8, and the largest absolute q-lambda
product is 1.46e-9. The saved status reports an inner iteration-cap exit and
does not certify convergence.

The q values and multipliers are stored data, not an independently recomputed
physical forward model. The eta derivative is only one stationarity component;
phase and scheduling gradients, full KKT, physical SINR, reference units,
MATLAB and original-figure agreement remain unverified. The producer's common
numeric tolerance is reported as an implementation convention and does not
establish common physical units for these residuals.
