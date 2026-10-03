"""Exact finite-grid exhaustive search, with spacing pruning and no hidden cap.

There is no hidden sample cap. D=12,N=6 remains very expensive; never launch
this automatically in a component test. Statistical objectives are invariant to
antenna permutation only for the exact statistical surrogate. The default
complete finite-MC objective is not invariant to permuting a fixed NLoS sample
array, so every ordered geometry is evaluated; there is no symmetry reduction.
"""
import time
import numpy as np
from core import mrt_statistics,zf_statistics,instantaneous


def exhaustive(c,n,D,mode,nlos):
    grid=np.array([[x,y] for x in np.linspace(c["region_lower"][0],c["region_upper"][0],D)
                   for y in np.linspace(c["region_lower"][1],c["region_upper"][1],D)])
    best=-np.inf;winner=None;tested=0;pruned=0;start=time.perf_counter()
    actual_MC=c["brute_force_objective"]=="instantaneous_MC"
    def visit(indices,start_index):
        nonlocal best,winner,tested,pruned
        if len(indices)==n:
            t=grid[indices]
            if actual_MC:value=instantaneous(t,c,nlos,mode)["mean_sum_rate"]
            elif c["brute_force_objective"]=="paper_statistical_design_objective":value=mrt_statistics(t,c)[0] if mode=="MRT" else zf_statistics(t,c)[0]
            else:raise ValueError("Explicit brute-force objective protocol required.")
            tested+=1
            if value>best:best=value;winner=t.copy()
            return
        remaining=n-len(indices)
        point_range=range(len(grid)) if actual_MC else range(start_index,len(grid)-remaining+1)
        for point in point_range:
            if indices and np.any(np.linalg.norm(grid[indices]-grid[point],axis=1)<c["minimum_distance"]):
                pruned+=1;continue
            visit(indices+[point],0 if actual_MC else point+1)
    visit([],0)
    if winner is None:raise RuntimeError("No feasible complete grid geometry.")
    return winner,{"D":D,"N":n,"mode":mode,"evaluated_feasible_geometries":tested,
                   "pruned_partial_branches":pruned,"objective":best,"elapsed_seconds":time.perf_counter()-start,
                   "complete":True,"permutation_symmetry_reduction":not actual_MC,"objective_protocol":c["brute_force_objective"]}
