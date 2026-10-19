# Budget and configuration provenance

The final Fig13 caption supplies A=(J3,N16,M25), B=(J3,N16,M15),
C=(J1,N48,M25), kappa-N10dB and kappa-R9dB. The earlier kappa-R0 transcription
is superseded. The reported author platform is MATLAB R2021a, i7-10700K3.80GHz,
32GB RAM. New current-platform measurements are not recovered historical bars.

The paper does not recover the executable seeds, solver settings, stopping
implementation, repetition/aggregation policy or exact own versus dependency
timing boundary. The preserved case088 configuration is an explicit
reconstruction contract, not an original-author budget certificate.

| Preserved setting | Value | Provenance and interpretation |
| --- | --- | --- |
| QT and AO caps |200 each| Disclosed configured caps; no reduction in the corrected implementation |
| RMO cap |100000| Disclosed implementation safety cap, not attributed to the paper |
| Relative / gradient stops |1e-4 /1e-6| Disclosed configured stopping controls |
| Objective / primal / QT tolerance |1e-5 each| Retained gates; no relaxed acceptance |
| Smoothing |1 to0.001, halving;50 repeat cap| Declared reconstruction controls with strict source improvement branch |
| Historical progress tolerance |1e-8| Stored setting retained; it is not substituted for the corrected strict Algorithm3 branch |
| Channel-moment validation |1000 draws| Full configured independent recipe; saved-only mode reuses existing moments and does not draw1000 fresh channels |
| Python solver |CLARABEL; same-input SCS numerical fallback| Same mathematical QT and recorded immutable inputs; every failed/returned attempt remains evidence |
| Native solver |External CVX/SDPT3| Actual runtime identity recorded; no bundled binary or preference file |

Geometry, single-satellite power/latitude not repeated in Fig13, numerical
solver details and all other unreported values must remain disclosed as
reconstructions. None is tuned to force reference agreement. A complete source-
bound external configuration is required; `CONFIGURATION_CONTRACT.json` is
documentation and must not be passed as a runnable case configuration.

A full8 run and saved-only two-TS run have distinct scopes. The latter reuses six
saved chains and MC1000 evidence. Exact dual-language equality, a reduced demo,
host exit0 or controller tests cannot replace complete own-state feasibility,
convergence, primal/QT, phase/domain/stop, original-budget and reference checks.

The exact complete A example is bundled as `examples/Fig13-A-full-configuration.json`
with SHA256 `0bac4efeba390b8b99fe80f31ae80c6eb6561100741b744a21ee5b314ce85971`.
It is the same historical source-bound input used in the import/input IO proof;
the new public full8 adapter has not executed it numerically. This file's
unreported seed, caps and solver settings remain reconstruction controls.

The selected historical Python C run used50W, central latitude0degrees and a6x8
satellite UPA (N48); the RIS has M25 elements. Its configuration digest is recorded in the numerical summary.
These values are explicit reconstructions and differ from the separate Fig12
fair single-satellite scenario at150W and latitude1.25degrees. Neither the C
input nor current timing records recover the author's unreported Fig13 geometry.
