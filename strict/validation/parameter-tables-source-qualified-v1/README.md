# Two supplied-author parameter tables: source-qualified evidence

The actual local audit read the complete supplied thesis Table4-1 and Table3-1,
after matching their inventoried chapter SHA-256 identities. It maps all36
parameter rows:16 cooperative-satellite rows and20 hotspot-satellite rows.
All34 rows with numeric configuration bindings match the canonical public
configurations, including SI conversions and the separately identified
instantaneous/statistical hotspot branches. The other two rows reference
external antenna-pattern documents and are **not** numeric pattern certificates.

Source labels, line anchors, chapter hashes and row hashes are retained; private
chapter bodies and absolute private paths are not redistributed. This is
evidence about the supplied author thesis, not an independently verified final
journal table or original unpublished simulation input.

From the repository root:

```sh
python strict/validation/parameter-tables-source-qualified-v1/audit_tables.py
```

This portable audit actually checks each canonical file's bytes, all numeric
keys/units, the byte-bound statistical runner overrides, and nine negative
parameter controls. It imports no optimizer. It replays the retained source
mapping, not the unavailable private TeX. A matching SHA is an identity check,
not by itself proof that the original source was read or a model is correct;
the separate actual local source-read receipt provides that provenance.

The hotspot table distinguishes instantaneous NHU3dB/ground-Rician0dB from
statistical LoS-labelled NHU−3dB/ground-Rician20dB. It does not overwrite the
instantaneous defaults. The cooperative interference level is a normalized
INR in dB, not a physical-watt threshold. Merely storing the HU pair-distance
interval10..20m does not validate a generated geometry; that requires the
separate actual all-pair checks. ESA/ITU pattern interpretations, historical
coordinates, Monte Carlo figures and final-publisher conformance remain
separate gates. No complete numerical figure is claimed here.
