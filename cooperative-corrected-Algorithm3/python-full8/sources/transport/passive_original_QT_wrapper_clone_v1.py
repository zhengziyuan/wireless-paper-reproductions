"""Frozen passive QT wrapper helpers; no Windows/timing driver import."""
import types


def cell_for(value):
    return (lambda:value).__closure__[0]


def clone_frozen_QT_recording_wrapper(wrapper, replacement_provider):
    """Same code/globals/tape/kind/count cells; change only provider cell."""
    names=wrapper.__code__.co_freevars
    assert names.count('function')==1 and {'count','kind','tape'}<=set(names)
    oldcells=dict(zip(names,wrapper.__closure__ or ()))
    assert oldcells['kind'].cell_contents=='mr_qt_update'
    assert oldcells['count'].cell_contents==8
    cells=tuple(cell_for(replacement_provider) if name=='function' else oldcells[name] for name in names)
    copied=types.FunctionType(wrapper.__code__,wrapper.__globals__,wrapper.__name__,wrapper.__defaults__,cells)
    copied.__kwdefaults__=wrapper.__kwdefaults__
    assert copied.__code__ is wrapper.__code__ and copied.__globals__ is wrapper.__globals__
    for name,cell in zip(names,copied.__closure__):
        assert (cell.cell_contents is replacement_provider) if name=='function' else (cell is oldcells[name])
    return copied,oldcells['tape'].cell_contents,dict(code_filename=wrapper.__code__.co_filename,
        code_first_line=wrapper.__code__.co_firstlineno,freevars=list(names),
        unchanged_cells=[name for name in names if name!='function'],
        replaced_only_function_cell=True,original_provider=str(oldcells['function'].cell_contents),
        new_provider_module=replacement_provider.__module__,new_provider_name=replacement_provider.__name__)
