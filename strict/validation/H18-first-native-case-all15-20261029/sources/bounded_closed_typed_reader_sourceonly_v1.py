"""SOURCE ONLY immutable H18PREFIX1 reader with lazy full raw-component spans.

One event tree at a time; no whole-campaign join or accumulating event list.
Numerical payload IO uses <=1MiB slices. JSON header and recursive per-event
metadata memory are not falsely claimed to be constant. No numerical import.
Actual construction requires the separately reviewed CLOSED-data authority.
"""
from dataclasses import dataclass
from bisect import bisect_right
import hashlib
import json
from pathlib import Path
import struct
import full18_scientific_scope_contract_stdlib_v1 as scope

SCRATCH = 1048576
WIDTH = scope.WIDTH


def need(value, message):
    if value is not True: raise ValueError(message)


def exact_integer(value, label):
    need(type(value) is int and value >= 0, 'Exact nonnegative integer: '+label)
    return value


class MemoryChunks:
    """Explicit synthetic-only source, never a native/data authority."""
    def __init__(self, chunks):
        need(type(chunks) in (tuple, list) and all(type(v) is bytes for v in chunks), 'Inert complete synthetic chunks')
        self.chunks = tuple(chunks);self.ends=[];total=0
        for chunk in self.chunks: total+=len(chunk);self.ends.append(total)
        self.total=total;self.actual_campaign_authority=False
    def slices(self, start, length):
        need(type(start) is int and type(length) is int and start >= 0 and length >= 0
             and start+length <= self.total, 'Entire original byte span')
        index=bisect_right(self.ends,start);offset=self.ends[index-1] if index else 0;stop=start+length
        for ordinal in range(index,len(self.chunks)):
            if offset>=stop:break
            chunk=self.chunks[ordinal];end=self.ends[ordinal]
            lo=max(start,offset);hi=min(stop,end)
            if lo<hi:
                for at in range(lo-offset,hi-offset,SCRATCH):yield chunk[at:min(at+SCRATCH,hi-offset)]
            offset=end


class ClosedChunks:
    """All file IO after ROOT review and a fully closed bound input contract.

    `authority` must be returned by the separate whole18 closed binder; this
    class cannot manufacture the binder's parent/runtime/receipt authority.
    """
    def __init__(self, root_reviewed, authority):
        if root_reviewed is not True: raise ValueError('ROOT full source/CLOSED review before IO')
        need(type(authority) is dict and authority.get('schema') == 'ACTUAL_ROOT_BOUND_CLOSED_FULL18_TYPED_INPUT_V1'
             and authority.get('actual_parent_exit_zero') is True
             and authority.get('actual_full18_storage_and_runtime_closed') is True
             and authority.get('source_runtime_and_all_closed_inputs_B_A_equal') is True,
             'Actual CLOSED parent/source/runtime authority, never future placeholders')
        directory=Path(authority['trace_root']).resolve(strict=True)
        status=authority['complete_stream_status']
        need(status['schema']=='H18_PREFIX_STREAM_STATUS_V1' and status['failed'] is False
             and status['closed'] is True and status['storage_completion_only'] is True
             and status['actual_native_scientific_or_independent_pass'] is False
             and status['physical_population_gate'] is False
             and Path(status['root']).resolve()==directory, 'Exact complete STORAGE-only status')
        total=exact_integer(status['totalbytes'],'total bytes');count=exact_integer(status['chunk'],'chunks')
        events=exact_integer(status['events'],'events');completed=exact_integer(status['completed_event_offset'],'last complete offset')
        need(count>0 and events>0 and status['limit']==8388608 and type(status['limit']) is int
             and status['scratch']==SCRATCH and type(status['scratch']) in (int,float)
             and completed==total-22, 'Original writer sizes and successful terminal geometry')
        self.paths=[];self.ends=[];self.metadata=[];offset=0;previous_event=0;previous_offset=0
        bound=authority['all_closed_trace_files']
        need(type(bound) is dict, 'Entire immutable trace file SHA map')
        for ordinal in range(1,count+1):
            path=directory/f'chunk-{ordinal:012d}.bin';meta_path=Path(str(path)+'.json')
            for item in (path,meta_path):
                need(item.as_posix() in bound and scope.sha(item)==bound[item.as_posix()], 'Every actual CLOSED chunk/meta SHA')
            meta=json.loads(meta_path.read_bytes());size=exact_integer(meta['bytes'],'chunk bytes');offset+=size
            need(meta['schema']=='H18_IMMUTABLE_PREFIX_CHUNK_V1' and type(meta['id']) is int and meta['id']==ordinal
                 and 0<size<=8388608 and (ordinal==count or size==8388608)
                 and path.stat().st_size==size and scope.sha(path)==meta['sha256']
                 and type(meta['global_end_offset']) is int and meta['global_end_offset']==offset,
                 'Every complete source-sized chunk and global endpoint')
            need(meta['chunk_boundary_is_not_necessarily_event_boundary'] is True and meta['no_scientific_certification'] is True,
                 'No event/physics claim inferred from a sealed chunk')
            current_event=exact_integer(meta['last_fully_written_event'],'chunk complete event')
            current_offset=exact_integer(meta['last_completed_event_offset'],'chunk complete event offset')
            need(previous_event<=current_event<=events and previous_offset<=current_offset<=offset, 'Monotonic complete prefix metadata')
            previous_event=current_event;previous_offset=current_offset
            self.paths.append(path);self.ends.append(offset);self.metadata.append(meta)
        complete_path=directory/'complete-stream.json'
        need(complete_path.as_posix() in bound and scope.sha(complete_path)==bound[complete_path.as_posix()]
             and json.loads(complete_path.read_bytes())==status, 'Exact actual closed status bytes')
        wanted={p.name for p in self.paths}|{p.name+'.json' for p in self.paths}|{'complete-stream.json'}
        need({p.name for p in directory.iterdir()}==wanted and {str(Path(p).resolve()) for p in bound}=={str(p.resolve()) for p in self.paths+[Path(str(p)+'.json') for p in self.paths]+[complete_path]},
             'No extra/active/partial/failure/omitted trace authority')
        need(offset==total and previous_event==events and previous_offset==completed
             and type(status['chunkbytes']) is int and status['chunkbytes']==self.paths[-1].stat().st_size,
             'Whole completed trace, not a successful prefix')
        self.total=total;self.status=status;self.actual_campaign_authority=True
    def slices(self,start,length):
        need(type(start) is int and type(length) is int and start>=0 and length>=0 and start+length<=self.total,
             'Entire original raw span in immutable chunks')
        index=bisect_right(self.ends,start);offset=self.ends[index-1] if index else 0;stop=start+length
        for ordinal in range(index,len(self.paths)):
            if offset>=stop:break
            path=self.paths[ordinal];end=self.ends[ordinal]
            lo=max(start,offset);hi=min(stop,end)
            if lo<hi:
                with path.open('rb') as stream:
                    stream.seek(lo-offset);remaining=hi-lo
                    while remaining:
                        block=stream.read(min(remaining,SCRATCH));need(bool(block),'Immutable CLOSED input became short')
                        remaining-=len(block);yield block
            offset=end


