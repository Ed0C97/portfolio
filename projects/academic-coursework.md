# Academic Coursework

> Graduate coursework from the MSc in Robotics and Artificial Intelligence at Sapienza University of Rome: interactive computer graphics and machine-learning assignments, implemented from scratch.

These are finished university assignments, grouped here for completeness rather than presented as products. They show fundamentals built by hand.

## Interactive graphics (JavaScript, GLSL, WebGL)

Six standalone browser assignments that build up from 2D raster compositing to GPU rendering and physical simulation: alpha compositing over RGBA buffers, composed affine transforms driving an animated scene, textured mesh rendering with Wavefront OBJ loading, per-fragment Blinn-Phong shading with directional lighting, GPU ray tracing in a GLSL fragment shader (shadows and recursive specular reflections against an environment cube map), and mass-spring physics for deformable meshes with gravity, damping, and collision handling. No build tooling. Adapted from the University of Utah CS4600 curriculum and distributed under the MIT License.

## Machine learning (Python, Jupyter)

Two assignments. The first benchmarks six supervised classifiers (Logistic Regression, Decision Tree, Random Forest, SVM, KNN, XGBoost) on synthetic 10-class datasets, weighing accuracy against wall-clock time and resource use so model choice accounts for runtime cost, not just accuracy. The second trains convolutional neural networks on labeled game frames to drive a car in the Gymnasium `CarRacing-v2` environment, handling class imbalance and scoring models both on offline metrics and on in-simulation episode reward.

## Status

Completed university coursework, not maintained as products.

---

_© 2026 Edoardo Caciolo, all rights reserved. Interactive-graphics assignments under the MIT License; other material proprietary and available for review on request._
