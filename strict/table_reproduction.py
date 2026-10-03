"""Parameter-table metadata route; no model, sampler or optimizer imports.

The frozen packet retains actual supplied-author source-read evidence.
Portable checks verify current canonical parameters, not new private TeX access
or external antenna-pattern/full-publisher conformance.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
PACKET = HERE / "validation/parameter-tables-source-qualified-v1"
EXPECTED_MANIFEST = "6603f0fa05cbcc92e8ef617b8123cc0a083d9972c5d5d27746cd856b2fb464a8"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_packet():
    manifest_path = PACKET / "freeze-manifest.json"
    if sha(manifest_path) != EXPECTED_MANIFEST:
        raise ValueError("Changed parameter-evidence manifest; preserve the original proof")
    for relative, expected in load(manifest_path)["files_sha256"].items():
        path = (PACKET / relative).resolve()
        path.relative_to(PACKET.resolve())
        if sha(path) != expected:
            raise ValueError("Missing or changed frozen table evidence: " + relative)
    contract = load(PACKET / "canonical-parameter-contract-v1.json")
    for relative, expected in contract["canonical_file_sha256"].items():
        if sha(HERE.parent / relative) != expected:
            raise ValueError("Canonical parameter source/configuration changed: " + relative)
    return contract


def table_plan(paper, table):
    inventory = load(HERE / "figure-catalog" / (paper + ".json"))
    item = next((entry for entry in inventory["tables"] if entry["table"] == table), None)
    if item is None or paper not in ("cooperative-satcom", "hotspot-satcom"):
        raise ValueError("Table is not in the supplied author-source inventory")
    contract = verify_packet()
    actual = load(PACKET / "actual-source-table-read-and-mapping-v1.json")
    evidence = next(entry for entry in actual["tables"] if entry["paper"] == paper)
    source = evidence["source"]
    if (source["source_sha256"] != inventory["source_sha256"]
            or source["source_sha256"] != contract["author_source_hashes"][paper]
            or source["caption_read_from_actual_UTF8_source"] != item["caption_tex"]):
        raise ValueError("Parameter evidence differs from its supplied-source caption/identity")
    rows = evidence["parameter_rows"]
    return {"paper_id": paper, "table": table, "artifact_kind": "parameter_table_source_metadata",
            "original_caption": item["caption_tex"], "source": source,
            "parameter_rows": rows, "parameter_row_count": len(rows),
            "numeric_parameter_row_count": sum(bool(row["bindings"]) for row in rows),
            "unverified_external_pattern_reference_row_count": sum(not row["bindings"] for row in rows),
            "canonical_configuration_and_source_sha256": contract["canonical_file_sha256"],
            "source_read_receipt_sha256": sha(PACKET / "actual-source-table-read-and-mapping-v1.json"),
            "portable_auditor": "strict/validation/parameter-tables-source-qualified-v1/audit_tables.py",
            "runnable": True, "execution_scope": "stdlib canonical-parameter replay of both supplied-author tables; no optimizer",
            "execution_engine": "python_metadata_audit_not_MATLAB_simulation",
            "executed": False, "automatic_downsizing": False,
            "table_reproduction_verified": False, "external_pattern_rows_certified": False,
            "final_publisher_table_equivalence_verified": False, "full_reproduction_passed": False,
            "actual_all_pairwise_realized_geometry_certified": False}


def execute_table(specification, language, output):
    if language != "python":
        raise ValueError("This table route is a source/configuration audit, not a MATLAB simulation. Use --language python for the metadata audit.")
    current = table_plan(specification["paper_id"], specification["table"])
    if current != specification:
        raise ValueError("Changed parameter-table plan; no mixed-source audit")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    receipt = output / "actual-both-table-canonical-parameter-replay.json"
    if receipt.exists():
        raise ValueError("Preserve earlier receipts; choose a fresh table-audit output directory")
    subprocess.run([sys.executable, str(PACKET / "audit_tables.py"), "--output", str(receipt)], check=True)
    return receipt
