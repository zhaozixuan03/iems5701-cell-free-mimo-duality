"""Topology-only CSI budget allocation across users, retaining total AP links.

The radio model and power solver derive from Lorenzo Miretti's GPL-2.0
upstream/main_problem.py. This class changes user AP cluster cardinalities.
"""
import numpy as np
from numpy.linalg import solve

from optimized_problem import OptimizedProblem


class VariableQProblem(OptimizedProblem):
    def set_constraints(self, SINR_target, P_max, Q, CSI):
        if Q != 4 or self.K != 16:
            raise ValueError('This prespecified comparison uses K=16, Q=4')
        super().set_constraints(SINR_target, P_max, Q, CSI)
        # The four weakest users receive 6 APs, the four strongest receive 2,
        # and the other eight receive 4. Total measured AP-UE links stays 64.
        strongest_q_sum = np.sort(self.Gamma, axis=1)[:, -Q:].sum(axis=1)
        order = np.argsort(strongest_q_sum)
        counts = np.full(self.K, Q, dtype=int)
        counts[order[:4]] = 6
        counts[order[-4:]] = 2
        assert counts.sum() == self.K * Q
        self.q_by_user = counts
        self.UE_clusters = [np.argsort(self.Gamma[k])[-counts[k]:]
                            for k in range(self.K)]
        self.AP_clusters = [[] for _ in range(self.L)]
        for k, cluster in enumerate(self.UE_clusters):
            for l in cluster:
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

    def optimize_beamforming_parameters(self, p, sig):
        if self.CSI != 'local':
            raise ValueError('Variable-Q implementation supports local CSI only')
        root_p = np.sqrt(p)
        pi_list, responses = [], []
        for l, h in enumerate(self._channels_by_ap()):
            hp = h * root_p[None, :, None]
            hh = hp.conj().transpose(0, 2, 1)
            m = hh @ hp + (p @ self.Psi[:, l] + sig[l]) * np.eye(self.N)
            x = solve(m, hh)
            responses.append(x)
            pi_list.append(np.mean(hp @ x, axis=0))
        self._response_cache = (p.copy(), sig.copy(), responses)
        c_list = [np.zeros((self.K, self.K), dtype=complex) for _ in range(self.L)]
        for k, cluster in enumerate(self.UE_clusters):
            q_count = len(cluster)
            a = np.zeros((self.K*q_count, self.K*q_count), dtype=complex)
            b = np.zeros(self.K*q_count, dtype=complex)
            for q in range(q_count):
                b[self.K*q + k] = 1
                for j in range(q_count):
                    a[self.K*q:self.K*(q+1), self.K*j:self.K*(j+1)] = (
                        np.eye(self.K) if q == j else pi_list[cluster[j]]
                    )
            c = solve(a, b)
            for q, l in enumerate(cluster):
                c_list[l][:, k] = c[self.K*q:self.K*(q+1)]
        return c_list
