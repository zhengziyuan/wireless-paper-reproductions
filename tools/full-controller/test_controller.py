"""STD metadata/toy host controls only; no paper computation or bank decoding."""
import ast
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import run_all_full as driver
import native_dispatch as native

REPO = driver.repo_root(sys.argv.pop() if len(sys.argv) > 1 and not sys.argv[-1].startswith("-") else None)


class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = driver.make_plan(REPO, Path(tempfile.gettempdir()) / "never-executed-all-paper-tests", sys.executable)

    def test_complete_73_2_150_and_12_exclusions(self):
        self.assertEqual((len(self.plan["artifacts"]), len(self.plan["tasks"]), len(self.plan["excluded_nonnumerical_figures"])), (75, 150, 12))
        self.assertEqual(sum(a["kind"] == "figure" for a in self.plan["artifacts"]), 73)
        self.assertFalse(self.plan["execution_requested"])
        self.assertFalse(self.plan["scientific_reproduction_certified"])

    def test_drop_duplicate_and_artifact_identity_rejected(self):
        for mutate in (lambda p: p["tasks"].pop(), lambda p: p["tasks"].__setitem__(0, p["tasks"][1]), lambda p: p["artifacts"].pop()):
            value = copy.deepcopy(self.plan)
            mutate(value)
            with self.assertRaises(ValueError):
                driver.validate_plan(value)

    def test_convergence_reuses_two_real_language_fig3_paths(self):
        for task in self.plan["tasks"]:
            if task["id"].startswith("mis-sensing-figure05") or task["id"].startswith("mis-sensing-figure06"):
                self.assertEqual(task["dependency"], driver.task_id("mis-sensing", "figure", 3, task["language"]))
                self.assertEqual(task["source_result"], str(Path(self.plan["output_dir"]) / task["dependency"] / ("bank/full-result-python.json" if task["language"] == "python" else "fig3-matlab.json")))
                value = copy.deepcopy(self.plan)
                next(t for t in value["tasks"] if t["id"] == task["id"])["dependency"] = "wrong-bank"
                with self.assertRaises(ValueError):
                    driver.validate_plan(value)

    def test_special_7000_not_generic5_and_corrected_ma(self):
        artifact = next(a for a in self.plan["artifacts"] if (a["paper_id"], a["number"]) == ("hotspot-satcom", 9))
        spec = artifact["strict_specification"]
        self.assertEqual(spec["effective_execution_grid"], list(range(4000, 28001, 4000)))
        self.assertEqual(spec["full_required_channel_realizations"], 7000)
        self.assertEqual(spec["effective_execution_parameter_overrides"], dict(U=6, K=10, M=25, N=16, J=16, kappa_satellite_db=12, reference_elements_per_subsurface=28000))
        for a in self.plan["artifacts"]:
            if a["paper_id"] == "two-timescale-ma" and a["number"] in (14, 16):
                self.assertEqual(a["strict_specification"]["scientific_branch"], "explicit_corrected_original_model_Schur_Laplace_Jensen")
                self.assertFalse(a["strict_specification"]["printed_undefined_formula_recovered"])
        value = copy.deepcopy(self.plan)
        value["artifacts"][self.plan["artifacts"].index(artifact)]["strict_specification"]["effective_execution_grid"] = [7000, 15750, 28000, 43750, 63000]
        with self.assertRaises(ValueError):
            driver.validate_plan(value)

    def test_table_and_RIS_native_interface_blockers_retained(self):
        blocked = [task for task in self.plan["tasks"] if task["blockers"]]
        self.assertEqual({task["id"] for task in blocked}, {"cooperative-satcom-table01-matlab", "hotspot-satcom-table01-matlab", "mis-sensing-figure15-matlab", "mis-sensing-figure16-matlab"})
        for task in blocked:
            self.assertIn("--execute", task["original_strict_cli_arguments"])
            self.assertFalse(task["scientific_reproduction_certified"])

    def test_no_override_or_downsize_flag(self):
        value = copy.deepcopy(self.plan)
        value["tasks"][0]["original_strict_cli_arguments"].append("--preview")
        with self.assertRaises(ValueError):
            driver.validate_plan(value)
        settings = {a["paper_id"]: a["strict_specification"].get("settings") for a in self.plan["artifacts"] if a["kind"] == "figure"}
        self.assertEqual(settings["mis-sensing"]["number_of_starts"], 6000)
        self.assertEqual(settings["mis-sensing"]["outer_iterations"], 30)
        self.assertEqual(settings["mis-sensing"]["rcg_max_iterations"], 4000)
        self.assertEqual(settings["rotatable-isac"]["channel_realizations"], 100)
        self.assertEqual(settings["two-timescale-ma"]["geometry_realizations"], 100)
        self.assertEqual(settings["two-timescale-ma"]["nlos_realizations_per_geometry"], 1000)

    def test_exact_original_matlab_function_positionAST_and_private_globals(self):
        module = driver.import_metadata(REPO / "strict/reproduce.py", "toy_clone_original_metadata")
        original = module.run_matlab
        with tempfile.TemporaryDirectory() as folder:
            facade = native.make_facade(original, Path(folder))
            self.assertIs(facade.__code__, original.__code__)
            self.assertIs(facade.__globals__["matlab_literal"], original.__globals__["matlab_literal"])
            self.assertIsNot(facade.__globals__, original.__globals__)
            self.assertIsNot(facade.__globals__["run"], original.__globals__["run"])
            self.assertIs(facade.__globals__["subprocess"], original.__globals__["subprocess"])
        tree = ast.parse((REPO / "strict/reproduce.py").read_text(encoding="utf-8-sig"))
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run_matlab")
        self.assertEqual(node.lineno, original.__code__.co_firstlineno)
        self.assertIn("-batch", ast.dump(node, include_attributes=True))

    def test_only_windows_wait_and_exact_statement_untouched(self):
        command = ["C:/MAT LAB/matlab.exe", "-batch", "maxNumCompThreads(1);f('D:/中文/o''neil',6000);exit(0,'force');"]
        self.assertEqual(native.waited_command(command, True), [command[0], "-wait", *command[1:]])
        self.assertEqual(native.waited_command(command, False), command)
        for bad in ([], ["matlab", "-r", "f"], ["matlab", "-batch", "f", "--preview"]):
            with self.assertRaises(ValueError):
                native.waited_command(bad, True)

    def test_forward_once_wait_stdio_error_and_unknown_retained(self):
        calls = []
        def toy_run_matlab(expression, matlab):
            run([matlab, "-batch", expression])
        for error in (None, RuntimeError("synthetic host exception")):
            with tempfile.TemporaryDirectory() as folder:
                original = type(toy_run_matlab)(toy_run_matlab.__code__, {"run": lambda cmd: calls.append(cmd)})
                facade = native.make_facade(original, Path(folder) / "receipts")
                with mock.patch.object(native, "native_resources", return_value={"admitted": True}), mock.patch.object(native.subprocess, "Popen") as popen:
                    popen.return_value.pid = 1234
                    popen.return_value.wait.side_effect = error
                    popen.return_value.wait.return_value = 7
                    with self.assertRaises((subprocess_error(), RuntimeError)):
                        facade("exact unchanged toy statement", sys.executable)
                    popen.assert_called_once()
                row = driver.load(Path(folder) / "receipts/call-001-completion.json")
                self.assertEqual(row["actual_exit_code"], 7 if error is None else None)
                self.assertIsNotNone(row["exception"])
                self.assertFalse(row["native_scientific_reproduction_certified"])
                self.assertIsNone(row["actual_backend_PID"])
        self.assertEqual(calls, [])

    def test_nonexistent_image_and_deferred_resources_never_launch(self):
        def toy(expression, matlab):
            run([matlab, "-batch", expression])
        for admitted, image in ((False, sys.executable), (True, "Z:/definitely-absent-matlab.exe")):
            with tempfile.TemporaryDirectory() as folder:
                original = type(toy)(toy.__code__, {"run": lambda c: None})
                facade = native.make_facade(original, Path(folder))
                with mock.patch.object(native, "native_resources", return_value={"admitted": admitted}), mock.patch.object(native.subprocess, "Popen") as popen:
                    with self.assertRaises((ValueError, RuntimeError)):
                        facade("toy", image)
                    popen.assert_not_called()
                row = driver.load(Path(folder) / "call-001-completion.json")
                self.assertIsNone(row["actual_exit_code"])

    def test_task_zero_unknown_and_nonzero_are_not_science_pass(self):
        for code in (0, 9, None):
            with tempfile.TemporaryDirectory() as folder:
                task = {"id": "synthetic", "output_dir": str(Path(folder) / "new"), "command": ["synthetic"], "blockers": [], "dependency": None, "language": "python", "required_outputs": [], "required_plot_directory": None}
                with mock.patch.object(driver.subprocess, "Popen") as popen:
                    popen.return_value.pid = 12
                    popen.return_value.wait.return_value = code
                    if code is None:
                        popen.return_value.wait.side_effect = RuntimeError("synthetic unknown exit")
                    row = driver.task_record(task, {}, {})
                self.assertEqual(row["actual_exit_code"], code)
                self.assertFalse(row["scientific_reproduction_certified"])
                self.assertFalse(row["genuine_native_backend_science_certified"])
                self.assertTrue((Path(folder) / "new/controller-stderr.bin").is_file())

    def test_missing_outputs_and_dependency_cannot_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            task = {"id": "synthetic", "output_dir": str(Path(folder) / "new"), "command": ["synthetic"], "blockers": [], "dependency": None, "language": "python", "required_outputs": [str(Path(folder) / "missing-bank.json")], "required_plot_directory": None}
            with mock.patch.object(driver.subprocess, "Popen") as popen:
                popen.return_value.pid = 12
                popen.return_value.wait.return_value = 0
                row = driver.task_record(task, {}, {})
            self.assertEqual(row["state"], "exit_zero_missing_outputs")
            task.update(output_dir=str(Path(folder) / "dependency"), dependency="missing-fig3", source_result=str(Path(folder) / "missing-bank.json"))
            with mock.patch.object(driver.subprocess, "Popen") as popen:
                row = driver.task_record(task, {}, {})
                popen.assert_not_called()
            self.assertEqual(row["state"], "blocked_missing_or_failed_exact_Fig3_dependency")

    def test_all150_continue_with_nonzero_aggregate_and_sourcechange(self):
        with tempfile.TemporaryDirectory() as folder:
            plan = copy.deepcopy(self.plan)
            plan["output_dir"] = str(Path(folder) / "new-campaign")
            records = [{"id": t["id"], "state": "host_exception_or_unknown_exit" if i == 1 else "exit_zero_outputs_present_scientific_unverified", "actual_exit_code": None if i == 1 else 0} for i, t in enumerate(plan["tasks"])]
            with mock.patch.object(driver, "task_record", side_effect=records) as run, mock.patch.object(driver, "metadata_inputs", side_effect=[plan["metadata_sha256"], {}]), mock.patch("sys.stdout", new=io.StringIO()):
                self.assertEqual(driver.execute_plan(plan), 1)
                self.assertEqual(run.call_count, 150)
            closure = driver.load(Path(folder) / "new-campaign/controller-command-completion.json")
            self.assertEqual(closure["task_count"], 150)
            self.assertFalse(closure["planning_metadata_B_A"])
            self.assertFalse(closure["scientific_reproduction_certified"])

    def test_default_cli_is_readonly_no_dispatch_or_output(self):
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(driver, "execute_plan") as execute, mock.patch("sys.stdout", new=io.StringIO()), mock.patch.object(sys, "argv", ["run_all_full.py", "--repo", str(REPO), "--output-dir", str(Path(folder) / "absent")]):
            self.assertEqual(driver.main(), 0)
            execute.assert_not_called()
            self.assertFalse((Path(folder) / "absent").exists())

    def test_pre_dispatch_directory_or_receipt_error_keeps_all150(self):
        with tempfile.TemporaryDirectory() as folder:
            plan = copy.deepcopy(self.plan)
            plan["output_dir"] = str(Path(folder) / "campaign")
            records = [OSError("synthetic directory/start receipt error")]
            records += [{"id": t["id"], "state": "exit_zero_outputs_present_scientific_unverified",
                         "actual_exit_code": 0} for t in plan["tasks"][1:]]
            with mock.patch.object(driver, "task_record", side_effect=records) as run, mock.patch.object(driver, "metadata_inputs", return_value=plan["metadata_sha256"]), mock.patch("sys.stdout", new=io.StringIO()):
                self.assertEqual(driver.execute_plan(plan), 1)
                self.assertEqual(run.call_count, 150)
            closure = driver.load(Path(folder) / "campaign/controller-command-completion.json")
            self.assertEqual(closure["task_count"], 150)
            first = closure["records"][0]
            self.assertIsNone(first["actual_exit_code"])
            self.assertFalse(first["task_receipt_closure_available"])
            self.assertTrue((Path(folder) / "campaign/controller-host-failures" / (first["id"] + ".json")).is_file())
            self.assertFalse(closure["all_command_and_declared_output_checks_complete"])

    def test_after_metadata_unavailable_retains_all150_without_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            plan = copy.deepcopy(self.plan)
            plan["output_dir"] = str(Path(folder) / "campaign")
            records = [{"id": t["id"], "state": "exit_zero_outputs_present_scientific_unverified",
                        "actual_exit_code": 0} for t in plan["tasks"]]
            with mock.patch.object(driver, "task_record", side_effect=records), mock.patch.object(driver, "metadata_inputs", side_effect=[plan["metadata_sha256"], OSError("synthetic after metadata unavailable")]), mock.patch("sys.stdout", new=io.StringIO()):
                self.assertEqual(driver.execute_plan(plan), 1)
            closure = driver.load(Path(folder) / "campaign/controller-command-completion.json")
            self.assertEqual(closure["task_count"], 150)
            self.assertIsNone(closure["metadata_sha256_after"])
            self.assertIn("synthetic after metadata unavailable", closure["metadata_after_error"])
            self.assertFalse(closure["planning_metadata_B_A"])
            self.assertFalse(closure["all_command_and_declared_output_checks_complete"])


def subprocess_error():
    return native.subprocess.CalledProcessError


if __name__ == "__main__":
    unittest.main()
