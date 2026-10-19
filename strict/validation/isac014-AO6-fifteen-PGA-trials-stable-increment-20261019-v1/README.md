# ISAC014 AO6: fifteen actual PGA trials and stable-increment evidence

This fixed-input packet preserves the last PGA incumbent and all fifteen
actual trial points captured from the original first-scheme prefix through AO6.
The passive capture naturally returned 0 with the original held handle/source
closed, and all six original AO scalar histories remained IEEE64-identical.
The original branches rejected fourteen trials and accepted one.

The independent MP80/MP100 calculation found that all fourteen rejections were
false rejections for the full physical utility at the same actual points and
original Armijo inequality. With the captured rounded binary64 effective
channels frozen, only one false rejection remained: channel-construction
rounding changes the other thirteen apparent improvements; binary64 objective
evaluation additionally rejects trial0. This is a demonstrated arithmetic cause
for this actual fixture, not a proof that a paper formula or theorem is wrong.
The rounded-source-dot addendum retained the same fifteen classifications.

The unchanged stable-increment candidate matched all fifteen existing MP100
decisions. Its maximum absolute increment error was
0.0000000000000000000000107180965835440873635724368377130883336732439198341771890547707917591992803015032418518789900000000000039
and maximum relative increment error was
0.000000000667422691025774699485630550972140751441137633791365008215735014819584003342242457724652269189840120245665
The exact source and per-trial numbers are included. The candidate uses the
same fixed W/theta/iota and actual r0/r1, without changing thresholds, selecting
new steps, fitting tolerances or producing a new trial.

## Limits that remain

The full-physical projected-gradient norm was 0.000001194690890376815373272251521211858820090446696127542672059786234294792929314217668745301234496087095, above the unchanged
1e-6 threshold: strict PGA stationarity remains false. An algorithm's original
OR stop is not a strict-gradient certificate. No W/RIS derivative result is
claimed here. The fixture had zero hemisphere crossings, minimum absolute
cosine 0.002513970286016187 and 1035 literal nonfront fallback cases; behavior
at sign crossings/near-zero boundaries is not established by these points.

A subsequent full first-scheme experiment is separate. This packet does not
assert its completion, convergence or pass. Historical not-started flags inside
the preserved handoff describe that earlier preparation epoch. Native, full
six-scheme, original-reference and full-paper gates remain unpassed here.

## Portable fixed-input reader: actual first use returned 0

With Python and NumPy installed, a fresh output outside the packet is required:

```text
python -B read_saved_fifteen.py --output-dir ../AO6-fixed15-inspect
python -B read_saved_fifteen.py --output-dir ../AO6-fixed15-replay --replay-stable
```

The first form verifies original captured input identities and inspects existing
closed MP results. The optional replay calls the exact original binary64
response/increment sources at the same fifteen saved endpoints and demands
that all three returned scalar values match the previous actual comparison
bit for bit. Neither command runs a new MP oracle, optimizer, line search,
Monte Carlo draw, RNG or trial. The unique actual `--replay-stable` first use
returned 0: all fifteen sets of three candidate scalar values were IEEE64-exact
matches to the earlier actual comparison. All original array dtype/shape/order
and NPZ identity checks passed; the ten mathematical/source/input dependencies
and input-manifest.json were identical before and after that call. The exact
path-free report is [included here](evidence/actual-first-portable-fixed15-replay.json).
This is a fixed-input binary64 replay and stored-MP readback, with zero fresh MP
calls. Strict PGA stationarity and the broader trajectory/reference gates remain
false. Documentation and this receipt were finalized after the call; the tested
input manifest, code and numerical data remain the exact executed bytes.

The independent MP formulas remain available through the repository-relative
source links and immutable digests in provenance.json. The supplied MP reports
are full per-trial results; this portable reader does not recompute them.

## Byte and evidence scope

The original NPZ is copied exactly (no pickle loading, dtype conversion or
array editing). Full capture metadata and both scientific reports are losslessly
gzip-compressed after replacing private absolute-path JSON strings only. Every
original numeric token and float64 bit remains unchanged; projection receipts
record the original and public digests. Both numerical source files are exact
bytes, including historical docstrings whose later fixed15 validation is stated
here rather than edited into the frozen code.

input-manifest.json contains only frozen numerical inputs and executable
sources. README, summaries, provenance and future first-use receipts are
delivery-only, so their later completion metadata cannot change the tested
mathematical dependency manifest. The delivery manifest covers the whole pack.
