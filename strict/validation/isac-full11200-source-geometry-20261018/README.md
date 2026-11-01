# Full ISAC input geometry and source-qualified No-RIS evidence

This packet retains all 11,200 configured original scenario slots and 23,900
first-user ray-pair observations. It verifies a source-qualified negative
geometry finding, not successful published-figure reproduction.

Use `tools/isac-source-geometry-audit/replay_full_evidence.py` to restore all 27
parts and replay every primitive, exact certificate and saved-state field.
The archive contains 16 complete payloads, including exact binary64 ray/gain
coordinates, source metadata, all original aliases, two complete scenario files
and four full No-RIS state reports. Archive SHA256:

```text
f7b9eadb433a93b889628c67d944fe702bfed0d10d10b887ce8257aac8dd40b4
```

The cold replay checks 322,600 primitive coordinate observations and freshly
evaluates all 61,056 physical field coordinates in each of MP80 and MP100 for
the four saved No-RIS states and two source variants. Thirty-two meaningful
invalid controls are rejected. Local QA and actual source-bound process exit0
are recorded separately in this directory. A successful evidence replay keeps
`literal_first_LoS_geometry_conformance_pass=false` and
`full_six_paper_goal_or_dual_language_pass=false`.

The exact supplied R1 TeX SHA256 is
`aa71da008c68caa605ec3ed17520fcb81796561f315667eeb2f7dddf1487d2d2`.
The [public arXiv v2](https://arxiv.org/html/2512.20987v2) TeX SHA256 is
`cfff38c69713dc60bc915622c0293654124ede1f2c55132f927db4ec9d437604`.
All 17 supplied figure assets were locally rebound to the original catalog.
All 16 numerical EPS files equal the public v2 files after only CRLF-to-LF
normalization. Manuscript text differs, including the No-RIS wording at R1
line1082 and v2 line1074. The first-path LoS declarations occur at R1 line160
and v2 line161. Full paper files and EPS assets are not redistributed here.

[Publisher-deposited DOI metadata](https://api.crossref.org/works/10.1109/JSTSP.2026.3693227)
identifies the same title in IEEE JSTSP and article11520277. A blocked public
PDF response does not prove nonpublication; final publisher-text equivalence
has not been verified. Default replay checks the supplied metadata only.

The local full-input audit found all supplied first user-ray supporting lines
disjoint. That conclusion applies to these configured iid directions under
the literal LoS interpretation. It does not establish what hidden inputs the
authors used, nor authorize fitting or replacing their numerical recipe.
The frozen producer-status/support cross-table retains failed or unverified
outcomes and is separate from complete-population convergence certification.
