---
title: "Hybrid RL-MPC Control for Autonomous Driving"
slug: "tesi-triennale"
lang: "en"
oneLiner: "Bachelor's thesis and Python digital twin: a layered RL-MPC control stack for a driverless race car under uncertain tire grip."
category: "Control Systems & RL"
year: "2026"
status: "Research prototype"
statusTone: "prototype"
featured: true
visible: true
order: 1
metrics:
  - value: "3 layers"
    label: "RL policy, CBF safety filter, MPC-LPV supervisor"
  - value: "100 Hz"
    label: "loop rate for estimation, policy and safety filter"
stack: ["Python", "Stable-Baselines3", "Gymnasium", "PyTorch", "OSQP", "ROS 2", "MATLAB/Simulink"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/tesi-triennale"
image: "/images/projects/tesi-triennale.svg"
---

## The problem

A driverless race car operates at the edge of tire grip, and grip is exactly the thing it cannot know for certain. Friction changes with the surface, the temperature and tire wear; cornering stiffness drifts with load and degradation. A classical model-based controller carries formal guarantees, but it trusts a model whose key parameters are already wrong a few minutes into a session. A reinforcement-learning policy adapts to what it experiences, but a neural network on its own guarantees nothing the one time it matters. Formula Student Driverless teams live inside this trade-off: tune the controller conservatively and give away lap time, or push it and accept that one bad friction estimate ends the run against a barrier. The question my thesis addresses is whether the two approaches have to exclude each other, or whether a learned controller can run inside an envelope enforced by provable control theory.

## What I built

My bachelor's thesis in Electronic Engineering at Sapienza University of Rome, together with digital_twin_pkg, a Python simulation framework that implements and exercises the architecture described in the text. The system is not one controller but a stack of specialized layers. An estimation layer measures, online, the quantities no sensor reads directly: lateral velocity, yaw rate, tire friction and cornering stiffness. A learned driving policy turns the vehicle state into steering and acceleration commands. A safety filter corrects every command before it reaches the vehicle, and a model-based supervisor watches a safety index and takes over when the situation degrades. Each layer runs as its own ROS 2 node; a bridge feeds them either from an internal vehicle simulation or from NVIDIA Isaac Sim, and a PyQt5 dashboard shows the loop in real time. Alongside the Python code, MATLAB scripts verify the mathematics of the thesis independently of the implementation.

![tesi-triennale detail placeholder 1](/images/projects/tesi-triennale-2.svg)

## How it works

Estimation is a selective Unscented Kalman Filter with the augmented state [vy, r, mu, Cf0]: it updates friction and stiffness only when cornering excites them and the estimate passes a consistency check. The policy is PPO (Stable-Baselines3) on a custom Gymnasium environment, with a 7-dimensional observation, a 2-dimensional normalized action, and a recorded training run of 500k steps under curriculum domain randomization from 5% to 100%. The safety filter is a Control Barrier Function QP solved with OSQP, with three barriers: track boundary, friction (Kamm) circle and a higher-order sideslip limit (HOCBF, relative degree 2). The supervisor is an MPC on an LPV model scheduled on speed and friction, horizon N=20, terminal cost from the DARE. Estimation, policy and CBF run at 100 Hz; the supervisor arbitrates at 10 Hz through a safety index with hysteresis. The non-obvious choice is keeping controller and safety separate: the same UKF estimates feed both the policy observation and the MPC model, so the whole stack closes the loop on uncertainty instead of ignoring it.

## Results

This is a research prototype, and no on-vehicle measurement is recorded. What exists and is verified: the full loop runs in simulation on a Pacejka single-track model integrated with RK4, with noise models for IMU, encoder and camera; a CycleGAN handles sim-to-real image adaptation; and MATLAB scripts independently confirm the mathematics, covering the CBF QP, the unscented transform, the LPV model, the open-loop poles, the relative degree and the inverse LQR. A 14-DOF MATLAB/Simulink digital twin complements the Python model.

![tesi-triennale detail placeholder 2](/images/projects/tesi-triennale-3.svg)

## Limits and what I'd redo

The honest limit is that the entire stack has only ever driven a simulated car: however randomized, the Pacejka model and the noise models are still my own assumptions about reality. If I started again, I would bring up the CBF filter and the MPC supervisor before training any policy, so that every training step already happens inside the safety envelope instead of adding the guarantees around a finished policy.
