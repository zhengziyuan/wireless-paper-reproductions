"""Generate a shared full-dimension count-only component fixture and receipt."""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.io import savemat
from hotspot_element_count import HERE,PACKAGE,SOURCE_COUNTS,sample_scenario,scale_reference

if __name__=='__main__':
    folder=HERE/'outputs'/'hotspot-count-contract';folder.mkdir(parents=True,exist_ok=True)
    config=json.loads((PACKAGE/'instantaneous_geometry_config.json').read_text(encoding='utf-8-sig'))
    reference=sample_scenario(config,np.random.default_rng(3309957))
    expected=np.empty(len(SOURCE_COUNTS),object)
    for i,count in enumerate(SOURCE_COUNTS):expected[i]=scale_reference(reference,count)
    fixture=folder/'full-dimension-count-fixture.mat'
    savemat(fixture,{'reference':reference,'counts':np.asarray(SOURCE_COUNTS),'expected':expected},long_field_names=True)
    evidence={'scope':'full_dimension_count_only_gain_component_NOT7000_optimization_runs',
        'dimensions':{'N':16,'J':16,'U':6,'K':10,'M':25},'all_source_counts':SOURCE_COUNTS,
        'reference_count':28000,'source_microelement_row_column_counts_inferred':False,
        'author_subpanel_centers_recovered':False,'shared_fixture_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),
        'geometry_contract':config['geometry_contract'],
        'scenario_geometry_source_sha256':hashlib.sha256((PACKAGE/'scenario_geometry.py').read_bytes()).hexdigest(),
        'implementation_sha256':hashlib.sha256((HERE/'hotspot_element_count.py').read_bytes()).hexdigest(),
        'full_reproduction_pass':False}
    (folder/'component-python.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(evidence))
