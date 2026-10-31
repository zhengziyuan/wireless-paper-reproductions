"""PREPARED ONLY: before-W2 physical MP plus fixed-QP residuals, no solve.
After-W2 original physical gradients and scalar-error bounds are read from the
already-completed MP report; its physical model is never evaluated at Wnew.
"""
from pathlib import Path
import argparse,ast,copy,hashlib,importlib.util,json,struct
import mpmath as mp
import numpy as np
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def norm(x):return mp.sqrt(mp.fsum(abs(v)**2 for v in x))
def dot(a,b):return mp.fsum(mp.conj(a[i,j])*b[i,j] for i in range(a.rows) for j in range(a.cols))
def show(x):return mp.nstr(x,105)
def maxabs(a):return max(abs(v) for v in a)
def comp(x):return dict(real=show(mp.re(x)),imag=show(mp.im(x)))
def vector(x):return [comp(x[i,j]) for i in range(x.rows) for j in range(x.cols)]
def same_real_bits(a,b):
    a=np.asarray(a,dtype=np.float64);b=np.asarray(b,dtype=np.float64)
    return a.shape==b.shape and a.tobytes(order='F')==b.tobytes(order='F')

def build_original(f,w,c,iota,exact):
    M,N=f.rows,w.cols;K=len(c['noise']);A=len(c['desired_pattern']);fc=f[:,:K];fs=f[:,K:];y=fc.H*w;z=fs.H*w
    pd=[exact(v) for v in c['desired_pattern']];noise=[exact(v) for v in c['noise']];rho=exact(c['rho']);cap=exact(c['power']);ii=exact(iota);den=ii**2*mp.fsum(v*v for v in pd)
    signal=[abs(y[u,u])**2 for u in range(K)];interference=[noise[u]+mp.fsum(abs(y[u,b])**2 for b in range(N) if b!=u) for u in range(K)];total=[signal[u]+interference[u] for u in range(K)];mu=[signal[u]/interference[u] for u in range(K)];eta=[y[u,u]/total[u] for u in range(K)]
    pattern=[mp.fsum(abs(z[a,b])**2 for b in range(N)) for a in range(A)];res=[pattern[a]-ii*pd[a] for a in range(A)];fnorm=[mp.fsum(abs(fs[m,a])**2 for m in range(M)) for a in range(A)];lip=[12*cap*t*t+4*ii*d*t for t,d in zip(fnorm,pd)]
    ga=4*fs*mp.diag(res)*z;alpha=rho*mp.fsum(lip)/(2*den);beta=rho/(2*den);Q=alpha*mp.eye(M);Pc=mp.zeros(M,N)
    for u in range(K):
        fu=fc[:,u];Q+=(1+mu[u])*abs(eta[u])**2/mp.log(2)*(fu*fu.H)
        for m in range(M):Pc[m,u]=(1+mu[u])*eta[u]*fc[m,u]/mp.log(2)
    P=Pc+alpha*w-beta*ga;G=mp.zeros(M,N)
    for m in range(M):
        for b in range(N):G[m,b]=2/mp.log(2)*mp.fsum(fc[m,u]*y[u,b]*(1/total[u] if b==u else -signal[u]/(total[u]*interference[u])) for u in range(K))-rho/den*ga[m,b]
    rate=mp.fsum(mp.log1p(mu[u])/mp.log(2) for u in range(K));nmse=mp.fsum(x*x for x in res)/den
    return dict(Q=Q,P=P,G=G,rate=rate,nmse=nmse,utility=rate-rho*nmse,alpha=alpha,beta=beta,mu=mu,eta=eta,Ga=ga,lip=lip,den=den)

def qp_report(Q,P,w0,w1,nu):
    d=w1-w0;res=2*(P-(Q+nu*mp.eye(Q.rows))*w1);scale=2*((norm(Q)+abs(nu))*norm(w1)+norm(P));gain=2*mp.re(dot(P-Q*w0,d))-mp.re(dot(d,Q*d))
    return dict(original_QP_KKT_residual_Fro_norm=show(norm(res)),relative_QP_residual_by_QW_P_scale=show(norm(res)/scale) if scale else None,QP_objective_gain=show(gain),Q_Fro_norm=show(norm(Q)),P_Fro_norm=show(norm(P)),no_new_QP_solve=True),res

