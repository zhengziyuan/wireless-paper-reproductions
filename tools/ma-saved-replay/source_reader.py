"""Load frozen independent mathematics with explicit Fig6 scope admission.

Only the Figure5->6/kappa100->6 predicates, an import route, and the known
absent optional MC-history assertion are adapted. Original numerical sources,
stops, dimensions and tolerances remain untouched on disk and in equations.
"""
import ast
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys
from types import ModuleType


HERE=Path(__file__).resolve().parent
CONTRACT_FUNCTIONS=('require','sha','retain_nonfinite','fresh_json','population','fixed_gap_tolerance','stops_contract','config_contract')
PRIMITIVE_FILES={
    'audit_full200_matlab_v1.py':'29c42f0a8920d179fd32f81aa47931119b2f890ef3ed4e7ae63be9a4c562707d',
    'audit_full200_coordinate_certificates_v1.py':'d740e6f6cae955f824131886cb8a510e7f478fc40e4f51e5eb5f24b2058c6834',
}
PARTIAL_SHA='7e9eb5623305d62805047548d0cade3f12302929bd333658b5bf6b146391be49'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()


def require(value,message):
    if not value:raise ValueError(message)


def read(path):return json.loads(Path(path).read_bytes())


def transform(raw,edits):
    text=raw.decode();records=[]
    for old,new in edits:
        require(text.count(old)==1,'Exactly one declared source anchor: '+old)
        index=text.index(old);records.append(dict(offset=index,old=old,new=new));text=text[:index]+new+text[index+len(old):]
    restored=text
    for row in reversed(records):
        i=row['offset'];require(restored[i:i+len(row['new'])]==row['new'],'Exact positioned source inverse')
        restored=restored[:i]+row['old']+restored[i+len(row['new']):]
    require(restored.encode()==raw,'Whole original source BYTE inverse')
    require(ast.dump(ast.parse(restored),include_attributes=True)==ast.dump(ast.parse(raw.decode()),include_attributes=True),'Whole positioned AST inverse')
    return text,dict(original_sha256=hashlib.sha256(raw).hexdigest(),virtual_sha256=hashlib.sha256(text.encode()).hexdigest(),
        exact_declared_edits=records,whole_BYTE_and_position_AST_inverse=True,numerical_equations_or_thresholds_changed=False)


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module


def source_paths(repo):
    files=[HERE/'source_reader.py',HERE/'audit_population.py',HERE/'case_archive.py',HERE/'frozen/manifest.json']
    manifest=read(HERE/'frozen/manifest.json')
    for record in manifest['files'].values():
        path=HERE/'frozen'/record['file']
        require(path.parent==HERE/'frozen' and sha(path)==record['sha256'] and path.stat().st_size==record['bytes'],'Exact frozen helper bytes')
        files.append(path)
    partial=repo/'strict/validation/two-timescale-ma-partial-dual-v1/audit_partial_dual_v1.py'
    require(sha(partial)==PARTIAL_SHA,'Whole original history/terminal reader differs');files.append(partial)
    for name,want in PRIMITIVE_FILES.items():
        path=repo/'strict/validation/two-timescale-ma-corrected-zf'/name
        require(sha(path)==want,'Whole independent physical/coordinate source differs');files.append(path)
    return files


def load(repo):
    paths=source_paths(repo);manifest=read(HERE/'frozen/manifest.json')
    def frozen(name):return HERE/'frozen'/manifest['files'][name]['file']
    raw=frozen('closed900_contract_stdlib_v2.py').read_bytes()
    contract,cp=transform(raw,[("plan['figure']==5","plan['figure']==6"),("'Fig5 only, not live Fig6'","'Fig6 only, not Fig5'"),
        ("(6,5,100,2)","(6,5,6,2)"),("'Original full kappa100 dimensions'","'Original full kappa6 dimensions'")])
    tree=ast.parse(contract);selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in CONTRACT_FUNCTIONS]
    require({n.name for n in selected}==set(CONTRACT_FUNCTIONS),'All exact contract functions required')
    c=ModuleType('ma6_saved_contract');c.__dict__.update(hashlib=hashlib,json=json,math=math,struct=struct,Path=Path,POWERS=[9,12,15,18,21,24,27,30,33])
    c.__file__=str(frozen('closed900_contract_stdlib_v2.py'));sys.modules[c.__name__]=c
    exec(compile(ast.Module(body=selected,type_ignores=[]),c.__file__+'::only-declared-functions','exec'),c.__dict__)
    raw=frozen('complete_saved_case_math_v2.py').read_bytes()
    extension,ep=transform(raw,[('import closed900_contract_stdlib_v2 as C','import ma6_saved_contract as C'),
        ('(5,6,5,100,2)','(6,6,5,6,2)'),('Exact Fig5 original full case','Exact Fig6 original full case')])
    e=ModuleType('ma6_saved_complete_state_math');e.__file__=str(frozen('complete_saved_case_math_v2.py'))
    exec(compile(extension,e.__file__+'::declared-Fig6-scope','exec'),e.__dict__)
    partial_path=repo/'strict/validation/two-timescale-ma-partial-dual-v1/audit_partial_dual_v1.py'
    original=load_module('ma6_whole_original_history_terminal',partial_path)
    independent,certificates,_=original.load_primitives()
    adapter_path=frozen('fig05_original_audit_adapter.py')
    namespace=dict(__name__='ma6_original_terminal_adapter',__file__=str(adapter_path))
    exec(compile(adapter_path.read_bytes(),str(adapter_path),'exec'),namespace)
    terminal,tp=namespace['build_terminal_adapter'](partial_path,original)
    proof=dict(scope='Fig6/kappa6 saved-state reader, equations and fixed comparisons retained',
        contract_scope=cp,complete_state_scope=ep,terminal_optional_MC_history=tp,
        selected_generic_contract_function_names=list(CONTRACT_FUNCTIONS),
        old_historical_approval_or_runtime_identity_reused=False)
    return c,original,independent,certificates,e,terminal,proof,paths
