"""Chapter3 Fig9 scalar-aperture contract with frozen subpanel centers.

The author says at fixed M the microelement count changes ONLY aperture gain.
There is no need to invent an integer row/column factorization. Generate the
declared reference28000-element geometry once and scale both RIS link fields
by sqrt(n/28000). Their variances scale by n/28000; the shared-G cascade field
scales by n/28000. This does not recover unreported author center coordinates.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
PACKAGE=HERE/'hotspot-satcom'
sys.path.insert(0,str(PACKAGE))
from scenario_geometry import sample_scenario

REFERENCE_COUNT=28000
SOURCE_COUNTS=list(range(4000,28001,4000))


def scale_reference(reference,count):
    if count not in SOURCE_COUNTS:raise ValueError('Exact original4000:4000:28000 count grid required')
    result=copy.deepcopy(reference);ratio=count/REFERENCE_COUNT;field=np.sqrt(ratio)
    result['cascade']=reference['cascade']*ratio
    moments=result['mean_inputs'];original=reference['mean_inputs']
    for name in ('matrix_mean','ground_mean'):moments[name]=original[name]*field
    for name in ('matrix_variance','ground_variance'):moments[name]=original[name]*ratio
    result['aperture_count_contract']={'elements_per_subsurface':count,'reference_elements_per_subsurface':REFERENCE_COUNT,
        'fixed_subpanel_centers':True,'ground_phase_changed_by_count':False,'RIS_phase_dimension':25,
        'two_link_field_multiplier':float(field),'cascade_field_multiplier':ratio,
        'row_column_factorization_inferred':False,'original_author_geometry_recovered':False}
    return result


def sample_count_scenario(config,rng):
    count=config['reported']['subsurface_element_count']
    if config['reported']['M']!=25:raise ValueError('Original25 phase-controlled subsurfaces required')
    reference=copy.deepcopy(config)
    reference['reported']['subsurface_elements']=[200,140]
    return scale_reference(sample_scenario(reference,rng),count)


def full_count_configuration(config):
    result=copy.deepcopy(config)
    if result['tuned_not_reported'].get('hu_cluster_radius_m')!=10:
        raise ValueError('Declared source-compliant radius10m geometry required; old radius15 violates pairwise10-20m')
    if result['tuned_not_reported']['monte_carlo_realizations']!=1000:
        raise ValueError('Full configured1000 optimizations per source count required')
    if result['reported']['N']!=16 or result['reported']['J']!=16 or result['reported']['M']!=25:
        raise ValueError('All original16 feeds/16 streams/25 subsurfaces required')
    result['reported'].update(U=6,K=10,kappa_satellite_db=12,subsurface_element_count=REFERENCE_COUNT)
    result['sweeps']=[{'id':'element_count','parameter':'subsurface_element_count','values':SOURCE_COUNTS,
                       'U':6,'kappa_satellite_db':12}]
    result['element_count_contract']={'source':'author_thesis Chapter3 Section3.6 Fig3-9 count changes ONLY aperture gain at fixed M',
        'reference_subpanel_centers':'unchanged declared numerical geometry at200x140 reference',
        'centers_are_unreported_numerical_choices':True,'original_author_geometry_recovered':False,
        'count_changes_centers_or_phase':False,'factorization_needed':False,'reference_ordinates_used':False}
    return result


def run_full(config,output,checkpoint_dir):
    # The original exact QT/SDR/RGD chains stay unchanged. Only the source count
    # scenario contract is injected, and its executed bytes enter every receipt.
    import run as instant
    original_sample=instant.sample_scenario
    original_hashes=instant.source_hashes
    wrapper=Path(__file__).resolve()
    def bound_hashes(files):
        hashes=original_hashes(files)
        hashes[str(wrapper)]=hashlib.sha256(wrapper.read_bytes()).hexdigest()
        geometry=PACKAGE/'scenario_geometry.py'
        hashes[str(geometry)]=hashlib.sha256(geometry.read_bytes()).hexdigest()
        return hashes
    configuration=full_count_configuration(config)
    instant.sample_scenario=sample_count_scenario;instant.source_hashes=bound_hashes
    try:result=instant.full_run(configuration,'element_count',checkpoint_dir=checkpoint_dir)
    finally:instant.sample_scenario=original_sample;instant.source_hashes=original_hashes
    result['configuration']=configuration;result['source_element_count_contract']=configuration['element_count_contract']
    result['geometry_contract']=configuration['geometry_contract'];result['historical_author_coordinates_recovered']=False
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,allow_nan=False,default=instant.numerical_json)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=PACKAGE/'instantaneous_geometry_config.json')
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--checkpoint-dir',type=Path,required=True)
    args=parser.parse_args();run_full(json.loads(args.config.read_text(encoding='utf-8-sig')),args.output,args.checkpoint_dir)
