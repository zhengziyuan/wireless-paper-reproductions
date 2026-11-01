"""Exact source AST extraction of the existing saved-MAT shape helpers only."""
import numpy as np

def sequence(x):
    if isinstance(x,dict):return [x]
    if isinstance(x,(list,tuple)):return list(x)
    return list(np.asarray(x,dtype=object).reshape(-1))

def channel_data(raw,J,U,N,M):
    K=np.asarray(raw['gt_second']).size//(J*N*N)
    shapes=dict(d_mean=(J,U,N),d_var=(J,U),G_mean=(J,U,N,M),G_var=(J,U),r_mean=(U,M),r_var=(U,),
        gt_second=(J,K,N,N),geo_d_mean=(U,),geo_d_var=(U,),geo_G_mean=(U,M),geo_G_var=(U,))
    return {key:np.asarray(raw[key]).reshape(shape) for key,shape in shapes.items()}
