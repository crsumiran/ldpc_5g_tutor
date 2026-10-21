# Optical flow: from gradients to motion

You already know edge detection, gradients and filtering. This course uses
those tools to estimate apparent image motion from two frames. The main lessons
read as short articles; each assignment defines its own notation, works one
example and states exact NumPy shapes. The code you write remains yours.

## The path

Derivatives → patch equations → checked least squares → dense small-motion flow
→ bilinear sampling → pull warping → iterative refinement → filtered reduction
→ flow upsampling → coarse-to-fine estimation → endpoint error → round-trip checks.

## Conventions worth keeping beside the editor

- Grayscale frames are finite 2-D arrays (H,W); convert to floating point before subtraction.
- Image indexing is image[y,x]. Flow indexing is flow[y,x,0]=u right and flow[y,x,1]=v down.
- Forward flow maps frame0 positions into frame1. Pull-warp samples frame1 at (x+u,y+v).
- Flow is displacement in pixels at the current level, not physical velocity.
- Out-of-frame, underconstrained and measured zero motion are different cases. Use validity masks.
- Each public suite runs offline in a fresh Python process. NumPy linear algebra is allowed; library optical-flow solvers are not the exercise.

## Scope

The capstone is an educational dense pyramidal Lucas–Kanade estimator with a
declared additive translation refinement using fixed reference gradients. It is not a production flow library,
benchmark result or recreation of every variant in the original papers.
Brightness changes, occlusions, motion boundaries, repetitive texture and
large initial errors remain important failure cases. Confidence and
forward–backward agreement are useful diagnostics, not ground truth.

The supplied analytic scene extends beyond the crop, so image generation does
not use circular shifts. Known displacement is for evaluation, never input to
the estimator. Start with synthetic pairs before trying normalized grayscale
crops from your own adjacent video frames. Color handling, file I/O, video
ingestion, learned optical flow and robust variational solvers are not implemented.

## Optional reading, after the corresponding experiments

For patch equations and refinement, read Lucas and Kanade, *An Iterative Image
Registration Technique with an Application to Stereo Vision* (1981), introduction
and the Newton–Raphson registration derivation, PDF pages 1–3:
https://publications.ri.cmu.edu/storage/publications/pub_files/pub3/lucas_bruce_d_1981_1/lucas_bruce_d_1981_1.pdf
An accessible interactive reproduction is at https://idl.uw.edu/living-papers-paper/lucas-kanade/.
Ask which motion is assumed common to a neighborhood and why iteration needs a good starting point.

For levels and scaling, read Bouguet, *Pyramidal Implementation of the Lucas
Kanade Feature Tracker*, image-pyramid construction and iterative tracking sections:
https://graphics.stanford.edu/courses/cs448a-00-fall/bouget00.pdf
Ask what changes units between pyramid levels and which pixels support the fit.
The paper describes feature tracking; our dense grid, border rules, derivative
stencil and fixed-reference update are explicitly stated teaching choices.
