# Figure 11: inclusive movable-panel count, not a fitted curve correction

The supplied communications R2 author source is internally inconsistent. Its
model defines `Ur = Mr - Nr + 1`, `Uc = Mc - Nc + 1`, and `U = Ur * Uc`
(lines 223–230). The Figure 11 discussion (line 913) instead states that a
1×64 panel and a 1×36 movable subpanel give **U = 28**. The model gives
**U = 29**: the final legal placement must not be discarded.

| Panel | Subpanel | Ur | Uc | Full legal positions U |
| --- | --- | --- | --- | --- |
| 1×64 | 1×36 | 1 | 29 | 29 |
| 1×64 | 1×16 | 1 | 49 | 49 |
| 1×64 | 1×4 | 1 | 61 | 61 |
| 8×8 | 6×6 | 3 | 3 | 9 |
| 8×8 | 4×4 | 5 | 5 | 25 |
| 8×8 | 2×2 | 7 | 7 | 49 |

The other comparison in the same sentence, 8×8 with 6×6 giving U = 9,
agrees with the formula. This is an exact integer-count contradiction in the
supplied source, **not a final-publisher erratum or a proved cause of any
historical SNR discrepancy**.

Source identity reviewed on 5 October 2026:

- Supplied `bare_jrnl.tex` R2 SHA256:
  `6e27fb9fd2ba0decc9d7bcfc54bcb73612553f91f6df923ab502e7d561058cb0`.
- Python strict engine SHA256:
  `eb90ca857df1cf3aed094c91c1ccee1461e571a96f15e42f7545768acaa1de77`
  (inclusive row-major placements at lines 69–73).
- MATLAB strict engine SHA256:
  `763a55bbcd74561c56f4bf668ef634863546b2cf235d16ab1854102d32da2108`
  (inclusive row-major placements at lines 106–110).
- Figure map SHA256:
  `2463594c5e4d85980e15eb6b2baf2465cd6962ad49df616f96f3899db59ef487`.

The current full Figure 11 route keeps all six shapes above and all eight
configured K values (2, 4, …, 16): **48 configurations**, each with a full MIS
and SMS bank of 6000 starts, or **576000 starts per language**. The K grid,
6000 starts, random seeds, 4000 inner allowance and unreported tolerances are
disclosed reconstruction controls, not recovered author history. Dynamic RIS
is the separate analytical comparison; it is not counted as an optimizer run.

No curve is rescaled, position removed, start filtered, or algorithm changed
by this audit. The existing engines already use the inclusive model. No new
full-48 optimizer execution, convergence, physical check, dual-language
agreement or original-figure agreement is certified here. Those gates remain
separate and nonpassing until their complete evidence exists.

Portable exact-arithmetic checks (no NumPy, MATLAB, draws, or optimizer):

```text
python -B audit_position_count.py
```

Run this command from this directory. The source hashes above identify the
reviewed private author source and existing implementations; this arithmetic
test does not retrieve or certify a publisher PDF.
