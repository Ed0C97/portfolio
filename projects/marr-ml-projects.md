# marr-ml-projects

> Two graduate machine learning coursework projects: a tabular multiclass classifier comparison and a CNN-based controller for a simulated racing car.

## Overview

Two assignments from the Machine Learning course in the Robotics and Artificial Intelligence master's program at Sapienza University of Rome. The first project trains and compares six supervised classifiers on synthetic 10-class datasets, weighing accuracy against compute cost. The second trains convolutional neural networks on labeled game frames to drive a car in the Gymnasium `CarRacing-v2` environment, evaluating them with both classification metrics and in-simulation reward.

## Highlights

- Benchmarks six supervised classifiers (Logistic Regression, Decision Tree, Random Forest, SVM, KNN, XGBoost) across datasets of differing dimensionality, reporting Accuracy, Precision, Recall, F1, and ROC/AUC.
- Profiles model quality against wall-clock time and system resource usage, so model selection accounts for runtime cost, not just accuracy.
- Uses cross-validation and hyperparameter search with standardized features for fair model comparison.
- Trains CNN architectures for frame-to-action driving control, including handling of class imbalance and a sweep over training settings.
- Closes the loop by running trained models in the `CarRacing-v2` simulation and scoring them on total episode reward, alongside offline metrics and confusion matrices.

## Tech Stack

| Category | Details |
| --- | --- |
| Language | Python (Jupyter Notebook) |
| ML / DL | scikit-learn, XGBoost, TensorFlow / Keras |
| RL environment | Gymnasium (`CarRacing-v2`, Box2D), pygame |
| Data / numerics | NumPy, pandas |
| Visualization | Matplotlib, seaborn |
| Profiling | psutil |

## Status

Academic coursework (completed assignments), not maintained as a product.

---

_© 2026 Edoardo Caciolo — all rights reserved. Proprietary and not open source; source code is private and available for review on request._
