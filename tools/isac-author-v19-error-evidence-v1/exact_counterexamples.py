"""Exact algebraic counterexamples for the specified arXiv author version.

No simulation, fitted parameter, source-provenance or full-paper claim is made.
"""
from fractions import Fraction as F


def main():
    # Scalar u=v=W=1; sqrt(G_B)=2 and sqrt(G_R)=1.
    root_b, root_r = F(2), F(1)
    direct = (root_b + root_r) ** 2
    correctly_expanded = root_b**2 + 2 * root_b * root_r + root_r**2
    printed_expansion = F(1) + 2 * root_b * root_r + root_b * root_r
    assert direct == correctly_expanded == 9
    assert printed_expansion == 7 and printed_expansion != direct

    # Two-element complex example: Q=W W^H, u=(1,i), v=(1,1), W=(1,i).
    # Integer-valued real/imaginary intermediates are exactly representable.
    u, v, w = (1, 1j), (1, 1), (1, 1j)
    dot = lambda x, y: sum(a.conjugate() * b for a, b in zip(x, y))
    abs2 = lambda z: z.real * z.real + z.imag * z.imag
    uw, vw = dot(u, w), dot(v, w)
    direct_term, reflected_term = abs2(uw), abs2(vw)
    cross = (uw * vw.conjugate()).real
    field = tuple(2 * a + b for a, b in zip(u, v))
    field_power = abs2(dot(field, w))
    correct_complex = 4 * direct_term + 4 * cross + reflected_term
    printed_complex = direct_term + 4 * cross + 2 * reflected_term
    assert field_power == correct_complex == 26
    assert printed_complex == 16 and printed_complex != field_power

    # For p=0 and nonzero desired energy, every positive scale gives NMSE 1.
    desired_energy, positive_iota = F(3), F(2)
    assert (positive_iota**2 * desired_energy) / (positive_iota**2 * desired_energy) == 1

    # The practical update nevertheless returns iota=0 when W=0 implies p=0.
    eps = F(1, 10)
    pattern_energy, overlap = F(0), F(0)
    safeguarded_iota = pattern_energy / (overlap + eps)
    assert safeguarded_iota == 0  # NMSE denominator iota**2 * ||p_d||**2 is zero.

    # p=(0,1), p_d=(1,0): d=0, c=e=1; the practical selection is finite.
    pattern_energy, desired_energy = F(1), F(1)
    safeguarded_iota = pattern_energy / eps
    nmse = (safeguarded_iota**2 + 1) / (safeguarded_iota**2 * desired_energy)
    assert safeguarded_iota == 10 and nmse == F(101, 100)
    print("PASS: scalar 9 versus 7; complex 26 versus 16; zero pattern has NMSE 1 at positive scale but update selects zero; disjoint-pattern safeguarded NMSE=101/100")


if __name__ == '__main__':
    main()
