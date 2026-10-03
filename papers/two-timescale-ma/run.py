"""Independent reduced-size MRT AO/SCA implementation of arXiv:2410.05912v2.

No author code, external solver, RNG, or stored performance curves are used.
The fixed NLoS samples are deterministic test inputs, not a Monte Carlo ensemble.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np


def statistical(t, f, antenna=None):
    """Eq. (13), with exact derivative and global antenna-wise curvature bound."""
    n, users = t.shape[0], len(f["beta"])
    beta = np.asarray(f["beta"])
    kap = np.asarray(f["rician"])
    dirs = np.asarray(f["directions"])
    wave = 2 * np.pi / f["wavelength"]
    numerator = beta**2 * (n**2 + n * (2 * kap + 1) / (kap + 1)**2)
    denominator = np.asarray(f["noise"]) * n * beta.sum() / f["power"]
    grad_d = np.zeros((users, n, 2))
    curvature_d = np.zeros(users)
    for m in range(users):
        bounds = np.zeros((2, 2))
        for j in range(users):
            if j == m:
                continue
            v = dirs[m] - dirs[j]
            e = np.exp(1j * wave * (t @ v))
            total = e.sum()
            coeff = beta[m] * beta[j] * kap[m] * kap[j] / ((kap[m]+1)*(kap[j]+1))
            denominator[m] += coeff * abs(total)**2
            denominator[m] += beta[m]*beta[j]*n*(kap[m]+kap[j]+1)/((kap[m]+1)*(kap[j]+1))
            grad_d[m] += 2 * coeff * np.real(np.conj(total) * (1j*wave*e[:, None]*v))
            if antenna is not None:
                tau = total - e[antenna]
                bounds += coeff * abs(tau) * np.abs(np.outer(v, v))
        curvature_d[m] = 2 * wave**2 * np.linalg.eigvalsh(bounds)[-1]
    weight = numerator / (np.log(2)*denominator*(denominator+numerator))
    rates = np.log2(1+numerator/denominator)
    grad = -(weight[:, None, None] * grad_d).sum(axis=0)
    curvature = float(weight @ curvature_d)
    return float(rates.sum()), grad, curvature, rates


def clip_polygon(poly, normal, bound):
    """Intersect a convex polygon with normal @ x >= bound."""
    out = []
    for i in range(len(poly)):
        p, q = poly[i], poly[(i+1) % len(poly)]
        dp, dq = float(normal @ p - bound), float(normal @ q - bound)
        pin, qin = dp >= -1e-12, dq >= -1e-12
        if pin:
            out.append(p)
        if pin != qin:
            out.append(p + (q-p)*dp/(dp-dq))
    return np.asarray(out)


def project_surrogate(z, t, antenna, f):
    lo, hi = f["region"]
    poly = np.array([[lo,lo], [hi,lo], [hi,hi], [lo,hi]], dtype=float)
    x = t[antenna]
    normals, bounds = [], []
    for i in range(len(t)):
        if i == antenna:
            continue
        d = x-t[i]
        normal = 2*d
        bound = f["minimum_distance"]**2 - d@d + normal@x
        normals.append(normal)
        bounds.append(bound)
        poly = clip_polygon(poly, normal, bound)
        if len(poly) == 0:
            raise RuntimeError("Empty SCA polygon: initial geometry is infeasible.")
    if np.all(z >= lo) and np.all(z <= hi) and all(a@z >= b-1e-12 for a,b in zip(normals,bounds)):
        return z
    best, best_d = None, np.inf
    for i in range(len(poly)):
        p, q = poly[i], poly[(i+1) % len(poly)]
        v = q-p
        alpha = np.clip((z-p)@v/max(v@v, 1e-30), 0, 1)
        cand = p+alpha*v
        dist = float((z-cand)@(z-cand))
        if dist < best_d:
            best, best_d = cand, dist
    return best


def optimize(t, f):
    t = t.copy()
    hist = [statistical(t,f)[0]]
    lower_bound_gap = []
    for _ in range(f["sweeps"]):
        for a in range(len(t)):
            val, grad, curv, _ = statistical(t,f,a)
            if curv <= 1e-14:
                continue
            candidate = project_surrogate(t[a]+grad[a]/curv, t, a, f)
            delta = candidate-t[a]
            lower = val+grad[a]@delta-0.5*curv*(delta@delta)
            trial = t.copy()
            trial[a] = candidate
            actual = statistical(trial,f)[0]
            lower_bound_gap.append(actual-lower)
            if actual < val-1e-10:
                raise RuntimeError("AO/SCA update lowered the actual Eq.13 objective.")
            t = trial
        hist.append(statistical(t,f)[0])
    return t, hist, lower_bound_gap


def zf_lower_bound(t, f):
    kap, beta = np.asarray(f["rician"]), np.asarray(f["beta"])
    hbar = np.exp(1j*2*np.pi/f["wavelength"]*(t@np.asarray(f["directions"]).T))
    n, users = hbar.shape
    scale = np.sqrt(kap/(1+kap))
    sigma = np.diag(1/(1+kap))+(hbar.conj().T@hbar)/n*scale[:,None]*scale[None,:]
    diagonal = np.real(np.diag(np.linalg.solve(sigma,np.eye(users))))
    return float(np.log2(1+f["power"]/users/np.asarray(f["noise"])*beta*(n-users)/diagonal).sum())


def instantaneous(t, f):
    beta, kap = np.asarray(f["beta"]), np.asarray(f["rician"])
    hbar = np.exp(1j*2*np.pi/f["wavelength"]*(t@np.asarray(f["directions"]).T))
    nlos = np.asarray(f["nlos_re"])+1j*np.asarray(f["nlos_im"])
    rates_mrt, rates_zf, powers, leaks = [], [], [], []
    users = len(beta)
    for sample in nlos:
        h = hbar*np.sqrt(beta*kap/(kap+1))+sample*np.sqrt(beta/(kap+1))
        w_mrt = h*np.sqrt(f["power"]/np.sum(abs(h)**2))
        v = h@np.linalg.solve(h.conj().T@h,np.eye(users))
        w_zf = v/np.linalg.norm(v,axis=0)*np.sqrt(f["power"]/users)
        for w, rates in [(w_mrt,rates_mrt),(w_zf,rates_zf)]:
            gain = abs(h.conj().T@w)**2
            desired = np.diag(gain)
            rates.append(float(np.log2(1+desired/(gain.sum(axis=1)-desired+f["noise"])).sum()))
            powers.append(float(np.sum(abs(w)**2)))
        hz = h.conj().T@w_zf
        leaks.append(float(np.max(abs(hz-np.diag(np.diag(hz))))))
    return rates_mrt, rates_zf, max(abs(np.asarray(powers)-f["power"])), max(leaks)


def run():
    f = json.loads(Path(__file__).with_name("fixture.json").read_text())
    initial = np.asarray(f["initial_positions"], dtype=float)
    final, hist, gap = optimize(initial,f)
    _, grad, _, _ = statistical(initial,f)
    numerical = np.zeros_like(initial)
    for a in range(len(initial)):
        for d in range(2):
            plus, minus = initial.copy(), initial.copy()
            plus[a,d] += 1e-6
            minus[a,d] -= 1e-6
            numerical[a,d] = (statistical(plus,f)[0]-statistical(minus,f)[0])/2e-6
    distance = np.linalg.norm(final[:,None,:]-final[None,:,:],axis=2)
    distance += np.eye(len(final))*1e9
    mrt0,zf0,p0,l0 = instantaneous(initial,f)
    mrt1,zf1,p1,l1 = instantaneous(final,f)
    rayleigh = dict(f, rician=[0.0]*len(f["rician"]))
    rdiff = abs(statistical(initial,rayleigh)[0]-statistical(final,rayleigh)[0])
    result = {
        "paper_id": "two-timescale-ma",
        "metrics": {"initial_positions":initial.tolist(), "optimized_positions":final.tolist(),
            "mrt_statistical_initial":hist[0], "mrt_statistical_optimized":hist[-1],
            "zf_bound_initial":zf_lower_bound(initial,f), "zf_bound_at_mrt_positions":zf_lower_bound(final,f),
            "mrt_fixture_initial":mrt0, "mrt_fixture_optimized":mrt1,
            "zf_fixture_initial":zf0, "zf_fixture_at_mrt_positions":zf1},
        "checks": {"gradient_max_error":float(np.max(abs(grad-numerical))),
            "gradient_pass":bool(np.max(abs(grad-numerical))<1e-7),
            "minimum_distance":float(distance.min()), "spacing_feasible":bool(distance.min()>=f["minimum_distance"]-1e-10),
            "box_feasible":bool(np.all(final>=f["region"][0]-1e-10) and np.all(final<=f["region"][1]+1e-10)),
            "objective_monotone":bool(np.min(np.diff(hist))>=-1e-10),
            "surrogate_lower_bound_min_gap":float(min(gap)), "power_max_error":float(max(p0,p1)),
            "zf_max_offdiagonal":float(max(l0,l1)), "rayleigh_position_invariance_error":rdiff},
        "history": {"mrt_statistical_sum_rate":hist}}
    assert result["checks"]["gradient_max_error"] < 1e-7
    assert all(result["checks"][s] for s in ["spacing_feasible","box_feasible","objective_monotone"])
    assert min(gap)>-1e-9 and max(p0,p1)<1e-10 and max(l0,l1)<1e-10 and rdiff<1e-12
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"paper_id":result["paper_id"], "checks":result["checks"]}))
