# Saved native statistical-bank replay

These tools consume the completed standard native 18-case statistical bank.
They do not launch a second optimization bank. All cases U=1..6 and satellite
Rician factors 0/10/20 dB, all 243 prescribed starts and all 54000 selected-
design rate samples are retained. The implemented branch is the explicitly
corrected vector-QT finite-Rician model, not the invalid printed scalar SOC.

Install `strict/requirements.txt` and this directory's `requirements.txt`.
The precision audit was executed with [mpmath 1.4.1](https://pypi.org/project/mpmath/1.4.1/).

## Portable numerical inputs and endpoint replay

The [saved numerical package](../../strict/validation/hotspot-native18-replay-20261017/README.md)
contains unchanged native case/configuration bytes and the replayed model
contexts. A fresh destination is required:

```text
python -B tools/hotspot-native-replay/unpack_saved_inputs.py --archive strict/validation/hotspot-native18-replay-20261017/native18-saved-inputs.tar.gz --output-dir native18-unpacked
python -B tools/hotspot-native-replay/audit_endpoint_mp.py --bank native18-unpacked/native18-saved-inputs/bank --contexts native18-unpacked/native18-saved-inputs/contexts --output-dir native18-endpoint-mp
```

`audit_saved_native.py` independently expands all finite-Gaussian second
moments and received powers, checks every initial/final design and stored
stop field, and separately checks terminal phase gradients through the Python
implementation. Its stricter absolute-only diagnostic retains 22 differences
above 1e-9. `audit_endpoint_mp.py` evaluates all 243 final physical metrics at
both 80 and 100 digits using the independent Gaussian formulas. It uses the
pre-existing field policy `1e-9 + 1e-10 * max(abs(reference), abs(recorded))`
and cross-precision absolute1e-40. Physical power/QoS and original gradient/
relative stopping thresholds are not changed.

## Native channel replay, without optimization

With MATLAB and the original source files, the two exporter functions rebuild
the declared constructor and the original 1000-draw RNG stream in every case.
They compare all saved producer source/configuration identities before use.
No CVX solve is required by either exporter.

```matlab
export_saved_native_contexts(repo, bank, newContextDirectory);
export_saved_native_mc(repo, bank, newChannelDirectory);
```

The exported channel file is explicitly little-endian float64 with recorded
shapes and column-major array order. The MC consumer independently constructs
the complex received signal for each of the 54 fixed saved designs and compares
all 54000 stored rate samples, means, standard errors and empirical expected-
power ratios:

```text
python -B tools/hotspot-native-replay/audit_saved_mc.py --bank native18-unpacked/native18-saved-inputs/bank --channels newChannelDirectory --output-dir native18-mc-replay
```

The approximately 477 MB regenerated channel payload remains an external
runtime output. Its bytes are not described as recovered historical callback
buffers. All 54000 recorded samples agree with its physical replay.

`compare_saved_curves.py` compares all 54 computed points to the already retained
original-EPS extraction, without fitting or a new EPS-access claim. Separate
native/Python optimization banks need not share an RNG stream or an identical
nonconvex trajectory. Agreement of their curves does not resolve missing
historical geometry/pattern conventions or establish original-figure agreement.

Every evidence stage explicitly retains its own scope. Full inner trajectories,
unobserved author conditions and all other paper figures are not certified here.
