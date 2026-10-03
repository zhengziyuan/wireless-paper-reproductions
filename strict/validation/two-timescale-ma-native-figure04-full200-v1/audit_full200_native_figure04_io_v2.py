"""I/O-only immutable-progress wrapper around unchanged frozen v1 maths."""
from pathlib import Path
import importlib.util
import json
import os
import time
import uuid

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "audit_full200_native_figure04_v1.py"
PLAN = HERE / "FIGURE04_IO_ONLY_WRAPPER_V2.md"
EXPECTED_SOURCE_SHA = "f014e63f98539482b5f788f81d1ab7c72c8ac61db7cfd77b284d06d9858f6139"
spec = importlib.util.spec_from_file_location("frozen_independent_Fig04_v1", SOURCE)
v1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v1)
assert v1.sha(SOURCE) == EXPECTED_SOURCE_SHA


def immutable_atomic(path, obj):
    path = Path(path)
    if path.name == "actual-audit-progress.json":
        path = path.with_name(f"actual-audit-progress-{obj['attempted']:03d}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    assert not path.exists(), "This wrapper never replaces earlier evidence."
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temporary.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(obj, indent=2, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    for attempt in range(60):
        try:
            os.replace(temporary, path)
            return
        except PermissionError:
            if attempt == 59:
                raise
            time.sleep(min(.025 * 2**min(attempt, 5), .5))


original_prepare = v1.prepare


def prepare_with_wrapper_identity(*args):
    cfg, cases, files, frozen, count = original_prepare(*args)
    files.update(io_only_entry=Path(__file__), io_only_plan=PLAN)
    frozen.update({name: v1.sha(files[name]) for name in ("io_only_entry", "io_only_plan")})
    return cfg, cases, files, frozen, count


v1.prepare = prepare_with_wrapper_identity
v1.atomic = immutable_atomic

if __name__ == "__main__":
    v1.main()
