"""Check a public output projection, without claiming a physics rerun."""
import json
import math
from pathlib import Path

path = Path(__file__).with_name("evidence.json")
e = json.loads(path.read_text(encoding="utf-8"))
assert e["schema"] == "MA20_D3G0_GRID_WINNERS_PYTHON_1000_QR_COMPONENT_V1"
assert e["scenario"]["channel_samples_per_mode"] == 1000
assert e["provenance"]["raw_input_bank_included"] is False
assert all(e["scope"][k] is False for k in (
    "matlab_cross_language_verified", "author_search_criterion_known",
    "MA_FPA_full_point_verified", "independent_precision_proven",
    "original_reference_verified", "full_figure_or_paper_pass"))
assert len(e["modes"]) == 2 and {m["mode"] for m in e["modes"]} == {"MRT", "ZF"}
for m in e["modes"]:
    rates = m["sample_sum_rates_bit_per_s_per_hz"]
    powers = m["sample_total_power_watts"]
    offdiag = m["sample_max_off_diagonal_absolute_amplitude"]
    assert all(len(x) == 1000 for x in (rates, powers, offdiag))
    assert all(math.isfinite(v) for x in (rates, powers, offdiag) for v in x)
    assert all(v >= 0 for v in rates + powers + offdiag)
    assert abs(math.fsum(rates) / 1000 - m["original_mean_sum_rate_bit_per_s_per_hz"]) < 1e-12
    assert max(abs(v - 1.0) for v in powers) < 1e-12
    assert len(m["positions_normalized_wavelength"]) == 6
    assert m["independent_qr_audit_summary"]["samples"] == 1000
print("Saved projection consistency checks passed; no physics or paper rerun.")
