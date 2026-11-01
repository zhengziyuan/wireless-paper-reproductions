"""Render every derived ordinate with its original final-publisher reference."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys

R = Path(__file__).resolve().parent
P = R / 'cooperative-user-supplied-final-PDF-20261018-v1'
O = P / 'Fig12-full-dual192-derived-sumrate-and-unfitted-original-reference-v1'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    assert sys.dont_write_bytecode and sys.flags.optimize == 0
    report = O / 'summary.json'
    data_path = O / 'all192-dual-language-source-bound-sumrates-and-unfitted-source-gaps.json'
    source_path = P / 'published-Fig12-all8-curves-all96-original-vector-reference-values-v1.json'
    watched = {p: sha(p) for p in [report, data_path, source_path]}
    rows = json.loads(data_path.read_bytes())['all192_derived_points']
    source = json.loads(source_path.read_bytes())
    assert len(rows) == 192 and source['actual_all_original_reference_markers'] == 96
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'svg.fonttype': 'none'})
    fig, axes = plt.subplots(2, 2, figsize=(15.6, 11.4), sharex=True, sharey=True)
    colors = {'AP-AO': '#9b2584', 'MR-TTS-TS': '#d64934'}
    plotted = {'original': 0, 'python': 0, 'matlab': 0}
    for ax, (architecture, kappa) in zip(axes.flat, [('MSC', 0), ('MSC', 20), ('SST1.25deg', 0), ('SST1.25deg', 20)]):
        for method in ['AP-AO', 'MR-TTS-TS']:
            original = [c for c in source['curves'] if (c['architecture'], c['kappa_N_dB'], c['method']) == (architecture, kappa, method)]
            assert len(original) == 1
            c = original[0]
            ax.plot(c['threshold_grid_W'], c['original_sum_rate_bpsHz'], color=colors[method], linestyle='-',
                    marker='o', markersize=4.5, markerfacecolor='white', linewidth=1.8, zorder=3)
            plotted['original'] += len(c['original_sum_rate_bpsHz'])
            for language, linestyle in [('python', '--'), ('matlab', ':')]:
                selected = sorted([x for x in rows if (x['architecture'], x['kappa_N_dB'], x['method'], x['language']) ==
                                   (architecture, kappa, method, language)], key=lambda x: x['actual_bank_interference_to_noise_ratio'])
                assert len(selected) == 12
                ax.plot([x['actual_bank_interference_to_noise_ratio'] for x in selected],
                        [x['actual_sum_rate_bpsHz'] for x in selected], color=colors[method],
                        linestyle=linestyle, linewidth=2.0 if language == 'python' else 1.7,
                        marker='x' if language == 'matlab' else None, markersize=3.6, zorder=4)
                plotted[language] += len(selected)
        title = 'Multi-satellite (J=3, N=16)' if architecture == 'MSC' else 'Single satellite (J=1, N=48, 1.25 deg)'
        ax.set_title(title + '\n' + r'$\kappa_N$ = ' + str(kappa) + ' dB', pad=9)
        ax.set_xlim(.008, .122)
        ax.set_ylim(0, max(24.5, max(x['actual_sum_rate_bpsHz'] for x in rows) * 1.06))
        ax.set_xticks([.01, .02, .04, .06, .08, .10, .12])
        ax.grid(alpha=.25)
        ax.set_xlabel('Numeric threshold (unit mapping unresolved)', labelpad=6)
        ax.set_ylabel('Sum achievable rate (bit/s/Hz)', labelpad=6)
    assert plotted == dict(original=96, python=96, matlab=96)
    fig.suptitle('Final Fig.12: complete saved states versus published vectors', y=.976, fontsize=19)
    fig.text(.5, .934, '4 scenes x 12 thresholds x 2 methods; 96 published points and 192 derived language points',
             ha='center', fontsize=12)
    legend = []
    for method in ['AP-AO', 'MR-TTS-TS']:
        for label, linestyle, marker in [('Published vector', '-', 'o'), ('Python saved state', '--', None), ('MATLAB saved state', ':', 'x')]:
            legend.append(Line2D([], [], label=method + ' / ' + label, color=colors[method], linestyle=linestyle,
                                 marker=marker, markerfacecolor='white', markersize=4, linewidth=1.8))
    fig.legend(handles=legend, loc='lower center', bbox_to_anchor=(.5, .116), ncol=3, fontsize=10.5,
               columnspacing=1.8, handlelength=3.1)
    fig.text(.05, .089, 'Threshold labels differ: paper uses W; completed input banks use I/N. Shared numeric ticks disclose this unresolved mapping.', fontsize=10.5)
    fig.text(.05, .064, r'Rates use $\sum_u \log_2(1+\gamma_u)$ from all required saved MP100 states; MP80 cross-check passed. No fitting or optimizer rerun.', fontsize=10.5)
    fig.text(.05, .038, 'Original-reference agreement remains unverified. Configured 1000 draws validate channel moments, not optimized-performance averages.', fontsize=10.5)
    fig.subplots_adjust(left=.07, right=.985, top=.88, bottom=.245, hspace=.37, wspace=.16)
    outputs = {}
    for extension in ['png', 'svg']:
        path = O / ('Fig12-all192-derived-and-all96-published-unfitted-diagnostic.' + extension)
        assert not path.exists()
        fig.savefig(path, dpi=150, facecolor='white')
        outputs[str(path)] = sha(path)
    plt.close(fig)
    assert all(sha(p) == h for p, h in watched.items())
    receipt = dict(observed_local=datetime.now().astimezone().isoformat(),
                   actual_plotted_point_counts=plotted, actual_all4_scenes_all8_source_curves_visible=True,
                   source_before={str(p): h for p, h in watched.items()}, source_after={str(p): sha(p) for p in watched},
                   outputs=outputs, actual_full_image_visual_QA_pending=True,
                   plot_does_not_certify_reference_agreement_or_full_paper=True,
                   writer=dict(path=str(Path(__file__)), SHA256=sha(Path(__file__))))
    with (O / 'plot-generation-summary.json').open('x', encoding='utf-8', newline='\n') as f:
        json.dump(receipt, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps(dict(actual_plotted_points=plotted, outputs=outputs)))


if __name__ == '__main__':
    main()
