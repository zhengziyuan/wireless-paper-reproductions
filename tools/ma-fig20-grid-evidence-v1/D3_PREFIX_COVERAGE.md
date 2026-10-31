# Saved MA Fig. 20 D3 prefix coverage

This check concerns one retained Python statistical-search checkpoint for
Fig. 20, D=3 and geometry 0. It does not rerun the search or evaluate a rate.
The compact `d3-prefixes.json` fixture contains only the grid parameters,
saved winners, leaf counts and pruned prefix indices selected from the two
retained checkpoints and their certificate frames. It does not by itself
prove their historical provenance.

The 3×3 grid has nine distinct points, each separated by at least 1.6
wavelengths, so all 84 unordered choices of six points satisfy the saved
0.5-wavelength minimum spacing. The MRT checkpoint has 38 saved pruned
prefixes covering 43 combinations without overlap; 41 remain, matching its
saved leaf count. The ZF checkpoint has 18 prefixes covering 58 combinations
without overlap; 26 remain, matching its saved leaf count. Both saved winners
are among the uncovered combinations.

This is a combinatorial consistency check. Matching counts do not prove
that each uncovered geometry was actually evaluated, nor that a numerical
upper bound justified any prefix. A separate [algebraic argument](STATISTICAL_PERMUTATION_INVARIANCE.md)
shows that unordered choices cover labelled permutations for the selected
statistical objectives in exact arithmetic. It does not validate the original author's
unknown search criterion, MATLAB, reference figures or the full paper.
See the [saved winner physics evidence](../../strict/validation/ma-figure20-d3-g0-grid-physics-component-20261030-v1/README.md)
for separate checks on the retained 1,000-sample evaluations.

From this directory, run with Python 3 and a new output path:

```text
python -B check_d3_prefix_coverage.py d3-prefixes.json /path/to/new-output.json
```
