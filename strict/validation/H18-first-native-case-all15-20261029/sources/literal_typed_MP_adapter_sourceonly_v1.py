"""SOURCE ONLY exact binary64 promotion and full MATLAB logical-index views.

No MP/NumPy/native import or call at import/preparation. A separately bound
future MP80/100 caller is supplied explicitly. RawSpan bytes remain the input
authority: finite binary64 values are promoted by integer ratio, not JSON or
decimal text, and a native complex zero-imaginary component is not erased from
the input identity. Signed-zero is preserved in raw provenance, although the
mathematical MP field cannot distinguish its two signs.
"""
import math
import struct
from bounded_closed_typed_reader_sourceonly_v1 import Node, need


def flat_binary64(node):
    node.numeric('double')
    real=node.parts[0].words('double')
    if node.header['isreal']:
        for value in real:
            need(math.isfinite(value),'Nonfinite actual science operand retained as failure, never repaired')
            yield value
    else:
        for a,b in zip(real,node.parts[1].words('double')):
            need(math.isfinite(a) and math.isfinite(b),'Nonfinite actual complex science operand retained as failure')
            yield complex(a,b)


def exact_number(mp,value):
    if type(value) is complex:return mp.mpc(exact_number(mp,value.real),exact_number(mp,value.imag))
    if type(value) is int:return mp.mpf(value)
    need(type(value) is float and math.isfinite(value),'Only finite literal binary64/int promotion')
    numerator,denominator=value.as_integer_ratio()
    return mp.mpf(numerator)/denominator


def values(mp,node,size=None,real=None):
    node.numeric('double',size,real)
    return [exact_number(mp,value) for value in flat_binary64(node)]


def scalar(mp,node):
    return values(mp,node,[1,1],True)[0]


def vector(mp,node,count):
    node.numeric('double')
    need(node.header['size'] in ([1,count],[count,1]),'Complete original row/column vector, no squeeze')
    return values(mp,node)


def matrix(mp,node,rows,cols):
    raw=values(mp,node,[rows,cols]);out=mp.matrix(rows,cols)
    for col in range(cols):
        for row in range(rows):out[row,col]=raw[col*rows+row]
    return out


def tensor_slices(mp,node,count,rows,cols):
    # MATLAB Q/Psi native leading user dimension: (u,n,j), not (n,j,u).
    raw=values(mp,node,[count,rows,cols]);out=[mp.matrix(rows,cols) for _ in range(count)]
    for col in range(cols):
        for row in range(rows):
            for user in range(count):out[user][row,col]=raw[user+count*(row+rows*col)]
    return out


def cell_matrices(mp,node,count,rows,cols):
    need(node.tag==b'C' and node.header['size']==[1,count] and len(node.parts)==count,
         'Every complete native factor cell in original row order')
    return [matrix(mp,value,rows,cols) for value in node.parts]


def mean_inputs(mp,node,U):
    source=node.scalar_struct()
    names=('direct_mean','direct_variance','matrix_mean','matrix_variance',
           'ground_mean','ground_variance','nhu_mean','nhu_variance')
    need(set(source)==set(names),'Every original mean/variance input, no reduced physical model')
    result={}
    for name in names:
        rows,cols=(U,16) if name.startswith('direct_') else (25,16) if name.startswith('matrix_') else (U,25) if name.startswith('ground_') else (16-U,16)
        if name.endswith('_variance'):source[name].numeric('double',[rows,cols],True)
        result[name]=matrix(mp,source[name],rows,cols)
        if name.endswith('_variance'):need(all(value>=0 for value in result[name]),'Original nonnegative full physical variances')
    return result


def flatten_matrix(matrix_value):
    return [matrix_value[row,col] for col in range(matrix_value.cols) for row in range(matrix_value.rows)]


def flatten_slices(slices):
    need(bool(slices),'Whole nonempty native user tensor')
    return [value[row,col] for col in range(slices[0].cols) for row in range(slices[0].rows) for value in slices]


def typed_config(node):
    """Metadata-only config adapter: raw floats, exact original field types.

    A scalar numerical MATLAB config is double even when integer-valued;
    integer dimensions are validated/canonicalized by the original fixed
    contract at its explicitly named boundary, not globally cast to integers.
    """
    if node.tag==b'S':return {key:typed_config(value) for key,value in node.scalar_struct().items()}
    if node.tag==b'H':return node.text()
    if node.tag==b'L':
        need(node.header['size']==[1,1],'Original scalar config logical');return node.boolean()
    if node.tag==b'C':return [typed_config(value) for value in node.parts]
    node.numeric('double',real=True);out=list(flat_binary64(node))
    if node.header['size']==[1,1]:return out[0]
    need(len(node.header['size'])==2 and 1 in node.header['size'],'Original config vector, no arbitrary matrix flatten')
    return out


def physical_config(node):
    result=typed_config(node)
    for key in ('N','J','U','K','M'):
        value=result['reported'][key]
        need(type(value) is float and value==math.trunc(value),'Actual full integer-valued native model dimension')
        result['reported'][key]=int(value)
    return result


def bit_identity(a,b):
    """Whole native numeric/cell/struct identity, not approximate math equality."""
    if a.tag!=b.tag or a.header!=b.header:return False
    if a.tag in (b'N',b'L',b'H'):
        return len(a.parts)==len(b.parts) and all(x.length==y.length and x.digest()==y.digest() for x,y in zip(a.parts,b.parts))
    return len(a.parts)==len(b.parts) and all(bit_identity(x,y) for x,y in zip(a.parts,b.parts))


def raw_complex_words(node):
    """STD synthetic transport controls only, no model arithmetic."""
    node.numeric('double')
    return [tuple(struct.pack('<d',word).hex() for word in part.words('double')) for part in node.parts]
