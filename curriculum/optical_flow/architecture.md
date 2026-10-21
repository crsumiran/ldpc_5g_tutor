# A pipeline you can inspect

Frames → gradients → window equations → conditioning → local motion
→ sampling/warping → residual correction → coarse-to-fine refinement.

Every estimator returns a separate validity mask. Keep frame0/frame1, current
flow, warped image, residual and correction as separate arrays. Inspect these
before interpreting a final quiver plot. A rendered arrow is not evidence of
correctness, and a dark residual is not ground truth.

Learner modules live in python/. Supplied scene generation lives in
python/provided/scene.py. Public tests contain small independent numeric
expectations, not an installed reference optical-flow solver. Private author
sanity checks are test infrastructure and are not copied into learner workspaces.

Store this course independently under optical-flow-lab-session and
optical-flow-theory-view-v1. The LDPC and cache sessions must remain untouched.
