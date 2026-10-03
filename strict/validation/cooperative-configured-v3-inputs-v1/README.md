# Actual M30/N48 input bytes + versioned v3 Python boundary

These are unchanged original JSON bytes used in the actual fullcase tests,
not fitted published-curve inputs. The attached boundary certificate verifies
the same frozen control-install AST and exact existing full_run call, actual
recording transparency, all final-state audits, and mocked argument/return
forwarding plus fail-closed refusal of full183. The NEW configured entry was
not itself another heavy run; that distinction is explicit in the proof.

The old frozen v3 entry is unchanged. From the repository root:

```text
python strict/cooperative-satcom/run_cooperative_v3_configured.py --configuration strict/validation/cooperative-configured-v3-inputs-v1/M30-configuration.json --full --sweep base --output NEW-M30-fullcase.json
```

Change M30 to N48 for the second configuration. Native v3 likewise accepts
this configuration path with its base-only guard. New results bind the NEW
entry/source/input bytes before and after execution, never fabricated old
source hashes. Missing/capped/failed original gates remain failures. This
input boundary performs no final-state recording; the separate actual-v4
evidence bank provides the saved-state replay. No full183 bank, native-v4,
1000 optimized-performance MC or historical figure agreement is certified.
