"""Independent Decimal60 physical channel/gradient check, never a solver.

The closed-simplex KKT measure is the previously disclosed implementation
erratum. A terminal smoothed-objective check is not a global/max-min proof.
"""
from __future__ import annotations
import argparse
from decimal import Decimal, localcontext
import hashlib
import json
import os
from pathlib import Path
import sys

for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT/'wireless-paper-reproductions/strict/mis-communications'
sys.path.insert(0, str(PACKAGE))
import run as original


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def D(value): return Decimal.from_float(float(value))
def add(a, b): return (a[0]+b[0], a[1]+b[1])
def mul(a, b): return (a[0]*b[0]-a[1]*b[1], a[0]*b[1]+a[1]*b[0])
def conj(a): return (a[0], -a[1])
def scale(a, b): return (a[0]*b, a[1]*b)
def norm2(a): return a[0]*a[0]+a[1]*a[1]
def complexes(value):
    real = value['real']; imag = value['imag']
    if not isinstance(real, list): real, imag = [real], [imag]
    return [(D(r), D(i)) for r, i in zip(real, imag)]


def simplex(row):
    ordered = sorted(row, reverse=True); total = Decimal(0); threshold = None
    for i, x in enumerate(ordered, 1):
        total += x; candidate = (total-1)/i
        if x > candidate: threshold = candidate
    assert threshold is not None
    return [max(Decimal(0), x-threshold) for x in row]


def verify(config, coefficients, indices, state, mu):
    with localcontext() as context:
        context.prec = 60
        p, t = complexes(state['phi']), complexes(state['theta'])
        X = [[D(x) for x in row] for row in state['X']]
        c = [[(D(r), D(i)) for r, i in zip(rr, ii)]
             for rr, ii in zip(coefficients['real'], coefficients['imag'])]
        K, M, N, U = len(c), len(p), len(t), len(indices)
        gamma = [[Decimal(0)]*U for _ in range(K)]
        q = [[(Decimal(0), Decimal(0))]*U for _ in range(K)]
        bars = [[(Decimal(1), Decimal(0))]*M for _ in range(U)]
        iota = D(config['reference_snr'])
        for u in range(U):
            for n, m in enumerate(indices[u]): bars[u][m] = t[n]
            for k in range(K):
                field = (Decimal(0), Decimal(0))
                for m in range(M): field = add(field, mul(c[k][m], mul(p[m], bars[u][m])))
                q[k][u] = field; gamma[k][u] = iota*norm2(field)
        g = [sum(x*y for x, y in zip(row, powers)) for row, powers in zip(X, gamma)]
        minimum = min(g); mmu = D(mu)
        ex = [(-(x-minimum)/mmu).exp() for x in g]; total = sum(ex)
        weights = [x/total for x in ex]
        gp = [(Decimal(0), Decimal(0)) for _ in range(M)]
        gt = [(Decimal(0), Decimal(0)) for _ in range(N)]
        for k in range(K):
            for u in range(U):
                factor = -2*iota*weights[k]*X[k][u]
                for m in range(M):
                    gp[m] = add(gp[m], scale(mul(conj(bars[u][m]), mul(conj(c[k][m]), q[k][u])), factor))
                for n, m in enumerate(indices[u]):
                    gt[n] = add(gt[n], scale(mul(conj(p[m]), mul(conj(c[k][m]), q[k][u])), factor))
        def projected(a, phases):
            return [add(v, scale(z, -mul(v, conj(z))[0])) for v, z in zip(a, phases)]
        pg, tg = projected(gp, p), projected(gt, t)
        xnorm = Decimal(0)
        for k in range(K):
            raw = [-weights[k]*x for x in gamma[k]]; mean = sum(raw)/U
            gradient = [x-mean for x in raw]
            projected_row = simplex([x-y for x, y in zip(X[k], gradient)])
            xnorm += sum((x-y)**2 for x, y in zip(X[k], projected_row))
        phi_norm = sum((norm2(x) for x in pg), Decimal(0)).sqrt()
        theta_norm = sum((norm2(x) for x in tg), Decimal(0)).sqrt()
        kkt = (phi_norm**2+theta_norm**2+xnorm).sqrt()
        binary = min(gamma[k][max(range(U), key=lambda u: X[k][u])] for k in range(K))
        phase_error = max([abs(norm2(z).sqrt()-1) for z in p+t] or [Decimal(0)])
        row_error = max(abs(sum(row)-1) for row in X)
        domain = phase_error < D(1e-12) and row_error < D(1e-12) and min(x for row in X for x in row) >= 0
        return {'precision_digits': 60, 'projected_kkt_norm_decimal': str(kkt),
            'projected_kkt_norm': float(kkt), 'phi_norm': float(phi_norm), 'theta_norm': float(theta_norm),
            'X_norm': float(xnorm.sqrt()), 'minimum_binary_snr': float(binary),
            'minimum_relaxed_snr': float(minimum), 'smoothed_minimized_objective': float(-minimum+mmu*total.ln()),
            'maximum_phase_radius_error': float(phase_error), 'maximum_simplex_sum_error': float(row_error),
            'domain_feasible': domain, 'original_unchanged_1e_minus6_control_pass': kkt <= D(1e-6)}


