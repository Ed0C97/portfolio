# Hybrid Multi-Layer Control for Robust Autonomous Driving

> A bachelor's thesis and simulation framework for a layered learning-plus-model-based control stack that keeps a Formula Student driverless race car safe and accurate when tire grip and vehicle parameters are uncertain.

## Overview

This project pairs a bachelor's thesis (Electronic Engineering, L-8, Sapienza University of Rome) with a Python simulation framework that implements and validates a hybrid control architecture for autonomous racing. It targets lateral control of a single-track race car under uncertain tire friction and cornering stiffness, combining online parameter estimation, a learned driving policy, and independent formal safety mechanisms so that a learned controller can operate inside provable safety bounds. The framework also serves as a sim-to-real research platform, with companion MATLAB scripts that independently verify the underlying mathematical claims.

## Highlights

- Online estimation layer that tracks vehicle state and uncertain physical parameters (friction, cornering stiffness) in real time, so the rest of the stack adapts as grip conditions change.
- A reinforcement-learning driving policy that produces steering and longitudinal commands, decoupled from the safety layer so the learned behavior can be formally constrained rather than blindly trusted.
- A formal safety filter based on Control Barrier Functions that keeps every command inside a safe set defined by track boundaries, the tire friction limit, and sideslip limits — turning an unverified policy output into a provably safe command.
- A model-based supervisory controller and arbitration scheme that can override the learned policy when a safety index indicates risk, giving robust fallback behavior under uncertainty.
- A physics-grounded vehicle and tire simulation with sensor noise models and domain randomization, enabling robust training and sim-to-real transfer.
- Perceptual domain adaptation for sim-to-real image transfer, and a real-time control dashboard for monitoring each layer of the stack.
- A modular, multi-rate control loop deployable as robotics nodes, with each estimation, control, and safety layer exposed independently and driven by external configuration.

## Tech Stack

| Category | Technologies |
|---|---|
| Languages | Python, MATLAB, TeX/LaTeX, Shell |
| RL / ML | Stable-Baselines3, Gymnasium, PyTorch, TorchVision, TensorBoard |
| Optimization / control | OSQP, SciPy, NumPy |
| Robotics / simulation | ROS 2, NVIDIA Isaac Sim, MATLAB/Simulink digital twin |
| Visualization | Matplotlib, PyQt5, pyqtgraph |
| Tooling | pytest, pytest-cov, PyYAML; biblatex/biber |

## Status

Academic research prototype (thesis project), not production software. Author retains rights to the thesis text; portions of the accompanying code are research-stage. Source code private/proprietary — review available on request.

---

_© 2026 Edoardo Caciolo — all rights reserved. Proprietary and not open source; source code is private and available for review on request._
