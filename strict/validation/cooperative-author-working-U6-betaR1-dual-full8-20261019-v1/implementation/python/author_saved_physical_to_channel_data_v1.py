"""Prepared input-only bridge; no optimizer, scenario generation or RNG.

Convert one explicitly admitted saved author U6 snapshot (NPZ or MATLAB v7
author_snapshot) to the existing data/power/limit interface. This is a separate
physical variant. Original cached-W/random-phase initializers, author MC count
and all published-reference agreement remain unrecovered by this conversion.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import io
import json

FIXED = dict(J=3, U=6, N=16, M=25, K=1, beta_N=100., beta_R=1., beta_G=1000.)
SHAPES = dict(d_mean=(3, 6, 16), d_var=(3, 6), G_mean=(3, 6, 16, 25),
              G_var=(3, 6), r_mean=(6, 25), r_var=(6,),
              gt_second=(3, 1, 16, 16), geo_d_mean=(6,), geo_d_var=(6,),
              geo_G_mean=(6, 25), geo_G_var=(6,))
VARIANCE_KEYS = ('d_var', 'G_var', 'r_var', 'geo_d_var', 'geo_G_var')
FULL_CONTROLS = dict(monte_carlo_realizations=1000, qt_max_iterations=200,
                     ao_max_iterations=200, rmo_max_iterations=100000,
                     relative_tolerance=1e-4, gradient_tolerance=1e-6,
                     solver_objective_tolerance=1e-5,
                     solver_primal_relative_tolerance=1e-5,
                     qt_bound_tolerance=1e-5, smoothing_initial=1,
                     smoothing_final=0.001, smoothing_max_repeats=50,
                     smoothing_progress_tolerance=1e-8)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def need(predicate, message):
    if not predicate:
        raise ValueError(message)


def save_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def load_saved_fields(path, expected_sha256):
    """Verify and parse exactly the same consumed bytes; do not generate H."""
    import numpy as np
    path = Path(path)
    raw = path.read_bytes()
    need(digest(raw) == expected_sha256.lower(), 'Saved source snapshot digest mismatch')
    if path.suffix.lower() == '.npz':
        with np.load(io.BytesIO(raw), allow_pickle=False) as archive:
            fields = {name: archive[name].copy() for name in archive.files}
        source_format = 'NPZ original field names; source_enabled_mu_RU is separate-stage field'
    elif path.suffix.lower() == '.mat':
        from scipy.io import loadmat
        loaded = loadmat(io.BytesIO(raw), struct_as_record=False, squeeze_me=False)
        need('author_snapshot' in loaded, 'MAT must contain the actual author_snapshot struct')
        cell = loaded['author_snapshot']
        need(isinstance(cell, np.ndarray) and cell.shape == (1, 1), 'One author_snapshot struct required')
        snapshot = cell[0, 0]
        need(hasattr(snapshot, '_fieldnames'), 'Unsupported author_snapshot MAT schema')
        fields = {name: np.array(getattr(snapshot, name), copy=True) for name in snapshot._fieldnames}
        # Native observer wrote this separately; never pretend it belonged to INIT.
        if 'source_enabled_mu_RU' in loaded:
            need('source_enabled_mu_RU' not in fields, 'Ambiguous enabled-stage field')
            fields['source_enabled_mu_RU'] = np.array(loaded['source_enabled_mu_RU'], copy=True)
        source_format = 'MAT v7 author_snapshot plus optional top-level source_enabled_mu_RU'
    else:
        raise ValueError('Only saved NPZ or ordinary MATLAB v7 MAT supported; no replay/generation fallback')
    return fields, dict(filename=path.name, bytes=len(raw), SHA256=digest(raw), format=source_format,
                        identity_scope='Exactly parsed input bytes; no claim of a historical whole-source interval')


def canonical(fields, name, shape, real=False):
    """Only pad trailing MATLAB singleton dimensions; never squeeze/reorder axes."""
    import numpy as np
    need(name in fields, 'Missing saved source field: ' + name)
    a = np.asarray(fields[name])
    need(a.dtype.kind in 'fc' and ((a.dtype.kind == 'f' and a.dtype.itemsize == 8)
                                 or (a.dtype.kind == 'c' and a.dtype.itemsize == 16)),
         'Expected saved double/complex-double field: ' + name)
    padded = a.shape + (1,) * max(0, len(shape) - a.ndim)
    need(padded == tuple(shape), 'Wrong original axes/shape for ' + name + ': ' + str(a.shape))
    a = a.reshape(shape).copy()
    need(bool(np.all(np.isfinite(a))), 'Required literal field is nonfinite: ' + name)
    if real:
        need(not np.iscomplexobj(a) or bool(np.all(a.imag == 0)),
             'Non-real required variance/coefficient field: ' + name)
        a = a.real.copy()
    return a


def scalar(fields, name):
    import numpy as np
    need(name in fields, 'Missing saved source scalar: ' + name)
    a = np.asarray(fields[name])
    need(a.size == 1 and a.dtype.kind in 'fc', 'Expected original numeric scalar: ' + name)
    need(bool(np.all(np.isfinite(a))) and (not np.iscomplexobj(a) or bool(np.all(a.imag == 0))),
         'Nonfinite/non-real source scalar: ' + name)
    return float(a.real.reshape(-1)[0])


def build_channel_data(fields, stage, varsigma=0.01):
    """Return exactly data, power_limit, interference_limit, conversion metadata.

    Source LOS already contains its original conjugate-transpose/ToF choices.
    The source cascade is H_NR diag(H_RU) phi and H_GR diag(H_RU) phi, exactly
    matching current G@(phi*r) and geo_G*(phi*r); no extra conjugation is used.
    """
    import numpy as np
    need(stage in ('enabled', 'init-no-ris'), 'Explicit enabled or init-no-ris stage required')
    need(type(varsigma) in (float, int) and float(varsigma) == 0.01,
         'This first prepared contract is fixed to varsigma=.01; no implicit sweep')
    for name, value in FIXED.items():
        need(scalar(fields, name) == value, 'Wrong original source dimension/linear K: ' + name)
    need(scalar(fields, 'lambda_c') == .025, 'Expected original wavelength .025m')
    beta_n, beta_r, beta_g = (scalar(fields, name) for name in ('beta_N', 'beta_R', 'beta_G'))
    mu_nn = canonical(fields, 'mu_NN', (3, 6), True)
    mu_nr = canonical(fields, 'mu_NR', (3, 6), True)
    mu_ng = canonical(fields, 'mu_NG', (3, 1), True)
    mu_gn = canonical(fields, 'mu_GN', (1, 6), True).reshape(6)
    mu_gr = canonical(fields, 'mu_GR', (1, 6), True).reshape(6)
    ru_name = 'source_enabled_mu_RU' if stage == 'enabled' else 'mu_RU'
    mu_ru = canonical(fields, ru_name, (1, 6), True).reshape(6)
    need(all(bool(np.all(mu >= 0)) for mu in (mu_nn, mu_nr, mu_ng, mu_gn, mu_gr, mu_ru)),
         'Negative literal large-scale coefficient; no sqrt/domain repair')
    need(bool(np.all(mu_ru > 0)) if stage == 'enabled' else bool(np.all(mu_ru == 0)),
         'Selected source stage contradicts its enabled/INIT-zero meaning')
    los_nn = canonical(fields, 'H_NN_LOS', (16, 1, 3, 6))
    los_nr = canonical(fields, 'H_NR_LOS', (16, 25, 3, 6))
    los_ng = canonical(fields, 'H_NG_LOS', (16, 1, 3, 1))
    los_ru = canonical(fields, 'H_RU_LOS', (25, 1, 6))
    los_gn = canonical(fields, 'H_GN_LOS', (1, 6)).reshape(6)
    los_gr = canonical(fields, 'H_GR_LOS', (1, 25, 6))
    data = {name: np.zeros(shape, dtype=np.float64 if name in VARIANCE_KEYS else np.complex128)
            for name, shape in SHAPES.items()}
    for j in range(3):
        for u in range(6):
            # Literal original amplitude order, not sqrt(mu*K/(1+K)).
            data['d_mean'][j, u] = np.sqrt(mu_nn[j, u]) * np.sqrt(beta_n/(beta_n+1)) * los_nn[:, 0, j, u]
            data['d_var'][j, u] = mu_nn[j, u]/(beta_n+1)
            data['G_mean'][j, u] = np.sqrt(mu_nr[j, u]) * np.sqrt(beta_n/(beta_n+1)) * los_nr[:, :, j, u]
            data['G_var'][j, u] = mu_nr[j, u]/(beta_n+1)
        h = los_ng[:, 0, j, 0]
        # INIT538 then544: original Psi expression and explicit Hermitian view.
        psi = (mu_ng[j, 0]/(1+beta_n))*np.eye(16) + (mu_ng[j, 0]*beta_n/(1+beta_n))*np.outer(h, np.conj(h))
        data['gt_second'][j, 0] = (psi + psi.conj().T)/2
    for u in range(6):
        data['r_mean'][u] = np.sqrt(mu_ru[u]) * np.sqrt(beta_r/(beta_r+1)) * los_ru[:, 0, u]
        data['r_var'][u] = mu_ru[u]/(beta_r+1)
        data['geo_d_mean'][u] = np.sqrt(mu_gn[u]) * np.sqrt(beta_g/(beta_g+1)) * los_gn[u]
        data['geo_d_var'][u] = mu_gn[u]/(beta_g+1)
        data['geo_G_mean'][u] = np.sqrt(mu_gr[u]) * np.sqrt(beta_g/(beta_g+1)) * los_gr[0, :, u]
        data['geo_G_var'][u] = mu_gr[u]/(beta_g+1)
    need(all(a.shape == SHAPES[name] and bool(np.all(np.isfinite(a))) for name, a in data.items()),
         'Nonfinite or wrong-shaped converted algorithm field')
    power = np.full(3, 50., dtype=np.float64)
    limit = np.full(1, float(varsigma), dtype=np.float64)
    meta = dict(stage=stage, selected_RU_source_field=ru_name, linear_Rician_K=FIXED.copy(),
                normalization='Satellite long-link mu already divide by kBT; r/mu_RU is dimensionless; receiver offset1. No second noise division, aperture gain or GEO power multiplier.',
                power='P_T50 per satellite, watt-valued constraint',
                interference='varsigma.01, dimensionless noise-normalized INR, not physicalW',
                required_algorithm_fields_finite=True,
                full_original_workspace_finiteness_or_literal_crosslanguage_equality_not_certified=True,
                unused_source_fields='mu_GG/H_GG and captured stochastic H arrays are not consumed by the active exogenous-INR channel interface; their domain/status is not repaired or certified.',
                source_formula_anchors='INIT279-287,342-350,405-412,419-435,458-483,512-518,523-545; enabled S_AO9-16',
                new_RNG_optimizer_MC_MP_or_geometry_calls=0,
                scientific_convergence_original_reference_or_full_paper_PASS=False)
    return data, power, limit, meta


def configuration_for_saved_factory(baseline, fields, stage, input_identity):
    """Keep actual solver/MC controls verbatim; geometry is a saved input only."""
    import numpy as np
    cfg = copy.deepcopy(baseline)
    need(all(k in cfg for k in ('reported', 'tuned_not_reported', 'sweeps', 'multi_vs_single')),
         'A complete existing algorithm configuration is required; no synthesized budget defaults')
    controls = copy.deepcopy(cfg['tuned_not_reported'])
    need(all(controls.get(k) == value for k, value in FULL_CONTROLS.items())
         and controls.get('solver') == 'CLARABEL' and isinstance(controls.get('solver_options'), dict),
         'Preserve complete declared existing controls, not a reduced demonstration')
    noise = (scalar(fields, 'k_b')*scalar(fields, 'B_u'))*scalar(fields, 'T_cs')
    need(noise > 0, 'Nonpositive source kBT')
    cfg['reported'].update(J=3, U=6, N=16, M=25, K=1, power_w=50.,
                           kappa_leo_db=20., kappa_ground_db=0., kappa_geo_db=30.,
                           interference_to_noise_ratio=.01,
                           interference_to_noise_db=float(10*np.log10(.01)),
                           noise_dbm=float(10*np.log10(noise)+30))
    cfg['run_label'] = 'source-literal-U6-fixed-varsigma001-'+stage+'-saved-physical-input-variant'
    cfg['physical_input_variant'] = dict(schema='source-literal-U6-saved-factory-required-v1',
        input_identity=input_identity, stage=stage, dimensions={k: FIXED[k] for k in ('J', 'U', 'N', 'M', 'K')},
        wavelength_m=scalar(fields, 'lambda_c'), source_linear_beta_N=100., source_linear_beta_R=1., source_linear_beta_G=1000.,
        original_kBT_W=noise, source_P_T_GSO=scalar(fields, 'P_T_GSO'),
        requires_explicit_saved_factory=True, legacy_scenario_generator_is_not_an_equivalent_fallback=True,
        retained_baseline_reported_geometry_and_gain_fields_are_not_consumed=True,
        baseline_solver_seed_initial_phase_and_MC_controls_preserved=True,
        author_cached_W_random_phase_initializers_and_MC_population_not_recovered=True,
        algorithm_initialization_scope='Existing corrected framework initialization; not original S_AO W.mat/randomphi trajectory.',
        optimizer_budget_scope='Preserved current reconstruction controls, not newly claimed original author Manopt budgets.',
        figure_scope='Source U6 varsigma variant for Fig4/5 investigation; not the missing finalU2 Fig2/3 power variant.',
        original_reference_or_fullpaper_PASS=False)
    need(cfg['tuned_not_reported'] == controls, 'Solver/MC/initializer controls must remain byte-value equivalent')
    return cfg


def make_saved_scenario_factory(data, power, limit, configuration):
    """Install before recorder.execute captures original.make_scenario.

    This ordinary closure does not load files, generate geometry or draw RNG.
    It accepts only this exact single-base configuration and returns fresh copies
    of the eleven already constructed data arrays and the two limits.
    """
    expected = copy.deepcopy(configuration)
    def make_scenario(scene):
        need(scene == expected, 'Source snapshot factory is fixed to one declared base configuration')
        return {k: v.copy() for k, v in data.items()}, power.copy(), limit.copy()
    return make_scenario


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-fields', type=Path, required=True)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--algorithm-config', type=Path, required=True)
    parser.add_argument('--algorithm-config-sha256', required=True)
    parser.add_argument('--stage', choices=('enabled', 'init-no-ris'), required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--execute-data-conversion', action='store_true')
    args = parser.parse_args()
    need(args.execute_data_conversion, 'Prepared only: explicit --execute-data-conversion required')
    need(not args.output_dir.exists(), 'Preserve prior successful or failed conversion')
    args.output_dir.mkdir(parents=True, exist_ok=False)
    report = dict(schema='actual-saved-author-U6-input-only-conversion-v1', complete=False,
                  stage=args.stage, scientific_acceptance_PASS=False, errors=[],
                  new_RNG_optimizer_MC_MP_or_geometry_calls=0)
    try:
        import numpy as np
        code = Path(__file__).read_bytes()
        fields, identity = load_saved_fields(args.source_fields, args.source_sha256)
        config_bytes = args.algorithm_config.read_bytes()
        need(digest(config_bytes) == args.algorithm_config_sha256.lower(), 'Algorithm config identity mismatch')
        baseline = json.loads(config_bytes)
        data, power, limit, metadata = build_channel_data(fields, args.stage)
        cfg = configuration_for_saved_factory(baseline, fields, args.stage, identity)
        data_file = args.output_dir/'channel-data-and-limits.npz'
        np.savez(data_file, **data, power_limit=power, interference_limit=limit)
        cfg_file = args.output_dir/'configuration-requires-saved-source-factory.json'
        save_json(cfg_file, cfg)
        report.update(complete=True, input=identity, conversion=metadata,
            baseline_configuration=dict(filename=args.algorithm_config.name, bytes=len(config_bytes), SHA256=digest(config_bytes)),
            adapter_SHA256=digest(code), adapter_source_unchanged=code == Path(__file__).read_bytes(),
            output_fields={name: dict(shape=list(a.shape), dtype=str(a.dtype),
                column_major_raw_SHA256=digest(a.tobytes(order='F'))) for name, a in data.items()},
            artifacts={p.name: dict(bytes=p.stat().st_size, SHA256=digest(p.read_bytes())) for p in (data_file, cfg_file)})
        need(report['adapter_source_unchanged'], 'Adapter source changed during conversion')
    except Exception as error:
        report['errors'].append(dict(type=type(error).__name__, message=str(error)))
    save_json(args.output_dir/'actual-input-only-conversion-receipt.json', report)
    print(json.dumps(dict(complete=report['complete'], errors=report['errors'], scientific_acceptance_PASS=False)))
    return 0 if report['complete'] and not report['errors'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
