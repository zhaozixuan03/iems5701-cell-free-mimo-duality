"""Safeguarded Anderson acceleration of the author's inner power fixed point.

The outer projected subgradient, radio model and infeasibility check follow
upstream/main_problem.py (Lorenzo Miretti, GPL-2.0). The accelerated inner
proposal is accepted only when it is positive, bounded, and predicts a smaller
fixed-point residual; otherwise the author's fixed-point step is used.
"""
import numpy as np
from numpy.linalg import norm

from optimized_problem import OptimizedProblem


class AndersonProblem(OptimizedProblem):
    memory = 3
    damping = 0.8
    improvement_factor = 0.8

    def solve(self, toll_fp=1e-3, toll_psg=1e-4, iter_max_psg=100,
              kappa=3, feas_only=False):
        self.solved = False
        self.feasible = False
        self.feasible_sum = True
        self.dual_obj = []
        self.powers = []
        self.anderson_stats = {"accepted": 0, "rejected": 0, "resets": 0}
        sig = np.ones(self.L)
        p = self.SINR_target / (self.N * np.sum(self.Gamma, axis=1))
        jj = 0
        while jj < iter_max_psg and not self.solved:
            self.solved_inner = False
            history_f = []
            history_r = []
            previous_residual = None
            previous_accelerated = False
            while not self.solved_inner:
                parameters = self.optimize_beamforming_parameters(p, sig)
                interf, signal, noise = self.compute_channel_coefficients(p, sig, parameters)
                SINR = self.compute_SINR(interf, signal, noise, p, sig)
                p_old = p
                base = np.array([self.SINR_target[k] * p[k] / SINR[k]
                                 for k in range(self.K)])
                residual = base - p_old
                residual_size = norm(residual)
                # A bad previous extrapolation restarts with the ordinary map.
                if previous_accelerated and previous_residual is not None \
                        and residual_size > 1.5 * previous_residual:
                    history_f.clear()
                    history_r.clear()
                    self.anderson_stats['resets'] += 1
                history_f.append(base.copy())
                history_r.append(residual.copy())
                history_f = history_f[-self.memory:]
                history_r = history_r[-self.memory:]
                p = base
                accelerated = False
                # Keep the first outer iteration exactly as the author wrote
                # it, including the early sum-power infeasibility screen.
                if jj > 0 and len(history_r) >= 2 and residual_size > 0:
                    d = np.column_stack([r - residual for r in history_r[:-1]])
                    try:
                        weights, *_ = np.linalg.lstsq(d, -residual, rcond=1e-10)
                        coeff = np.r_[weights, 1 - np.sum(weights)]
                        predicted = residual + d @ weights
                        candidate = np.sum([c * f for c, f in zip(coeff, history_f)], axis=0)
                        candidate = self.damping * candidate + (1-self.damping) * base
                        if (np.all(np.isfinite(candidate)) and np.all(candidate > 0)
                                and np.max(np.abs(coeff)) <= 2
                                and norm(candidate-base) <= 2 * residual_size
                                and norm(predicted) <= self.improvement_factor * residual_size):
                            p = candidate
                            accelerated = True
                            self.anderson_stats['accepted'] += 1
                        else:
                            self.anderson_stats['rejected'] += 1
                    except np.linalg.LinAlgError:
                        self.anderson_stats['rejected'] += 1
                SINR = self.compute_SINR(interf, signal, noise, p, sig)
                if jj == 0 and np.sum(p) > np.sum(self.P_max):
                    self.solved_inner = True
                    self.feasible_sum = False
                elif (abs(sum(p)-sum(p_old))/sum(p_old) < toll_fp
                      and (jj == 0 or residual_size / max(norm(p_old), 1e-30) < toll_fp)):
                    self.solved_inner = True
                previous_residual = residual_size
                previous_accelerated = accelerated

            dual = np.sum(p)-np.sum((sig-np.ones(self.L))*self.P_max)
            self.dual_obj.append(dual)
            powers = self.compute_downlink_powers(interf, signal, noise, p, sig, SINR)
            self.powers.append(powers)
            dual_gap = sum(powers)-dual
            sub_grad = powers-self.P_max
            print('Dual: %.4f' % dual, '| surrogate dual gap: %.4f' % abs(dual_gap),
                  '| max power gap: %.4f' % max(sub_grad),
                  '| max SINR gap: %.4f' % max(self.SINR_target-SINR))
            length = norm(sub_grad)
            if length > 0:
                sig = np.maximum(sig + kappa/np.sqrt(jj+1)*sub_grad/length,
                                 np.ones(self.L))
            if np.max(sub_grad) < toll_psg and (feas_only or dual_gap < toll_psg):
                self.feasible = True
                self.solved = True
            if dual > np.sum(self.P_max):
                self.feasible = False
                self.solved = True
            jj += 1
        self.p_opt = p
        self.sig_opt = sig
