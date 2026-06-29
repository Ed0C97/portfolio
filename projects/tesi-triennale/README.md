# tesi-triennale: control and estimation excerpts

Selected, self-contained excerpts from the supporting numerical layers of a bachelor's thesis on a hybrid control architecture for autonomous vehicles. These show estimation, dynamics-modelling and control-discretization craft; the learning/control method that is the actual contribution is kept out (see "Deliberately omitted").

**Context:** see [../tesi-triennale.md](../tesi-triennale.md) for the project overview.

**Stack:** Python 3, NumPy, SciPy (`scipy.linalg.expm`, `scipy.stats.chi2`). No framework dependencies in these excerpts, just pure numerical code.

## What each file shows

- **`bicycle_model.py`**: A dynamic single-track (bicycle) vehicle model: nonlinear Pacejka "Magic Formula" tyre forces with friction/stiffness scaling, aerodynamic drag, first-order powertrain lag, and 4th-order Runge-Kutta integration. Includes a central-difference Jacobian linearizer that operates on temporary parameter overrides without mutating model state, and a slip-angle computation with a `vx_min` clamp to keep `atan2` well-conditioned at low speed.
- **`ukf_estimation.py`**: The reusable estimation core of an Unscented Kalman Filter: Van der Merwe scaled sigma-point generation with correct mean/covariance weights, plus a chi-squared (NIS) filter-consistency monitor that replaces a brittle +1/-1 counter with a deque-backed sliding window of normalized-innovation violations, eliminating verdict flickering. Textbook estimation (Van der Merwe 2004; Bar-Shalom et al. 2001).
- **`lpv_discretization.py`**: A Linear-Parameter-Varying lateral model: bilinear interpolation over a 2-D scheduling polytope, with each polytope vertex discretized by exact zero-order-hold via the Van Loan (1978) augmented-matrix exponential rather than an Euler-forward approximation, exact for LTI systems and numerically stable at large time steps.

## Deliberately omitted

To protect the thesis's actual contribution and keep these excerpts as supporting craft only, the following are **not** included here:

- the hybrid RL and MPC arbitration and switching logic and its safety-index formulation;
- the selective-excitation parameter-learning gates and adaptive process-noise scheduling;
- the Control Barrier Function safety filter and its QP / constraint-tightening;
- the full MPC optimal-control problem (cost shaping, terminal DARE cost, solver);
- reward design, policy architecture, training procedure, and any tuned weights;
- all configuration files, vehicle-identification data, and runtime/ROS integration.

Excerpts have been trimmed and lightly adapted from the original sources (imports minimized, comments translated/condensed) while preserving the author's structure and style. They are illustrative, not a runnable system.

_© 2026 Edoardo Caciolo, all rights reserved. Portfolio excerpt shared to demonstrate engineering; not licensed for reuse. Full source is private._
