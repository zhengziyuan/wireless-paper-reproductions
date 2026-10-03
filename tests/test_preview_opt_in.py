"""Entry guards only; these tests never run a reduced or full optimizer."""
from __future__ import annotations

from contextlib import redirect_stderr
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def preview_module():
    spec = importlib.util.spec_from_file_location("preview_entry_guard", ROOT / "scripts/run_python.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PreviewEntryGuard(unittest.TestCase):
    def test_default_refuses_before_outputs_or_numerical_calls(self):
        module = preview_module()
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "must-not-be-created"
            with mock.patch.object(module.sys, "argv", ["run_python.py", "--output-dir", str(output)]), \
                    mock.patch.object(module.subprocess, "run") as run, redirect_stderr(io.StringIO()) as errors:
                with self.assertRaises(SystemExit) as failure:
                    module.main()
                self.assertEqual(failure.exception.code, 2)
                self.assertIn("strict/reproduce.py", errors.getvalue())
                run.assert_not_called()
                self.assertFalse(output.exists())

    def test_explicit_preview_opt_in_keeps_original_command_and_fixture(self):
        module = preview_module()
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "explicit-preview"
            arguments = ["run_python.py", "--legacy-preview", "--paper", "mis-communications", "--output-dir", str(output)]
            with mock.patch.object(module.sys, "argv", arguments), mock.patch.object(module.subprocess, "run") as run:
                module.main()
                run.assert_called_once_with(
                    [module.sys.executable, str(ROOT / "papers/mis-communications/run.py"),
                     "--output", str(output.resolve() / "mis-communications.json")], check=True, cwd=ROOT)

    def test_unknown_preview_id_still_fails_closed(self):
        module = preview_module()
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "must-not-be-created"
            arguments = ["run_python.py", "--legacy-preview", "--paper", "not-a-paper", "--output-dir", str(output)]
            with mock.patch.object(module.sys, "argv", arguments), \
                    mock.patch.object(module.subprocess, "run") as run, redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as failure:
                    module.main()
                self.assertEqual(failure.exception.code, 2)
                run.assert_not_called()
                self.assertFalse(output.exists())

    def test_matlab_prepared_guard_precedes_any_fixture_or_optimizer(self):
        # Static source ordering is not an actual licensed MATLAB dispatch test.
        source = (ROOT / "scripts/run_all_matlab.m").read_text(encoding="utf-8")
        self.assertIn("legacy_preview (1,1) logical = false", source)
        guard = source.index("if ~legacy_preview")
        for operation in ("root =", "mkdir(output_dir)", "papers =", "addpath(folder)", "feval(item.matlab_entry"):
            self.assertLess(guard, source.index(operation))


if __name__ == "__main__":
    unittest.main()
