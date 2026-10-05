"""Plan all 73 numerical figures and two tables; explicit --execute runs CLIs.

This is a scheduler, not a numerical oracle. Exit zero never certifies a paper.
It does not import scientific models, decode numerical banks, or shrink scope.
"""
from __future__ import annotations
import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

PAPERS = ("mis-communications", "mis-sensing", "rotatable-isac",
          "two-timescale-ma", "cooperative-satcom", "hotspot-satcom")
NUMERICAL = dict(zip(PAPERS, (range(7, 12), range(2, 17), range(2, 18),
                             range(3, 21), range(2, 12), range(2, 11))))
LANGUAGES = ("python", "matlab")
GIB = 1024 ** 3


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def repo_root(explicit=None):
    candidates = [Path(explicit)] if explicit else [Path(__file__).resolve().parent, *Path(__file__).resolve().parents]
    for candidate in candidates:
        candidate = candidate.resolve()
        if (candidate / "strict/reproduce.py").is_file():
            return candidate
    raise ValueError("Repository with strict/reproduce.py required; use --repo")


def import_metadata(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def metadata_inputs(repo):
    strict = repo / "strict"
    paths = [strict / "reproduce.py", strict / "table_reproduction.py", strict / "mis_population_evidence.py",
             strict / "render_figure.py", strict / "mis-sensing/mis_sensing_strict_engine.m"]
    for paper in PAPERS:
        paths.append(strict / "figure-catalog" / (paper + ".json"))
        package = strict / paper
        mapping = "figure_map.json" if paper.startswith("mis-") else "figure_catalog.json" if paper in PAPERS[2:4] else "figure_coverage.json"
        paths.append(package / mapping)
    for relative in ("mis-communications/settings.json", "mis-sensing/settings_corrected.json",
                     "rotatable-isac/full_config.json", "two-timescale-ma/configs/full-ao10000-fig03-18-v2.json",
                     "two-timescale-ma/configs/figure19-full-axis-ao10000-fixed-mc-protocol-v2.json",
                     "two-timescale-ma/configs/figure20-full-axis-ao10000-fixed-mc-protocol-v2.json",
                     "cooperative-satcom/spectral_config.json", "hotspot-satcom/instantaneous_geometry_config.json",
                     "hotspot-satcom/statistical_validated_config.json"):
        paths.append(strict / relative)
    packet = strict / "validation/parameter-tables-source-qualified-v1"
    paths.append(packet / "freeze-manifest.json")
    paths.extend(packet / item for item in load(packet / "freeze-manifest.json")["files_sha256"])
    paths.extend(repo / item for item in load(packet / "canonical-parameter-contract-v1.json")["canonical_file_sha256"])
    return {path.relative_to(repo).as_posix(): sha(path) for path in sorted(set(paths))}


def result_paths(paper, figure, language, output, specification):
    """Literal central CLI return locations, not evidence of scientific success."""
    if paper.startswith("mis-"):
        if paper == "mis-sensing" and figure in (5, 6):
            return []  # Same-language Fig3 dependency is separately recorded.
        if language == "python" and (paper == "mis-communications" or figure in (3, 4)):
            return [str(output / "bank/full-result-python.json")]
        return [str(output / f"fig{figure}-{language}.json")]
    if paper in PAPERS[2:4]:
        if paper == "two-timescale-ma" and figure in (14, 16):
            return [str(output / ("plots/derivation-summary.json" if language == "python" else "matlab-corrected/derivation-summary-matlab.json"))]
        if language == "python":
            return [str(output / "bank/full_summary.json")]
        return [str(output / "matlab")]  # Per-job native results; file contents remain unverified here.
    paths = []
    for sweep in specification["execution_sweeps"]:
        if paper == "hotspot-satcom" and sweep == "statistical" and language == "matlab":
            paths.append(str(output / "checkpoints/statistical/matlab/full18-matlab.json"))
        else:
            paths.append(str(output / f"{sweep}-{language}.json"))
    return paths


def task_id(paper, kind, number, language):
    return f"{paper}-{kind}{number:02d}-{language}"


def make_plan(repo, output, python, matlab=None, workers=1):
    repo, output = Path(repo).resolve(), Path(output).resolve()
    if workers not in (1, 2, 3):
        raise ValueError("Existing CLI workers1/2/3 only; no population controls")
    before = metadata_inputs(repo)
    strict = repo / "strict"
    central = import_metadata(strict / "reproduce.py", "all_full_central_metadata")
    tables = import_metadata(strict / "table_reproduction.py", "all_full_table_metadata")
    artifacts, excluded, tasks = [], [], []
    for paper in PAPERS:
        inventory = load(strict / "figure-catalog" / (paper + ".json"))
        figures = inventory["figures"]
        if ([item["figure"] for item in figures] != list(range(1, inventory["figure_count"] + 1))
                or inventory["paper_id"] != paper):
            raise ValueError("Changed/duplicate author figure inventory: " + paper)
        for source in figures:
            number = source["figure"]
            try:
                specification, error = central.plan(paper, number), None
            except Exception as exc:
                specification, error = None, f"{type(exc).__name__}: {exc}"
            numerical = number in NUMERICAL[paper]
            if specification is not None and bool(specification["runnable"]) != numerical:
                raise ValueError("Numerical scope changed; review rather than silently drop: " + paper + str(number))
            if not numerical:
                excluded.append({"paper_id": paper, "figure": number, "source": source,
                                 "reason": specification.get("kind") if specification else error})
                continue
            artifact = {"paper_id": paper, "kind": "figure", "number": number,
                        "source": source, "strict_specification": specification, "planning_error": error}
            artifacts.append(artifact)
            for language in LANGUAGES:
                identifier = task_id(paper, "figure", number, language)
                destination = output / identifier
                original = ["--paper", paper, "--figure", str(number), "--language", language,
                            "--workers", str(workers), "--output-dir", str(destination), "--execute"]
                dependency, source_result = None, None
                if paper == "mis-sensing" and number in (5, 6):
                    dependency = task_id(paper, "figure", 3, language)
                    source_result = result_paths(paper, 3, language, output / dependency, {})[0]
                    original += ["--source-result", source_result]
                if matlab and language == "matlab":
                    original += ["--matlab", str(matlab)]
                blockers = [error] if error else []
                if paper == "mis-sensing" and number in (15, 16) and language == "matlab":
                    blockers.append("Current MATLAB ris_baselines omits target_start_banks; strict renderer requires every target's6000 summaries. No expensive incomplete full-render command is launched.")
                command = [str(python), "-B", str(strict / "reproduce.py"), *original]
                if language == "matlab":
                    command = [str(python), "-B", str(Path(__file__).with_name("native_dispatch.py")),
                               "--repo", str(repo), "--receipt-dir", str(destination / "host-native-calls"),
                               "--expected-reproduce-sha", before["strict/reproduce.py"], "--", *original]
                tasks.append({"id": identifier, "artifact_index": len(artifacts) - 1, "language": language,
                              "command": command, "original_strict_cli_arguments": original,
                              "output_dir": str(destination), "dependency": dependency, "source_result": source_result,
                              "required_outputs": result_paths(paper, number, language, destination, specification) if specification else [],
                              "required_plot_directory": str(destination / ("matlab-corrected" if paper == "two-timescale-ma" and number in (14, 16) and language == "matlab" else "plots")), "blockers": blockers,
                              "scientific_reproduction_certified": False})
        for source in inventory["tables"]:
            if paper not in PAPERS[4:] or source["table"] != 1:
                raise ValueError("Changed table inventory requires review")
            try:
                specification, error = tables.table_plan(paper, source["table"]), None
            except Exception as exc:
                specification, error = None, f"{type(exc).__name__}: {exc}"
            artifacts.append({"paper_id": paper, "kind": "table", "number": 1,
                              "source": source, "strict_specification": specification, "planning_error": error})
            for language in LANGUAGES:
                identifier = task_id(paper, "table", 1, language)
                destination = output / identifier
                argv = ["--paper", paper, "--table", "1", "--language", language,
                        "--output-dir", str(destination), "--execute"]
                tasks.append({"id": identifier, "artifact_index": len(artifacts) - 1, "language": language,
                              "command": [str(python), "-B", str(strict / "reproduce.py"), *argv],
                              "original_strict_cli_arguments": argv, "output_dir": str(destination),
                              "dependency": None, "source_result": None,
                              "required_outputs": [str(destination / "actual-both-table-canonical-parameter-replay.json")],
                              "required_plot_directory": None,
                              "blockers": ([error] if error else []) + (["No MATLAB table interface: execute_table only accepts Python metadata audit; no MATLAB substitute."] if language == "matlab" else []),
                              "scientific_reproduction_certified": False})
    after = metadata_inputs(repo)
    if before != after:
        raise ValueError("Planning metadata changed during read")
    result = {"schema": "all-paper-full-controller-plan-v1", "created_utc": utc(),
              "repo": str(repo), "output_dir": str(output), "artifacts": artifacts,
              "excluded_nonnumerical_figures": excluded, "tasks": tasks,
              "metadata_sha256": before, "metadata_unchanged_during_plan": True,
              "execution_requested": False, "scientific_reproduction_certified": False,
              "all_scientific_source_runtime_or_RNG_certified": False,
              "native_resource_minimum_free_RAM_bytes": 3 * GIB,
              "native_resource_minimum_free_disk_bytes": 16 * GIB,
              "scope": "73 numerical figures +2 source-parameter tables, both language slots; known unsupported routes remain blocked; full strict CLI defaults only"}
    validate_plan(result)
    return result


def validate_plan(plan):
    artifacts, tasks = plan["artifacts"], plan["tasks"]
    expected = {(paper, "figure", number) for paper in PAPERS for number in NUMERICAL[paper]}
    expected |= {(paper, "table", 1) for paper in PAPERS[4:]}
    actual = [(entry["paper_id"], entry["kind"], entry["number"]) for entry in artifacts]
    if len(actual) != 75 or set(actual) != expected or len(plan["excluded_nonnumerical_figures"]) != 12:
        raise ValueError("All73+2 artifact identities and12 nonnumerical exclusions required")
    identities = [entry["id"] for entry in tasks]
    required = {task_id(paper, kind, number, language) for paper, kind, number in expected for language in LANGUAGES}
    if len(identities) != 150 or set(identities) != required:
        raise ValueError("All150 dual-language task slots required; no dropped/duplicate task")
    for entry in tasks:
        arguments = entry["original_strict_cli_arguments"]
        if "--execute" not in arguments or any(flag in arguments for flag in ("--settings", "--source-bank", "--component", "--preview", "--quick", "--reduced")):
            raise ValueError("No scientific overrides/reduced flags")
        artifact = artifacts[entry["artifact_index"]]
        if entry["id"] != task_id(artifact["paper_id"], artifact["kind"], artifact["number"], entry["language"]):
            raise ValueError("Task/artifact identity mismatch")
        if artifact["paper_id"] == "mis-sensing" and artifact["number"] in (5, 6):
            if entry["dependency"] != task_id("mis-sensing", "figure", 3, entry["language"]) or entry["source_result"] not in arguments:
                raise ValueError("Convergence must reuse same-language exact Fig3 output")
    hot9 = next(entry["strict_specification"] for entry in artifacts if (entry["paper_id"], entry["kind"], entry["number"]) == ("hotspot-satcom", "figure", 9))
    if hot9 is not None and (hot9["effective_execution_grid"] != list(range(4000, 28001, 4000)) or hot9["full_required_channel_realizations"] != 7000):
        raise ValueError("Hot9 requires seven scalar counts/7000, never the generic five shape grid")


def native_resources(directory):
    """Read-only host admission, not numerical budgets or paper feasibility."""
    directory = Path(directory).resolve()
    while not directory.exists():
        directory = directory.parent
    free_disk = shutil.disk_usage(directory).free
    free_ram = None
    if os.name == "nt":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong),
                        *[(name, ctypes.c_ulonglong) for name in ("total_phys", "avail_phys", "total_page", "avail_page", "total_virtual", "avail_virtual", "avail_extended")]]
        status = MemoryStatus()
        status.length = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            free_ram = int(status.avail_phys)
    elif Path("/proc/meminfo").is_file():
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                free_ram = int(line.split()[1]) * 1024
    elif hasattr(os, "sysconf"):
        try:
            free_ram = os.sysconf("SC_AVPHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")
        except (OSError, ValueError):
            pass
    return {"observed_utc": utc(), "free_RAM_bytes": free_ram, "free_disk_bytes": free_disk,
            "admitted": free_ram is not None and free_ram >= 3 * GIB and free_disk >= 16 * GIB}


