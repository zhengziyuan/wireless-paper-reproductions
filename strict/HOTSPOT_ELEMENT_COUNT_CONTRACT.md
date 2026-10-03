# Chapter3 Fig3-9: count changes aperture gain only

The supplied author's Chapter3 subsection on Fig3-9 states that with the
number of phase-controlled subsurfaces fixed, the microelement count determines
only the maximum aperture gain. The source plot has all seven counts
4000,8000,12000,16000,20000,24000,28000, with U6,M25 and satellite Rician12dB.

The old provisional row/column sweep was not that source grid. Moreover,
recomputing center coordinates proportional to sqrt(aperture area) would
change propagation phases, contrary to the source's count-only experiment.
This is a reconstruction error, not proof that the published curve is wrong.

`hotspot_element_count.py` retains the full declared reference geometry of
the200x140/28000-element configuration. At count n:

```text
area = n * element_area
receiving/reradiating aperture gain multiplier = n /28000
each of satellite-RIS and RIS-HU field multipliers = sqrt(n/28000)
each finite-Rician link variance multiplier = n/28000
shared-G cascade field multiplier = n/28000
```

Direct/NHU links, ground propagation phases, subpanel centers, phase dimension,
normalized noise, common400m ground amplitude, Rician ratios and shared-G
structure remain unchanged. An integer row/column factorization is irrelevant
to this aperture-only channel model and is neither guessed nor fitted.
The declared centers remain **unreported numerical choices**; this does not
claim recovery of the author's hidden original geometry or historical plots.
The current generator separately enforces the source10-20m range for **every**
HU pair with a disclosed radius10m cluster. Old radius15m component fixtures
and receipts are preserved as historical evidence, not reused. Python and
MATLAB count adapters now invoke `scenario_geometry.py` /
`strict_hotspot_geometry.m`; scalar aperture scaling never changes that
fixed geometry as the count varies. Feed/LoS phase conformance remains separate
from this proven pairwise/count contract.

Independent MATLAB scaling is in `strict_hotspot_element_count.m`. The complete
MATLAB runner mechanically preserves the original QT/SDR/RGD body; a source
equality test rejects an outdated body. Its own actual runtime files and the
input configuration are hashed at beginning/end. Python adds the executed
count adapter to every immutable source/checkpoint contract.

Component tests check all seven counts at16 feeds/16 streams/6 HUs/10 NHUs/
25 subsurfaces, identical RNG consumption and invariance of direct/NHU links,
finite-Rician factors and shared-cascade fourth-power scaling. They are **not**
7000 optimizer sample executions or an original-figure certificate.

The full entry point retains1000 configured optimizations per count, all
original scheme/budget endpoints and every Gaussian SDR randomization.1000 is
a disclosed reconstruction count where the author source does not specify it.

```sh
python strict/reproduce.py --paper hotspot-satcom --figure 9 --language python --execute
python strict/reproduce.py --paper hotspot-satcom --figure 9 --language matlab --execute
```

Computed curves are accepted only after all seven complete populations pass
physical, actual stopping, primal and QT/SDR checks. Earlier shape-changing
candidate data are rejected, and reference agreement is evaluated separately.
