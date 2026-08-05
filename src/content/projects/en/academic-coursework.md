---
title: "ML and Computer Graphics Coursework"
slug: "academic-coursework"
lang: "en"
oneLiner: "University coursework (Sapienza): a six-classifier benchmark, CNN driving controllers, and six from-scratch graphics projects in WebGL."
category: "ML & Graphics Coursework"
status: "Completed coursework"
statusTone: "spec"
featured: false
visible: true
order: 14
metrics:
  - value: "6 models"
    label: "classifier benchmark from logistic regression to XGBoost"
  - value: "0 libraries"
    label: "six graphics assignments in plain JavaScript and GLSL"
stack: ["Python", "scikit-learn", "XGBoost", "TensorFlow/Keras", "Gymnasium", "JavaScript", "WebGL/GLSL"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/academic-coursework"
image: "/images/projects/academic-coursework.svg"
---

## The problem

In machine learning and in computer graphics alike, the tooling has become good enough to hide the discipline. A few lines of scikit-learn produce a trained classifier; a rendering engine produces a lit, textured scene. What the tools do not answer is what sits underneath: which model is actually worth its compute cost on this data, whether an offline accuracy number says anything about behavior inside a running system, and what really happens between a triangle and a pixel. These questions matter to an engineer, because the practical decisions (model selection, evaluation design, GPU work) come down to exactly them. The honest way to answer them is to be forced to work below the abstractions: benchmark models under a fixed methodology while accounting for their cost, evaluate a controller in the loop it is supposed to close, and write the rendering and simulation code with no library to lean on. That is what this coursework did.

## What I built

Two sets of assignments from university coursework (Sapienza), for the Machine Learning and Interactive Graphics courses. For ML, two projects. First, a benchmark of six classifiers (Logistic Regression, Decision Tree, Random Forest, SVM, KNN, XGBoost) on two synthetic 10-class datasets, one with 100 features and one with 1000, run with and without 5-fold cross-validation, tuned with GridSearchCV, and profiled for wall-clock time and system resources alongside accuracy. Second, two Keras CNN architectures trained on labeled 96x96 game frames to drive a car in the Gymnasium CarRacing-v2 environment. For graphics, six self-contained browser projects adapted from the Utah CS4600 assignments: alpha compositing on raw pixel buffers, 2D matrix transforms, textured WebGL mesh rendering, per-fragment Blinn-Phong shading, a GPU ray tracer written in a GLSL fragment shader, and a mass-spring physics simulation. Every graphics project runs entirely client-side with zero dependencies and no build step: open the HTML file and it works.

![academic-coursework detail placeholder 1](/images/projects/academic-coursework-2.svg)

## How it works

The benchmark records quality metrics and psutil resource usage per model, so selection weighs accuracy against cost. The CNN work grid-searches batch size, learning rate and epochs, saving every model as an .h5 file named by its hyperparameters; evaluation is double: confusion matrices on a held-out test set, and a closed-loop run where the saved model maps each 96x96 frame to a discrete action and is scored by total episode reward. That is the non-obvious choice: offline accuracy does not tell you what a controller does once its own mistakes feed back into its inputs. On the graphics side: column-major 3x3 transform matrices, a WebGL MeshDrawer with OBJ parsing and MVP matrices, ray-sphere intersection with hard shadow rays and recursive reflections held under a bounce limit with a cube-map fallback, and semi-implicit Euler integration with Hooke spring forces and restitution-based collisions against a unit cube.

## Results

All assignments are complete and working. The benchmark closes with a cost-aware pick: the SVM for the 100-feature dataset, Random Forest for the 1000-feature one. The CNN controllers are scored both offline and by episode reward in the simulator, and each ML project ships its source, a written report and result artifacts. The six graphics projects open and run as-is in a modern browser.

![academic-coursework detail placeholder 2](/images/projects/academic-coursework-3.svg)

## Limits and what I'd redo

The limit is that this is coursework frozen at submission: the ML repository has no dependency manifest, and the datasets and trained models are not committed, so the scripts only run once those assets are supplied locally. The CarRacing controller is also pure frame-by-frame supervised classification, with no temporal context. Redoing it, I would make everything reproducible from a clean checkout, and I would use the closed-loop reward, not offline accuracy, as the primary selection criterion from the start.
