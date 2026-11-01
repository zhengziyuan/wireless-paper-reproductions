# Official GT pattern checks and an all-diameter NoRIS bound

This packet verifies a specific physical-input hypothesis while preserving the
original numerical results. It does not recover the author's hidden antenna
gains or certify the complete source scenario.

Three official sources were obtained and visually checked:

- [ITU-R S.1503-3, the cited2018 edition](https://www.itu.int/dms_pubrec/itu-r/rec/s/R-REC-S.1503-3-201801-S!!PDF-E.pdf), PDF page130/printed128, D6.5.1.1, directs the FSS earth-station pattern to S.1428. Its gain conventions include the peak gain; relative-gain use requires removing it.
- [ITU-R S.1428-1](https://www.itu.int/dms_pubrec/itu-r/rec/s/R-REC-S.1428-1-200102-I!!PDF-E.pdf), recommends1 pp2–3, gives the three D/lambda ranges and their main, transition, side and back lobes. The actual12GHz configuration lies in its stated frequency range.
- [ITU-R S.1419,1999](https://www.itu.int/dms_pubrec/itu-r/rec/s/R-REC-S.1419-0-199911-I!!PDF-E.pdf) discusses coordination techniques and examples for19.3–19.7/29.1–29.5GHz. Those references do not uniquely specify the missing12GHz simulation diameter or satellite/terminal beam gains.

The private PDFs are not redistributed. Their exact SHA256 values, edition,
page locations and the author's bibliography/source hashes are recorded in
`primary-reference-and-scope-bindings.json`. Initial Poppler renders lost
Symbol glyphs; formula admission used the correctly rendered Ghostscript pages.

Actual scalar evidence covers **517 inputs in both Python and MATLAB** across
all three diameter regimes and both angular signs. The native scalar function
is an exact byte extraction of the executed original function with only its
name changed; the inverse and before/after source/input bindings are retained.
Independent MP80/MP100 checks pass at all **500 explicitly defined-domain
probes**, with1e-12 absolute/relative linear-gain tolerances. Maximum precision
difference is2.967e-68; maximum observed Python/native relative gap is5.036e-16.

The other **17 probes remain explicit conventions**:11 boresight values use
the continuous peak extension, and six signed small-q33.1deg cases use a left
extension at a gap between the printed strict clauses. They are not relabelled
as printed-domain coverage. Algebraically defined transition angles are probed
on their strict sides, not asserted representable as exact floating equalities.
The packet is a source/finite-precision audit, not a continuum interval proof.

The current original geometry gives GT off-axis angles approximately
29.0541056,0,29.0541056deg. An independent meridional atan2 identity checks the
production acos geometry without boresight cancellation. The chosen1.2m diameter
at12GHz gives D/lambda=48.0332297; it remains an unreported reconstruction choice.

The new NoRIS relaxation covers **every diameter with D/lambda>=20** while all
other saved inputs stay fixed. At the two side angles, both standard diameter
families are already beyond their transition lobes, so their gains do not depend
on diameter. At boresight the smallest peak occurs at D/lambda20. Taking each
satellite's smallest gain independently gives a permissive leakage envelope,
even though the minima need not be simultaneously attained by one diameter.

GT second moments scale linearly with that receive gain. Therefore every
previously verified useful/leakage quotient scales by
`gain(original diameter)/gain_floor`; the existing min-SINR relaxation then
bounds the entire diameter family. Its original full-matrix MP quotients are
reused under exact array/configuration hashes. No diameter grid search, new
matrix solve, optimizer or random draw is used. A separately disclosed1e-10
relative/1e-12 absolute upward numerical envelope makes the bound more permissive;
all original physical and solver gates remain unchanged.

For all18 RIS-size source slots, **all54 NoRIS reference ordinates per language
still exceed this all-diameter bound**, after the EPS rounding allowance and
the upward envelope. The largest relaxed bounds across the complete cohort are
0.509552 for AP-NoRIS,0.453212 for MR-S-NoRIS and1.397289 for MR-TTS-NoRIS.
Thus changing only the unreported GT diameter cannot explain these source gaps
within the same pattern family and fixed remaining inputs. This does not rule
out a different source geometry, satellite/terminal gain, normalization or
receive-pattern class, and is not proof of an error in the author paper.

The author's Chapter4 states that pathloss uses multibeam patterns. The full
source patterns and absolute LEO/GEO/LU gains remain unrecovered; the current
40/40/0dBi defaults are disclosed choices. IEEE search found article10679992,
but the existing profile reported a sign-in page and returned no PDF; the author
PDF request returned429. Final-publisher conformance remains unverified, with
no document-absence inference from those failed accesses.

Restore the linked real inputs and replay both independent checks:

```powershell
python tools/cooperative-stable-replay/unpack_input_bank.py --packet strict/validation/cooperative-original183-inputs-20261017 --output-dir strict/outputs/source-original183
python tools/cooperative-stable-replay/unpack_power_evidence.py --packet strict/validation/cooperative-subsurfaces18-dual-final-states-20261017 --output-dir strict/outputs/source-M18
python tools/satellite-source-audit/replay_evidence.py --packet strict/validation/satellite-GT-pattern-and-diameter-family-20261017 --M18-directory strict/outputs/source-M18 --input-bank strict/outputs/source-original183 --output-dir strict/outputs/source-GT-replay
```

Replay needs NumPy and mpmath. The stored native scalar observations avoid a
new MATLAB execution. The full independent state/coordinate/phase audits and
original-reference/full-paper gates retain their separate scopes.
