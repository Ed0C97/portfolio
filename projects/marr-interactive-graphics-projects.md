# Interactive Graphics Projects

> A set of six browser-based computer graphics assignments implementing core rendering and simulation techniques from scratch in JavaScript and GLSL.

## Overview

A collection of coursework projects from the Interactive Graphics course of the MSc in Robotics and Artificial Intelligence at Sapienza University of Rome. Each project is a standalone web page that runs entirely client-side, progressing from 2D raster image compositing through 3D mesh rendering and shading to GPU ray tracing and physically based animation. The assignments are adapted from the University of Utah CS4600 graphics curriculum.

## Highlights

- 2D image compositing with alpha blending over RGBA pixel buffers.
- Affine 2D transformations using composed matrices to drive an animated scene.
- Textured triangular mesh rendering through the WebGL rasterization pipeline, including Wavefront OBJ model loading.
- Per-fragment Blinn-Phong shading with directional lighting, adjustable specular response, and texture-driven diffuse color.
- GPU ray tracing in a GLSL fragment shader, with shadows and recursive specular reflections against an environment cube map.
- Mass-spring physics simulation for deformable meshes, including gravity, damping, and collision handling.

## Tech Stack

| Category | Details |
| --- | --- |
| Languages | JavaScript, GLSL, HTML |
| Graphics APIs | WebGL, HTML5 Canvas 2D |
| Techniques | Alpha compositing, affine transforms, mesh rendering, Blinn-Phong shading, ray tracing, mass-spring physics |
| Assets | PNG/JPG textures, Wavefront OBJ models, environment cube map |
| Dependencies | None (no build tooling) |

## Status

Completed university coursework: a set of finished, working assignments rather than a maintained library. Distributed under the MIT License.

---

_© 2026 Edoardo Caciolo — all rights reserved. Proprietary and not open source; source code is private and available for review on request._
