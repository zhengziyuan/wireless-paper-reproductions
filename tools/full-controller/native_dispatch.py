"""Host-only waiting facade over the unchanged strict MATLAB CLI function."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback
import types
from run_all_full import import_metadata, native_resources, sha, utc, write_new


def waited_command(original, windows):
    if not isinstance(original, list) or len(original) != 3 or original[1] != "-batch" or not isinstance(original[2], str):
        raise ValueError("Exact original three-item MATLAB batch command required")
    return [original[0], "-wait", *original[1:]] if windows else list(original)


def environment():
    value = dict(os.environ)
    value.setdefault("PYTHONUTF8", "1")
    for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        value.setdefault(key, "1")
    return value


def make_facade(original, receipt_dir):
    """Original code object/globals except private run; no stdlib monkeypatch."""
    ordinal = 0
    def dispatch(command):
        nonlocal ordinal
        ordinal += 1
        receipt_dir.mkdir(parents=True, exist_ok=True)
        command_after = waited_command(command, os.name == "nt")
        executable = shutil.which(command_after[0]) or command_after[0]
        image = Path(executable).resolve()
        resources = native_resources(receipt_dir)
        record = {"ordinal": ordinal, "started_utc": utc(), "original_command": command,
                  "actual_command": command_after, "Windows_wait_added": os.name == "nt",
                  "original_expression_preserved": command_after[-1] == command[-1],
                  "actual_command_PID": None, "actual_exit_code": None, "exception": None,
                  "actual_backend_PID": None, "genuine_backend_PID_independently_verified": False,
                  "native_scientific_reproduction_certified": False,
                  "resource_admission": resources, "executable_path": str(image),
                  "executable_sha256_before": sha(image) if image.is_file() else None}
        write_new(receipt_dir / f"call-{ordinal:03d}-start.json", record)
        try:
            if not resources["admitted"]:
                record["state"] = "deferred_native_resources_not_success"
                raise RuntimeError("Native command deferred: RAM3GiB/disk16GiB admission or known RAM observation required")
            if not image.is_file():
                raise ValueError("MATLAB executable unavailable; no Python substitution")
            process = subprocess.Popen(command_after, env=environment(),
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            record["actual_command_PID"] = process.pid
            record["actual_exit_code"] = process.wait()
            record["state"] = "waited_command_exit_zero_science_unverified" if record["actual_exit_code"] == 0 else "waited_command_nonzero"
            if record["actual_exit_code"] != 0:
                raise subprocess.CalledProcessError(record["actual_exit_code"], command_after)
        except Exception:
            record["exception"] = traceback.format_exc()
            raise
        finally:
            record["finished_utc"] = utc()
            record["executable_sha256_after"] = sha(image) if image.is_file() else None
            record["executable_B_A"] = record["executable_sha256_before"] == record["executable_sha256_after"] and record["executable_sha256_before"] is not None
            changed_return = not record["executable_B_A"] and record["exception"] is None
            if changed_return:
                record["state"] = "host_executable_identity_changed_not_success"
                record["exception"] = "ValueError: MATLAB executable changed or disappeared during command"
            write_new(receipt_dir / f"call-{ordinal:03d}-completion.json", record)
            if changed_return:
                raise ValueError("MATLAB executable changed or disappeared during command")
    selected_globals = dict(original.__globals__)
    selected_globals["run"] = dispatch
    selected = types.FunctionType(original.__code__, selected_globals, original.__name__, original.__defaults__, original.__closure__)
    selected.__kwdefaults__ = original.__kwdefaults__
    if selected.__code__ is not original.__code__:
        raise ValueError("Original complete run_matlab code object must be identical")
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--receipt-dir", type=Path, required=True)
    parser.add_argument("--expected-reproduce-sha", required=True)
    parser.add_argument("strict_arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    argv = args.strict_arguments
    if not argv or argv.pop(0) != "--" or "--execute" not in argv:
        raise ValueError("Explicit original strict CLI --execute arguments after -- required")
    if "--language" not in argv or argv[argv.index("--language") + 1] != "matlab":
        raise ValueError("Facade is for the genuine MATLAB language slot only")
    source = args.repo.resolve() / "strict/reproduce.py"
    before = sha(source)
    if before != args.expected_reproduce_sha:
        raise ValueError("Strict source differs from declared plan identity")
    module = import_metadata(source, "all_full_unchanged_strict_native_cli")
    original = module.run_matlab
    module.run_matlab = make_facade(original, args.receipt_dir.resolve())
    sys.path.insert(0, str(source.parent))  # Same imports as invoking the genuine strict script.
    sys.argv = [str(source), *argv]
    try:
        module.main()
    finally:
        after = sha(source)
        write_new(args.receipt_dir / "unchanged-strict-source-closure.json",
                  {"source": str(source), "source_sha256_before": before, "source_sha256_after": after,
                   "whole_source_B_A": before == after, "run_matlab_code_object_identity_preserved": module.run_matlab.__code__ is original.__code__,
                   "native_scientific_reproduction_certified": False,
                   "scope": "private run binding +Windows-wait only; exact original main/execute/math source unchanged"})
        if before != after:
            raise ValueError("Strict source changed during native route; not certified")


if __name__ == "__main__":
    main()
