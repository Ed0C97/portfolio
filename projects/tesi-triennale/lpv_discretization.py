# Portfolio excerpt, adapted.
"""Polytopic LPV model for lateral control.

MPC state x = [vy, r], input u = [delta_f], scheduling rho = [vx, mu].

Lateral subsystem linearized at polytope vertices, discretized by exact ZOH
(Van Loan), then interpolated bilinearly at runtime.
"""
from typing import Callable, List, Tuple

import numpy as np
from scipy.linalg import expm

IVY, IR, IDELTA = 4, 5, 0


class LPVModel:
    """Polytopic LPV model for lateral control.

    linearize_fn(state) returns continuous-time Jacobians (A_full, B_full) of
    the vehicle model at state; we keep only the lateral [vy, r] / [delta] block.
    """

    def __init__(self, linearize_fn: Callable[[np.ndarray], Tuple[np.ndarray, np.ndarray]],
                 set_mu_fn: Callable[[float], None],
                 vx_range: Tuple[float, float] = (5.0, 35.0),
                 mu_range: Tuple[float, float] = (0.4, 1.1),
                 dt: float = 0.1):
        self._linearize = linearize_fn
        self._set_mu = set_mu_fn
        self.vx_min, self.vx_max = vx_range
        self.mu_min, self.mu_max = mu_range
        self.dt = float(dt)

        self.vertices = [
            (self.vx_min, self.mu_min),
            (self.vx_max, self.mu_min),
            (self.vx_max, self.mu_max),
            (self.vx_min, self.mu_max),
        ]
        self.vertex_systems = self._compute_vertex_systems()

    def _compute_vertex_systems(self) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Linearize and discretize the lateral subsystem at each polytope vertex."""
        systems = []
        state_eq = np.zeros(6)

        for vx, mu in self.vertices:
            self._set_mu(mu)
            state_eq[IVX_:= 3] = vx

            Ac_full, Bc_full = self._linearize(state_eq)
            A_lat = np.array([[Ac_full[IVY, IVY], Ac_full[IVY, IR]],
                              [Ac_full[IR, IVY],  Ac_full[IR, IR]]])
            B_lat = np.array([[Bc_full[IVY, IDELTA]],
                              [Bc_full[IR, IDELTA]]])

            systems.append(self._zoh_discretize(A_lat, B_lat))
        return systems

    def _zoh_discretize(self, A: np.ndarray, B: np.ndarray
                        ) -> Tuple[np.ndarray, np.ndarray]:
        """Exact zero-order-hold discretization via Van Loan (1978).

        ZOH is exact for the held LTI segment, so it stays stable at large dt
        where explicit Euler diverges. One matrix exponential of the augmented
        block gives Ad and Bd together:

            M = [ A  B ] * dt   =>   expm(M) = [ Ad  Bd ]
                [ 0  0 ]                        [  0   I ]
        """
        n, m = A.shape[0], B.shape[1]
        M = np.zeros((n + m, n + m))
        M[:n, :n] = A * self.dt
        M[:n, n:] = B * self.dt
        eM = expm(M)
        return eM[:n, :n], eM[:n, n:]

    def get_system_matrices(self, vx: float, mu: float
                            ) -> Tuple[np.ndarray, np.ndarray]:
        """Return discrete (Ad, Bd) at scheduling point rho = [vx, mu]."""
        vx = np.clip(vx, self.vx_min, self.vx_max)
        mu = np.clip(mu, self.mu_min, self.mu_max)

        # bilinear weights over the four (vx, mu) corners
        a = (vx - self.vx_min) / (self.vx_max - self.vx_min)
        b = (mu - self.mu_min) / (self.mu_max - self.mu_min)
        weights = [(1 - a) * (1 - b), a * (1 - b), a * b, (1 - a) * b]

        Ad = np.zeros((2, 2))
        Bd = np.zeros((2, 1))
        for w, (Ad_i, Bd_i) in zip(weights, self.vertex_systems):
            Ad += w * Ad_i
            Bd += w * Bd_i
        return Ad, Bd
