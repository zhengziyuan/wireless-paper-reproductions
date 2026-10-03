"""Source-qualified table parameters, not a full model/figure certificate.

This portable replay does not possess or redistribute private author TeX. Its
source provenance is the retained actual local source-read receipt; this replay
checks the byte-bound canonical public configurations and the recorded mappings.
No optimizer, channel generator or production solver is imported.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def check_parameters(tables,coop,hot):
    records=[]
    for table in tables:
        values=coop if table['paper']=='cooperative-satcom' else hot
        for row in table['parameter_rows']:
            checks=[]
            for b in row['bindings']:
                key=b['config_key'];checks.append({'key':key,'unit':b['unit'],
                    'expected':b['expected_SI_or_declared_value'],'observed':values.get(key),
                    'passed':values.get(key)==b['expected_SI_or_declared_value']})
            records.append({'paper':table['paper'],'parameter_id':row['parameter_id'],
                'source_line':row['source_line'],'has_numeric_parameter_binding':bool(checks),
                'checks':checks,'machine_bindings_pass':all(x['passed'] for x in checks),
                'pattern_or_realized_geometry_certified':False})
    return records

def run():
    provenance=load(HERE/'source-evidence-bindings-v1.json')
    source_receipt=HERE/'actual-source-table-read-and-mapping-v1.json'
    assert sha(source_receipt)==provenance['actual_source_read_receipt_sha256']
    tables=load(source_receipt)['tables']
    contract=load(HERE/'canonical-parameter-contract-v1.json')
    assert contract['author_source_hashes']=={t['paper']:t['source']['source_sha256'] for t in tables}
    assert all(not t['source']['private_source_body_redistributed'] for t in tables)
    paths={relative:REPO/relative for relative in contract['canonical_file_sha256']}
    before={r:sha(p) for r,p in paths.items()}
    assert before==contract['canonical_file_sha256'],'Canonical source/configuration changed; not a current table replay'
    coop=load(paths['strict/cooperative-satcom/spectral_config.json'])['reported']
    hot=copy.deepcopy(load(paths['strict/hotspot-satcom/instantaneous_geometry_config.json'])['reported'])
    # These values are byte-bound literal source runner overrides. The base
    # instantaneous default3dB/0dB is not mistaken for the statistical branch.
    py=paths['strict/hotspot-satcom/run_statistical_validated.py'].read_text(encoding='utf-8-sig')
    mat=paths['strict/hotspot-satcom/run_strict_hotspot_statistical_validated.m'].read_text(encoding='utf-8-sig')
    assert 'kappa_ground_db=20,nhu_statistical_sinr_db=-3' in py
    assert 'kappa_ground_db=20' in mat and 'nhu_statistical_sinr_db=-3' in mat
    hot.update(kappa_ground_statistical_db=20,nhu_statistical_sinr_db=-3)
    rows=check_parameters(tables,coop,hot)
    assert len(rows)==36 and sum(r['has_numeric_parameter_binding'] for r in rows)==34
    assert all(r['machine_bindings_pass'] for r in rows)
    negatives=[]
    for label,paper,key,value in [
        ('unconverted_GEO_kW','cooperative-satcom','geo_power_w',2),
        ('unconverted_LEO_km','cooperative-satcom','leo_height_m',550),
        ('wrong_cooperative_ground_Rician','cooperative-satcom','kappa_ground_db',20),
        ('instantaneous_negative3','hotspot-satcom','nhu_sinr_db',-3),
        ('statistical_positive3','hotspot-satcom','nhu_statistical_sinr_db',3),
        ('statistical_zero_ground_Rician','hotspot-satcom','kappa_ground_statistical_db',0),
        ('wrong_hotspot_element_counts','hotspot-satcom','subsurface_elements',[100,100]),
        ('wrong_hotspot_common_amplitude_distance','hotspot-satcom','ris_hu_distance_m',410),
        ('missing_source_pairwise_spacing_interval','hotspot-satcom','hu_spacing_m_range',None),
    ]:
        c,h=copy.deepcopy(coop),copy.deepcopy(hot)
        (c if paper=='cooperative-satcom' else h)[key]=value
        rejected=not all(r['machine_bindings_pass'] for r in check_parameters(tables,c,h));assert rejected
        negatives.append({'control':label,'rejected':True})
    after={r:sha(p) for r,p in paths.items()};assert before==after
    return {'scope':'Fresh portable canonical-byte/parameter replay of two retained author-table mappings; no optimizer or new private-source access',
        'actual_source_read_receipt_sha256':sha(source_receipt),
        'author_source_hashes':contract['author_source_hashes'],
        'canonical_source_and_configurations_before':before,'canonical_source_and_configurations_after':after,
        'all_canonical_bytes_match_recorded_source_evidence':True,'all36_row_mappings_checked':True,
        'all34_numeric_parameter_rows_match':True,'two_external_pattern_reference_rows_are_not_certified':True,
        'all_pairwise_realized_geometry_checks_performed':False,'full_figure_optimization_performed':False,
        'final_publisher_table_equivalence_verified':False,'rows':rows,'negative_controls':negatives}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path)
    args=parser.parse_args();result=run()
    if args.output:
        assert not args.output.exists(),'Preserve old receipts; choose a fresh output path'
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'rows':36,'numeric_rows':34,'negative_controls':9,'canonical_bytes_unchanged':True,
        'full_figure_or_final_publisher_certificate':False}))

if __name__=='__main__':main()
