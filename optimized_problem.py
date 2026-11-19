"""Algebraically equivalent linear-solve acceleration of the author's code.

Copyright (C) 2026 project contributors. GPL-2.0-only, see upstream/LICENSE.
The model and stopping rule remain in upstream/main_problem.py.
"""
import numpy as np
from numpy.linalg import solve
from upstream.main_problem import Problem, herm


class OptimizedProblem(Problem):
    def optimize_beamforming_parameters(self, p, sig):
        if self.CSI != "local":
            return super().optimize_beamforming_parameters(p, sig)
        K, L, N, Q = self.K, self.L, self.N, self.Q
        root_p = np.sqrt(p)
        pi_list = []
        for l in range(L):
            h = np.stack([self.H_hat_list[n][l] for n in range(self.N_sim)])
            h = h * root_p[None, :, None]
            hh = h.conj().transpose(0, 2, 1)
            m = hh @ h + (p @ self.Psi[:, l] + sig[l]) * np.eye(N)
            x = solve(m, hh)
            pi_list.append(np.mean(h @ x, axis=0))
        c_list = [np.zeros((K, K), dtype=complex) for _ in range(L)]
        b = np.zeros((K * Q, K), dtype=complex)
        for q in range(Q):
            b[K*q:K*(q+1), :] = np.eye(K)
        for k in range(K):
            a = np.zeros((K*Q, K*Q), dtype=complex)
            for q in range(Q):
                for j in range(Q):
                    a[K*q:K*(q+1), K*j:K*(j+1)] = (
                        np.eye(K) if q == j else pi_list[self.UE_clusters[k][j]]
                    )
            c = solve(a, b[:, k])
            for q in range(Q):
                l = self.UE_clusters[k][q]
                c_list[l][:, k] = c[K*q:K*(q+1)]
        return c_list

    def beamformers(self, H_hat, p, sig, parameters):
        if self.CSI != "local":
            return super().beamformers(H_hat, p, sig, parameters)
        root_p = np.sqrt(p)
        out = []
        for l in range(self.L):
            h = H_hat[l]
            m = herm(h) @ np.diag(p) @ h + (
                p @ self.Psi[:, l] + sig[l]
            ) * np.eye(self.N)
            out.append(solve(m, herm(h) * root_p[None, :]) @ parameters[l])
        return out

    def compute_downlink_powers(self, interf, signal, noise, p, sig, SINR):
        noise_ue = noise.T @ sig
        d = np.diag(signal / np.asarray(SINR))
        a = d - interf
        q = solve(a, (d - interf.T) @ p / noise_ue)
        return noise @ q
