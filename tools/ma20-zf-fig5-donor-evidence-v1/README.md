# Conditional reuse check: MA Fig. 20 D3/g0 ZF trajectory

This record checks whether the **currently saved** Fig. 5 case 7 / geometry 0
ZF result can supply a conditional candidate for Fig. 20 D3 / geometry 0,
without running the coordinate optimizer again. It does not authenticate the
historical producer, its inputs at production time, or the complete paper.

The currently saved jobs have matching geometry and 1,000 matching NLoS draws
when their real and imaginary components are compared bit for bit. Those
draws are *not* evaluated in this check. The Fig. 5 job has no explicit
region. The bound current run.scenario code therefore supplies the default
box \([-2,-3]\) to \([2,3]\); the Fig. 20 job supplies the smaller box
\([-1.6,-1.6]\) to \([1.6,2.4]\). This is a current-source reconstruction,
not independent authentication of the historical run's box.

Only the 34 saved sweep-boundary position arrays and 198 saved coordinate
records are available. The reader reconstructs intermediate positions by
assuming the bound current implementation's single-coordinate update order.
It checks current-source ZF objective values, box and minimum-distance
constraints, linearized spacing constraints, and the original implementation's
acceptance and stopping conditions. It recomputes the surrogate gradient and
its tangent gap over the source's polygon vertices for both boxes. The 33rd
sweep is the first saved threshold crossing.

| Conditional check | Observed value |
| --- | ---: |
| Reconstructed coordinate records | 198 of 198 |
| Saved sweeps | 33 |
| Recorded check failures | 0 |
| Maximum saved large-box floating gap | \(9.40825\times10^{-13}\) |
| Maximum recomputed large-box floating gap | \(9.54340\times10^{-13}\) |
| Maximum recomputed smaller-box floating gap | \(7.29399\times10^{-13}\) |
| Maximum source objective discrepancy | 0 in binary64 |
| Minimum smaller-box margin | 1.03241 |
| Minimum spacing | 0.5 |
| Minimum linearized spacing residual | \(-5.55112\times10^{-17}\) |

All checks use floating-point arithmetic and the **same current source**.
In particular, the polygon enumeration uses determinant thresholds and is not
an interval proof that every geometric vertex was found. The reported tangent
gaps are not rigorous global certificates. Box inclusion alone also cannot
authenticate the historical optimizer or reconstruct unrecorded trajectories.
The old and current job bytes were held stable only during this read; that
does not authenticate earlier data generation. The original optimizer was not
rerun, and MATLAB independent AO, per-user physical feasibility, sample-rate
agreement for this ZF endpoint, Fig. 20 reference agreement, and all-paper
acceptance remain outstanding. Conditional pass is not a full-science pass.

The first audit attempt failed before replay because its reader incorrectly
required an explicit old-job region. Its preserved terminal reports child
exit 1 and KeyError: region_lower; this record keeps that failure. The second
reader followed the current source's paired-override/default behavior, and its
guard exited naturally in 2.046 s. Monitored output before the terminal was
1,568 bytes; polling is not a hard filesystem quota. The result and both
redacted guard terminals are in recorded_zf_conditional_audit.json.

The file verify_saved_zf.py is the source used by the second reader. It exposes
a function accepting already decoded job, configuration and result objects and
the source modules. The saved channel bank and historical result are not
redistributed here. The comparison uses the configured 10,000 AO sweep cap;
the 1,000-draw bank was checked for current bitwise equality, not rerun.
