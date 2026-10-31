"""SOURCE ONLY exact literal-input/precision/source keyed independent kernels.

Top-level STD only. No kernel runs here or in preparation. Cache hits may
reuse an independently computed reference only for every identical complete
operand byte/header/precision/source key. Actual native records are NEVER
replaced; every original event and component still goes through comparison.
"""
import hashlib
import json
import math
from bounded_closed_typed_reader_sourceonly_v1 import Node, need


def canonical_literal(value):
    """Exact config type/float bits; never rounding decimal JSON tokens."""
    if value is None:return ['null']
    if type(value) is bool:return ['bool',value]
    if type(value) is int:return ['int',str(value)]
    if type(value) is float:
        need(math.isfinite(value),'Finite actual source config operand')
        return ['binary64',value.hex()]
    if type(value) is str:return ['text',value]
    if type(value) is list:return ['list',[canonical_literal(v) for v in value]]
    if type(value) is dict:
        need(all(type(key) is str for key in value),'Exact string config field names')
        return ['dict',[[key,canonical_literal(value[key])] for key in sorted(value)]]
    raise ValueError('No repr/source-guess/mutable-object cache key')


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')).hexdigest()


def scope_key(precision,runtime_lineage,formula_lineage,kind):
    need(type(precision) is int and precision in (80,100),'Original independent MP80/100, not a reduced precision')
    need(type(runtime_lineage) is dict and type(formula_lineage) is dict
         and bool(runtime_lineage) and bool(formula_lineage),'Whole actual selected source/runtime/function lineage')
    return dict(kernel=kind,precision_decimal_digits=precision,
                runtime=canonical_literal(runtime_lineage),formulas=canonical_literal(formula_lineage),
                key_is_exact_complete_literal_operand_not_case_or_array_index=True)


def node_key(node):
    need(isinstance(node,Node),'Original lazy typed node only')
    if node.tag in (b'N',b'L',b'H'):
        return [node.tag.decode(),node.header,[[part.length,part.digest()] for part in node.parts]]
    return [node.tag.decode(),node.header,[node_key(child) for child in node.parts]]


def deterministic_geometry_key(config,precision,runtime_lineage,formula_lineage,lane):
    need(lane in ('full_physical_MP_pi','literal_binary64_constants_point'),'Explicit separate constructor diagnostic lineage')
    return digest(dict(scope=scope_key(precision,runtime_lineage,formula_lineage,'complete_deterministic_geometry'),
                       config=canonical_literal(config),constructor_lane=lane))


def literal_row_bits(node,row):
    """All16 logical row words from actual MATLAB column-major raw components.

    This declared metadata/bit-view adapter preserves each word verbatim and
    does not promote/reconstruct floating values or inject a model row. The
    enclosing K dimension is not a mathematical input to an individual Pk.
    """
    node.numeric('double');shape=node.header['size']
    need(len(shape)==2 and shape[1]==16 and type(row) is int and 0<=row<shape[0],
         'Every actual complete16-entry logical NHU row')
    parts=[]
    for part in node.parts:
        words=[]
        for col in range(16):
            offset=part.offset+8*(col*shape[0]+row)
            words.append(b''.join(part.source.slices(offset,8)).hex())
        parts.append(words)
    return dict(original_class='double',declared_logical_row_shape=[1,16],
                original_component_isreal=node.header['isreal'],all16_original_component_words=parts,
                original_column_major_row_view_no_numeric_cast=True)


def projector_row_key(mean_row,variance_row,precision,runtime_lineage,formula_lineage,row=0):
    mean_row.numeric('double');variance_row.numeric('double',real=True)
    need(mean_row.header['size']==variance_row.header['size'],'Same complete NHU mean/variance row population')
    return digest(dict(scope=scope_key(precision,runtime_lineage,formula_lineage,'one_complete_finite_CN_NHU_projector16'),
                       mean=literal_row_bits(mean_row,row),variance=literal_row_bits(variance_row,row),
                       conjugated_mean_original_model=True,interval_splits=['0','0.5','0.9','0.99','1'],
                       transform='t=s/(1-s)',all16x16_entries=True,Hermitian_partners_are_mathematical_not_native_bits=True))


def whole_projector_key(mean,variance,precision,runtime_lineage,formula_lineage):
    need(mean.tag==variance.tag==b'N' and mean.header['class']==variance.header['class']=='double'
         and len(mean.header['size'])==2 and mean.header['size']==variance.header['size']
         and mean.header['size'][1]==16 and 10<=mean.header['size'][0]<=15
         and variance.header['isreal'] is True,'Complete original K10..15 by16 NHU operands')
    return digest(dict(scope=scope_key(precision,runtime_lineage,formula_lineage,'whole_original_NHU_projector_square'),
                       mean=node_key(mean),variance=node_key(variance),
                       ordered_pair_sum='all k!=j',symmetrization='(B+B.H)/2'))


class ExactReferenceCache:
    """Fresh independent-worker local reference cache; never native result injection.

    Capacity is a metadata-memory bound only: once full, compute uncached.
    No precision/source/operand omission, no eviction-dependent science, no
    historical file reuse, no checkpoint sharing and no change to event scope.
    """
    def __init__(self,capacity):
        need(type(capacity) is int and capacity>=0,'Exact nonnegative local kernel cache capacity')
        self.capacity=capacity;self.values={};self.hits=0;self.misses=0;self.uncached=0
    def independent(self,key,compute):
        need(type(key) is str and len(key)==64 and callable(compute),'Exact independent kernel key and reviewed callable')
        if key in self.values:self.hits+=1;return self.values[key]
        self.misses+=1;value=compute()
        if len(self.values)<self.capacity:self.values[key]=value
        else:self.uncached+=1
        return value
    def report(self):
        return dict(hits=self.hits,misses=self.misses,uncached_capacity_fallback=self.uncached,
                    retained_kernel_count=len(self.values),capacity=self.capacity,
                    event_or_component_sampling_or_native_value_replacement=False,
                    native_scientific_speedup_measured_or_forward_certificate=False)
