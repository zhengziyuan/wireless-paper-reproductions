# MIS sensing: conditional high-precision check of saved start 3072

This check concerns the nine selected targets of one saved Fig. 3/5/6 start,
not an independent experiment or reproduction of the complete figure or
paper. The previously retained selected state and field values are used as
inputs; the calculation does not optimize the state or draw new samples.

The saved configuration interprets the echo-to-noise reference as inverse
watts, uses raw noise per PRI and an effective processing gain of one. The
user's indication that the noise was probably raw per PRI is tentative; the
author's reference unit and processing gain remain unconfirmed. The code uses
azimuths `[0, 45, 90]` degrees repeated three times and elevations `[30, 30,
30, 50, 50, 50, 70, 70, 70]` degrees, as recovered in the existing code
model. These are conditions of the result, not independently established
physical measurements or source conventions.

Under those assumptions, all nine 80- and 100-decimal-digit calculations were
finite. Their largest absolute difference was approximately 4.43e-74. The
largest absolute difference between the 100-digit results and the saved
Python field values was approximately 1.18e-13. The saved Python values and
this calculation use the same retained state and model; they are not
independent measurements.

The minimum 100-digit SINR was approximately 65.17456997305443. The saved
eta exceeds it by approximately **1.10709e-8**: a strict comparison using the
reported 100-digit approximations fails at this saved point. The difference is less than the saved
1e-6 feasibility tolerance, so all nine targets are within that tolerance.
This tolerance result does not establish strict feasibility. The saved start
also has an inner-iteration-cap exit, so the forward calculation does not
establish convergence of its optimization history.

The original guarded task exited naturally in 1.078 seconds and used 2,990 B
in its output tree before the terminal record. Its minimum observed E-drive
free space was 139,762,470,912 B. The monitor polled and was not a hard
filesystem quota. The retained historical input content, mpmath dependency
content and a whole-state atomic snapshot were not freshly authenticated.
Agreement between two working precisions is not an interval error bound, a
MATLAB check, validation against the published reference, or a physical-unit
certificate.

## Replay the arithmetic

The already-published inputs are
`strict/validation/mis-sensing-fig3-5-6-saved6000-20261019-v1/data/selected-fixed-final-state.json`
and the adjacent `evidence/actual-output-and-visual-review.json`. The
recorded arithmetic output is `selected3072_mp_recorded.json` in this
directory. With Python 3.12 and mpmath 1.4.1 using its pure Python backend,
run from the repository root:

```text
python -B tools/mis-sensing-evidence-v1/verify_selected3072_mp.py --expected tools/mis-sensing-evidence-v1/selected3072_mp_recorded.json
```

The verifier reads only those two existing inputs and the optional recorded
result, recomputes the nine values at 80 and 100 digits, compares the
calculation fields, and prints its report. It does not reproduce the original
external process/storage guard or authenticate historical data.
