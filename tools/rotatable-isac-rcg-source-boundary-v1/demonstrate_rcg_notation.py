"""Unit-circle demonstration of the IEEE early-version RCG notation.

F(z)=Re(z) is an illustrative smooth objective, not an experiment or a
claim that any stored ISAC instance has this objective.
"""
import json


def value(z):
    return z.real


def project(z, ambient):
    return ambient - (ambient * z.conjugate()).real * z


def retract(z, step):
    trial = z + step
    return trial / abs(trial)


def main():
    # With the standard real complex inner product, gradient of Re(z) is 1.
    z = 1j
    ambient = 1 + 0j
    tangent = project(z, ambient)
    printed_direction = -tangent
    correct_direction = tangent  # descent direction for -F
    printed_derivative = (ambient.conjugate() * printed_direction).real
    corrected_derivative = (ambient.conjugate() * correct_direction).real
    step = 0.1
    printed_value = value(retract(z, step * printed_direction))
    corrected_value = value(retract(z, step * correct_direction))
    # z=1 is the true circle maximizer: grad F is normal, not zero.
    z_star = 1 + 0j
    tangent_star = project(z_star, ambient)
    assert printed_derivative < 0 < corrected_derivative
    assert printed_value < value(z) < corrected_value
    assert abs(ambient) == 1 and abs(tangent_star) == 0
    print(json.dumps({'scope': 'illustrative scalar unit-circle objective',
                      'initial_utility': value(z),
                      'printed_direction_derivative': printed_derivative,
                      'corrected_direction_derivative': corrected_derivative,
                      'printed_retracted_utility': printed_value,
                      'corrected_retracted_utility': corrected_value,
                      'maximizer_ambient_gradient_norm': abs(ambient),
                      'maximizer_riemannian_gradient_norm': abs(tangent_star),
                      'saved_scientific_run_checked': False,
                      'final_typeset_publication_checked': False,
                      'full_paper_pass': False}, indent=2))


if __name__ == '__main__':
    main()
