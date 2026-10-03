"""Negative coverage/reference tests: good-looking plots must not hide missing work."""
import json
from pathlib import Path
import tempfile
import unittest
from figure_reference import catalog, eps_paths, extract
from figure_validation import compare
from render_figure import render
from reproduce import PAPERS, plan


class FigureTests(unittest.TestCase):
    def test_caption_numbering(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)/"paper.tex"
            source.write_text(r"""% \begin{figure}\caption{hidden}\end{figure}
\begin{figure}\begin{algorithm}\caption{Algorithm}\end{algorithm}\end{figure}
\begin{figure}long equation\end{figure}
\begin{figure*}\caption[short]{Text {nested} and \{escaped\}}\label{one}\end{figure*}
\iffalse\begin{figure}\caption{hidden}\end{figure}\fi
\begin{figure}\caption{Two}\end{figure}""", encoding="utf-8")
            result = catalog("test", source)
            self.assertEqual(result["figure_count"], 2)
            self.assertEqual(result["unnumbered_equation_or_algorithm_floats"], 2)
            self.assertIn("{nested}", result["figures"][0]["caption_tex"])
            self.assertFalse(result["full_reproduction_passed"])

    def test_reference_calibration_and_labels(self):
        content = "Apache XML Graphics\n%%EndProlog\nGS\n1 0 0 RC\n[1 0 0 -1 0 0] CT\nN\n0 0 M\n5 5 L\n10 10 L\nS\nGR"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"source.eps"
            path.write_text(content)
            result = extract(path, [0,0,10,10], [15,30], [0,30], ["MIS"], "test", 15, True)
            self.assertEqual(result["curves"][0]["x"], [15,22.5,30])
            self.assertEqual(result["curves"][0]["y"], [30,15,0])
            with self.assertRaises(ValueError):
                extract(path, [0,0,10,10], [15,30], [0,30], ["MIS"], "test", 15, False)
            with self.assertRaises(ValueError):
                extract(path, [0,0,10,10], [15,30], [0,30], ["MIS","extra"], "test", 15, True)
        with self.assertRaises(ValueError):
            eps_paths(content.replace("Apache XML Graphics", "unknown"), [0,0,10,10])
        with self.assertRaises(ValueError):
            eps_paths(content.replace("[1 0 0 -1 0 0]", "[1 0 0 -1 50 0]"), [0,0,10,10])

    def documents(self):
        curve = {"label":"a", "x":[1,2,3], "y":[2,3,4]}
        sim = {"paper_id":"test", "figure":2, "data_kind":"independent_simulation_curves", "full_execution_verified":True, "curves":[curve]}
        ref = dict(sim, data_kind="original_plot_vector_reference_NOT_simulation")
        return sim, ref

    def test_explicit_comparison_criterion(self):
        sim, ref = self.documents()
        self.assertFalse(compare(sim,ref)["full_execution_and_reference_agreement"])
        self.assertTrue(compare(sim,ref,.01)["full_execution_and_reference_agreement"])
        self.assertFalse(compare(sim,ref,.01)["published_figure_reproduction_certified"])

    def test_partial_bank_missing_grid_and_curve(self):
        sim, ref = self.documents()
        sim["full_execution_verified"] = False
        self.assertFalse(compare(sim,ref,0)["full_execution_and_reference_agreement"])
        sim["curves"] = [{"label":"a", "x":[1,3], "y":[2,4]}]
        self.assertFalse(compare(sim,ref,0)["all_curves_and_grids_complete"])
        sim["curves"][0]["label"] = "wrong"
        self.assertEqual(compare(sim,ref,0)["missing_curves"], ["a"])

    def test_reference_cannot_masquerade_as_simulation(self):
        sim, ref = self.documents()
        with self.assertRaises(ValueError):
            compare(ref,ref,0)
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)/"reference.json"
            source.write_text(json.dumps(ref))
            with self.assertRaises(ValueError):
                render(source, Path(tmp)/"plots")

    def test_all_author_figure_plans_are_explicit(self):
        total = 0
        for paper in PAPERS:
            inventory = json.loads((Path(__file__).parent/"figure-catalog"/(paper+".json")).read_text())
            for figure in inventory["figures"]:
                value = plan(paper, figure["figure"])
                self.assertFalse(value["executed"])
                self.assertFalse(value["full_reproduction_passed"])
                self.assertFalse(value["automatic_downsizing"])
                self.assertIsInstance(value["runnable"], bool)
                total += 1
        self.assertEqual(total, 85)


if __name__ == "__main__":
    unittest.main()
