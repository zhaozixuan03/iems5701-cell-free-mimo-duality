"""Check that the variable-size beamforming algebra reduces to fixed Q=4."""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from optimized_problem import OptimizedProblem
from variable_q_problem import VariableQProblem


def main():
    for seed in (109, 137, 166):
        problems = []
        for cls in (OptimizedProblem, VariableQProblem):
            np.random.seed(seed)
            p = cls(16, 16, 4, 1000, N_sim=10)
            p.set_constraints((2**3.5-1)*np.ones(16), 1000*np.ones(16), 4, 'local')
            problems.append(p)
        base, variable = problems
        assert sum(map(len, variable.UE_clusters)) == 64
        assert np.array_equal(base.Gamma, variable.Gamma)
        assert np.array_equal(base.H_list[0][0], variable.H_list[0][0])
        # Force equal associations to isolate the variable-dimensional solver.
        variable.UE_clusters = [c.copy() for c in base.UE_clusters]
        variable.AP_clusters = base.AP_clusters
        variable.H_hat_list = base.H_hat_list
        variable.Psi = base.Psi
        variable._h_stack = None
        power = base.SINR_target/(base.N*np.sum(base.Gamma,axis=1))
        sig = np.ones(16)
        a = base.optimize_beamforming_parameters(power,sig)
        b = variable.optimize_beamforming_parameters(power,sig)
        assert max(np.max(np.abs(x-y)) for x,y in zip(a,b)) < 1e-10
        ac = base.compute_channel_coefficients(power,sig,a)
        bc = variable.compute_channel_coefficients(power,sig,b)
        assert max(np.max(np.abs(x-y)) for x,y in zip(ac,bc)) < 1e-10
        print(seed,'equal-association coefficient and channel checks passed')


if __name__ == '__main__':
    main()
