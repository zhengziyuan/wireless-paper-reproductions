"""Prepare local paths for the unchanged saved-input full8 sources.

This only writes plans. It does not launch Python science, MATLAB or a worker.
The recorded evidence is already complete; a fresh rerun is optional and costly.
"""
from pathlib import Path
import argparse, hashlib, json, shutil, sys

CAP = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def put(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository-root', type=Path, required=True)
    parser.add_argument('--work-dir', type=Path, required=True)
    parser.add_argument('--cvx-root', type=Path)
    parser.add_argument('--cvx-prefs', type=Path)
    parser.add_argument('--matlab', default='matlab')
    args = parser.parse_args()
    assert sys.dont_write_bytecode and not sys.flags.optimize, 'Use python -B'
    repo = args.repository_root.resolve(); work = args.work_dir.resolve()
    assert not work.exists(), 'Preserve every previous output; choose a fresh path'
    providers = json.loads((CAP/'implementation/EXACT_ALREADY_PUBLIC_PROVIDER_IDENTITIES.json').read_bytes())['repository_relative_source_SHA256']
    for relative, expected in providers.items():
        assert sha(repo/relative) == expected, relative
    source = repo/'cooperative-corrected-Algorithm3/python-full8'
    import numpy as np
    input_path = CAP/'inputs/canonical-eleven-arrays-and-limits.npz'
    fields = {}
    with np.load(input_path, allow_pickle=False) as saved:
        for name in saved.files:
            if name in ('power_limit', 'interference_limit'):
                continue
            v = saved[name]
            fields[name] = dict(dtype=str(v.dtype), shape=list(v.shape),
                               column_major_raw_SHA256=hashlib.sha256(v.tobytes(order='F')).hexdigest())
    assert len(fields) == 11
    work.mkdir()
    config = CAP/'configuration/reproduction-science-controls-short.json'
    pyentry = CAP/'implementation/python/run_canonical_native_saved_U6_corrected_full8_python_v1.py'
    adapter = CAP/'implementation/python/author_saved_physical_to_channel_data_v1.py'
    observer = CAP/'implementation/python/python_mc_passive_tape_v1.py'
    pins = {str(repo/p): value for p, value in providers.items()}
    for p in (config, input_path, pyentry, adapter, observer, source/'portable_corrected_fresh_full8_v1.py'):
        pins[str(p)] = sha(p)
    plan = dict(configuration=str(config), canonical_data_npz=str(input_path),
                fresh_output_directory=str(work/'python-full8'),
                public_full8_entry=str(source/'portable_corrected_fresh_full8_v1.py'),
                public_full8_source_root=str(source/'sources'),
                saved_factory_adapter=str(adapter), passive_MC_observer=str(observer),
                canonical_output_field_identities=fields, source_and_input_pins=pins)
    pyplan = work/'fresh-python-full8-plan.json'; put(pyplan, plan)
    commands = dict(python=[sys.executable, '-X', 'utf8', '-B', str(pyentry), '--plan', str(pyplan), '--execute'],
                    scope='Fresh optional full8 rerun on the canonical working betaR1 input with original complete reconstruction budgets and new1000 moment-validation draws. Not a saved-state recovery or final betaR10 experiment.',
                    current_preparer_launched_science=False)
    if args.cvx_root is not None or args.cvx_prefs is not None:
        assert args.cvx_root is not None and args.cvx_prefs is not None
        assert (args.cvx_root/'cvx_startup.m').is_file() and args.cvx_prefs.is_file()
        native = repo/'cooperative-corrected-Algorithm3/native'
        nr = CAP/'implementation/native'; output = work/'native-full8'
        (output/'prefs').mkdir(parents=True); (output/'temp').mkdir()
        shutil.copyfile(args.cvx_prefs, output/'prefs/cvx_prefs.mat')
        short = json.loads(config.read_bytes())
        full = CAP/'configuration/original-exact-working-betaR1.json'
        assert sha(full) == '998a1c191e60897eef08fac565b3aeb95fc5e0024572dbb4ba3874feeb44f79d'
        short['original_config_JSON_path'] = str(full)
        short['original_config_JSON_SHA256'] = sha(full)
        nconfig = work/'native-short-config.json'; put(nconfig, short)
        mat = CAP/'inputs/canonical-eleven-arrays-and-limits.mat'
        npins = {str(repo/p): h for p, h in providers.items() if p.startswith('cooperative-corrected-Algorithm3/native/')}
        for p in list(nr.glob('*.m')) + [nconfig, full, mat]:
            npins[str(p)] = sha(p)
        njob = work/'native-full8-job.json'
        put(njob, dict(schema='portable-corrected-native-single-case-job-v1', mode='full8',
                       source_root=str(native), data_dir=str(output), configuration=str(nconfig),
                       canonical_input_MAT=str(mat), passive_MC_source_root=str(nr),
                       cvx_root=str(args.cvx_root.resolve()),
                       source_pins=[dict(path=p, sha256=h) for p, h in npins.items()]))
        expression = "addpath('"+nr.as_posix().replace("'", "''")+"','-begin');portable_native_canonical_U6_full8_entry_v3('"+njob.as_posix().replace("'", "''")+"');"
        commands['native'] = dict(command=[args.matlab, '-sd', str(nr), '-batch', expression],
                                  process_environment=dict(TEMP=str(output/'temp'), TMP=str(output/'temp'), MATLAB_PREFDIR=str(output/'prefs')),
                                  CVX_preferences_SHA256=sha(args.cvx_prefs))
    put(work/'EXACT_OPTIONAL_FRESH_REPRODUCTION_COMMANDS.json', commands)
    print(json.dumps(dict(prepared_commands=str(work/'EXACT_OPTIONAL_FRESH_REPRODUCTION_COMMANDS.json'), launched_science=False)))


if __name__ == '__main__':
    main()
