# Fig. 5 publisher versus retained thesis vector summary

This is a narrow comparison of the final IEEE Fig. 5 artwork, DOI
10.1109/JSAC.2024.3460068, with the previously retained 96-point thesis EPS
ordinate summary. It does not establish historical simulation provenance,
parameter identity, figure generation, algorithm correctness or reproduction.
The separately documented working-archive parameter mismatch remains relevant:
[parameter scope](../cooperative-fig4-fig5-author-parameter-scope-v1/README.md).
The previous [zero-inclusive 60-triplet screen](https://github.com/zhengziyuan/wireless-paper-reproductions/blob/e016ddfd5f884cab2c2a3d29f7e33443bd516afe/tools/cooperative-fig5-all-triplets-v1/README.md)
is a separate, limited comparison against the thesis reference; it does not
rule out other saved-data mappings or producer revisions.

The figure legend in the publisher PDF was visually checked against eight
colored polylines. Their axis frame was independently read as x = 0.01–0.12
in 0.01 increments and y = 0–4.5. The tool locates that exact vector geometry,
verifies the curve colors and geometry in this PDF extraction, converts the
eight polylines to 12 labeled ordinals each, and compares their ordinates with
the retained thesis summary. One ordinal on the flat MR-TTS-NoRIS segment has
no separate polyline vertex and is linearly interpolated. It records all
96 derived publisher coordinates and interpolation flags but not the PDF,
EPS, original vector paths or thesis reference points. No raster files are
written. `pdftocairo` streams the selected PDF page into memory.

On the supplied source files the 96 absolute ordinate differences have a
maximum of about **0.00010144** and RMS of about **0.00004880**, versus the
4.5-unit vertical span. All eight corresponding series are numerically very
close, but the small differences have not been traced to a particular
quantization or conversion step. The compact retained thesis summary contains
ordinals and y values, not the thesis EPS colors or x coordinates; these
cannot be compared here. The result therefore supports visual/numerical
correspondence and does not establish byte identity or identical source data.

Python 3 and Poppler `pdftocairo` are required. Supply the publication PDF separately; it is not redistributed. The retained 96-point thesis numeric summary is included under `strict/validation/cooperative-author-working-U6-betaR1-dual-full8-20261019-v1/fig5-thesis-eps-reference.json`; the EPS source is not redistributed.

```text
python -I -S -B tools/cooperative-fig5-publisher-eps-vector-v1/compare_figure.py --paper-pdf /path/to/final.pdf --thesis-summary strict/validation/cooperative-author-working-U6-betaR1-dual-full8-20261019-v1/fig5-thesis-eps-reference.json
python -I -S -B -m unittest discover -s tools/cooperative-fig5-publisher-eps-vector-v1 -p test_compare_figure.py
```

The recorded JSON is derived evidence from the specified inputs. The PDF
geometry and color checks are intentionally strict and can reject a different
Poppler version or PDF encoding; refusal is not evidence of a scientific
contradiction. Source files and prior triplet results were not rerun or changed.
