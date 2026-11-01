"""Versioned correction of MIS literal-mode zero-displacement exit reporting.

The original RCG implementation remains unchanged. For supported policies,
this adapter changes only the returned stop reason when a simplex-boundary
projected step is zero and the literal row-mean gradient exceeds tolerance.
It rejects unknown policies before evaluation and does not alter iterates,
objective, directions, backtracking, or budgets.
"""
from types import FunctionType


def run_rcg(engine, z, evaluate, options):
    policy = options.get("non_descent_policy", "literal_printed")
    if type(policy) is not str or policy not in (
            "literal_printed", "documented_non_descent_restart"):
        raise ValueError("Unknown MIS non_descent_policy")
    original = engine.block_backtracking

    def corrected(state, gradient, direction, evaluator, value, opts):
        result = original(state, gradient, direction, evaluator, value, opts)
        candidate, used_direction, info, reason = result
        if (policy == "literal_printed"
                and reason == "gradient_tolerance"
                and engine.norm(gradient) > opts["gradient_tolerance"]):
            reason = "zero_projected_PR_direction"
        return candidate, used_direction, info, reason

    namespace = dict(engine.rcg.__globals__)
    namespace["block_backtracking"] = corrected
    entry = FunctionType(engine.rcg.__code__, namespace, engine.rcg.__name__,
                         engine.rcg.__defaults__, engine.rcg.__closure__)
    return entry(z, evaluate, options)
