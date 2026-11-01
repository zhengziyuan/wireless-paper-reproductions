"""Explicit SI power/reference/noise contract for the published quartic metric.

An effective gain is not evidence of a particular PRI count. Reference ratios
already defined using processed noise must not receive that gain twice.
"""
from __future__ import annotations
import math


def normalization_contract(settings: dict, power_dbm: float | None = None) -> dict:
    """Return the exact, auditable coefficients used by Eq. (9).

    Internally sample-noise power is normalized to 1 W. Consequently the
    stored echo_beta_squared equals the inverse-watt reference ratio; it is
    already a POWER coefficient and must not be squared a second time.
    """
    required=("reference_echo_db", "reference_echo_unit",
              "reference_echo_noise_domain", "effective_reference_gain_factor")
    missing=[name for name in required if name not in settings]
    if missing:
        raise ValueError("Explicit sensing normalization fields required: "+", ".join(missing))
    unit=settings["reference_echo_unit"]
    if unit not in ("inverse_watt", "inverse_milliwatt"):
        raise ValueError("reference_echo_unit must be inverse_watt or inverse_milliwatt")
    domain=settings["reference_echo_noise_domain"]
    if domain not in ("raw_per_PRI", "processed"):
        raise ValueError("reference_echo_noise_domain must be raw_per_PRI or processed")
    gain=float(settings["effective_reference_gain_factor"])
    if not math.isfinite(gain) or gain <= 0:
        raise ValueError("effective_reference_gain_factor must be finite and positive")
    if domain == "processed" and gain != 1.:
        raise ValueError("Processed reference already includes its processing gain; double counting rejected")
    echo_db=float(settings["reference_echo_db"])
    pd=float(settings["power_dbm"] if power_dbm is None else power_dbm)
    if not math.isfinite(echo_db) or not math.isfinite(pd):
        raise ValueError("Reference level and power_dbm must be finite")
    si_db=echo_db+(30. if unit == "inverse_milliwatt" else 0.)
    try:
        ratio=10.**(si_db/10.)
        power_watt=10.**((pd-30.)/10.)
    except OverflowError as error:
        raise ValueError("SI reference ratio and power exceed finite arithmetic") from error
    if not math.isfinite(ratio) or ratio <= 0 or not math.isfinite(power_watt) or power_watt <= 0:
        raise ValueError("SI reference ratio and power must remain finite and positive")
    effective_ratio=ratio*gain
    effective_power=power_watt*gain
    if not math.isfinite(effective_ratio) or effective_ratio <= 0 or not math.isfinite(effective_power) or effective_power <= 0:
        raise ValueError("Effective products must remain finite and positive")
    noise_over_power=1./effective_power
    if not math.isfinite(noise_over_power) or noise_over_power <= 0:
        raise ValueError("Effective noise coefficient must remain finite and positive")
    return {
        "physical_power_dbm":pd, "physical_power_watt":power_watt,
        "input_reference_echo_db":echo_db, "input_reference_echo_unit":unit,
        "reference_echo_db_per_watt":si_db,
        "reference_echo_ratio_per_watt":ratio,
        "reference_echo_noise_domain":domain,
        "effective_reference_gain_factor":gain,
        "effective_reference_ratio_per_watt":effective_ratio,
        "echo_beta_squared":ratio,
        "noise_over_power":noise_over_power,
        "normalization_status":settings.get("normalization_status", "explicit_contract_not_source_parameter_certification"),
        "physical_processing_origin_verified":False,
    }


def matched_filter_effective_ratio(raw_ratio_per_watt: float, pri_count: int,
                                   bs_antennas: int = 1) -> float:
    """Unit-norm BS filters and coherent-PRI echo/incoherent target powers.

    This is a mathematical equivalence, not a default for unreported Tp.
    Each PRI has unit-modulus waveform symbols; unresolved echoes have the
    same correlation Tp, while processed AWGN variance is Tp*sigma_sample².
    """
    if isinstance(pri_count,bool) or int(pri_count) != pri_count or pri_count <= 0:
        raise ValueError("pri_count must be a positive integer")
    if isinstance(bs_antennas,bool) or int(bs_antennas) != bs_antennas or bs_antennas <= 0:
        raise ValueError("bs_antennas must be a positive integer")
    raw=float(raw_ratio_per_watt)
    if not math.isfinite(raw) or raw <= 0:
        raise ValueError("raw_ratio_per_watt must be finite and positive")
    return raw*pri_count*bs_antennas**2
