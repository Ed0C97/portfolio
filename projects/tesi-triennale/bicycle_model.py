# Portfolio excerpt, adapted. Single-track (bicycle) vehicle dynamics model.
# Trimmed from a thesis on autonomous-vehicle control; comments condensed/translated.
"""Single-track vehicle dynamics with Pacejka tyre forces.

state x = [x, y, psi, vx, vy, r], input u = [delta_f, T_cmd].
RK4 at 100 Hz; lateral force from the Magic Formula, first-order motor lag.
"""
from __future__ import annotations

import numpy as np
from typing import Dict, Optional, Tuple

IX, IY, IPSI, IVX, IVY, IR = range(6)
IDELTA, ITORQUE = range(2)


class BicycleModel:
    """Single-track dynamics with Pacejka tyre forces."""

    # illustrative values, not a real vehicle
    DEFAULT_PARAMS: Dict[str, float] = dict(
        m=350.0, Iz=450.0, a=1.1, b=1.4,
        Cf0=80000.0, Cr0=90000.0, mu=1.05,
        B_pac=10.0, C_pac=1.9, D_pac=1.0, E_pac=0.97,
        Cd=1.15, Af=1.1, rho_air=1.225,
        R_eff=0.2286, T_max=230.0, tau_motor=0.005, delta_max=0.35,
        vx_min=3.0, vx_max=35.0, ax_min=-15.0,
    )

    def __init__(self, params: Optional[Dict[str, float]] = None) -> None:
        self.p: Dict[str, float] = dict(self.DEFAULT_PARAMS)
        if params:
            self.p.update(params)
        self._T_actual: float = 0.0

    # --- force / lag sub-models --------------------------------------------
    @staticmethod
    def _pacejka(alpha, B, C, D, E, mu, C_stiffness):
        # rescale the peak so the small-slip slope equals the supplied cornering stiffness
        D_scaled = C_stiffness / (B * C)
        Ba = B * alpha
        return mu * D_scaled * np.sin(C * np.arctan(Ba - E * (Ba - np.arctan(Ba))))

    def _slip_angles(self, vx, vy, r, delta):
        # floor vx so the slip angle doesn't blow up as the car comes to a stop
        vx_safe = max(abs(vx), self.p["vx_min"])
        alpha_f = delta - np.arctan2(vy + self.p["a"] * r, vx_safe)
        alpha_r = -np.arctan2(vy - self.p["b"] * r, vx_safe)
        return float(alpha_f), float(alpha_r)

    def _aero_drag(self, vx):
        return 0.5 * self.p["rho_air"] * self.p["Cd"] * self.p["Af"] * vx ** 2

    def _powertrain_step(self, T_cmd, dt):
        # first-order lag; exact discrete coefficient for tau_motor over this dt
        alpha_pt = 1.0 - np.exp(-dt / self.p["tau_motor"])
        self._T_actual += alpha_pt * (T_cmd - self._T_actual)
        return self._T_actual

    # --- continuous-time dynamics ------------------------------------------
    def _dynamics(self, state, delta, T_eff):
        _x, _y, psi, vx, vy, r = state
        p = self.p
        Fx = T_eff / p["R_eff"]
        alpha_f, alpha_r = self._slip_angles(vx, vy, r, delta)
        Fyf = self._pacejka(alpha_f, p["B_pac"], p["C_pac"], p["D_pac"],
                            p["E_pac"], p["mu"], p["Cf0"])
        Fyr = self._pacejka(alpha_r, p["B_pac"], p["C_pac"], p["D_pac"],
                            p["E_pac"], p["mu"], p["Cr0"])
        F_drag = self._aero_drag(vx)
        cd, sd = np.cos(delta), np.sin(delta)
        cp, sp = np.cos(psi), np.sin(psi)
        return np.array([
            vx * cp - vy * sp,
            vx * sp + vy * cp,
            r,
            (Fx - Fyf * sd - F_drag) / p["m"] + vy * r,
            (Fyf * cd + Fyr) / p["m"] - vx * r,
            (p["a"] * Fyf * cd - p["b"] * Fyr) / p["Iz"],
        ])

    # --- public API --------------------------------------------------------
    def step(self, state: np.ndarray, action: np.ndarray, dt: float) -> np.ndarray:
        """Integrate one RK4 step of duration dt."""
        state = np.asarray(state, dtype=np.float64)
        action = np.asarray(action, dtype=np.float64)
        delta = np.clip(action[IDELTA], -self.p["delta_max"], self.p["delta_max"])
        T_cmd = np.clip(action[ITORQUE], self.p["ax_min"] * self.p["m"], self.p["T_max"])
        T_eff = self._powertrain_step(T_cmd, dt)

        def f(s):
            return self._dynamics(s, delta, T_eff)

        k1 = f(state)
        k2 = f(state + 0.5 * dt * k1)
        k3 = f(state + 0.5 * dt * k2)
        k4 = f(state + dt * k3)
        ns = state + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        ns[IVX] = np.clip(ns[IVX], self.p["vx_min"], self.p["vx_max"])
        ns[IPSI] = np.arctan2(np.sin(ns[IPSI]), np.cos(ns[IPSI]))  # wrap heading to (-pi, pi]
        return ns

    def get_linearized(self, state: np.ndarray,
                       params: Optional[Dict[str, float]] = None
                       ) -> Tuple[np.ndarray, np.ndarray]:
        """Return Jacobians A (6x6) and B (6x2) at state via central differences.

        params, if given, are applied for the linearization and restored after, so
        you can linearize at hypothetical parameter values without mutating the model.
        """
        old = None
        if params:
            old = dict(self.p)
            self.p.update(params)
        state = np.asarray(state, dtype=np.float64)
        eps = 1e-5
        A = np.zeros((6, 6))
        for i in range(6):
            sp, sm = state.copy(), state.copy()
            sp[i] += eps
            sm[i] -= eps
            A[:, i] = (self._dynamics(sp, 0.0, 0.0) -
                       self._dynamics(sm, 0.0, 0.0)) / (2 * eps)
        B = np.zeros((6, 2))
        B[:, 0] = (self._dynamics(state, eps, 0.0) -
                   self._dynamics(state, -eps, 0.0)) / (2 * eps)
        B[:, 1] = (self._dynamics(state, 0.0, eps) -
                   self._dynamics(state, 0.0, -eps)) / (2 * eps)
        if old:
            self.p = old
        return A, B

    def reset_powertrain(self) -> None:
        self._T_actual = 0.0

    def update_params(self, params: Dict[str, float]) -> None:
        self.p.update(params)