def task_record(task, environment, earlier):
    destination = Path(task["output_dir"])
    destination.mkdir(parents=True, exist_ok=False)
    record = {"id": task["id"], "command": task["command"], "started_utc": utc(),
              "actual_command_PID": None, "actual_exit_code": None, "exception": None,
              "state": "unknown", "scientific_reproduction_certified": False,
              "genuine_native_backend_science_certified": False}
    write_new(destination / "controller-task-start.json", record)
    stdout, stderr = destination / "controller-stdout.bin", destination / "controller-stderr.bin"
    try:
        if task["blockers"]:
            record.update(state="blocked_interface", blockers=task["blockers"])
        elif task["dependency"] and (earlier.get(task["dependency"], {}).get("state") != "exit_zero_outputs_present_scientific_unverified" or not Path(task["source_result"]).is_file()):
            record.update(state="blocked_missing_or_failed_exact_Fig3_dependency")
        else:
            if task["language"] == "matlab" and task["required_plot_directory"] is not None:
                resources = native_resources(destination)
                record["resource_observation"] = resources
                if not resources["admitted"]:
                    record["state"] = "deferred_native_resources"
                    return record
            write_new(destination / "controller-dispatch.json", {"command": task["command"], "utc": utc()})
            with stdout.open("xb") as out, stderr.open("xb") as err:
                process = subprocess.Popen(task["command"], stdout=out, stderr=err, env=environment,
                                           creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
                record["actual_command_PID"] = process.pid
                record["actual_exit_code"] = process.wait()
            missing = [path for path in task["required_outputs"] if not Path(path).exists()]
            if task["required_plot_directory"] is not None and not Path(task["required_plot_directory"]).is_dir():
                missing.append(task["required_plot_directory"])
            record["missing_declared_outputs"] = missing
            record["state"] = ("command_failed" if record["actual_exit_code"] != 0 else
                               "exit_zero_missing_outputs" if missing else "exit_zero_outputs_present_scientific_unverified")
            record["closed_result_file_sha256"] = {path: sha(path) for path in task["required_outputs"] if Path(path).is_file()}
    except Exception:
        record.update(state="host_exception_or_unknown_exit", exception=traceback.format_exc())
    finally:
        record["finished_utc"] = utc()
        record["stdio_sha256"] = {str(path): sha(path) for path in (stdout, stderr) if path.is_file()}
        write_new(destination / "controller-task-completion.json", record)
    return record


def execute_plan(plan):
    validate_plan(plan)
    repo, output = Path(plan["repo"]), Path(plan["output_dir"])
    if metadata_inputs(repo) != plan["metadata_sha256"]:
        raise ValueError("Changed immutable planning inputs; regenerate and review plan")
    output.mkdir(parents=True, exist_ok=False)
    write_new(output / "controller-plan.json", plan)
    environment = dict(os.environ)
    environment.setdefault("PYTHONUTF8", "1")
    for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        environment.setdefault(key, "1")
    records, earlier = [], {}
    for task in plan["tasks"]:
        try:
            record = task_record(task, environment, earlier)
        except Exception:
            # Directory/start/final-receipt failures can occur outside the
            # per-task dispatch try. Retain them without dropping later slots.
            record = {"id": task["id"], "command": task["command"],
                      "actual_command_PID": None, "actual_exit_code": None,
                      "finished_utc": utc(), "state": "host_exception_or_unknown_exit",
                      "exception": traceback.format_exc(),
                      "task_receipt_closure_available": False,
                      "scientific_reproduction_certified": False,
                      "genuine_native_backend_science_certified": False}
            try:
                write_new(output / "controller-host-failures" / (task["id"] + ".json"), record)
            except Exception:
                record["fallback_receipt_error"] = traceback.format_exc()
        records.append(record)
        earlier[task["id"]] = record
        print(f"{task['id']}: {record['state']} exit={record['actual_exit_code']}", flush=True)
    try:
        after, metadata_after_error = metadata_inputs(repo), None
    except Exception:
        after, metadata_after_error = None, traceback.format_exc()
    failed = [row["id"] for row in records if row["state"] != "exit_zero_outputs_present_scientific_unverified"]
    completion = {"schema": "all-paper-full-controller-command-completion-v1", "finished_utc": utc(),
                  "task_count": len(records), "required_task_count": 150, "records": records,
                  "failed_blocked_deferred_or_unknown_tasks": failed,
                  "metadata_sha256_before": plan["metadata_sha256"], "metadata_sha256_after": after,
                  "metadata_after_error": metadata_after_error,
                  "planning_metadata_B_A": after == plan["metadata_sha256"],
                  "all_command_and_declared_output_checks_complete": not failed and after == plan["metadata_sha256"],
                  "scientific_reproduction_certified": False, "reference_curve_agreement_verified": False,
                  "all_scientific_source_runtime_or_RNG_certified": False,
                  "scope": "real command exits/declared output existence only; independent numerical/figure gates not inferred"}
    write_new(output / "controller-command-completion.json", completion)
    return 0 if completion["all_command_and_declared_output_checks_complete"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--matlab")
    parser.add_argument("--workers", type=int, choices=(1, 2, 3), default=1)
    parser.add_argument("--output-dir", type=Path, default=Path("full-paper-campaign"))
    parser.add_argument("--plan-output", type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    plan = make_plan(repo_root(args.repo), args.output_dir, args.python, args.matlab, args.workers)
    if args.plan_output:
        write_new(args.plan_output, plan)
    if not args.execute:
        print(json.dumps(plan, indent=2, ensure_ascii=False, allow_nan=False))
        return 0
    return execute_plan(plan)


if __name__ == "__main__":
    raise SystemExit(main())