def model_inputs():
    settings = json.loads((PACKAGE/'settings.json').read_text(encoding='utf-8'))
    model = original.make_model({'ms1':[2,2], 'ms2':[1,1], 'K':4}, settings)
    return model.config, {'real':model.c.real.tolist(), 'imag':model.c.imag.tolist()}, model.indices.tolist()


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--snapshot-directory', type=Path)
    parser.add_argument('--native-receipt', type=Path); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); before, sources = original.implementation_digest(); records = []
    if args.snapshot_directory:
        folder = args.snapshot_directory; summary_path = folder/'all-snapshot-cold-components.json'
        summary = json.loads(summary_path.read_text(encoding='utf-8')); config, c, indices = model_inputs()
        assert len(summary['actual_attempts']) == summary['expected_snapshot_failed_starts'] == 14
        for item in summary['actual_attempts']:
            path = folder/f"{item['baseline']}-{item['start']:04d}.json"
            assert item['baseline'] == 'MIS' and sha(path) == item['actual_receipt_sha256']
            raw = json.loads(path.read_text(encoding='utf-8')); assert raw['science_digest_before'] == before == raw['science_digest_after']
            truth = verify(config, c, indices, raw['final_state'], raw['stages'][-1]['mu'])
            measured = raw['stages'][-1]['stop']['projected_kkt_norm']
            truth['recorded_KKT_absolute_error'] = abs(measured-truth['projected_kkt_norm'])
            truth['recorded_binary_snr_absolute_error'] = abs(raw['metrics']['minimum_binary_SNR']-truth['minimum_binary_snr'])
            truth['input_receipt_sha256'] = sha(path); truth['start'] = item['start']; truth['baseline'] = 'MIS'
            truth['pass'] = truth['domain_feasible'] and truth['original_unchanged_1e_minus6_control_pass'] and truth['recorded_KKT_absolute_error'] <= 5e-13 and truth['recorded_binary_snr_absolute_error'] <= 5e-14
            records.append(truth)
    if args.native_receipt:
        raw = json.loads(args.native_receipt.read_text(encoding='utf-8'))
        assert raw['source_unchanged_during_run'] and raw['original_numerical_suffix_byte_identical']
        config, c = raw['model_config'], raw['coefficients']; indices = [[u] for u in range(4)]
        for stage_index, stage in enumerate(raw['extended100000']['stages']):
            truth = verify(config, c, indices, stage['state'], stage['mu'])
            truth['recorded_KKT_absolute_error'] = abs(stage['stop']['projected_kkt_norm']-truth['projected_kkt_norm'])
            truth['input_receipt_sha256'] = sha(args.native_receipt); truth['stage_index'] = stage_index; truth['engine'] = 'native_matlab'
            truth['pass'] = truth['domain_feasible'] and truth['original_unchanged_1e_minus6_control_pass'] and truth['recorded_KKT_absolute_error'] <= 5e-13
            records.append(truth)
    assert records, 'Actual inputs required'
    after, _ = original.implementation_digest(); assert before == after
    result = {'scope':'independent_Decimal60_physical_full_Fig8_input_checks_NOT_full12000',
        'science_digest_before':before, 'science_digest_after':after, 'sources':sources,
        'executed_checker_sha256':sha(__file__), 'checked_records':len(records), 'records':records,
        'all_checks_pass':all(x['pass'] for x in records), 'full_figure_reproduction_pass':False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    assert not args.output.exists(), 'Fresh independent receipt required'
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'all_checks_pass':result['all_checks_pass'], 'checked_records':len(records)}))
    assert result['all_checks_pass']


if __name__ == '__main__': main()