@dataclass(frozen=True)
class RawSpan:
    source: object
    offset: int
    length: int
    def slices(self):return self.source.slices(self.offset,self.length)
    def digest(self):
        digest=hashlib.sha256()
        for block in self.slices():digest.update(block)
        return digest.hexdigest()
    def small_bytes(self):
        """Caller intentionally materializes ONE bounded-size original node."""
        need(self.length<=SCRATCH,'Only <=1MiB scalar/small native node materialization')
        return b''.join(self.slices())
    def words(self,cls):
        formats={'double':'d','single':'f','int8':'b','uint8':'B','int16':'h','uint16':'H',
                 'int32':'i','uint32':'I','int64':'q','uint64':'Q','logical':'B','char':'H'}
        need(cls in formats and self.length%WIDTH[cls]==0, 'Original complete class-word sequence')
        tail=b'';width=WIDTH[cls]
        for block in self.slices():
            value=tail+block;count=len(value)//width;end=count*width
            for row in struct.iter_unpack('<'+formats[cls],value[:end]):yield row[0]
            tail=value[end:]
        need(tail==b'','No incomplete original scalar word')


@dataclass(frozen=True)
class Node:
    tag: bytes
    header: dict
    parts: tuple
    global_start: int
    global_end: int
    def scalar_struct(self):
        need(self.tag==b'S' and self.header['size']==[1,1], 'Original scalar struct, not an element squeeze')
        return dict(zip(self.header['fields'],self.parts))
    def struct_elements(self):
        need(self.tag==b'S','Original struct array required');fields=self.header['fields'];count=len(fields)
        for ordinal in range(self.header['numel']):yield dict(zip(fields,self.parts[ordinal*count:(ordinal+1)*count]))
    def numeric(self,cls='double',size=None,real=None):
        need(self.tag==b'N' and self.header['class']==cls, 'Actual full original numeric class')
        if size is not None:need(self.header['size']==list(size),'All native dimensions, no squeeze')
        if real is not None:need(self.header['isreal'] is real,'Actual real/complex flag')
        return self
    def metadata_scalar(self,integer=False):
        self.numeric('double',[1,1],True);value=next(self.parts[0].words('double'))
        need(scope.math.isfinite(value) and (not integer or value==scope.math.trunc(value)), 'Finite scalar metadata identity')
        return int(value) if integer else value
    def text(self):
        need(self.tag==b'H' and len(self.header['size'])==2 and (self.header['size'][0]==1 or self.header['size']==[0,0]),
             'Actual metadata row char or original empty literal')
        return self.parts[0].small_bytes().decode('utf-16le',errors='surrogatepass')
    def boolean(self):
        need(self.tag==b'L' and self.header['size']==[1,1], 'Original scalar logical flag')
        return self.parts[0].small_bytes()==b'\x01'


