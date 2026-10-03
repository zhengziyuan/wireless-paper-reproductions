"""Exact SI arithmetic and literal supplied-source footnote consistency audit.

No simulation, movement model, optimizer or historical figure is modified.
The only issue proved is the footnote's half-wavelength/unit inconsistency.
"""
from __future__ import annotations
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re


def entry(value):
    return {"numerator": value.numerator, "denominator": value.denominator,
            "decimal_approximation": float(value)}


def arithmetic():
    speed_of_light = Fraction(299792458)
    frequency = Fraction(12_000_000_000)
    wavelength_m = speed_of_light/frequency
    half_wavelength_mm = wavelength_m*1000/2
    literal_displacement_mm = Fraction(25)
    antennas, motor_W = 6, Fraction(8)
    motor_mm_per_ms = Fraction(94, 100)
    transmit_W, frame_seconds = Fraction(1, 10), Fraction(3, 10)
    # Two orthogonal per-antenna displacements, milliseconds converted to s.
    actual_halfwave_J = antennas*motor_W*(2*half_wavelength_mm/motor_mm_per_ms)/1000
    literal_25mm_J = antennas*motor_W*(2*literal_displacement_mm/motor_mm_per_ms)/1000
    transmit_J = transmit_W*frame_seconds
    approximate_12_5mm_J = antennas*motor_W*(2*Fraction(25,2)/motor_mm_per_ms)/1000
    checks = {
        "12_GHz_half_wavelength_not_25_mm": half_wavelength_mm != literal_displacement_mm,
        "25_mm_is_approximately_one_wavelength_not_half": abs(literal_displacement_mm-wavelength_m*1000) < Fraction(1, 10),
        "energy_1_28_J_matches_physical_half_wavelength_at_two_decimal_places": round(float(actual_halfwave_J), 2) == 1.28,
        "literal_25_mm_energy_is_about_2_55_J_not_1_28": round(float(literal_25mm_J), 2) == 2.55,
        "radio_frame_energy_is_0_03_J": transmit_J == Fraction(3,100),
        "ratio_about42_requires_half_wavelength_not_literal25mm": 42 < actual_halfwave_J/transmit_J < 43,
        "literal25mm_ratio_is_about85": 85 < literal_25mm_J/transmit_J < 86,
    }
    assert all(checks.values())
    return {"exact_SI_c_m_per_s": 299792458, "frequency_Hz": 12_000_000_000,
            "wavelength_m": entry(wavelength_m), "half_wavelength_mm": entry(half_wavelength_mm),
            "source_literal_displacement_mm": entry(literal_displacement_mm),
            "per_antenna_motor_power_W": entry(motor_W), "antennas": antennas,
            "motor_speed_mm_per_ms": entry(motor_mm_per_ms), "two_axes_per_antenna": True,
            "energy_for_physical_half_wavelength_J": entry(actual_halfwave_J),
            "energy_for_rounded_12_5_mm_J": entry(approximate_12_5mm_J),
            "energy_if_literal25_mm_is_used_J": entry(literal_25mm_J),
            "transmit_energy_J": entry(transmit_J),
            "physical_half_wavelength_move_to_radio_energy_ratio": entry(actual_halfwave_J/transmit_J),
            "literal25mm_move_to_radio_energy_ratio": entry(literal_25mm_J/transmit_J),
            "checks": checks}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args=parser.parse_args()
    assert not args.output.exists(), "Preserve existing receipts."
    result={"scope": "exact_fraction_SI_unit_audit_of_MA_energy_footnote_not_figure_reproduction",
            "arithmetic": arithmetic(), "audit_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "supplied_author_source_literally_verified": False,
            "final_IEEE_publisher_version_error_confirmed": False,
            "simulation_parameters_or_results_modified": False,
            "claimed_explanation_for_Fig3_or_Fig4_discrepancy": False,
            "full_reproduction_pass": False}
    if args.source:
        raw=args.source.read_bytes()
        text=raw.decode("utf-8-sig")
        matched=[(i+1,line) for i,line in enumerate(text.splitlines())
                 if "E_n=P_x" in line and "12 GHz" in line]
        assert len(matched)==1
        line_number,line=matched[0]
        assert re.search(r"\\lambda/2\s*=\s*25",line)
        assert "1.28" in line and "42 times higher" in line and "0.03" in line
        assert "300" in line and "0.94" in line and "8\\," in line and "N=6" in line
        assert hashlib.sha256(args.source.read_bytes()).hexdigest()==hashlib.sha256(raw).hexdigest()
        result.update(supplied_author_source_literally_verified=True,
                      supplied_author_source_filename=args.source.name,
                      supplied_author_source_sha256=hashlib.sha256(raw).hexdigest(),
                      source_footnote_line=line_number,
                      source_before_after_unchanged=True,
                      source_units_identified_from_same_footnote=True)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(result),flush=True)


if __name__=="__main__":main()
