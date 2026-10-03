"""Synthetic I/O-only tests; no numerical jobs or paper results generated."""
import importlib.util
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


class BankIORetryTests(unittest.TestCase):
    def test_both_runners_retry_transient_replace_without_changing_receipt(self):
        for folder in [Path(__file__).parent,Path(__file__).parents[1]/"rotatable-isac"]:
            sys.path.insert(0,str(folder));spec=importlib.util.spec_from_file_location("io_runner_"+folder.name,folder/"execute_bank.py")
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            with TemporaryDirectory() as temporary:
                target=Path(temporary)/"progress.json";real_replace=Path.replace;attempts=[]
                def replace(source,destination):
                    attempts.append(source)
                    if len(attempts)==1:raise PermissionError(13,"synthetic transient sharing lock")
                    return real_replace(source,destination)
                payload={"scope":"synthetic_IO_only_test_not_science","unchanged_sample_count":1000}
                with patch.object(Path,"replace",replace),patch.object(module.time,"sleep"):
                    module.atomic_json(target,payload)
                self.assertEqual(len(attempts),2);self.assertEqual(json.loads(target.read_text()),payload)
                self.assertFalse(target.with_suffix(".json.tmp").exists())


if __name__=="__main__":unittest.main(verbosity=2)
