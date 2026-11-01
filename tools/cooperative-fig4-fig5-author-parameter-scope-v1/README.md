# Cooperative Fig. 4/5: visible working-script parameter scope

This is a **source-scope check**, not a reconstruction or acceptance of the
paper. It compares the user's supplied working archive with the final IEEE
publication, DOI 10.1109/JSAC.2024.3460068, printed pages 291–292. The
publisher's discussion of Figs. 4/5 specifies the following Rician factors:

| Context | Satellite-to-ground | Terrestrial |
| --- | ---: | ---: |
| Fig. 4 | 20 dB | 10 dB |
| Fig. 5 | 0 dB | 10 dB |
| Visible archive `main.m` and `INIT...m` | 20 dB | 0 dB |

The visible `main.m` fixes the second sweep variable to 2 and contains an
uncommented invocation of the named INIT script; the visible INIT
script sets the satellite factor to 10 raised to that variable and the
terrestrial factor to 1. In that convention the values are 100 and 1, or
20 dB and 0 dB. Static source inspection does not establish an actual
execution of that invocation. The archive's two `plot_record0119.mat` and
`plot_record0120.mat` files each contain a single top-level real-double
`plot_record` array of shape 18×20×5 and no top-level Rician metadata.
Consequently these files do not establish which parameters or source revision
produced their values. The currently visible working script cannot simply be
treated as the published Fig. 5 source. Fig. 4's previously documented
graphical agreement with three saved means remains a graphical observation;
it does not prove that this visible working revision generated those means.

The supplied user confirmation that Figs. 4/5 used six LEO users is separate
from final Table I's two-user setting. Neither the Rician differences nor
the user-count difference establish a publisher error, a particular
historical author run, a Fig. 5 data mapping, a physical-feasibility result,
or a complete reproduction. The exact original plotting script and its
parameter/RNG records, or original numerical arrays labeled by figure and
configuration, would resolve the present source-identification gap.

From the repository root, supply the original author ZIP and final PDF
independently; neither is redistributed. Python 3 and Poppler `pdftotext`
must be available:

```text
python -I -S -B tools/cooperative-fig4-fig5-author-parameter-scope-v1/check_parameter_scope.py --author-zip /path/to/test_varsigma_316.zip --paper-pdf /path/to/final.pdf
```

The command reads two small MAT members and the selected source files in
memory, calls `pdftotext` for the two pages without saving page images or
text, and emits only compact derived metadata. It performs no optimizer,
channel simulation, archive extraction, or historical-content authentication.
It checks the specific page wording and source syntax used here, rejects
MATLAB block-comment markers rather than trying to interpret them, and checks
for a standalone, uncommented INIT invocation; a different
PDF extraction order or source revision can cause an explicit refusal rather
than proving a contradiction. `recorded-parameter-scope.json` is the retained
local result. Synthetic tests use only in-memory fabricated inputs.
