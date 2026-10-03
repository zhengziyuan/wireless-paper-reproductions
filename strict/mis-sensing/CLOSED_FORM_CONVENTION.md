# Same-reference closed-form convention

This is a mathematically consistent implementation of Section VI's quadratic
phase pairing and original displacement law. It is **not yet a recovery or
certification of the original Figure 2's finite-aperture phase settings**.
The original 20 × 20 / 16 × 16 dimensions, nine targets, all 25 placements,
and finite zero-phase **one-padding** are retained.

## Exact phase and field identity

The author manuscript's Section VI Eqs. (60)–(66) uses the same reference
point for both phase functions, `Theta(x,y) = -Phi(x,y)`, and a negative
array-factor exponent. In zero-based coordinates measured in wavelengths,

```
Phi[r,c] = +A d² (r²+c²)
Theta[i,j] = -A d² (i²+j²)
V[r,c;t] = 2 A d² (t_r r+t_c c) - A d² ||t||².
```

The constant is retained by evaluating the exact chirps. It does not affect
overlap-only steering, but affects the relative phase of the overlapped and
non-overlapped fields, so deleting it in the finite padded model is incorrect.

The implemented Eq. (11) steering vector has a **positive** array exponent,
and fields are evaluated with an ordinary transpose. Therefore we conjugate
**both** same-reference phase vectors:

```
implemented Phi[r,c] = -A d² (r²+c²)
implemented Theta[i,j] = +A d² (i²+j²).
```

Conjugating both chirps and reversing the array exponent conjugates the whole
finite field, including the one-padded cells. Consequently the array powers
and quartic echo metrics are exactly identical to the Section VI convention.
No MS2-only coordinate offset is used. The earlier maximum-span offset was
an inferred compensation for inconsistent phase/field signs, not a uniquely
specified source design; its historical outputs must not be silently reused
under this corrected convention.

## Original placement law, not a numerical maximiser

With the source coverage choice
`A = pi/d * max(1/(Ur-1),1/(Uc-1))`, continuous shifts are
`t = pi/(A d) [sin(theta) cos(phi), sin(theta) sin(phi)]`.
Each coordinate is recovered by `floor(t+0.5)` and clipped to the admissible
placement range. No objective-based placement search is substituted.
For Figure 2, the complete nine-target zero-based positions are
`[10,6,2,15,12,3,20,18,4]`.

The source's coarse direction-cosine grid and finite one-padding can cause
miscentred beams and leakage. These are evaluated rather than hidden.
In particular the ideal overlap-only second beam points at approximately
azimuth 45° / elevation 20.70°, while its designated target is 45° / 30°.
Original-reference units and historical finite-aperture coordinates remain
separate provenance questions; this fix does not fit a plotted endpoint.

## Dedicated verification

Python, full dimensions and all placements:

```
python strict/mis-sensing/test_closed_form.py
```

MATLAB, after adding `strict/mis-sensing` to its path:

```
run_mis_sensing('closed-form-matlab-tests.json','closed-form-test');
```

Tests independently check exact finite quadratic differences (including the
constant), coherent overlap alignment, ordinary-transpose field conjugacy,
full finite padding, shared reference/no layer-only offset, row-major mapping,
and all nine placements. These are identity tests, not all-figure runs.
Their receipts and new output metadata explicitly retain
`original_figure_reproduction_certified=false`.
