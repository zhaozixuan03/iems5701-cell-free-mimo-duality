"""Experimental AP association using large-scale gain and current AP load.

The author's strongest-Q association and channel-estimation construction are
in upstream/main_problem.py (Lorenzo Miretti, GPL-2.0). This class changes
only the association; it keeps Q, channel realizations and solver unchanged.
"""
import numpy as np

from optimized_problem import OptimizedProblem


class LoadAwareProblem(OptimizedProblem):
    load_penalty = 1.0

    def set_constraints(self, SINR_target, P_max, Q, CSI):
        super().set_constraints(SINR_target, P_max, Q, CSI)
        load = np.zeros(self.L, dtype=int)
        clusters = np.empty((self.K, Q), dtype=int)
        # Serve users with the weakest best link first. This avoids spending
        # their few strong AP choices on users with many alternatives.
        order = np.argsort(np.max(self.Gamma, axis=1))
        for k in order:
            score = self.Gamma[k] / (1.0 + self.load_penalty * load)
            chosen = np.argsort(score)[-Q:]
            clusters[k] = chosen[np.argsort(self.Gamma[k, chosen])]
            load[chosen] += 1
        self.UE_clusters = clusters
        self.AP_clusters = [[] for _ in range(self.L)]
        for k in range(self.K):
            for l in clusters[k]:
                self.AP_clusters[l].append(k)
        self.H_hat_list = []
        for H in self.H_list:
            H_hat = [np.zeros((self.K, self.N), dtype=complex)
                     for _ in range(self.L)]
            for l, users in enumerate(self.AP_clusters):
                H_hat[l][users] = H[l][users]
            self.H_hat_list.append(H_hat)
        self.Psi = np.copy(self.Gamma)
        for l, users in enumerate(self.AP_clusters):
            self.Psi[users, l] = 0
        self._h_stack = None
        self._response_cache = None
        self.ap_load = load
