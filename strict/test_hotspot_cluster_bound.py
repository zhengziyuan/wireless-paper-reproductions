"""Independent exact algebra of the qualified current-model cluster bound.

This proves no published-paper bound or final source identity. Matrix-sandwich
and noise-domain assumptions require separate actual numerical evidence.
"""
from fractions import Fraction as F
import random
import unittest


class ClusterBoundAlgebra(unittest.TestCase):
    def test_exact_pair_merging_polynomial_and_necessary_scope(self):
        rng=random.Random(3309957)
        for _ in range(500):
            lower=F(rng.randrange(1,100),73)
            upper=lower*(1+F(rng.randrange(101),100))
            a,b,others=(F(rng.randrange(101),17) for _ in range(3))
            constant=1+lower*others
            left=constant*(constant+lower*b+upper*a)*(constant+lower*a+upper*b)
            right=(constant+upper*(a+b))*(constant+lower*a)*(constant+lower*b)
            exact_gap=upper*a*b*(constant*(2*lower-upper)+lower**2*(a+b))
            self.assertEqual(right-left,exact_gap)
            self.assertGreaterEqual(exact_gap,0)
        # Without upper<=2*lower, the theorem is not generally true.
        lower,upper,a,b,constant=F(1),F(3),F(1,100),F(1,100),F(1)
        self.assertLess(upper*a*b*(constant*(2*lower-upper)+lower**2*(a+b)),0)

    def test_all_user_merges_keep_total_power_and_other_denominators(self):
        lower,upper=F(9,10),F(11,10)
        values=[F(i,13) for i in range(1,17)]
        total=sum(values)
        product=lambda xs:__import__('functools').reduce(lambda a,b:a*b,
            (1+upper*x/(1+lower*(total-x)) for x in xs),F(1))
        previous=product(values)
        while len(values)>1:
            values=[values[0]+values[1],*values[2:]]
            actual=product(values)
            self.assertGreaterEqual(actual,previous)
            self.assertEqual(sum(values),total)
            previous=actual
        self.assertEqual(previous,1+upper*total)


if __name__=='__main__':unittest.main()
