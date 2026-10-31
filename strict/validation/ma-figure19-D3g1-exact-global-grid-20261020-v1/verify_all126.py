"""Portable independent exhaustive D3/g1 verifier. Python standard library only.
No original evaluator/model, optimizer, inverse, DFS, bound, MC or RNG is loaded.
"""
import argparse
from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path
import traceback
Z0=(Fraction(0),Fraction(0))
Z1=(Fraction(1),Fraction(0))


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def need(condition, message):
    if not condition:
        raise ValueError(message)

def q(value):
    """Exact rational value of a finite binary64 scalar, not decimal rounding."""
    number = float(value)
    need(math.isfinite(number), "Nonfinite frozen primitive")
    return Fraction.from_float(number)

def zadd(a, b):
    return (a[0] + b[0], a[1] + b[1])

def zmul(a, b):
    return (a[0]*b[0] - a[1]*b[1], a[0]*b[1] + a[1]*b[0])

def zconj(a):
    return (a[0], -a[1])

def znorm(a):
    return a[0]*a[0] + a[1]*a[1]

def zsum(values):
    result = Z0
    for value in values:
        result = zadd(result, value)
    return result

def determinant(matrix):
    """Leibniz permutation expansion, with exact Gaussian rational products.

    No elimination, inverse, eigensolver, determinant library, or original
    implementation is called.  Here the largest determinant is only 3 by 3.
    """
    n = len(matrix)
    if n == 0:
        return Z1
    result = Z0
    for permutation in itertools.permutations(range(n)):
        inversions = sum(permutation[i] > permutation[j]
                         for i in range(n) for j in range(i+1, n))
        term = Z1
        for row, column in enumerate(permutation):
            term = zmul(term, matrix[row][column])
        sign = -1 if inversions % 2 else 1
        result = zadd(result, (sign*term[0], sign*term[1]))
    return result

def real_positive_det(matrix):
    value = determinant(matrix)
    need(value[1] == 0 and value[0] > 0,
         "Exact determinant is not strictly positive real")
    return value[0]

def minor(matrix, excluded):
    return [[value for j, value in enumerate(row) if j != excluded]
            for i, row in enumerate(matrix) if i != excluded]

def rational_record(value):
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}

def rebuild_rational_constants(c, n, m, mode):
    beta = list(map(q, c["beta"]))
    kap = list(map(q, c["rician"]))
    noise = list(map(q, c["noise"]))
    power = q(c["power"])
    need(n == 4 and m == 3 and all(x > 0 for x in beta+noise) and power > 0,
         "Expected N4/M3 strictly positive physical constants")
    if mode == "MRT":
        desired = [beta[u]**2 * (n*n + n*(2*kap[u]+1)/(kap[u]+1)**2)
                   for u in range(m)]
        offset = [noise[u]*n*sum(beta)/power +
                  sum(beta[u]*beta[v]*n*(kap[u]+kap[v]+1)/((kap[u]+1)*(kap[v]+1))
                      for v in range(m) if v != u) for u in range(m)]
        coefficient = {(u,v): beta[u]*beta[v]*kap[u]*kap[v]/((kap[u]+1)*(kap[v]+1))
                       for u in range(m) for v in range(m) if u != v}
        return {"desired": desired, "offset": offset, "coefficient": coefficient}
    return {"offset": [1/(value+1) for value in kap],
            "eta": [power*beta[u]*(n-m)/(m*noise[u]) for u in range(m)]}

def independent_product(operands, indices, mode):
    m = operands["m"]
    total = Fraction(1)
    if mode == "MRT":
        for u in range(m):
            interference = operands["offset"][u]
            for v in range(m):
                if v != u:
                    resultant = zsum(operands["terms"][u,v][i] for i in indices)
                    interference += operands["coefficient"][u,v]*znorm(resultant)
            need(interference > 0, "MRT denominator is not positive")
            total *= 1 + operands["desired"][u]/interference
        return total
    matrix = [[Z0 for _ in range(m)] for _ in range(m)]
    for u in range(m):
        matrix[u][u] = (operands["offset"][u] +
                         sum(operands["diagonal"][i][u] for i in indices), Fraction(0))
    for u,v in itertools.combinations(range(m),2):
        matrix[u][v] = zsum(operands["terms"][u,v][i] for i in indices)
        matrix[v][u] = zconj(matrix[u][v])
    # Sylvester's criterion is checked with independent exact determinants.
    for k in range(1,m):
        real_positive_det([row[:k] for row in matrix[:k]])
    det = real_positive_det(matrix)
    for u in range(m):
        cofactor = real_positive_det(minor(matrix,u))
        # Cramer's diagonal identity: (Sigma^-1)_uu=C_uu/det(Sigma).
        total *= 1 + operands["eta"][u]*det/cofactor
    return total

