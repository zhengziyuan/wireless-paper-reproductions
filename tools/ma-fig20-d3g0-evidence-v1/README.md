# MA Fig. 20: saved-winner MATLAB/Python comparison

This is a comparison at the same two saved Python-selected positions for one
Fig. 20 scenario (point D3, realization 0). The computation reused all 1,000
saved fading samples per mode. It does not perform an independent MATLAB
search and does not verify a complete figure or paper. The historical sample
contents were not freshly authenticated.

| Mode | Grid indices (zero based) | MATLAB mean sum rate | Max. per-sample rate difference | Max. power difference | Max. off-diagonal amplitude difference |
| --- | --- | ---: | ---: | ---: | ---: |
| MRT | 1, 2, 4, 5, 7, 8 | 11.069791030425774 | 1.4210854715202004e-14 | 1.1102230246251565e-15 | 2.710505431213761e-20 |
| ZF | 1, 2, 5, 6, 7, 8 | 27.741546262008846 | 2.1316282072803006e-14 | 5.551115123125783e-16 | 3.2204082560447825e-20 |

The coordinates and grid indices match between the saved outputs. All compared
values are finite; the MATLAB rates are nonnegative. The original MATLAB task
exited naturally, used R2025b, took about 75.719 s and had a monitored task-tree
peak of 865,073 bytes. Polling is not a hard filesystem quota. Small floating
point deviations do not by themselves establish feasibility or infeasibility.

`python_winner_projection.json` contains only the Python output fields needed
for this comparison, not the 1,000-sample fading bank. `matlab-result.json` is
the retained MATLAB output. Neither file authenticates the historical inputs.
The comparison script is portable Python 3 and only compares these two saved
outputs; it does not run MATLAB, recreate the input samples, or execute the
search or original experiment. From the repository root:

```text
python -I -S -B tools/ma-fig20-d3g0-evidence-v1/compare_saved_outputs.py
```
