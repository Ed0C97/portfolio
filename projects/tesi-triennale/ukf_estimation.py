# Portfolio excerpt, adapted. Reusable building blocks of an Unscented Kalman Filter.
# Merged from two source files; comments condensed/translated. Textbook estimation
# (Van der Merwe 2004; Bar-Shalom et al. 2001); the application-specific filter
# (process/measurement models, parameter learning) is intentionally not included.
"""Scaled sigma points and a chi-squared consistency monitor for the UKF."""
from __future__ import annotations

from collections import deque

import numpy as np
from scipy.stats import chi2


class MerweScaledSigmaPoints:
    """Generate 2n+1 sigma points and weights for the Van der Merwe scaled unscented transform.

    beta=2 is the standard choice for Gaussian priors.
    """

    def __init__(self, n: int, alpha: float = 1e-3,
                 beta: float = 2.0, kappa: float = 0.0):
        self.n = n
        self.alpha = alpha
        self.beta = beta
        self.kappa = kappa
        self.lambda_ = alpha ** 2 * (n + kappa) - n
        self._compute_weights()

    def _compute_weights(self) -> None:
        n, lam = self.n, self.lambda_
        self.Wm = np.full(2 * n + 1, 1.0 / (2.0 * (n + lam)))
        self.Wc = np.full(2 * n + 1, 1.0 / (2.0 * (n + lam)))
        self.Wm[0] = lam / (n + lam)
        self.Wc[0] = lam / (n + lam) + (1.0 - self.alpha ** 2 + self.beta)

    def sigma_points(self, x: np.ndarray, P: np.ndarray) -> np.ndarray:
        """Return the 2n+1 sigma points as rows (shape 2n+1 x n).

        Cholesky needs P positive definite; a numerically indefinite covariance
        will raise here rather than degrade silently.
        """
        n = self.n
        S = np.linalg.cholesky((n + self.lambda_) * P)
        sigmas = np.zeros((2 * n + 1, n))
        sigmas[0] = x
        for i in range(n):
            sigmas[i + 1] = x + S[i]
            sigmas[n + i + 1] = x - S[i]
        return sigmas


class ConsistencyCheck:
    """Flag filter divergence from the chi-squared statistics of the innovations.

    Per step NIS = nu^T S^-1 nu is chi-squared with ny dof when the filter is
    consistent. We gate on the violation rate over a sliding window rather than a
    single NIS, so one outlier never trips the alarm.
    """

    def __init__(self, ny: int = 3, confidence: float = 0.95,
                 window: int = 50, violation_rate_threshold: float = 0.6):
        self.ny = ny
        self.threshold = chi2.ppf(confidence, df=ny)
        self.window = window
        self._vr_threshold = violation_rate_threshold

        self._buffer: deque = deque(maxlen=window)
        self._violations: deque = deque(maxlen=window)

        self.is_consistent = True
        self.chi2_stat = 0.0
        self.violation_rate = 0.0

    def update(self, innovation: np.ndarray, S: np.ndarray) -> bool:
        """Feed one innovation nu and its covariance S; return whether the filter is still consistent."""
        S_inv = np.linalg.inv(S)
        eps = float(innovation @ S_inv @ innovation)
        self.chi2_stat = eps

        self._buffer.append(eps)
        self._violations.append(float(eps > self.threshold))
        self.violation_rate = float(np.mean(self._violations)) if self._violations else 0.0

        # hold off until the window is half full, otherwise startup transients read as divergence
        min_samples = max(1, self.window // 2)
        if len(self._violations) >= min_samples:
            self.is_consistent = self.violation_rate < self._vr_threshold
        else:
            self.is_consistent = True
        return self.is_consistent

    @property
    def mean_nis(self) -> float:
        """Windowed mean NIS; sits near ny when the filter is consistent."""
        return float(np.mean(self._buffer)) if self._buffer else 0.0
