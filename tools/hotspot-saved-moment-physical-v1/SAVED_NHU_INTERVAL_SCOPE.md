# Conditional interval check for one saved hotspot design

`check_saved_nhu_interval.py --result RESULT.json` examines the 13 non-hotspot
users in the saved U3, 16-feed/16-stream, RIS-enabled design. For the publicly
saved `statistical-validated18-final/U3-beta20/AO-start0.json`, all 13 lower
bounds on the full-interference QoS margin are positive; the smallest is about
`3.73579644286612e-9` in linear ratio units. All other streams are included in
each denominator. No optimization or new channel sample is performed.

This is a **conditional interval result**. JSON integers are exact integers;
JSON fractional numbers are decoded as Python binary64 and then embedded as
exact binary64 values into the intervals. The source's Boltzmann constant is
likewise embedded as its binary64 value; pi is the interval library's enclosure
of mathematical pi. Arithmetic subsequently evaluates the reconstructed ideal
real-valued geometry model, rather than emulating every binary64 rounding step
of the historical NumPy execution. The NHU feed means share a propagation
phase, which cancels from each second-moment quadratic form.

The antenna pattern uses the entire even series for
`J1(x)/(2*x)+36*J3(x)/x^3`, summed from index 0 through 160. For `0 <= x < 30`, an
explicit bound on the first omitted terms and the maximal geometric ratio
encloses the remaining tail. Other elementary operations use 65-digit
`mpmath.iv` interval arithmetic; their claimed enclosure is conditional on the
library implementation. The saved configuration fixes the feed spacing and
source ordering used by this check. Run with Python and `mpmath` available on
the import path. The tool reads only the explicitly supplied result and writes
no output file.

The result does not authenticate the historical source or physical inputs,
establish the exact behavior of the old floating-point program, or prove the
RIS phase unit-modulus equality for the serialized binary64 phases. It does not
establish convergence, MATLAB agreement, an original figure, or full-paper
acceptance. The source's all-stream interference is an explicit correction to
the K-only printed statistical formula, not a claim about the authors' runs.
