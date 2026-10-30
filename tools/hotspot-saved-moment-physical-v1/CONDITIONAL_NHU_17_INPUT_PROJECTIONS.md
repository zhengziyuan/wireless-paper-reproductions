# Saved-state NHU input projections

`conditional_nhu_17_input_projections_v1.json` contains 17 compact projections
of saved inputs for the conditional NHU interval check. Each projection keeps
only the reported and tuned configuration fields, RIS flag, and 16-by-16
complex beam matrix used by `check_saved_nhu_interval.check`. It is not the
original full result or an optimizer checkpoint. U3/beta20 is omitted: its
earlier receipt was reused separately and is not part of this file.

The JSON scenario order is U=1..6 and beta=0,10,20 dB, excluding U3/beta20.
For each `cases` entry, pass `entry["projection"]` to `check` after importing
`check_saved_nhu_interval` from this directory. Python's ordinary JSON decoder
recovers the same binary64 values as the source files. The fields and matrix
components were compared individually with the 17 saved files; no interval
calculation was repeated to create or verify this projection.

The associated retained computation checks NHU ratio margins for one saved
beam under reconstructed geometry and the stated interval arithmetic
assumptions. It does not authenticate historical inputs, prove unit-modulus
phases, verify other constraints or convergence, reproduce a figure, or
establish a full-paper pass. The source-relative labels identify case files;
they are not assertions of original-author provenance.
