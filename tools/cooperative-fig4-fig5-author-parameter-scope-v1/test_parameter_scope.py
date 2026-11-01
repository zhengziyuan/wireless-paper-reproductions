"""In-memory format and mismatch tests; no author files or PDF are needed."""
import io
import struct
import types
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import check_parameter_scope as checked


def tag(kind, data):
    return struct.pack('<II', kind, len(data)) + data + b'\0' * ((-len(data)) % 8)


def mat(name='plot_record', extra=False, corrupt=False):
    header = bytearray(128)
    header[126:128] = b'IM'
    def matrix(n):
        fields = tag(6, struct.pack('<II', 6, 0))
        fields += tag(5, struct.pack('<iii', 18, 20, 5))
        fields += tag(1, n.encode('ascii'))
        fields += tag(9, bytes(8 * (1799 if corrupt else 1800)))
        return tag(14, fields)
    return bytes(header) + matrix(name) + (matrix('beta_N') if extra else b'')


def archive(*, ground=1, sweep=2, extra=False, corrupt=False, later_override=False,
            init_line='INIT_S_AO_beta_N_100_SCSI_u2_k1_j2'):
    result = io.BytesIO()
    with zipfile.ZipFile(result, 'w') as z:
        root = 'test_varsigma_316/'
        z.writestr(root + 'main.m', f'for test_variable_2={sweep}\n{init_line}\nend\n')
        init = f'beta_N=10^test_variable_2;\nbeta_R={ground};\n'
        if later_override:
            init += 'beta_R=10;\n'
        z.writestr(root + 'INIT_S_AO_beta_N_100_SCSI_u2_k1_j2.m', init)
        for name in ('plot_record0119.mat', 'plot_record0120.mat'):
            z.writestr(root + name, mat(extra=extra, corrupt=corrupt))
    return result.getvalue()


def paper(valid=True):
    context = ('Fig. 4 and Fig. 5 present synthetic context κN = 20 dB, κR = 10 dB '
               'and κN = 0 dB, κR = 10 dB') if valid else 'unrelated figure'
    return types.SimpleNamespace(stdout=context.encode('utf-8'), stderr=b'', returncode=0)


class ParameterScopeTest(unittest.TestCase):
    def evaluate(self, zip_data, pdf_valid=True):
        with patch.object(Path, 'read_bytes', return_value=zip_data), \
             patch.object(checked.subprocess, 'run', return_value=paper(pdf_valid)):
            return checked.check('ignored.zip', 'ignored.pdf')

    def test_observed_context(self):
        r = self.evaluate(archive())
        self.assertEqual(r['visible_working_script']['terrestrial_rician_db'], 0)
        self.assertEqual(r['paper_figure_context']['Fig5']['terrestrial_rician_db'], 10)
        self.assertFalse(r['working_script_produced_retained_mats_proved'])

    def test_wrong_sweep_or_ground_rejected(self):
        for data in (archive(sweep=0), archive(ground=10), archive(later_override=True)):
            with self.assertRaises(ValueError):
                self.evaluate(data)

    def test_missing_or_commented_call_rejected(self):
        for line in ('', '% INIT_S_AO_beta_N_100_SCSI_u2_k1_j2',
                     '%{\nINIT_S_AO_beta_N_100_SCSI_u2_k1_j2\n%}',
                     "x = 'INIT_S_AO_beta_N_100_SCSI_u2_k1_j2';"):
            with self.subTest(line=line), self.assertRaises(ValueError):
                self.evaluate(archive(init_line=line))

    def test_extra_metadata_rejected(self):
        with self.assertRaises(ValueError):
            self.evaluate(archive(extra=True))

    def test_truncated_array_rejected(self):
        with self.assertRaises(ValueError):
            self.evaluate(archive(corrupt=True))

    def test_wrong_figure_context_rejected(self):
        with self.assertRaises(ValueError):
            self.evaluate(archive(), pdf_valid=False)


if __name__ == '__main__':
    unittest.main()
