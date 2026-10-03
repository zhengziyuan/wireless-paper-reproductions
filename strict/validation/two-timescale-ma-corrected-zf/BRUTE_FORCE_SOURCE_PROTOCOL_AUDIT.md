# Figs19/20: source-supported grid, undisclosed search objective

Direct read-only audit of the author's R2 `bare_jrnl.tex` and original EPS.
No private source files are redistributed; no frozen engine or live bank changed.
The matching public text is [arXiv v2, Section VI](https://arxiv.org/html/2410.05912v2#S6).

Source anchors:

- TeX L1032 defines Fig19 N4/M3, x/y[-1.6,1.6]lambda; Fig20 N6/M5,
  x[-1.6,1.6]lambda, y[-1.6,2.4]lambda, both kappa20dB.
- L1035–1036 /1041–1042 associate the panels with `bruteforce2.eps` /
  `bruteforce1.eps`. L1045 explicitly says D points **per axis**, D^(2N),
  and D10/N4 =1e8 evaluations before pruning.
- Fig19 EPS L1246 and Fig20 EPS L998 independently identify the same per-axis
  horizontal meaning. Axis ticks span3:18 and3:12. A further direct EPS path
  audit, not merely tick inference, finds Fig19's brute-force polyline and circle
  markers at all16 equally spaced x positions from30.75 to318.75 (19.2 units
  apart), and Fig20's at all10 x positions from30.75 to318.75 (32 units apart).
  Those positions coincide with D3:18 and D3:12 respectively. Fig19 marker
  definitions are around EPS L1780–1920; Fig20 polyline/markers aroundL1520–1640.
  Thus future full source-axis configurations must be separate: do not truncate
  Fig19 to the old shared D3:12 configuration, or extend Fig20 to18.
- The four legends name MRT/ZF brute-force and SCA. Neither those legends nor
  TeX L1032–1047 identifies which candidate search objective was used.
- TeX L230 onward formulates the MRT expected-rate problem before expression13;
  L517 onward formulates the ZF expected-rate problem before expressions37/39.
  The design expressions are distinct from actual finite-sample MC evaluation.
  Original MC counts and draw coupling between candidate layouts are not stated.

Source identities: TeX SHA256
`9ba173a0da8fcd472bb211155e0a4c1e7b9a0104a718bd88ac166808be876b19`;
Fig19 EPS `184ac50c96cd221757ba36bfd7dc7058dbcd073596e99b57dfab012e9f51d689`;
Fig20 EPS `a3dd1980d6125e9abc885bcc7823f29d1a19e37ca0437b6da6f4d32e1eeccb8a`.

Consequently there are two separately labelled reconstructed protocols, neither
certified as the unique historical source procedure:

1. Exhaustively maximize original statistical expression13/39 on the full feasible
   grid, then independently evaluate the selected geometry with all configured1000
   original-channel draws.
2. Exhaustively maximize the actual finite-draw MC mean over all feasible **ordered**
   layouts, using the unchanged per-antenna draw array.

For protocol1, antenna-row permutations leave LoS pair inner products and
`Hbar^H Hbar` unchanged, as well as region/spacing constraints. One unordered
grid combination therefore exactly covers all corresponding ordered layouts;
this is duplicate removal, not sampling or a different objective. The population
ergodic rate shares that symmetry because Gaussian row permutations have the
same distribution. Protocol2's particular fixed draw array is not invariant;
permuting LoS rows while keeping NLoS rows fixed changes candidate sample channels.
**Do not transfer protocol1's symmetry reduction to protocol2.**

The raw count D^(2N) is source-supported. For protocol1 its exact duplicate-free
upper count is binomial(D^2,N), before spacing pruning; this can still be large.
For protocol2, D10/N6 gives1e12 ordered layouts before pruning, each with1000
draws in the current disclosed reconstruction. These are candidate counts,
not measured runtime estimates. The100 geometry/1000 NLoS counts are configured
choices, not recovered original counts.

Any future branch-and-bound must certify the **same explicitly chosen objective**
on every omitted subtree, retain all original axis points and constraints, and be
checked against complete small-grid enumeration. A local solver, random subset
or survivor average cannot be called exhaustive. No complete-grid optimum or
historical-figure recovery is established by this semantic audit.
