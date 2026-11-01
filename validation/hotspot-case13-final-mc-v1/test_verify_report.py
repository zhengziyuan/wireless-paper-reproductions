"""Synthetic tests for strict replay comparison and bounded local reads."""
import importlib.util
import io
import unittest
from pathlib import Path
from unittest import mock

spec=importlib.util.spec_from_file_location('verify_mc',Path(__file__).with_name('verify_report.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
    def test_exact_nested_match(self):
        self.assertTrue(m.same({'x':[True,1.0,None]},{'x':[True,1.0,None]}))

    def test_reject_bool_numeric_equivalence(self):
        self.assertFalse(m.same({'x':True},{'x':1}))
        self.assertFalse(m.same([1],[1.0]))

    def test_reject_changed_nested_fields(self):
        self.assertFalse(m.same({'x':[1,2]},{'x':[1,3]}))
        self.assertFalse(m.same({'x':1},{'x':1,'y':2}))

    def test_read_cap(self):
        with mock.patch.object(m.Path,'open',side_effect=lambda *args,**kwargs:io.BytesIO(b'12345')):
            self.assertEqual(m.read('toy',5),b'12345')
            with self.assertRaises(ValueError):m.read('toy',4)


if __name__=='__main__':unittest.main()
