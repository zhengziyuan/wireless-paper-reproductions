# Conditional QoS intervals for 18 saved designs

`conditional_nhu_17_events_v1.ndjson` preserves the real 17-case event stream.
The separately computed U3/beta20 result is represented by the first event, and
was not rerun. There are 17 result events, zero failed cases and 212 NHU
intervals; all recorded lower endpoints are positive. The smallest lower
endpoint is approximately `1.0144056598e-11`, for U2/beta20, NHU 13 (one-based
within that case). The earlier U3/beta20 receipt records 13 more positive
intervals, for 225 NHU values across 18 cases in all. The prior event records
the prior receipt's summary, not its individual 13 intervals.

The interval calculations use the saved binary64 beam values, ideal-real
reconstructed geometry and all-stream interference. Their enclosure assumes
`mpmath.iv` elementary operations are correct; the antenna pattern series
uses an explicit tail bound. The saved input projections are in
`conditional_nhu_17_input_projections_v1.json`, with their own scope notes.
Those projections and event reports do not authenticate the historical
runtime or inputs. They do not establish exact phase unit modulus, other
constraints, convergence, MATLAB agreement, the original figures or complete
paper reproduction.

The actual single worker exited normally after about 16 seconds; its terminal
reported no resource limit and approximately 54.7 KiB in its attempt directory
before the terminal record. It retained a 101 GiB early-free threshold and a
900 KiB output early-stop threshold. One-second polling is not a hard file
system quota. The event stream is evidence of this numerical check, not a claim
that every original published scenario or scientific acceptance gate passed.
