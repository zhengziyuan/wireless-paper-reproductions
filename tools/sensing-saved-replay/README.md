# Reuse complete saved sensing states and record missing native slots

`audit_population.py` independently reconstructs the actual Fig3 geometry and
all nine target responses, quartic echo powers, self-excluded interference,
relaxed/binary metrics and original constrained KKT residual. It imports no
production evaluator or optimizer. Geometry uses MP80/MP100; the full-state
arithmetic is binary64, with an independent Decimal60 simplex projection.
Original stationarity, primal, dual, complementarity and storage gates remain
unchanged. Every saved inner stop is checked separately from final KKT.

The [actual complete6000 audit](../../strict/validation/MIS-sensing-all6000-saved-state-audit-20261017/README.md)
confirms every saved physical/KKT field and original flag. It retains5251
fully passing starts and749 failed/unverified starts. Final KKT alone passes
5959; it does not erase earlier caps. No optimization was repeated.

`run_population_resilient.py` adds only transient Windows checkpoint-write
retries. The unchanged mathematical auditor and completed source-bound
per-start results can resume after an interrupted write.

`prepare_native_population.py` preserves the original6000-start initializer,
all400/256 phase elements,25 patterns,nine targets and30/4000 budgets.
It verifies every881-draw Park-Miller jump against the full serial stream.
`run_native_population.m` uses the existing frozen v5 native scientific engine
without editing it. Missing slot n is dispatched as one diagnostic start with
the exact original before-state seed; raw dispatcher index1 and original
population identity n remain separate. Actual old native377 is reused with its
full numerical return and original source interval binding. It is not rerun.

Each actual native return is preserved as verified lossless gzip, with final
state, complete own outer/inner logs, original stopping fields and source/input
hashes. Failure slots are retained. Unexpected unclosed outputs stop resumption
for inspection rather than causing a duplicate optimizer call. This is a new
missing-population execution, not a completion claim or an upgrade of old flags.

`follow_native_population.py` holds the exact Windows producer process object
and checks each closed native final state with the same independent physical
reader. It validates the source-bound serial input mapping and each stored
inner stopping decision, while keeping original failed starts failed.

These tools apply to the supplied **corrected-paper product-PR branch**. They
do not relabel it as the printed separate-block rule or establish the missing
historical normalization, author initialization or original-figure agreement.
