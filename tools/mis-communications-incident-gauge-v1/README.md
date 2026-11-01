# Incidence direction in the ideal MIS communication model

For fixed free unit-modulus MS1 phases and the rank-one far-field model, a
change of the BS incidence direction multiplies element `m` of the incident
steering vector by some unit complex number `d_m`, independent of user and
MS2 position. Replacing `phi_m` by `phi_m/d_m` leaves the effective field
for every user and every MS2 position unchanged. The mapping is bijective on
the product of unit circles, and it does not change the MS2 phases or schedule.
Therefore the attainable beampatterns, objective ranges and global optimum
values are the same for all such incidence directions in this ideal model.
This does not assert that finite nonconvex runs return the same objective.

`check_incident_gauge.py --saved-native NATIVE_ENDPOINTS.json` independently
checks this identity for the publicly saved Fig. 8 native start 1, all 17
continuation endpoints, four positions and 361 angles. A fixed alternative
direction is used, not inferred or fitted from the original figure. The
observed maximum field and linear-SNR differences are about 1.61e-15 and
1.25e-16, respectively. This is one real start, not the selected Fig. 8 winner
or a MATLAB/Python optimizer replay.

The identity rules out a change of the ideal incidence angle **by itself** as
an explanation for a change in the attainable set. It does not determine the
author's historical phases or solve the Fig. 8 curve mismatch. An unchanged
numeric initial phase can map to a different starting point, so finite
nonconvex solver runs may still select different local solutions. The proof
does not cover incidence-dependent element amplitudes, coupling, quantized
phases or other models that violate the stated assumptions. It is not a full
physics, dual-language or original-reference acceptance.
