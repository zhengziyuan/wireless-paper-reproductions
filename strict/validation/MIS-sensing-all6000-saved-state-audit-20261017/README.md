# Actual complete saved6000-state sensing audit; original failures retained

The full saved Python Fig3 population has now been checked without another
optimizer or random generator call. All6000 original state slots are present;
each compressed source record is bound by SHA256 and rechecked after the audit.
The geometry retains400/256 phase elements,25 shifts and all nine targets.
All saved physical metrics, original constrained-KKT residual fields, KKT flags
and stored inner-stop decisions match independent calculations.

The reader independently constructs the9x400 array response using MP80 and
MP100, reconstructs every one-padded second-layer position, forms quartic echo
powers and explicitly sums all other-target interference. It then evaluates
the original relaxed Lagrangian gradient. Full-state arithmetic is binary64;
the probability-simplex projection uses Decimal60 on exact binary state and
computed gradient inputs. This is not a claim of full MP80/MP100 gradients for
all6000 states. No production model/evaluator/projector is imported.

The maximum same-state physical-metric error is2.6291e-13; the maximum original
KKT-norm difference is9.6307e-15. The response MP80/MP100 difference is below
9.77e-80. Numerical field comparisons use the explicit1e-9+1e-10*abs(reference)
policy; original physical and stationarity thresholds are unchanged.

| Scope | Actual count |
|---|---:|
| Saved starts independently inspected |6000|
| Saved physical/KKT fields and stopping decisions consistent |6000|
| All original per-start convergence/feasibility conditions pass |5251|
| Original failed or unverified starts retained |749|
| Final original constrained KKT passes |5959|
| Earlier inner cap retained despite a passing final KKT |708|
| Final KKT or feasibility still fails |41|

The distinction matters: a final stationary state does not certify that every
earlier4000-budget inner problem reached its own required accuracy. The749
old failures are not changed. The source's full30-outer/4000-inner execution
and the supplied corrected product-PR branch remain explicitly scoped; no
global optimum or whole-population convergence is claimed.

The archive includes the complete actual6000-record independent audit, original
manifest/execution summary, source hashes and every old pass/failure flag. It
also includes six actual Python final-state witnesses with all outer stop
headers:1,2,369,377,405,851. They cover an ordinary pass, an earlier cap with a
passing final state, terminal stationarity failure, the previously checked377,
terminal feasibility failure and the saved best feasible state. The original
inner iteration logs remain in the local raw archive; the compact views retain
their raw source hashes and every final numerical value.

Three complete actual native returns are additionally included: the first two
new missing-population starts and the existing source-bound377 receipt. The
new two runs pass their own original gates and independent saved-state physics.
Old377 is reused, not recomputed. For the new original6000 native schedule,
5999 optimizer slots are missing; each receives the exact original serial RNG
before-state. All6000 jumps are checked against the full881-draw-per-start
stream. The unchanged native diagnostic dispatcher reports local index1;
separate receipts retain each original population identity and initialization.
The original native scientific source bytes are unchanged. Completion,
convergence and whole-population language/reference agreement remain pending.
The seed and numerical safeguards remain disclosed reconstruction controls;
none is claimed recovered from the author's original execution code.

The public replay verifies every archive byte and all6000 audit-report slots,
then independently recomputes the **nine included actual final states**:

```powershell
python tools/sensing-saved-replay/replay_evidence.py --packet strict/validation/MIS-sensing-all6000-saved-state-audit-20261017 --output-dir strict/outputs/sensing-saved-witnesses
```

That command does not numerically replay6000 unavailable raw states. To perform
that full replay, provide the original local raw bank containing its manifest,
full-result JSON and all6000 compressed start records:

```powershell
python tools/sensing-saved-replay/run_population_resilient.py --bank PATH_TO_ORIGINAL_COMPLETE_V5_BANK --output-dir NEW_AUDIT_DIRECTORY
```

The reader requires NumPy and mpmath. Per-start audits are durable and reused
only with identical source/input/runtime bindings. A transient Windows atomic
write interruption was recovered by reusing the first600 completed audits;
only checkpoint I/O retry behavior changed. The mathematical reader stayed
unchanged. The complete native/Python raw bank is not included in this compact
public packet; the complete audit report and nine numerical witnesses are.

The literal inverse-watt, single-PRI reference normalization remains a declared
reconstruction. The author's unreported reference unit/processing convention
and historical figure agreement are unresolved. Full6000 convergence, all
historical inner states and complete paper reproduction remain uncertified.
The archive SHA256 is
`6c65955bd84a02ca996d84658aad4bfec28c18b9a452f53027cbe941056a29d1`.
