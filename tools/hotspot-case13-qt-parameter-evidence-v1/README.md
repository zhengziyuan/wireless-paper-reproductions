# Case 13: saved QT parameter consistency

This evidence checks eight recorded `QT_begin` events, covering four AO
iterations for each of two starts of the U=1, beta=20 dB hotspot-satellite
case. It does not establish optimization convergence or complete either
language's paper reproduction.

For each event, the saved noise, total-power limit, and 15 non-hotspot-user
SINR targets were compared with the `execute_final` record for the same
start. All **136 binary64 numbers** (8 × (1 + 1 + 15)) matched bit for bit.
Each record saved a normalized noise of 1, a power limit of 100, and 15
targets equal to the saved binary64 representation of approximately
0.5011872336272722. The recorded values alone do not establish physical units.

The eight `QT_begin` identifiers run from 718 to 725; each was associated with
a `QT_end` of the same identifier. The first and final saved event ordinals
were 1327581 and 1327965, respectively. The focused reader checked eight
indexed event windows, consuming 1,618,685 bytes of metadata and context and
skipping 219,533,917 bytes of numeric spans. The single controlled task exited
naturally with code zero in 12.062 seconds; its output total before the
terminal receipt was 5,408 bytes. Monitoring was polling, not a hard
filesystem quota.

The [`recorded_qt_parameters.json`](recorded_qt_parameters.json) file contains
the eight saved records, their paired event ordinals and per-field comparison
flags. The corresponding final-record values are in the previously published
[`final_parameters_projection.json`](../hotspot-case13-evidence-v1/final_parameters_projection.json).
These are small extracted records, not complete original trajectories. The
source trajectory chunks, index and final records were not freshly
authenticated, and the individually locked reads do not establish an atomic
snapshot of a whole event. The check supports the earlier use of each start's
final parameters for its four recorded QT updates, subject to those source
limitations; it does not independently establish the propagation model,
physical feasibility, full optimization convergence, MATLAB reproduction or
agreement with published figures.
