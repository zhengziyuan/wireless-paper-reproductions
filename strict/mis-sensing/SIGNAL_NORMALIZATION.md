# Sensing signal and power normalization

This file distinguishes the explicit printed optimization model, a physically
consistent reciprocal echo, and an inferred effective-noise candidate. The
original RALM, full apertures, target counts and iteration budgets are retained.
The candidate is not evidence of a particular original pulse count.

## Why the earlier unconditional bound statement was incomplete

The paper reports `beta_k² / sigma_k² = -73.88 dB` and `P = 30 dBm`, but does
not state the inverse-power reference unit or whether noise is measured before
or after pulse integration. If beta is a dimensionless channel amplitude,
beta²/sigma² is an inverse-power ratio, not a unitless number. The 30.20 dB
M400 and 6.12 dB M100 bounds are conditional on an inverse-watt, single-PRI
interpretation. They are not an unconditional proof that the original plots
are impossible.

The code now requires an explicit contract:

| Setting | Meaning |
|---|---|
| `reference_echo_db` | Reported logarithmic power ratio, converted once by 10^(dB/10) |
| `reference_echo_unit` | `inverse_watt` or `inverse_milliwatt` |
| `reference_echo_noise_domain` | `raw_per_PRI` or already `processed` noise |
| `effective_reference_gain_factor` | Explicit effective reduction of raw-noise power; not implicitly a PRI count |

Internal calculations always use physical power in watts. A -73.88 dB
inverse-milliwatt ratio equals -43.88 dB inverse-watt; both produce exactly the
same SINR if units are converted together. The physical transmit power remains
30 dBm = **1 W** in either representation. It is never changed to 1000 W.

An already processed reference must have processing factor 1; the helper rejects
double counting. A raw reference with factor 100 is mathematically equivalent
to an already processed inverse-watt reference increased by 20 dB. The stored
`echo_beta_squared` is a power coefficient: it must not be squared again.

## Reciprocal round-trip and matched filtering

Write D_u = diag(v_u), R = a_MIS a_BS^T, and c_k = a_MIS elementwise ak.
With unit-norm transmit and receive BS beams, the reciprocal scalar echo is

```
alpha_k = sqrt(P) L beta_k (c_k^T v_u)^2
echo power = P L^2 |beta_k|^2 |c_k^T v_u|^4
```

This follows from reverse-channel ordinary transpose and agrees with the
paper's Eq. (9)/(11), where v^H G_k v = |c_k^T v|². The earlier printed signal
equation uses ak ak^H but its following equations change that to ak ak^T;
the former does not generally yield this quartic echo. The code uses the
explicit PSD/quartic optimization model, not a silent Hermitian-channel swap.

For Tp unit-modulus PRIs, the unnormalized waveform matched filter yields
`s^H s = Tp`, while its AWGN variance is `Tp sigma_sample²`. A correct unit-norm
receive filter does not multiply thermal noise by transmit sqrt(P). For
unresolved directions with the same waveform correlation Tp and an incoherent
sum of target echo powers, the post-filter SINR is

```
gamma_k = |beta_k|² |q_k|^4 /
          (sum_{i!=k} |beta_i|² |q_i|^4 + sigma_sample²/(P L² Tp))
```

If the noise in the printed Eq. (9) is already the processed effective noise,
that factor is already absorbed. Actual delayed waveforms have correlations
`r_i = sum_t conj(s[t]) s[t + tau_k - tau_i]`; deterministic coherent echo
interference requires the squared modulus of the echo sum. Those waveform,
delay and coherence assumptions are not recovered from the manuscript, so this
repository does not invent them as verified original experimental settings.
The published numerical setting has L = 1.

## Two explicit settings, not a hidden correction

- `settings.json` preserves the literal inverse-watt/single-PRI interpretation
  with gain 1, marked as a declared contract whose source normalization remains
  incomplete.
- `settings_reference_candidate.json` preserves 6000 starts, 30 outer iterations,
  4000 inner-iteration caps and the original stopping schedule, but declares an
  **inferred** 100-fold effective reference/noise factor. It does not say that
  the author used Tp = 100.

The effective factor is identified by the entire six-power continuous-RIS curve,
not by matching a single favorable point. In an initial original-RALM diagnostic
with the original 10x10 RIS and all four targets, one deterministic matched-field
start per target/power reproduces the reference curve within 0.00836 dB. That
is a parameter fingerprint, **not** the complete 6000-start original figure.
Coherent integration over 100 PRIs is one possible physical origin; a processed
noise convention or reference-level difference can produce the same metric.
The physical attribution is not uniquely identified.

## Reproducible fingerprint diagnostic

From the repository root:

```sh
python strict/mis-sensing/test_normalization.py
python strict/mis-sensing/reference_candidate_fingerprint.py
```

In MATLAB, add `strict/mis-sensing` to the path and run:

```matlab
run_reference_candidate();
```

Both use the same original RALM and complete per-start budgets, execute all four
targets at all six original power points, and retain each phase, original stop
flags and actual constraint residual. The figures overlay computed candidate
data with clearly labelled **original EPS reference** vectors; those vectors
are never copied into a simulation result. Outputs are under
`strict/mis-sensing/outputs/reference-candidate-v2/`, separately from full bank
outputs. Actual convergence flags are retained even if the curve looks close.

Nearest 1-bit/2-bit phase quantization uses a fixed zero-phase alphabet without
fitted global rotations or an invented discrete optimizer. Its agreement may
be weaker because the paper does not specify the discrete baseline's phase
gauge, initialization or exact optimizer. No current receipt sets
`original_figure_reproduction_certified` to true.
