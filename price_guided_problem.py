"""AP association weighted by dual AP prices from a separate pilot solve.

The radio model and solver derive from Lorenzo Miretti's GPL-2.0 code in
upstream/main_problem.py. This class changes only the Q APs serving each UE.
"""
import numpy as np

from optimized_problem import OptimizedProblem


class PriceGuidedProblem(OptimizedProblem):
    def __init__(self, *args, prices, **kwargs):
        super().__init__(*args, **kwargs)
        self.prices = np.asarray(prices, dtype=float)
        if self.prices.shape != (self.L,) or not np.all(np.isfinite(self.prices)) \
                or np.any(self.prices < 1):
            raise ValueError('AP prices must be finite, length L, and at least one')

    def set_constraints(self, SINR_target, P_max, Q, CSI):
        super().set_constraints(SINR_target, P_max, Q, CSI)
        # A large multiplier means that extra power at this AP is expensive
        # in the dual problem. Keep exactly Q APs per UE, using only long-term
        # channel gains and the pilot-sample prices for selection.
        score = self.Gamma / self.prices[None, :]
        selected = np.argsort(score, axis=1)[:, -Q:]
        clusters = np.take_along_axis(
            selected, np.argsort(np.take_along_axis(self.Gamma, selected, axis=1), axis=1), axis=1
        )
        self.UE_clusters = clusters
        self.AP_clusters = [[] for _ in range(self.L)]
        for k in range(self.K):
            for l in clusters[k]:
                self.AP_clusters[l].append(k)
        self.H_hat_list = []
        for H in self.H_list:
            H_hat = [np.zeros((self.K, self.N), dtype=complex) for _ in range(self.L)]
            for l, users in enumerate(self.AP_clusters):
                H_hat[l][users] = H[l][users]
            self.H_hat_list.append(H_hat)
        self.Psi = np.copy(self.Gamma)
        for l, users in enumerate(self.AP_clusters):
            self.Psi[users, l] = 0
        self._h_stack = None
        self._response_cache = None
