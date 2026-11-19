"""Projected-subgradient step-size experiment on the unchanged radio model.

The fixed-point loop and author stopping rule are copied from
upstream/main_problem.py (Lorenzo Miretti, GPL-2.0). Only the outer step length
is adapted from observed changes in the maximum AP power violation.
"""
import numpy as np
from numpy.linalg import norm

from optimized_problem import OptimizedProblem


class AdaptiveProblem(OptimizedProblem):
    growth = 1.05
    shrink = 0.5
    max_scale = 1.5
    min_scale = 0.25
    growth_alignment = 0.8
    shrink_alignment = -0.1
    decay_exponent = 0.5
    adapt_mode = 'violation'

    def solve(self, toll_fp=1e-3, toll_psg=1e-4, iter_max_psg=100,
              kappa=3, feas_only=False):
        self.solved = False
        self.feasible = False
        self.feasible_sum = True
        self.dual_obj = []
        self.powers = []
        self.step_trace = []
        sig = np.ones(self.L)
        p = self.SINR_target / (self.N * np.sum(self.Gamma, axis=1))
        scale = 1.0
        previous_direction = None
        previous_violation = None
        previous_dual_gap = None
        jj = 0
        while jj < iter_max_psg and not self.solved:
            self.solved_inner = False
            while not self.solved_inner:
                parameters = self.optimize_beamforming_parameters(p, sig)
                interf, signal, noise = self.compute_channel_coefficients(p, sig, parameters)
                SINR = self.compute_SINR(interf, signal, noise, p, sig)
                p_old = p
                p = np.array([self.SINR_target[k] * p[k] / SINR[k]
                              for k in range(self.K)])
                SINR = self.compute_SINR(interf, signal, noise, p, sig)
                if jj == 0 and np.sum(p) > np.sum(self.P_max):
                    self.solved_inner = True
                    self.feasible_sum = False
                elif abs(sum(p) - sum(p_old)) / sum(p_old) < toll_fp:
                    self.solved_inner = True

            dual = np.sum(p) - np.sum((sig - np.ones(self.L)) * self.P_max)
            self.dual_obj.append(dual)
            powers = self.compute_downlink_powers(interf, signal, noise, p, sig, SINR)
            self.powers.append(powers)
            dual_gap = sum(powers) - dual
            sub_grad = powers - self.P_max
            print('Dual: %.4f' % dual,
                  '| surrogate dual gap: %.4f' % abs(dual_gap),
                  '| max power gap: %.4f' % max(sub_grad),
                  '| max SINR gap: %.4f' % max(self.SINR_target - SINR))

            length = norm(sub_grad)
            direction = sub_grad / length if length > 0 else np.zeros_like(sub_grad)
            alignment = (float(previous_direction @ direction)
                         if previous_direction is not None else None)
            # Increase slightly on clear progress, shrink when AP violation
            # worsens, and bound the multiplier. Alignment mode is retained
            # solely to reproduce the unsuccessful development ablation.
            violation = max(0.0, float(np.max(sub_grad)))
            if self.adapt_mode == 'violation' and previous_violation is not None:
                if violation > previous_violation * 1.01 + 0.1:
                    scale = max(self.min_scale, scale * 0.7)
                elif violation < previous_violation * 0.8 and violation > toll_psg:
                    scale = min(self.max_scale, scale * self.growth)
                elif violation <= toll_psg and previous_dual_gap is not None \
                        and abs(dual_gap) < 0.8 * abs(previous_dual_gap):
                    scale = min(self.max_scale, scale * self.growth)
            elif self.adapt_mode == 'alignment' and alignment is not None:
                if alignment > self.growth_alignment:
                    scale = min(self.max_scale, scale * self.growth)
                elif alignment < self.shrink_alignment:
                    scale = max(self.min_scale, scale * self.shrink)
            step = kappa * scale / (jj + 1) ** self.decay_exponent
            self.step_trace.append({"iteration": jj + 1, "alignment": alignment,
                                    "scale": scale, "step": step,
                                    "max_power_gap_mw": float(np.max(sub_grad)),
                                    "surrogate_dual_gap_mw": float(dual_gap)})
            sig = np.maximum(sig + step * direction, np.ones(self.L))
            previous_direction = direction
            previous_violation = violation
            previous_dual_gap = float(dual_gap)

            if np.max(sub_grad) < toll_psg and (feas_only or dual_gap < toll_psg):
                self.feasible = True
                self.solved = True
            if dual > np.sum(self.P_max):
                self.feasible = False
                self.solved = True
            jj += 1
        self.p_opt = p
        self.sig_opt = sig