def main():
    p=argparse.ArgumentParser();p.add_argument('--admission',type=Path,required=True);p.add_argument('--expected-admission-sha',required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();assert sha(a.admission)==a.expected_admission_sha
    ad=json.loads(a.admission.read_bytes());assert ad.get('root_admitted_once_saved_W2_before_and_fixed_QP_MP') is True and str(a.output_dir.resolve())==ad['unique_output_directory']
    manifest=HERE/'FROZEN_BEFORE_QP_MP_SOURCE_AND_ACTUAL_INPUTS_V1.json';assert sha(manifest)==ad['source_manifest_SHA256'];cfg=json.loads(manifest.read_bytes());pins=dict(cfg['files_SHA256']);pins[str(manifest)]=sha(manifest);pins[str(a.admission.resolve())]=a.expected_admission_sha;assert pins[str(Path(__file__).resolve())]==sha(__file__)
    assert all(sha(Path(p))==s for p,s in pins.items());assert not a.output_dir.exists();a.output_dir.mkdir()
    paths=cfg['paths'];cl=json.loads(Path(paths['actual_replay_closure']).read_bytes());held=json.loads(Path(paths['actual_held_terminal']).read_bytes());old=json.loads(Path(paths['existing_after_MP']).read_bytes());fixture=json.loads(Path(paths['existing_after_provider_fixture']).read_bytes());c=json.loads(Path(paths['scene']).read_bytes())
    assert cl['same_original_W2_path_pass'] and cl['source_and_input_interval_closed'] and cl['actual_structured_QP_calls']==1 and cl['actual_original_evaluate_calls']==2 and not cl['observer_errors']
    assert held['actual_child_terminal_exit_code']==held['effective_host_exit_code']==0 and held['natural_wait_completed'] and held['exact_original_handle_birth_and_exit_match'] and held['all_watched_source_and_job_bytes_unchanged'] and not held['host_errors']
    assert old['source_input_interval_closed'] and old['crossprecision_pass'] and sha(Path(paths['operands']))==cl['raw_operands_SHA256']
    with np.load(paths['operands'],allow_pickle=False) as z:z={k:z[k].copy() for k in z.files}
    assert all(np.all(np.isfinite(v)) for v in z.values());state=next(x['state'] for x in fixture['states'] if x['method']=='update_w' and x['call']==2)
    wn=z['actual_return__W'];assert same_real_bits(wn.real,state['w_re']) and same_real_bits(wn.imag,state['w_im']) and struct.pack('>d',float(z['EVALUATE00001__utility']))==struct.pack('>d',state['utility']) and struct.pack('>d',float(z['actual_input__iota']))==struct.pack('>d',state['iota'])
    assert same_real_bits(z['actual_input__theta'].real,np.asarray(state['theta_re']).reshape(z['actual_input__theta'].shape))
    assert same_real_bits(z['actual_input__theta'].imag,np.asarray(state['theta_im']).reshape(z['actual_input__theta'].shape))
    assert same_real_bits(z['actual_input__r'],np.asarray(state['rotation']).reshape(z['actual_input__r'].shape))
    # Load only the independent physical helper and selected reference definitions.
    spec=importlib.util.spec_from_file_location('frozen_independent_mp_physical',paths['physical_helper']);physical=importlib.util.module_from_spec(spec);spec.loader.exec_module(physical);exact=physical.exact
    tree=ast.parse(Path(paths['objective_helper']).read_bytes());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='mpmatrix' or isinstance(n,ast.ClassDef) and n.name=='FixedObjective'];ns=dict(mp=mp,np=np,exact=exact,field_parts=physical.field_parts);exec(compile(ast.Module(body=copy.deepcopy(nodes),type_ignores=[]),paths['objective_helper']+':definitions-only','exec'),ns);matrix=ns['mpmatrix']
    ref=next(n for n in ast.parse(Path(paths['W_gradient_reference']).read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='reference');part=copy.deepcopy(ref);cut=next(i for i,n in enumerate(part.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='eps' for t in n.targets));part.body=part.body[:cut]
    # Skip unused RIS gradient work; original before metric and W-gradient formulas unchanged.
    metric_call=next(n for n in ast.walk(part) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='evaluate');assert len(metric_call.args)==2 and isinstance(metric_call.args[1],ast.Constant) and metric_call.args[1].value is True;metric_call.args=metric_call.args[:1]
    part.body.append(ast.parse('return gw,metric,f').body[0]);ast.fix_missing_locations(part);exec(compile(ast.Module(body=[part],type_ignores=[]),paths['W_gradient_reference']+':before-W-only-no-rotation-differences','exec'),ns);before_ref=ns['reference']
    lanes={};signatures={}
    for digits in (80,100):
        with mp.workdps(digits):
            w0=matrix(z['actual_input__W']);w1=matrix(wn);theta=z['actual_input__theta'];r=z['actual_input__r'];iota=float(z['actual_input__iota']);d=w1-w0;M,N=w0.rows,w0.cols;K=len(c['noise']);nu=exact(float(z['QP00000__info__nu']));assert nu==0
            Graw,before_metric,fphys=before_ref(z['actual_input__W'],theta,r.tolist(),c,iota);Gphys=mp.matrix(Graw);theory=build_original(fphys,w0,c,iota,exact);frozen=build_original(matrix(z['WITER00000__f']),w0,c,iota,exact)
            fc=matrix(z['QP00000__arg__fc']);mu=[exact(float(v)) for v in z['QP00000__arg__mu']];eta=[exact(complex(v)) for v in z['QP00000__arg__eta']];lip=[exact(float(v)) for v in z['QP00000__arg__lip']];ga=matrix(z['QP00000__arg__Ga']);den=exact(float(z['QP00000__arg__den']));rho=exact(c['rho']);alpha=rho*mp.fsum(lip)/(2*den);beta=rho/(2*den);Qc=alpha*mp.eye(M);Pc=mp.zeros(M,N)
            for u in range(K):
                fu=fc[:,u];Qc+=(1+mu[u])*abs(eta[u])**2/mp.log(2)*(fu*fu.H)
                for m in range(M):Pc[m,u]=(1+mu[u])*eta[u]*fc[m,u]/mp.log(2)
            Pc+=alpha*w0-beta*ga
            # Actual rounded factor/preprocessing and actual SVD/basis representations.
            A=matrix(z['QP00000__info__factor']);gamma=[exact(complex(v)) for v in z['QP00000__info__gamma']];alpha_actual=exact(float(z['QP00000__info__alpha']));beta_actual=exact(float(z['QP00000__info__beta']));QA=A*A.H+alpha_actual*mp.eye(M);PA=alpha_actual*w0-beta_actual*ga
            for u in range(K):
                for m in range(M):PA[m,u]+=A[m,u]*gamma[u]
            U=matrix(z['QP00000__info__left']);diag=[exact(float(v)) for v in z['QP00000__info__original_positive_diagonal']];coords=matrix(z['QP00000__info__total_coordinates']);Qb=U*mp.diag(diag)*U.H;Pb=U*coords;Vh=matrix(z['QP00000__info__right_h']);sing=[exact(float(v)) for v in z['QP00000__info__singular']]
            qpc,rc=qp_report(Qc,Pc,w0,w1,nu);qpa,ra=qp_report(QA,PA,w0,w1,nu);qpb,rb=qp_report(Qb,Pb,w0,w1,nu);qpt,rt=qp_report(theory['Q'],theory['P'],w0,w1,nu);qpf,rf=qp_report(frozen['Q'],frozen['P'],w0,w1,nu)
            after_row=next(x for x in old['precision_lanes'][str(digits)] if x['method']=='update_w' and x['call']==2);gg=after_row['block_gradient']['reference_gradient'];assert len(gg)==M*N;Gafter=mp.matrix(M,N)
            for i,x in enumerate(gg):Gafter[i//N,i%N]=mp.mpc(mp.mpf(x['real']),mp.mpf(x['imag']))
            touch=Gphys-2*(Pc-Qc*w0);drift=Gafter-Gphys;move=2*Qc*d;Rafter=Gafter-2*nu*w1;decomposition_error=Rafter-(drift+rc+move+touch)
            # Existing after report stores an absolute error, not signed true utility.
            error_after=mp.mpf(after_row['fields']['utility']['maximum_absolute_error']);after64=exact(float(z['EVALUATE00001__utility']));delta_interval=(after64-error_after-before_metric['utility'],after64+error_after-before_metric['utility'])
            energy=norm(d)**2
            column_energy=[norm(U[:,j].H*d)**2 for j in range(M)]
            positive_columns=[j for j in range(M) if j<len(sing) and sing[j]!=0]
            exact_zero_columns=[j for j in range(M) if j>=len(sing) or sing[j]==0]
            strong_energy=mp.fsum(column_energy[j] for j in positive_columns)
            zero_energy=mp.fsum(column_energy[j] for j in exact_zero_columns)
            direction=mp.re(dot(Gphys,d));curvature=mp.re(dot(d,Qc*d))
            row={
                'before_original_physics':dict(
                    utility=show(before_metric['utility']),rate=show(before_metric['rate']),
                    nmse=show(before_metric['nmse']),W_gradient=vector(Gphys),
                    W_gradient_Fro_norm=show(norm(Gphys)),
                    actual_binary64_before_utility_error=show(abs(
                        exact(float(z['EVALUATE00000__utility']))-before_metric['utility']))),
                'layer1_captured_rounded_auxiliary_original_formula':dict(
                    alpha=show(alpha),beta=show(beta),
                    ln2_convention='Original mathematical ln2; actual factor preprocessing is separate layer2',
                    QP=qpc,old_contact_vs_fullphysical_gradient_Fro_norm=show(norm(touch))),
                'layer2_actual_factor_and_SVD':dict(
                    actual_alpha=show(alpha_actual),actual_beta=show(beta_actual),
                    actual_diagonal=[show(x) for x in diag],
                    actual_diagonal_ratio=show(max(diag)/min(diag)),
                    ratio_scope='Ratio of recorded positive diagonal, not a certified original-Q eigenspectrum',
                    actual_factor_QP=qpa,actual_basis_QP=qpb,
                    Q_factor_minus_layer1_Fro_norm=show(norm(QA-Qc)),
                    P_factor_minus_layer1_Fro_norm=show(norm(PA-Pc)),
                    Q_basis_minus_factor_Fro_norm=show(norm(Qb-QA)),
                    P_basis_minus_factor_Fro_norm=show(norm(Pb-PA)),
                    U_unitarity_defect_Fro_norm=show(norm(U.H*U-mp.eye(M))),
                    factor_SVD_reconstruction_error_Fro_norm=show(norm(A-U[:,:K]*mp.diag(sing)*Vh)),
                    actual_legacy_dense_QP_residual_Fro_norm=show(norm(
                        (matrix(z['WITER00000__q'])+nu*mp.eye(M))*w1-matrix(z['WITER00000__p'])))),
                'layer3_original_physical_theoretical_auxiliaries':dict(
                    physical_theory_QP=qpt,same_frozen_binary64_field_theory_QP=qpf,
                    theoretical_mu=[show(x) for x in theory['mu']],
                    physical_theory_contact_defect_Fro_norm=show(norm(
                        Gphys-2*(theory['P']-theory['Q']*w0))),
                    same_frozen_field_contact_defect_Fro_norm=show(norm(
                        frozen['G']-2*(frozen['P']-frozen['Q']*w0))),
                    Ga_captured_minus_physical_theory_Fro_norm=show(norm(ga-theory['Ga'])),
                    alpha_physical_theory=show(theory['alpha']),
                    physical_vs_frozen_before_gradient_Fro_norm=show(norm(Gphys-frozen['G']))),
                'reused_after_MP':dict(
                    source='Existing actual W2 row; no new after geometry/objective/gradient evaluation',
                    existing_projected_residual=after_row['block_gradient']['unit_gradient_step_projected_power_ball_residual'],
                    scalar_true_gain_reference_based_interval=[show(x) for x in delta_interval],
                    interval_scope='after64 +/- existing MP absolute error, minus new before. Reference-based bound, not signed recovery or interval arithmetic.'),
                'residual_decomposition':dict(
                    identity='Gafter-2nuWnew = (Gafter-Gbefore)+R_QP+2Q_DeltaW+contact_defect',
                    after_original_gradient_residual_Fro_norm=show(norm(Rafter)),
                    gradient_change_Fro_norm=show(norm(drift)),
                    captured_aux_QP_residual_Fro_norm=show(norm(rc)),
                    two_Q_DeltaW_Fro_norm=show(norm(move)),contact_defect_Fro_norm=show(norm(touch)),
                    identity_closure_Fro_norm=show(norm(decomposition_error))),
                'actual_saved_displacement_and_direction':dict(
                    absolute_DeltaW_norm=show(norm(d)),
                    original_physical_before_gradient_directional_derivative=show(direction),
                    captured_aux_QT_MM_quadratic_curvature=show(curvature),
                    per_recorded_U_column_energy=[show(x) for x in column_energy],
                    positive_singular_columns=positive_columns,exact_zero_singular_columns=exact_zero_columns,
                    strong_communication_column_energy=show(strong_energy),
                    exact_zero_singular_subspace_energy=show(zero_energy),
                    strong_energy_fraction=show(strong_energy/energy) if energy else None,
                    zero_energy_fraction=show(zero_energy/energy) if energy else None,
                    U_coordinate_energy_closure_defect=show(mp.fsum(column_energy)-energy),
                    scope='Exact-input saved-state MP diagnostic using actual numerical U; no rank cutoff, projection repair or new W step.'),
                'absolute_DeltaW_scope':'New saved-state arithmetic, not a scalar recorded by original history'
            }
            lanes[str(digits)]=row;signatures[digits]=[before_metric['utility'],norm(Gphys),norm(rc),norm(ra),norm(rb),norm(rt),norm(touch),max(diag)/min(diag),delta_interval[0],delta_interval[1],direction,curvature,strong_energy,zero_energy]+[x for mat in (Gphys,Qc,Pc,rc,ra,rt) for v in mat for x in (mp.re(v),mp.im(v))]
    with mp.workdps(110):gap=max(abs(x-y) for x,y in zip(signatures[80],signatures[100]));stable=gap<=mp.mpf('1e-35')
    after={p:sha(Path(p)) for p in pins};closed=after==pins
    report=dict(schema='actual-before-only-and-fixed-W2-QP-three-layer-MP80-MP100-no-solve-v1',source_before=pins,source_after=after,source_and_input_interval_closed=closed,precision_lanes=lanes,MP80_MP100_maximum_absolute_difference=show(gap),existing_crossprecision_bound='1e-35',crossprecision_pass=stable,after_W2_physics_or_gradient_recomputed=False,new_QP_solve_W_iteration_optimizer_MC_RNG_calls=0,source_replay_actual_math_not_repeated=True,original_author_absolute_W_KKT_gate_reported=False,W_stationarity_or_whole_scenario_reference_or_paper_PASS_not_assigned=True)
    out=a.output_dir/'ACTUAL_W2_BEFORE_ONLY_AND_FIXED_QP_THREE_LAYER_MP80_MP100_V1.json'
    with out.open('x',encoding='utf8') as f:json.dump(report,f,indent=2,allow_nan=False);f.write('\n')
    return 0 if closed and stable else 1
if __name__=='__main__':raise SystemExit(main())
