"""Inventory author figures and recover *reference* polylines, never simulations.

EPS extraction is deliberately limited to the straight-line paths exported by
MATLAB's Apache XML Graphics exporter. It does not execute PostScript, infer
unknown axes, synthesize missing samples, or turn a reference into a reproduction.
The operator supplies and verifies the axis calibration from the original plot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def balanced(text, start):
    if start >= len(text) or text[start] != "{":
        raise ValueError("Expected balanced TeX argument")
    depth = 0
    for index in range(start, len(text)):
        if index and text[index - 1] == "\\":
            continue
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if not depth:
                return text[start + 1:index], index + 1
    raise ValueError("Unclosed TeX argument")


def active_tex(text):
    text = re.sub(r"(?<!\\)%[^\n]*", "", text)
    text = re.sub(r"\\begin\{comment\}.*?\\end\{comment\}", "", text, flags=re.S)
    # This utility is an inventory, not a general TeX interpreter. Refuse rather
    # than incorrectly number figures inside unsupported conditional programs.
    if "\\iffalse" in text:
        text = re.sub(r"\\iffalse.*?\\fi\b", "", text, flags=re.S)
    return text


def catalog(paper, source):
    source = Path(source)
    text = active_tex(source.read_text(encoding="utf-8-sig"))
    figures = []
    unnumbered = 0
    for match in re.finditer(
            r"\\begin\{(figure\*?)\}(.*?)\\end\{\1\}", text, re.S):
        block = match.group(2)
        # IEEE source often uses uncaptioned figure floats for long equations,
        # or wraps an algorithm float in a figure. Neither advances the figure
        # counter. Algorithm captions belong to the algorithm counter.
        caption_scope = re.sub(r"\\begin\{algorithm\*?\}.*?\\end\{algorithm\*?\}", "", block, flags=re.S)
        caption_match = re.search(r"\\caption(?:\[[^\]]*\])?\s*(?=\{)", caption_scope)
        if not caption_match:
            unnumbered += 1
            continue
        caption = balanced(caption_scope, caption_match.end())[0]
        labels = re.findall(r"\\label\{([^}]+)\}", block)
        assets = []
        for asset in re.findall(r"\\includegraphics\*?(?:\[[^\]]*\])?\{([^}]+)\}", block):
            relative = Path(asset)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Figure asset must be a manuscript-relative name")
            path = source.parent / relative
            assets.append({"file": relative.as_posix(), "available": path.is_file(),
                           "sha256": sha(path) if path.is_file() else None})
        figures.append({"figure": len(figures) + 1, "labels": labels, "caption_tex": caption,
                        "assets": assets, "simulation_reproduction_verified": False,
                        "reference_curve_agreement_verified": False})
    if not figures:
        raise ValueError("No active figure environments found")
    tables = []
    for match in re.finditer(r"\\begin\{(table\*?)\}(.*?)\\end\{\1\}", text, re.S):
        block = match.group(2)
        caption_match = re.search(r"\\caption(?:\[[^\]]*\])?\s*(?=\{)", block)
        if caption_match:
            tables.append({"table":len(tables)+1, "caption_tex":balanced(block, caption_match.end())[0],
                           "labels":re.findall(r"\\label\{([^}]+)\}", block),
                           "content_classification":"Needs explicit parameter/complexity/numerical/measurement classification",
                           "table_reproduction_verified":False})
    return {"paper_id": paper, "source_file": source.name, "source_sha256": sha(source),
            "scope": "Author-source figure inventory; NOT simulation results",
            "figure_count": len(figures), "unnumbered_equation_or_algorithm_floats": unnumbered, "figures": figures,
            "table_count":len(tables), "tables":tables,
            "numbering_note": "Active captioned figure order, excluding nested algorithm captions; verify chapter/publication numbering separately",
            "full_reproduction_passed": False}


def eps_paths(text, rectangle):
    if "Apache XML Graphics" not in text:
        raise ValueError("Unsupported EPS exporter; no guessed extraction")
    body = text.split("%%EndProlog", 1)[-1]
    left, top, right, bottom = rectangle
    if not left < right or not top < bottom:
        raise ValueError("Rectangle is left, top, right, bottom in exported path coordinates")
    paths = []
    # Only simple, unclosed, stroked, identity-origin line paths are eligible.
    # Marker shapes, clipping polygons, image streams and legend samples fail
    # these structural/domain checks; unrecognized paths are not approximated.
    for block in re.findall(r"GS\s+(.*?)\s+GR", body, re.S):
        color = re.search(rf"({NUMBER})\s+({NUMBER})\s+({NUMBER})\s+RC", block)
        transform = re.search(r"\[([^\]]+)\]\s+CT", block)
        path_match = re.search(r"(?:^|\n)N\s*\n(.*?)\nS(?:\s|$)", block, re.S)
        if not color or not transform or not path_match:
            continue
        matrix = [float(x) for x in transform.group(1).split()]
        # Calibration uses the original path-coordinate frame, not physical
        # page pixels. A common exporter scale (e.g.0.75) cancels against the
        # axis rectangle, but translation/shear/nonuniform scaling cannot be
        # silently mixed. Every recovered curve must share this exact frame.
        if len(matrix) != 6 or matrix[0] <= 0 or abs(matrix[3]) != matrix[0] or matrix[1:3] != [0,0] or matrix[4:] != [0,0]:
            continue
        content = path_match.group(1).strip()
        lines = content.splitlines()
        coordinates = []
        for index, line in enumerate(lines):
            point = re.fullmatch(rf"\s*({NUMBER})\s+({NUMBER})\s+({'M' if index == 0 else 'L'})\s*", line)
            if not point:
                coordinates = []
                break
            coordinates.append([float(point[1]), float(point[2])])
        if len(coordinates) < 3:
            continue
        xs = [p[0] for p in coordinates]
        if not all(xs[i] < xs[i + 1] for i in range(len(xs) - 1)):
            continue
        if not all(left - .02 <= x <= right + .02 and top - .02 <= y <= bottom + .02
                   for x, y in coordinates):
            continue
        paths.append({"rgb": [float(x) for x in color.groups()], "path_coordinate_transform":matrix,
                      "path_coordinates": coordinates})
    if not paths:
        raise ValueError("No supported in-domain curve polylines; require another extraction method")
    if any(path["path_coordinate_transform"] != paths[0]["path_coordinate_transform"] for path in paths):
        raise ValueError("Mixed curve coordinate frames; axis calibration cannot be assumed common")
    return paths


def extract(source, rectangle, x_range, y_range, labels, paper, figure, axes_verified):
    if not axes_verified:
        raise ValueError("Explicit visual axis/scale verification is required")
    paths = eps_paths(Path(source).read_text(encoding="latin-1"), rectangle)
    if len(labels) != len(paths) or len(set(labels)) != len(labels):
        raise ValueError(f"Need exactly {len(paths)} unique curve labels in path order; found {len(labels)}")
    left, top, right, bottom = rectangle
    xmin, xmax = x_range
    ymin, ymax = y_range
    if not xmin < xmax or not ymin < ymax:
        raise ValueError("Only strictly increasing linear/display-coordinate axes are supported")
    curves = []
    for label, path in zip(labels, paths):
        xy = path.pop("path_coordinates")
        curves.append(dict(path, label=label,
                           x=[xmin + (p[0] - left) / (right - left) * (xmax - xmin) for p in xy],
                           y=[ymax - (p[1] - top) / (bottom - top) * (ymax - ymin) for p in xy]))
    return {"paper_id": paper, "figure": figure, "source_file": Path(source).name,
            "source_sha256": sha(source), "data_kind": "original_plot_vector_reference_NOT_simulation",
            "axis_calibration": {"rectangle": rectangle, "x_range": x_range, "y_range": y_range,
                                 "axes_visually_verified": True,
                                 "scale": "linear in displayed coordinates; dB labels stay dB"},
            "curves": curves, "precision_note": "Limited by decimal coordinates in the author's EPS, not raw simulation precision",
            "simulation_reproduction_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    inventory = sub.add_parser("catalog")
    inventory.add_argument("--source", type=Path, required=True)
    inventory.add_argument("--paper", required=True)
    inventory.add_argument("--output", type=Path, required=True)
    curve = sub.add_parser("eps-reference")
    curve.add_argument("--source", type=Path, required=True)
    curve.add_argument("--paper", required=True)
    curve.add_argument("--figure", type=int, required=True)
    curve.add_argument("--rectangle", type=float, nargs=4, required=True)
    curve.add_argument("--x-range", type=float, nargs=2, required=True)
    curve.add_argument("--y-range", type=float, nargs=2, required=True)
    curve.add_argument("--labels", nargs="+", required=True)
    curve.add_argument("--axes-verified", action="store_true")
    curve.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = catalog(args.paper, args.source) if args.operation == "catalog" else extract(
        args.source, args.rectangle, args.x_range, args.y_range, args.labels,
        args.paper, args.figure, args.axes_verified)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"paper": args.paper, "operation": args.operation,
                      "count": result.get("figure_count", len(result.get("curves", []))),
                      "full_reproduction_passed": False}))


if __name__ == "__main__":
    main()
