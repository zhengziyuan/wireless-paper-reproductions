"""Recheck the complete MA6 source/closed-return comparison and geometry SD/SE.

This command verifies two compact evidence packets, all4500 aggregate rows and
all45 source ordinates per language. It does not recreate900 optimization jobs,
their absent4.5million RAW samples, or the full independent mathematical audit.
"""
import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from compare_closed_curve_reference import run as compare


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(args):
    if args.output_dir.exists():
        raise FileExistsError('Use a fresh source-comparison replay directory')
    m=json.loads((args.packet/'manifest.json').read_bytes())
    for name,spec in m['files'].items():
        if Path(name).name!=name or ':' in name or '\\' in name:
            raise ValueError('Unsafe evidence member')
        p=args.packet/name
        if p.stat().st_size!=spec['bytes'] or sha(p)!=spec['sha256']:
            raise ValueError('Source comparison evidence changed: '+name)
    actual=compare(SimpleNamespace(closed_packet=args.closed_packet,
        reference=args.packet/'original-figure6-vector-reference.json',source_eps=None,output_dir=args.output_dir))
    previous=json.loads((args.packet/'actual-all45-original-reference-comparison.json').read_bytes())
    for key in ('comparisons','summaries','all_same_grid_scheme_orderings',
                'source_figure_additional_non9dBm_MA_ZF_ranking_exceptions'):
        if actual[key]!=previous[key]:
            raise ValueError('Fresh source/return/variability calculation differs: '+key)
    if actual['source_figure_additional_non9dBm_MA_ZF_ranking_exceptions']!=[12]:
        raise ValueError('Supplied R2 source-ordering qualification differs')
    csv_name='all90-source-comparisons-and-geometry-variability.csv'
    if (args.packet/csv_name).read_bytes()!=(args.output_dir/csv_name).read_bytes():
        raise ValueError('Complete paired source/variability table differs')
    summary=dict(actual_reference_packet_payloads_verified=len(m['files']),
        closed900_packet_payloads_also_verified=8,actual_complete_geometry_scheme_rows_replayed=4500,
        complete_source_points_compared_per_language=45,all90_reference_and_geometry_SD_SE_rows_exactly_replayed=True,
        supplied_R2_source_extra_non9dBm_ordering_exception=[12],maximum_absolute_source_gap=actual['maximum_absolute_gap'],
        original_author_EPS_or_TeX_bytes_repeated_by_this_compact_reader=False,
        full900_RAW_physics_coordinate_FPA_KKT_or_original_reference_or_paper_pass=False,
        optimizer_or_RNG_calls=0,replayer_SHA256=sha(Path(__file__)))
    (args.output_dir/'public-replay-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary),flush=True)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--packet',type=Path,required=True)
    p.add_argument('--closed-packet',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    run(p.parse_args())