def enumerate_all126(operands, mode, saved_winner, saved_product):
    grid = [[q(value) for value in row] for row in operands["grid"]]
    need(len(grid) == 9 and operands["n"] == 4, "Only this D3/g1 scope is permitted")
    spacing2 = operands["spacing"]**2
    chain = hashlib.sha256()
    best = None
    winner = None
    ties = []
    feasible = 0
    evaluated = []
    total = 0
    for indices in itertools.combinations(range(9),4):
        total += 1
        # This filter does not use the original compatible mask or a tree.
        admissible = all(sum((grid[i][axis]-grid[j][axis])**2 for axis in range(2)) >= spacing2
                         for i,j in itertools.combinations(indices,2))
        record = {"indices_zero_based": indices, "spacing_feasible": admissible}
        if admissible:
            feasible += 1
            product = independent_product(operands,indices,mode)
            record["product"] = rational_record(product)
            evaluated.append((indices,product))
            if best is None or product > best:
                best, winner, ties = product, indices, [indices]
            elif product == best:
                ties.append(indices)
        chain.update(encode(record) + b"\n")
    need(total == math.comb(9,4) == 126 and feasible > 0, "Incomplete independent enumeration")
    saved_values = [product for indices,product in evaluated if indices == tuple(saved_winner)]
    need(len(saved_values) == 1, "Saved winner is not independently spacing feasible")
    distinct = sorted({product for _,product in evaluated}, reverse=True)
    checks = {
        "all126_canonical_sets_visited_without_pruning": total == 126,
        "saved_winner_is_spacing_feasible": True,
        "independent_product_at_saved_winner_equals_stored_rational": saved_values[0] == saved_product,
        "independent_global_maximum_equals_stored_rational": best == saved_product,
        "saved_winner_is_global_maximizer": saved_values[0] == best,
        "strict_greater_earliest_lexicographic_tie_winner_matches": list(winner) == list(saved_winner),
    }
    return {
        "mode": mode, "enumerated_sets": total, "spacing_feasible_sets": feasible,
        "spacing_rejected_sets": total-feasible, "exact_objective_evaluations": feasible,
        "all126_decision_and_exact_product_SHA256": chain.hexdigest(),
        "independent_winner_zero_based": list(winner), "stored_winner_zero_based": list(saved_winner),
        "number_of_exact_global_ties": len(ties), "all_global_ties_zero_based": [list(t) for t in ties],
        "independent_global_product": rational_record(best), "stored_product": rational_record(saved_product),
        "strict_gap_to_second_distinct_product": rational_record(distinct[0]-distinct[1]) if len(distinct)>1 else None,
        "display_only_log2_global_product": math.log2(best.numerator)-math.log2(best.denominator),
        "checks": checks, "independent_global_grid_gate_pass": all(checks.values()),
    }


def hx(value):
    number=float.fromhex(value)
    need(math.isfinite(number),'Nonfinite primitive')
    need(number.hex()==value,'Noncanonical binary64 hex encoding')
    return number


def exact_complex(value):
    need(len(value)==2,'Complex primitive must have real and imaginary components')
    return (q(hx(value[0])),q(hx(value[1])))


