"""Read-only decoder for this frozen recording-v4 MAT-v7.3 schema.

No MATLAB code is executed. Numeric dimensions are returned in MATLAB order;
cells and struct arrays are traversed in MATLAB column-major element order.
This is not a general MATLAB object/deserialization engine: unsupported classes,
external links, sparse arrays and cycles fail closed. Actual native proof requires
the actual native output, not the synthetic decoder test.
"""
from pathlib import Path
import sys
import numpy as np

DEPENDENCY_DIRECTORY = Path(__file__).resolve().parents[1] / 'mat73-audit-deps'
sys.path.insert(0, str(DEPENDENCY_DIRECTORY))
import h5py


def class_name(node):
    value = node.attrs.get('MATLAB_class', b'')
    if isinstance(value, bytes):
        return value.decode('ascii')
    if isinstance(value, str):
        return value
    if isinstance(value, np.ndarray) and value.size == 1:
        return class_name_from_value(value.item())
    raise ValueError(f'Unsupported MATLAB_class metadata at {node.name}')


def class_name_from_value(value):
    return value.decode('ascii') if isinstance(value, bytes) else str(value)


def matlab_axes(array):
    return np.transpose(array, tuple(reversed(range(array.ndim))))


class Reader:
    def __init__(self, path):
        self.file = h5py.File(Path(path), 'r')
        self.cache = {}
        self.active = set()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.file.close()

    def child(self, group, name):
        link = group.get(name, getlink=True)
        if not isinstance(link, h5py.HardLink):
            raise ValueError(f'Non-hard HDF5 link rejected: {group.name}/{name}')
        return group[name]

    def read(self, obj):
        if isinstance(obj, str):
            obj = self.child(self.file, obj)
        if isinstance(obj, h5py.Reference):
            if not obj:
                raise ValueError('Null MATLAB object reference rejected')
            obj = self.file[obj]
        name = obj.name
        if name in self.cache:
            return self.cache[name]
        if name in self.active:
            raise ValueError(f'Cyclic MATLAB object graph rejected: {name}')
        self.active.add(name)
        try:
            value = self._read(obj)
            self.cache[name] = value
            return value
        finally:
            self.active.remove(name)

    def _read(self, obj):
        kind = class_name(obj)
        if isinstance(obj, h5py.Group):
            if kind not in ('', 'struct') or 'MATLAB_sparse' in obj.attrs:
                raise ValueError(f'Unsupported MATLAB group class {kind}: {obj.name}')
            names = list(obj.keys())
            if kind != 'struct':
                return {name: self.read(self.child(obj, name)) for name in names}
            fields = {}
            struct_size = None
            for name in names:
                field = self.child(obj, name)
                if isinstance(field, h5py.Dataset) and h5py.check_dtype(ref=field.dtype) and class_name(field) == '':
                    refs = matlab_axes(field[()]).ravel(order='F')
                    values = [self.read(ref) for ref in refs]
                    if struct_size is None:
                        struct_size = len(values)
                    if len(values) != struct_size:
                        raise ValueError(f'Struct field element count mismatch at {obj.name}')
                    fields[name] = values
                else:
                    # Scalar structs may encode fields directly, rather than refs.
                    if struct_size not in (None, 1):
                        raise ValueError('Direct fields only supported for scalar struct')
                    struct_size = 1
                    fields[name] = [self.read(field)]
            if struct_size is None:
                return {}
            values = [{name: fields[name][i] for name in names} for i in range(struct_size)]
            return values[0] if struct_size == 1 else values
        if h5py.check_dtype(ref=obj.dtype):
            if kind not in ('', 'cell'):
                raise ValueError(f'Unsupported referenced dataset class {kind}')
            return [self.read(ref) for ref in matlab_axes(obj[()]).ravel(order='F')]
        if int(np.asarray(obj.attrs.get('MATLAB_empty', 0)).item()) == 1:
            shape = tuple(int(x) for x in np.asarray(obj[()]).ravel())
            if not shape or any(x < 0 for x in shape):
                raise ValueError('Invalid empty MATLAB shape')
            return np.empty(shape, dtype=bool if kind == 'logical' else float)
        array = obj[()]
        if obj.dtype.names:
            if set(obj.dtype.names) != {'real', 'imag'}:
                raise ValueError(f'Unsupported compound MATLAB dtype {obj.dtype}')
            array = array['real'] + 1j * array['imag']
        array = matlab_axes(np.asarray(array))
        if kind == 'char':
            if array.ndim != 2 or min(array.shape) > 1:
                raise ValueError('Only single MATLAB char row/column supported')
            return bytes(np.asarray(array.ravel(order='F'), dtype='<u2')).decode('utf-16le')
        if kind == 'logical':
            array = array.astype(bool)
        elif kind not in ('double', 'single', 'int8', 'uint8', 'int16', 'uint16',
                          'int32', 'uint32', 'int64', 'uint64', ''):
            raise ValueError(f'Unsupported MATLAB numeric class {kind}')
        return array.item() if array.size == 1 else array


def read(path, names):
    with Reader(path) as reader:
        return {name: reader.read(name) for name in names}


def dependency_metadata():
    return {'h5py': h5py.__version__, 'HDF5': h5py.version.hdf5_version,
            'numpy': np.__version__, 'read_only_mode': 'r',
            'dependency_scope': 'WORK isolated h5py wheel --no-deps; existing repro-venv NumPy',
            'official_reference_documentation': ['https://docs.h5py.org/en/stable/refs.html',
                'https://docs.h5py.org/en/stable/high/dataset.html']}

