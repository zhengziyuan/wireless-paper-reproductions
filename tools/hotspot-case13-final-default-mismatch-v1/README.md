# Case 13 and final IEEE simulation defaults

This is a parameter-provenance observation, not a reconstruction of the
author's Fig. 10, an optimizer run, or proof of the cause of its numerical
discrepancy. The user-supplied final publication is DOI
10.1109/TWC.2023.3309957. Its Section VI simulation setup, printed page 3658,
sets the non-hotspot SINR threshold to 3 dB and the terrestrial RIS-to-HU
Rician factor to 0 dB. The Fig. 10 caption, its legend and Section VI.G
(printed pages 3661–3662) do not themselves specify a different value for
either. This is an observation about the text and figure examined, not proof
that no unpublished simulation-specific override was used by the authors.

The retained case-13 final parameter projections for both starts contain 15
identical non-hotspot target values of `0.5011872336272722`, approximately
−3 dB. This is 6 dB below the final publication's stated global default.
The retained 25 RIS-to-HU mean/variance component pairs satisfy
`abs(mean)^2 / variance` approximately 100; with the implementation's
unit-modulus LoS steering convention, this corresponds to Rician factor
20 dB rather than the stated 0 dB global default. The source code for the
current Python and MATLAB statistical runners explicitly chooses the same
−3/20 dB variant; their separate full publisher conformance remains unproved.

For the three selected saved states, all 15 reported non-hotspot SINRs per
scheme fall below `10^(3/10)` in the *implemented full-J interference
evaluation*. These are saved binary64 reports, not an independent recomputation
of the original paper's constraints. Paper Eq. (32b) indexes interference over
K-only, while the implementation includes all J streams. The selected reports
therefore cannot by themselves decide feasibility under the literal printed
K-only expression. A subsequent exact fixed-state calculation applies the
K-only and full-J index sets separately to the **saved** Psi matrices and
saved mean/variance inputs. In each of the three schemes, both calculation
paths prove 12 of 15 NHU SINRs below 1.99, which is strictly below the 3 dB
threshold; the other three users are **inconclusive** under that one-sided
bound and are not declared feasible. With full-J interference all 15 are
proved below 1.99. See the
[exact threshold evidence](../../validation/hotspot-case13-default-threshold-v1/README.md).
This index comparison still uses the saved channel matrices, which have not
been shown to match the publisher's printed isotropic moments or the authors'
original channels. The historical origin and atomicity of the saved fields
have not been authenticated.

The target/ground deviations are concrete reasons that this saved case should
not be certified as the final IEEE Fig. 10 scenario on nominal labels alone.
They may affect the numerical gap; the present evidence does **not** establish
their individual or combined causal contribution, the original authors'
simulation settings, or that the paper's figure is erroneous. A future
final-default experiment needs fresh complete scenarios with 3 dB / 0 dB,
explicitly separated checkpoints and verified source/model assumptions.

From a complete repository checkout, run with Python's standard library:

```text
python -I -S -B tools/hotspot-case13-final-default-mismatch-v1/verify_recorded_parameters.py
python -I -S -B tools/hotspot-case13-final-default-mismatch-v1/test_saved_parameter_reader.py
```

The script reads only existing compact projections and does not parse or
redistribute the copyrighted PDF. Its output reports the saved values; the
paper-default transcription must be independently checked against the PDF.
The initially retained `recorded-parameters.json` was computed without
pre-binding the script's bytes; replay with the current script can reproduce
the arithmetic but does not authenticate that earlier process identity.
To check the paper transcription, inspect Section VI's global setup and Fig. 10's caption,
legend and Section VI.G. Absence of a figure-specific override in that scope
does not authenticate the unpublished author code.