def load_operands(model):
    need((model['N'],model['M'],model['D'])==(4,3,3),'Only N4/M3/D3 is supported')
    c={key:[hx(x) for x in model[key]] for key in ('beta','rician','noise')}
    c['power']=hx(model['power'])
    constants=rebuild_rational_constants(c,4,3,model['mode'])
    grid=[[hx(x) for x in row] for row in model['grid']]
    need(len(grid)==9 and all(len(row)==2 for row in grid),'Expected nine two-dimensional positions')
    terms={};diagonal=None
    if model['mode']=='MRT':
        for pair in model.get('ordered_pair_phasors',[]):
            u,v=pair['users_zero_based'];terms[u,v]=[exact_complex(x) for x in pair['phasors']]
        for pair in model.get('unordered_pair_phasors',[]):
            u,v=pair['users_zero_based'];values=[exact_complex(x) for x in pair['phasors']]
            need(u<v,'Native unordered phasor pair ordering')
            terms[u,v]=values;terms[v,u]=[zconj(x) for x in values]
        need(set(terms)=={(u,v) for u in range(3) for v in range(3) if u!=v} and all(len(x)==9 for x in terms.values()),'MRT pair schema')
    elif model['mode']=='ZF':
        los=model['LOS_phasors'];scale=[q(hx(x)) for x in model['binary64_sqrt_scale']]
        need(len(los)==9 and all(len(row)==3 for row in los) and len(scale)==3,'ZF primitive schema')
        weighted=[]
        for row in los:
            values=[]
            for u,raw in enumerate(row):
                z=exact_complex(raw);values.append((z[0]*scale[u],z[1]*scale[u]))
            weighted.append(values)
        diagonal=[[znorm(row[u])/4 for u in range(3)] for row in weighted]
        for u,v in itertools.combinations(range(3),2):
            values=[zmul(zconj(row[u]),row[v]) for row in weighted]
            terms[u,v]=[(x[0]/4,x[1]/4) for x in values]
    else:
        raise ValueError('Unsupported mode')
    return dict(constants,grid=grid,spacing=q(hx(model['minimum_distance'])),terms=terms,diagonal=diagonal,m=3,n=4)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path(__file__).resolve().parent/'four-frozen-binary64-models.json')
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    need(not args.output_dir.exists(),'Fresh outside-public output directory required')
    args.output_dir.mkdir(parents=True)
    report=dict(schema='portable-all126-own-frozen-binary64-global-grid-actual-v1',rows=[],errors=[],
                optimizer_calls=0,original_model_calls=0,MC_evaluations_or_draws=0,
                full2600_global_grid_gate=False,author_historical_target_recovered=False,
                original_reference_gate=False)
    before={};watched={};code=1
    try:
        root=Path(__file__).resolve().parent
        raw_manifest=(root/'manifest.json').read_bytes();manifest=json.loads(raw_manifest)
        watched={str(root/'manifest.json'):digest(raw_manifest)}
        for path in [Path(__file__).resolve(),args.input.resolve()]:
            expected=manifest['files'][path.name]['SHA256']
            raw=path.read_bytes();need(digest(raw)==expected,'Public source/input manifest mismatch')
            watched[str(path)]=expected
        before={path:digest(Path(path).read_bytes()) for path in watched}
        need(before==watched,'Public files changed before evaluation')
        fixture=json.loads(args.input.read_bytes())
        need(fixture['schema']=='four-frozen-binary64-D3g1-statistical-models-hex-v1','Wrong fixture schema')
        need(len(fixture['models'])==4 and {m['id'] for m in fixture['models']}=={'python-MRT','python-ZF','native-MRT','native-ZF'},'Exactly four own-language models required')
        report['original_source_bound_report_SHA256']=fixture['source_report_SHA256']
        for model in fixture['models']:
            exp=model['expected_from_actual_closed_private_verification']
            saved=exp['independent_global_product']
            row=enumerate_all126(load_operands(model),model['mode'],exp['independent_winner_zero_based'],Fraction(int(saved['numerator']),int(saved['denominator'])))
            row['model_id']=model['id'];row['language']=model['language']
            row['exact_enumeration_digest_matches_original_actual_report']=(row['all126_decision_and_exact_product_SHA256']==exp['all126_decision_and_exact_product_SHA256'])
            row['feasibility_and_exact_tie_counts_match_original_actual_report']=all(row[k]==exp[k] for k in ('spacing_feasible_sets','spacing_rejected_sets','number_of_exact_global_ties'))
            report['rows'].append(row)
        report['all_four_independent_complete_global_grid_and_original_exact_product_comparisons_pass']=all(
            row['independent_global_grid_gate_pass'] and row['exact_enumeration_digest_matches_original_actual_report'] and row['feasibility_and_exact_tie_counts_match_original_actual_report'] for row in report['rows'])
        code=0 if report['all_four_independent_complete_global_grid_and_original_exact_product_comparisons_pass'] else 2
    except Exception as exc:
        report['errors'].append(dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
        report['all_four_independent_complete_global_grid_and_original_exact_product_comparisons_pass']=False
        code=1
    finally:
        after={}
        for path in watched:
            try:after[path]=digest(Path(path).read_bytes())
            except OSError as exc:report['errors'].append(dict(type=type(exc).__name__,message=str(exc)))
        # Published report uses relative file identities, not local directories.
        report['finite_source_and_input_before']={Path(p).name:s for p,s in before.items()}
        report['finite_source_and_input_after']={Path(p).name:s for p,s in after.items()}
        report['finite_source_and_input_interval_closed']=bool(watched) and before==after==watched
        if not report['finite_source_and_input_interval_closed']:code=1
        report['actual_reader_exit_code']=code
        report['scope']='Independent exhaustive optimality of four supplied frozen binary64 operand models at one D3/g1 point. Original primitive provenance is separately source-bound; no entire2600, author protocol, symbolic trig, pruning or reference claim.'
        (args.output_dir/'ACTUAL_PORTABLE_ALL126_EXACT_GLOBAL_GRID_READBACK_V1.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(actual_exit_code=code,models=len(report['rows']),pass_all=report.get('all_four_independent_complete_global_grid_and_original_exact_product_comparisons_pass',False),source_input_closed=report['finite_source_and_input_interval_closed'])))
    return code


if __name__=='__main__':
    raise SystemExit(main())
