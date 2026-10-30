# Saved ZF tangent-point weights for MA Fig. 20 D3

For the retained D3/g0 ZF search, each pruned prefix records a dyadic
tangent-point candidate over the remaining grid points. This compact fixture
contains only those 18 prefix lists and their saved integer weights. It is
selected from the checkpoint's compressed witness frame; the fixture itself
does not establish historical provenance.

The companion checker uses exact integer arithmetic with denominator 2^32.
For each prefix it checks that there is one weight per remaining candidate,
each weight is in [0, 1], and the weights sum to the number of positions
still to be selected. All 18 saved rows meet these hypersimplex conditions.

Being a valid tangent point does **not** prove the tangent upper bound, its
saved digest, the historical incumbent, or the safety of pruning. Those need
an independent calculation of the five-user statistical objective and the
actual search chronology. This check is not MATLAB, reference-figure or paper
acceptance.

From this directory with Python 3 and a new output path:

```text
python -B check_d3_zf_dyadic.py d3-prefixes.json d3-zf-dyadic.json /path/to/new-output.json
```
