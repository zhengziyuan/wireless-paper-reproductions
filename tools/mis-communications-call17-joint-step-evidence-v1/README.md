# MIS communications: reconstructed one-joint-step diagnostic

This record concerns the saved Fig. 11 point 0, start 4869, call 17, whose
recorded historical stop was `block_line_search_exhausted_phi`. The diagnostic
explicitly retracted the saved phi once at zero step, recomputed the objective
and gradient, and made **one** current-source `block_backtracking` call from
the modified state, with the initial direction equal to minus the projected
gradient. It is not a continuation of the historical RCG trajectory or a full
optimization. The original failure remains recorded.

The reconstructed implementation accepted phi at step `0.001953125`
after 9 halvings and theta at `0.0078125` after 7. The X block had zero
projected motion and was inactive after its documented non-descent restart.
The combined candidate at coupling scale 1 was rejected: its binary64 stable
objective difference relative to the normalized start was approximately
`+8.182153207714022e-15`. Scale 0.5 passed the implementation's actual-
displacement Armijo check with stable difference approximately
`-6.581304862070182e-16` and right-hand side `-4.441094079059721e-19`.
The joint coupling safeguard and its constants are documented implementation
choices, not a claim that the paper specified them.

The normalization itself produced a binary64 stable difference of approximately
`+9.428909532249407e-16` relative to the saved starting point. The raw printed
binary64 objective before and after the accepted joint step is identical at
displayed precision; the small stable difference above is relative to the
**normalized** starting point. The projected KKT measure changed from
`1.5959628106968166e-6` at that starting point to
`2.135206707036992e-6` after the joint step; both exceed the retained `1e-6`
threshold. The original saved-point value was `1.5959605003772517e-6`.
Adding those two separately computed binary64 stable differences gives about
`+2.847604670179225e-16` relative to the saved starting point. This is a
near-machine-precision floating-point inference, not a direct high-precision
evaluation or an interval certificate; it cannot establish the exact sign.
This one step does not establish monotone KKT residual, convergence, feasibility
of every published scenario, or agreement with the paper's figures.

`recorded_joint_step_redacted.json` preserves the structured result and guard
terminal, without local paths or process identity. `recorded_joint_step_events.jsonl`
is the complete 23-event append-only journal: input, modified start/gradient,
20 actually evaluated candidate differences and the returned state. Phase,
candidate block, step and recorded displacement slopes identify which retained
decision each trial supports. The event journal is not a claim about trials the
historical process did not record or a replacement for a complete experiment.

The current engine and figure descriptions matched hashes recorded in the saved
manifest; input identities were held during this run. The historical source and
whole historical state were not independently authenticated. The saved runtime
reported NumPy 2.5.3 whereas the diagnostic used NumPy 2.3.5. The printed figures
are binary64 calculations, not interval certificates. The run naturally exited
under the single-task storage monitor after about 1.078 seconds; its reported
pre-terminal output was 41,424 bytes. Monitoring used polling, not a hard
filesystem quota. Neither a successful monitor nor this diagnostic is scientific
acceptance of the complete reproduction.
