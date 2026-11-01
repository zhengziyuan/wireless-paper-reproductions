"""Fixed, explicitly oriented UPA spatial response; no propagation factor.

Ordering and default sign match the conjugate-transposed row in the supplied
initializer. This module does not change any original input or channel.
"""

import operator

import numpy as np


def _unit(vector, name):
    a = np.asarray(vector, dtype=float)
    if a.shape != (3,) or not np.isfinite(a).all():
        raise ValueError(f"{name} must be a finite three-vector")
    norm = np.linalg.norm(a)
    if not np.isfinite(norm) or norm == 0:
        raise ValueError(f"{name} must have finite nonzero norm")
    return a / norm


def response(boresight, first_axis, direction, n_rows, n_columns,
             spacing_over_wavelength, *, handedness=1, phase_sign=-1):
    """Return the flattened unit-modulus UPA response, n_columns fastest.

    second axis = handedness * cross(unit boresight, unit first axis).
    Each axis is fixed for the *array*, not selected independently per user.
    phase_sign=-1 matches the source's conjugate transpose; +1 gives its
    unconjugated row convention. No time-of-flight/common phase is included.
    Direction may be along either normal: the response is then all ones.
    """
    b = _unit(boresight, "boresight")
    a = _unit(first_axis, "first_axis")
    d = _unit(direction, "direction")
    if abs(float(np.dot(b, a))) > 1e-10:
        raise ValueError("first_axis must be perpendicular to boresight")
    # Correct only insignificant floating-point nonorthogonality; do not
    # silently repair an inconsistent array frame.
    a = _unit(a - np.dot(a, b) * b, "first_axis")
    if handedness not in (-1, 1) or phase_sign not in (-1, 1):
        raise ValueError("handedness and phase_sign must be +1 or -1")
    try:
        rows, columns = operator.index(n_rows), operator.index(n_columns)
    except TypeError as exc:
        raise ValueError("array dimensions must be positive integers") from exc
    if isinstance(n_rows, (bool, np.bool_)) or isinstance(n_columns, (bool, np.bool_)) or rows < 1 or columns < 1:
        raise ValueError("array dimensions must be positive integers")
    spacing = float(spacing_over_wavelength)
    if not np.isfinite(spacing) or spacing <= 0:
        raise ValueError("spacing_over_wavelength must be finite and positive")
    second = handedness * np.cross(b, a)
    first_projection, second_projection = np.dot(a, d), np.dot(second, d)
    phase = (np.arange(rows)[:, None] * first_projection +
             np.arange(columns)[None, :] * second_projection)
    return np.exp(phase_sign * 2j * np.pi * spacing * phase).reshape(-1)