class Cursor:
    def __init__(self,source):self.source=source;self.offset=0
    def read(self,length):
        exact_integer(length,'metadata length');need(self.offset+length<=self.source.total,'Complete protocol metadata/footer')
        value=b''.join(self.source.slices(self.offset,length));need(len(value)==length,'Complete original metadata read')
        self.offset+=length;return value
    def u64(self):return struct.unpack('<Q',self.read(8))[0]
    def blob(self):return self.read(self.u64())
    def span(self,length):
        exact_integer(length,'numeric component length');need(self.offset+length<=self.source.total,'Whole full raw component within CLOSED stream')
        result=RawSpan(self.source,self.offset,length);self.offset+=length;return result
    def node(self):
        start=self.offset;tag=self.read(1);header=json.loads(self.blob())
        # Use frozen ABI header semantics without allocating raw payloads.
        need(type(header) is dict and header.get('order')=='MATLAB_column_major','Original native order')
        dims=header.get('size');need(type(dims) is list and len(dims)>=2 and all(type(x) is int and x>=0 for x in dims),'Whole typed dimensions')
        count=scope.math.prod(dims);need(type(header.get('numel')) is int and header['numel']==count
            and type(header.get('ndims')) is int and header['ndims']==len(dims),'Exact original numel/ndims')
        cls=header.get('class')
        if tag in (b'N',b'L',b'H'):
            need(cls in WIDTH and ((tag==b'N' and cls not in ('logical','char') and type(header.get('isreal')) is bool)
                 or (tag==b'L' and cls=='logical') or (tag==b'H' and cls=='char')), 'Full numeric/logical/char ABI')
            parts=[self.span(count*WIDTH[cls])]
            if tag==b'N' and not header['isreal']:parts.append(self.span(count*WIDTH[cls]))
            if tag==b'L':need(all(x in (0,1) for x in parts[0].words('logical')), 'Every actual logical byte')
        elif tag in (b'C',b'S'):
            if tag==b'C':need(cls=='cell','Original cell class');children=count
            else:
                fields=header.get('fields');need(cls=='struct' and type(fields) is list and all(type(x) is str for x in fields)
                    and len(set(fields))==len(fields),'Original ordered distinct struct fields');children=count*len(fields)
            parts=[self.node() for _ in range(children)]
        elif tag==b'P':
            nnz=header.get('nnz');need(cls in WIDTH and cls!='char' and type(header.get('isreal')) is bool
                and type(nnz) is int and 0<=nnz<=count,'Sparse original shape/count/class')
            parts=[self.node() for _ in range(3)]
            for index in parts[:2]:index.numeric('double',[nnz,1],True)
            values=parts[2];need(values.tag in (b'N',b'L') and values.header['class']==cls
                and values.header['size']==[nnz,1] and values.header.get('isreal',True) is header['isreal'],'Sparse full original value components')
            last=(0,0)
            for row,col in zip(parts[0].parts[0].words('double'),parts[1].parts[0].words('double')):
                need(scope.math.isfinite(row) and scope.math.isfinite(col) and row==scope.math.trunc(row)
                    and col==scope.math.trunc(col) and 1<=row<=dims[0] and 1<=col<=dims[1], 'Every original sparse find index')
                current=(int(col),int(row));need(current>last,'Complete MATLAB find column-major uniqueness/order');last=current
        else:raise ValueError('Unsupported native tag; no repr/cast fallback')
        return Node(tag,header,tuple(parts),start,self.offset)


def events(source):
    """Yield all complete original events; final generator exhaustion required."""
    cursor=Cursor(source);need(cursor.read(10)==b'H18PREFIX1' and cursor.u64()==1,'Original complete prefix/version')
    ordinal=0;last_end=0;chunk_index=0
    def completion(until,new_event,new_offset):
        nonlocal chunk_index
        if not getattr(source,'actual_campaign_authority',False):return
        while chunk_index<len(source.ends) and source.ends[chunk_index]<=until:
            end=source.ends[chunk_index];meta=source.metadata[chunk_index]
            event,offset=(new_event,new_offset) if end==new_offset else (ordinal,last_end)
            need(meta['last_fully_written_event']==event and meta['last_completed_event_offset']==offset,
                 'Every chunk completion exactly matches independently parsed full-event footer')
            chunk_index+=1
    while True:
        start=cursor.offset;tag=cursor.read(1)
        if tag==b'T':
            need(cursor.u64()==ordinal and cursor.read(13)==b'ENDH18PREFIX1' and cursor.offset==source.total,
                 'Whole actual terminal event census and no trailing bytes')
            completion(cursor.offset,ordinal,last_end)
            if getattr(source,'actual_campaign_authority',False):
                need(source.status['events']==ordinal and source.status['completed_event_offset']==last_end
                     and chunk_index==len(source.metadata),'Entire source status and every chunk metadata verified')
            return
        need(tag==b'E' and cursor.u64()==ordinal+1,'No missing/reordered/duplicate actual event')
        name=cursor.blob().decode('utf-8');node=cursor.node()
        need(cursor.read(1)==b'Z' and cursor.u64()==ordinal+1,'Whole actual event footer before yield')
        completion(cursor.offset,ordinal+1,cursor.offset)
        ordinal+=1;last_end=cursor.offset
        yield dict(ordinal=ordinal,action=name,node=node,global_start=start,global_end=last_end)
