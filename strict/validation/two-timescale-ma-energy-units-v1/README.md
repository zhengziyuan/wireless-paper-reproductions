# Supplied MA source: energy-footnote unit correction

The supplied author LaTeX `bare_jrnl.tex`, SHA-256
`9ba173a0da8fcd472bb211155e0a4c1e7b9a0104a718bd88ac166808be876b19`,
line 178, writes half a wavelength as 25 mm at 12 GHz. These values are
inconsistent: using exact SI c = 299792458 m/s, the wavelength is
24.9827048333 mm and **half the wavelength is 12.4913524167 mm**.

With the same footnote's six antennas, two displacement axes, motor power
8 W and speed 0.94 mm/ms, the stated movement model gives:

| Displacement on each axis | All-six-antenna movement energy | Ratio to 0.03 J radio energy |
| --- | ---: | ---: |
| Physical half-wavelength, 12.4913524167 mm | 1.2757125872 J | 42.5237529078 |
| Rounded half-wavelength, 12.5 mm | 1.2765957447 J | approximately 42.55 |
| Literal 25 mm | 2.5531914894 J | 85.1063829787 |

Thus the supplied source's approximately 1.28 J and approximately 42-fold
energy ratio are consistent with the **half-wavelength displacement**, not
with the written 25 mm. The appropriate dimensional correction is to write
approximately 12.5 mm at 12 GHz. If 25 mm is intentionally retained, the
energy and ratio instead need approximately 2.55 J and 85-fold values.

The actual receipt contains exact rational numerators/denominators, the seven
arithmetic gates, the supplied manuscript hash/line, and source before/after
identity. No private manuscript is included. This is a proved inconsistency
of that supplied source, **not verification of the final IEEE version**.
The motor model itself is not experimentally validated here.

No simulation parameter, optimizer, trajectory or saved result was changed.
This unit error is not asserted to explain the Fig. 3/Fig. 4 discrepancies,
and is not evidence of full reproduction.

The byte-exact arithmetic audit is runnable without MATLAB or a private
manuscript:

```text
python audit_MA_energy_footnote_units_v1.py --output NEW-arithmetic-audit.json
```

That fresh arithmetic-only receipt correctly leaves supplied-source reading
false. The adjacent original receipt records the actual source-bound run.
Use `--source PATH_TO_THE_SAME_AUTHOR_TEX` for a fresh literal-source check;
the original complete source hash, not a similar paragraph alone, identifies
the manuscript version being discussed.
