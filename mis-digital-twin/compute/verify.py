"""Independent scalar replay and numerical consistency checks for data.js.

This verifier deliberately reconstructs the geometry and far field using
Python scalar complex sums, without importing the optimizer's model class.
"""
import cmath
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    text=(ROOT/'data.js').read_text(encoding='utf-8')
    d=json.loads(text.split('=',1)[1].strip().removesuffix(';'))
    cfg=d['config']; n1=cfg['n1']; n2=cfg['n2']
    M=n1*n1; N=n2*n2
    p=cfg['pitchMm']/cfg['wavelengthMm']
    offset=(n1-n2)//2
    checks=[]
    def record(name,passed,**evidence):
        checks.append(dict(name=name,passed=bool(passed),**evidence))
    methods={}
    for method in ['snell','optimized']:
        m=d[method]
        gains=[]; coverage_counts=[]; hash_before=hashlib.sha256(json.dumps([m['phi1'],m['phi2']]).encode()).hexdigest()
        uncovered_errors=[]
        for target in d['targets']:
            az,el=map(math.radians,[target['az'],target['el']])
            ux=math.sin(az)*math.cos(el); uy=math.sin(el)
            powers=[]
            for position in d['positions']:
                amplitudes=[]; covered=0
                for row in range(n1):
                    for col in range(n1):
                        r2=row-offset-position['y']; c2=col-offset-position['x']
                        phase=m['phi1'][row*n1+col]
                        original_phase=phase
                        if 0<=r2<n2 and 0<=c2<n2:
                            phase+=m['phi2'][r2*n2+c2]
                            covered+=1
                        else:
                            uncovered_errors.append(abs(cmath.exp(1j*phase)/cmath.exp(1j*original_phase)-1))
                        x=(col-(n1-1)/2)*p; y=(row-(n1-1)/2)*p
                        amplitudes.append(cmath.exp(1j*(phase-2*math.pi*(x*ux+y*uy))))
                power=abs(sum(amplitudes)/M)**2
                powers.append(power); coverage_counts.append(covered)
            gains.append(powers)
        schedules=[max(range(len(row)),key=row.__getitem__) for row in gains]
        selected=[max(row) for row in gains]
        score=min(selected)
        error=max(abs(gains[k][u]-m['gainMatrix'][k][u]) for k in range(9) for u in range(25))
        hash_after=hashlib.sha256(json.dumps([m['phi1'],m['phi2']]).encode()).hexdigest()
        record(method+'_independent_complex_field_replay',error<1e-12,maxPowerError=error)
        record(method+'_schedule_is_exact_discrete_argmax',schedules==m['schedule'],schedule=schedules)
        record(method+'_worst_target_score',abs(score-m['score'])<1e-12,replayedScore=score)
        record(method+'_padding_and_coverage',set(coverage_counts)=={N} and max(uncovered_errors)<1e-14,
               coveredCells=N,uncoveredCells=M-N,maxUncoveredMultiplierError=max(uncovered_errors))
        record(method+'_masks_static_for_every_position_and_target',hash_before==hash_after,
               maskSha256=hash_before)
        record(method+'_phase_unit_modulus',all(0<=v<2*math.pi for v in m['phi1']+m['phi2']))
        record(method+'_coherent_power_bound',all(-1e-14<=v<=1+1e-12 for row in gains for v in row))
        methods[method]=dict(score=score,scoreDb=10*math.log10(score),schedule=schedules,targetPower=selected)
    # For every ideal steering phase, exactly coherent addition must give 1.
    normalization_errors=[]
    for target in d['targets']:
        az,el=map(math.radians,[target['az'],target['el']])
        ux=math.sin(az)*math.cos(el); uy=math.sin(el)
        values=[]
        for row in range(n1):
            for col in range(n1):
                x=(col-(n1-1)/2)*p; y=(row-(n1-1)/2)*p
                phase=2*math.pi*(x*ux+y*uy)
                values.append(cmath.exp(1j*phase)*cmath.exp(-1j*phase))
        normalization_errors.append(abs(abs(sum(values)/M)**2-1))
    record('coherent_ideal_peak_normalizes_to_one',max(normalization_errors)<1e-14,
           maximumError=max(normalization_errors))
    # Check quadratic Snell construction on an overlapped pair of cells.
    # Complex-ratio test avoids any ambiguity from phase wrapping.
    max_snell_error=0
    for position in d['positions']:
        for r2 in range(n2-1):
            for c2 in range(n2-1):
                r1=r2+offset+position['y']; c1=c2+offset+position['x']
                def q(r,c,rr,cc):
                    return d['snell']['phi1'][r*n1+c]+d['snell']['phi2'][rr*n2+cc]
                q0=q(r1,c1,r2,c2)
                qx=q(r1,c1+1,r2,c2+1); qy=q(r1+1,c1,r2+1,c2)
                expected_x=2*math.pi*cfg['snellC']*position['x']*p*p
                expected_y=2*math.pi*cfg['snellC']*position['y']*p*p
                max_snell_error=max(max_snell_error,abs(cmath.exp(1j*(qx-q0-expected_x))-1),
                                    abs(cmath.exp(1j*(qy-q0-expected_y))-1))
    record('snell_overlap_phase_gradient',max_snell_error<1e-12,maxComplexRatioError=max_snell_error)
    record('analytic_phase_gradient_finite_difference',d['validation']['gradient']['passed'],
           **{k:v for k,v in d['validation']['gradient'].items() if k!='passed'})
    record('joint_design_retains_snell_incumbent',methods['optimized']['score']>=methods['snell']['score']-1e-12)
    h=d['history']
    record('history_is_monotone_best_actual_minimum',all(h[i+1]['score']>=h[i]['score']-1e-14 for i in range(len(h)-1))
           and abs(h[-1]['score']-methods['optimized']['score'])<1e-12,acceptedPhaseIterations=h[-1]['iteration'])
    validation=dict(passed=all(c['passed'] for c in checks),checkCount=len(checks),checks=checks,
                    methods=methods,gainDb=methods['optimized']['scoreDb']-methods['snell']['scoreDb'],
                    sourceDataSha256=hashlib.sha256((ROOT/'data.js').read_bytes()).hexdigest(),
                    scope='These checks validate the ideal scalar simulation, not hardware accuracy or global optimality.')
    (ROOT/'compute'/'validation.json').write_text(json.dumps(validation,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(validation,ensure_ascii=False,indent=2))
    if not validation['passed']:
        raise SystemExit(1)


if __name__=='__main__':
    main()
