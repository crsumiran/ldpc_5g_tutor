# Optical flow with NumPy

Teaching-text snapshot: 18 October 2026. Five chapters, twelve learner-written functions and 36 public checks. Demonstrations use supplied deterministic values, separate from learner results. The numerical explanations below also form the tutor context.

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


## From image gradients to image motion

Use the image-processing ideas you know to ask where a pattern went.

### Follow a piece of the pattern

Imagine a small textured patch painted on a card. Between two photographs the card slides right. We will follow that same patch throughout this course. Call the first image I0 and the second I1. An image location has horizontal coordinate x and vertical coordinate y; y increases downward. At a point p=(x,y), forward flow is the displacement [u,v] to the corresponding point (x+u,y+v) in I1. The array stores this vector at p in the first image.

A point at (2,2) that moves half a pixel right arrives at (2.5,2). The brightness carried by that point may stay the same even though the value at the fixed array position (2,2) changes. Subtracting images compares fixed positions. Following correspondence compares moving positions. Those are different questions.

The supplied timeline below renders the same pattern at successive positions. Scene motion changes the second frame. Proposed flow changes where we read that frame. Keeping those controls separate lets us test a guess rather than accidentally changing the answer to match it.

For the supplied picture, use the simple textured surface I0(x,y)=x·y. Its intensity at (2,2) is 4. At the final time, a half-pixel rightward shift makes I1(2,2)=3 while the corresponding intensity at (2.5,2) remains 4. Play reveals intermediate positions; it starts at time zero. We will unpack that change with a simpler ramp next.

Interactive demonstration: correspondence. Its worked numerical explanation is included above; controls run locally.

### A ramp makes the sign visible

Before using a full texture, take a horizontal intensity ramp I0(x,y)=10+2x. Intensity is in arbitrary linear units. Moving this ramp right by u=0.5 gives I1(x,y)=10+2(x−0.5)=9+2x. At x=2, the first image is 14 and the second is 13. The fixed-position temporal difference, called It, is I1−I0=−1.

The horizontal gradient Ix is 2 intensity units per pixel. Reading I1 at x+0.5 adds 2×0.5=1 intensity unit, bringing 13 back to 14. Thus 2u=1, or Ix·u=−It. The negative sign is a consequence of following the moved pattern: a rightward-moving rising ramp becomes darker at a fixed position.

An intensity change of −1 is not itself a displacement of −1 pixel. On a gentler ramp with Ix=1 it would suggest u=1; on a flat patch with Ix=0 it provides no horizontal motion information. A lighting change could also cause that −1 without any motion.

### From the ramp to two dimensions

Brightness constancy says I1(x+u,y+v)≈I0(x,y): the corresponding visible point keeps its brightness. A first-order approximation predicts a small shift from the local slope. Let Iy be the vertical intensity gradient. Call the later image’s horizontal and vertical gradients I1x and I1y. Expanding the later image gives I1(x+u,y+v)≈I1(x,y)+I1x·u+I1y·v. Subtract I0 and collect terms to obtain I1x·u+I1y·v≈−It.

For nearby frames we approximate those later-frame slopes by the reference-frame gradients Ix and Iy measured in I0. Our working equation is therefore:
~~~
Ix·u + Iy·v = −It
~~~
This fixed-reference approximation makes the same derivative images reusable during refinement. It is not an exact derivative of every warped image. It is useful when the remaining shift is small and gradients change slowly; larger shifts or changing appearance can invalidate it.

For I0(x,y)=x+2y, Ix=1 and Iy=2. If It=−0.5, the equation is u+2v=0.5. Both [0.5,0] and [0,0.25] fit. One brightness equation cannot generally determine two motion components. We need the surrounding patch.

In FLOW-01 you will return three floating arrays Ix, Iy and It, each shaped (H,W), where H is the number of rows and W the number of columns. Cast before subtraction, use centered spatial differences inside I0 and one-sided differences at its border. Image access is image[y,x], while the vector order is [u,v]. These conventions will stay fixed through all twelve assignments.

Check your understanding: Why does a large frame difference not necessarily mean large motion?

Intensity can change because of illumination, and its sensitivity to motion also depends on the spatial gradient. Frame difference alone has neither a unique cause nor two motion components.

Next assignments: FLOW-01 — Turn the two frames into spatial and temporal measurements with a consistent sign.

## Why corners reveal motion and edges hide part of it

Understand the Lucas–Kanade patch model before writing the solver.

### Nine observations, two unknowns

Return to the textured card. Within a small patch we assume every visible point shares one translation [u,v]. To make all the arithmetic visible, replace the texture locally with I0(x,y)=x·y on a 5×5 image. This small analytic patch has gradients Ix=y and Iy=x. Select the 3×3 patch centered at (2,2), containing coordinates x,y=1,2,3. Its intensities are rows [1,2,3], [2,4,6], [3,6,9]. Different rows and columns have different slopes, just as a textured patch does.

The gradients and temporal difference are not generally constant across a patch. For this image, Ix=y and Iy=x change at every coordinate; It also has its own value at every pixel. The patch model makes a different assumption: the unknown displacement [u,v] is shared by all nine pixels. That shared motion lets us combine nine different local measurements into evidence about one vector. A real translated, noisy patch will only approximately agree with one shared vector.

For this first linear experiment, deliberately set It=−0.5y+0.25x at each pixel. At y=1 the three values across x=1,2,3 are [−0.25,0,0.25]; at y=2 they are [−0.75,−0.5,−0.25]; at y=3 they are [−1.25,−1,−0.75]. These values are constructed to illustrate the linear equations. They are not an exact finite translation of x·y; the first-order model is the approximation being studied. The nine equations in row-major order (across a row, then down) are:
~~~
(x,y)  Ix·u + Iy·v = −It
(1,1)    u +   v =  0.25
(2,1)    u +  2v =  0
(3,1)    u +  3v = −0.25
(1,2)   2u +   v =  0.75
(2,2)   2u +  2v =  0.50
(3,2)   2u +  3v =  0.25
(1,3)   3u +   v =  1.25
(2,3)   3u +  2v =  1
(3,3)   3u +  3v =  0.75
~~~
Put each pair [Ix,Iy] into a row of a matrix A and each right-hand side into a vector b. A has nine rows and two columns; b has nine entries. Matrix multiplication A@[u,v] simply evaluates the left-hand side of all nine equations. FLOW-02 constructs these observations; it does not yet estimate motion.

Interactive demonstration: patch. Its worked numerical explanation is included above; controls run locally.

### What least squares is choosing

Real measurements usually disagree because of noise, interpolation or different motion within the window. For a proposed vector q=[u,v], define the residual vector r=A@q−b. Each entry says how far one brightness equation misses. Squaring prevents positive and negative misses from canceling. The sum E=r.T@r is the squared error; T means transpose, which turns a column into a row for a dot product.

On our nine rows, q=[0,0] gives E=4.125. Trying [0.5,0] gives E=2.625. Trying [0.5,−0.25] gives E=0. Least squares chooses the vector with the smallest sum, even when no vector reaches zero. It fits one shared vector, not nine independent motions.

To find the minimum, differentiate that sum with respect to the two components. Setting both derivatives to zero gives (A.T@A)@q=A.T@b, the normal equations. The small matrix collects products of gradients:
~~~
A.T@A = [[sum(Ix²), sum(Ix·Iy)],
         [sum(Ix·Iy), sum(Iy²)]]
sum(Ix²) = 3×(1²+2²+3²) = 42
sum(Iy²) = 42
sum(Ix·Iy) = (1+2+3)×(1+2+3) = 36
A.T@b = [12, 7.5]
42u + 36v = 12
36u + 42v = 7.5
~~~
Subtract the last equations: 6(u−v)=4.5. Add them: 78(u+v)=19.5. Hence u−v=0.75, u+v=0.25, and [u,v]=[0.5,−0.25]. In code a least-squares routine can solve directly from A and b; explicitly inverting A.T@A is unnecessary and can amplify numerical errors.

### Eigenvalues tell us which direction is missing

A small error is not enough: a flat patch fits any displacement equally well. To measure directional evidence, normalize the matrix by N, the number of pixels: G=(A.T@A)/N. An eigenvector is a direction that G scales without turning. Its eigenvalue is that scale factor. Moving the candidate along a direction with a large eigenvalue changes the predicted brightness strongly; a zero eigenvalue means no evidence in that direction.

For our patch, G=[[42,36],[36,42]]/9. Applying it to [1,1] gives (78/9)[1,1]; applying it to [1,−1] gives (6/9)[1,−1]. These are its two eigenvector directions, with eigenvalues 26/3 and 2/3. Both are positive, so both components can be constrained.

Compare a flat patch: every gradient is [0,0], so G is zero and both eigenvalues are zero. For a vertical ramp or edge with all gradients [1,0], G=[[1,0],[0,0]], with eigenvalues 1 and 0. Horizontal motion changes the image; vertical motion is invisible. This missing along-edge information is the aperture problem. For balanced corner evidence with gradient rows [1,0] and [0,1], G is half the identity and both eigenvalues are 0.5.

FLOW-03 compares the smaller eigenvalue with min_eigenvalue. Normalizing by N keeps a repeated set of observations from artificially increasing confidence. Reject unsupported windows with valid=False and a placeholder [0,0]; adding an epsilon does not create missing evidence. FLOW-04 repeats this fit at complete patch centers and stores flow with shape (H,W,2) plus a boolean validity mask. A valid zero vector means stationary supported texture. An invalid zero vector means no estimate. A larger window gathers more information but can cross a boundary between moving objects.

Interactive demonstration: ambiguity. Its worked numerical explanation is included above; controls run locally.

Check your understanding: Why can a flat patch and a stationary textured patch both return zero flow but require different validity flags?

The flat patch cannot determine motion; zero is a placeholder. The textured stationary patch can constrain both directions and support an actual zero-displacement estimate.

Next assignments: FLOW-02 — Assemble one row per observation without confusing pixels with unknowns. FLOW-03 — Solve only when the patch supports both motion directions. FLOW-04 — Place checked local estimates on a dense grid.

## Warp first, then solve for what remains

Make fractional coordinates, flow direction and iterative updates concrete.

### Four pixels can describe a fractional location

Our patch may move half a pixel. Its destination still exists even though the array contains only integer pixel centers. Bilinear interpolation estimates the intensity from four neighbors. Use the tiny image with top row [0,10] and bottom row [20,30], and read at x=0.25,y=0.5. The fractional distances from the upper-left neighbor are a=0.25 horizontally and b=0.5 vertically.

The weights are (1−a)(1−b)=0.375 at (0,0), a(1−b)=0.125 at (1,0), (1−a)b=0.375 at (0,1), and ab=0.125 at (1,1). Their contributions are 0, 1.25, 7.5 and 3.75. They sum to 12.5. The weights sum to one, so constant intensity stays constant. This smaller example isolates exactly the sampler we will use on the moving patch.

FLOW-05 accepts arrays of lookup coordinates and returns both sampled values and validity. The last pixel center is inside the image: collapse the neighbor index at that border. A location beyond it is outside. Store zero for an absent sample and mark it False; that zero is not an observation of darkness.

Interactive demonstration: sampling. Its worked numerical explanation is included above; controls run locally.

### Forward flow is a lookup instruction

Take I0(x,y)=x·y again, now really translated horizontally by 0.5: I1(x,y)=(x−0.5)y. At p=(2,2), I0=4. Forward flow [0.5,0] points to (2.5,2). The two horizontal neighbors in I1 are 3 at (2,2) and 5 at (3,2). Equal weights give 4, exactly the reference brightness.

A pull-warp keeps the output on the first frame’s grid: output[y,x]=I1 sampled at (x+u,y+v). “Forward” describes the correspondence direction; “pull” describes how we fill the output. No sign reversal is needed. Looking at (1.5,2) instead gives 2, the wrong point.

FLOW-06 applies this lookup at every pixel using that pixel’s vector. The explorer keeps scene displacement separate from proposed flow. Brightness changes affect the later frame and its residual; proposed flow affects only sampled values, support and residual. On a flat scene, changing the lookup leaves all supported intensities the same. Along a vertical edge, changing v leaves interior intensity unchanged. Borders can still change validity.

Interactive demonstration: alignment. Its worked numerical explanation is included above; controls run locally.

### Fit a correction to an actual sampled patch

Suppose the same translated patch is currently estimated at [0.25,0], short of the true [0.5,0]. Use the patch centered at (2,2), with x,y=1,2,3. Every sample uses this center’s current translation. At each patch coordinate (x,y), read I1 at (x+0.25,y). Since I1 is linear along each row, bilinear interpolation is exact here. The reference and sampled intensities are:
~~~
reference I0           sampled I1
[1, 2, 3]              [0.75, 1.75, 2.75]
[2, 4, 6]              [1.50, 3.50, 5.50]
[3, 6, 9]              [2.25, 5.25, 8.25]
~~~
Define the image residual as sampled−reference. Its rows are [−0.25,−0.25,−0.25], [−0.5,−0.5,−0.5] and [−0.75,−0.75,−0.75]. A correction [du,dv] should compensate that deficit, so the fitting right-hand side is reference−sampled, the negative residual. Using fixed gradients [y,x] gives:
~~~
A.T@A = [[42,36],[36,42]]
A.T@(reference−sampled) = [10.5,9]
42du+36dv=10.5; 36du+42dv=9
[du,dv]=[0.25,0]
new flow = [0.25,0]+[0.25,0] = [0.5,0]
~~~
Sampling again at the updated translation returns the reference patch exactly. The next correction is zero. The demonstration steps through sampling, fitting, updating and resampling so each number has a visible source.

Interactive demonstration: refinement. Its worked numerical explanation is included above; controls run locally.

### Why the whole patch follows its center

The fit has two unknowns because we assume a single translation of this patch. If every neighbor used its own current flow, the sampled patch would already be deformed by many different vectors; its residual would no longer describe the center’s two-parameter problem. FLOW-07 therefore samples all coordinates of a patch with flow[y_center,x_center], then updates only that center. The pixelwise warp from FLOW-06 teaches sampling direction but is not a substitute for this patchwise lookup when neighboring flows differ.

Compute reference gradients once. At every round sample the original I1, fit reference−sampled, and add the correction. Require the entire destination patch to lie inside the image and the smaller eigenvalue to meet the threshold. If rejected, retain that center’s previous vector and mark it invalid for this round. Return the final round’s mask. With zero rounds return an independent copy of the initial field and an all-False mask.

A smaller residual does not prove correct correspondence: repeated texture can fit the wrong repetition, and lighting changes need not be motion. Also, keeping reference gradients is an approximation. Pyramids help bring larger displacement into the range where this local update is useful.

Check your understanding: For a point moving right by one pixel, why does pull-warping frame1 use x+1 rather than x-1?

We keep the output at the frame0 location x and read the point's corresponding location in frame1, which is x+1. We are selecting an input sample, not moving the output grid.

Next assignments: FLOW-05 — Sample fractional locations with explicit border validity. FLOW-06 — Align the later frame using the declared forward-flow direction. FLOW-07 — Use residual motion for repeated, masked additive updates.

## Large motion, smaller images

Build a pyramid without losing the meaning of pixel units.

### Make the displacement smaller before refining

Return to the moving textured card, now displaced [8,−4] pixels. A local gradient is unlikely to predict brightness accurately that far away. If both images are reduced by two, the same displacement is [4,−2] in the smaller image. Reduce again and it is [2,−1]. The physical correspondence is unchanged; a pixel at the coarser scale covers more of the original image.

For a 17×21 image, the three grids are 17×21, 9×11 and 5×6. Their coordinate spacing is 1, 2 and 4 original pixels. A point (8,8) becomes (4,4), then (2,2). Estimate at the coarsest level, carry that estimate upward and refine what remains. Two coarse pixels can still be challenging; these numbers explain units, not a guarantee of convergence.

Interactive demonstration: pyramid. Its worked numerical explanation is included above; controls run locally.

### Smooth before keeping alternate samples

Simply taking columns 0,2,4,… from stripes [0,1,0,1,…] gives all zeros. Taking the other phase gives all ones. Both erase the true average of 0.5. Filtering before reduction removes this dependence on sampling phase.

Use the one-dimensional kernel k=[1,4,6,4,1]/16 horizontally and vertically. At an even stripe location its neighborhood is [0,1,0,1,0]; the weighted sum is (0+4+0+4+0)/16=0.5. At an odd location [1,0,1,0,1] gives (1+0+6+0+1)/16=0.5 too. A vertically constant image is unchanged by the vertical pass because the weights sum to one.

At borders, reflect the data without repeating the endpoint, as np.pad(mode="reflect") does. For a row [0,1,2,3,4], the first neighborhood is [2,1,0,1,2], giving 12/16=0.75. At x=2 the filtered value is 2; at x=4 it is 3.25. Keeping even centers returns [0.75,2,3.25]. FLOW-08 applies these two separable filtering passes before selecting [::2,::2]. A 5×7 image becomes 3×4, rounding each dimension upward.

### Grid interpolation and unit conversion are two operations

A coarse field stores vectors only at coarse grid points. To obtain a value at fine coordinate (x,y), first sample each coarse component at (x/2,y/2). This interpolates the field’s positions. Then multiply both vector components by two to convert coarse-pixel displacement into fine-pixel displacement.

For coarse horizontal values [0,2] at columns 0 and 1, fine columns 0,1,2,3 query coarse columns 0,0.5,1,1.5. Extend the last coarse value by clamping 1.5 to 1. Interpolation gives [0,1,2,2]; unit conversion gives [0,2,4,4]. These are separate steps even though a library resize call may obscure them.

For a constant 3×4 field [1,−0.5], expanding to 5×7 yields [2,−1] everywhere. Neither 7/4 nor 5/3 is the scale factor: coarse centers came from fine coordinates 0,2,4,…, so the spacing is exactly two. On an even target size the last query can exceed the coarse domain by half a pixel; border extension is intentional here, unlike image sampling for correspondence. FLOW-09 makes that distinction explicit.

### Assemble the journey back to full resolution

FLOW-10 builds identical pyramids for the two frames. Initialize zero flow only on the coarsest grid. Refine there, expand to the next grid using FLOW-09, and refine with that level’s original images. Continue until the field has the original shape and its vectors are in original-image pixels. Return only the final refinement mask; a coarse valid estimate cannot certify a later lookup.

Check every requested level has at least two pixels per axis and enough space for a complete patch of side 2·radius+1. A radius is the number of pixels from the center to each edge. Too many reductions remove the patch itself. Even before that limit, smoothing may erase a small feature or mix different motions. Choose levels for the displacement and texture, then measure the result rather than assuming more levels always help.

Check your understanding: Why does upsampling a constant [1,-0.5] coarse flow to an odd-sized finer image still produce [2,-1]?

The coordinate spacing is a factor-two pyramid regardless of rounded array dimensions. Interpolation changes where vectors are stored; multiplying by two converts their displacement units.

Next assignments: FLOW-08 — Reduce images with low-pass filtering and a fixed sampling phase. FLOW-09 — Interpolate vector positions and convert displacement units separately. FLOW-10 — Assemble and inspect the full coarse-to-fine estimator.

## When should you believe a flow field?

Separate agreement, confidence, image residual and actual motion error.

### Measure the vector against known motion

A smoothly drawn arrow field can still follow the wrong features. Synthetic images let us separate appearance from truth. Render the moving texture at shifted coordinates and keep its known displacement in a separate truth field; never pass that truth into the estimator. The supplied scene generator uses an analytic texture, so objects leaving one border do not wrap around to the other.

Endpoint error is the distance between estimated and true arrow tips. If the true vector is [2,−1] and the estimate is [1,1], their difference is [−1,2]. Its length is sqrt((−1)²+2²)=sqrt(5)≈2.236 pixels. Summing signed errors would let mistakes cancel. FLOW-11 uses the Euclidean length along the final component axis of the (H,W,2) arrays.

### Always name the pixels being measured

Suppose an image has six pixels and the evaluation mask selects only two. Their vector errors are [3,4] and [0,0], with lengths 5 and 0. Mean endpoint error is (5+0)/2=2.5 pixels and coverage is 2/6≈33.3%. The other four errors are stored as NaN (not measured), not as zeros. Rejecting the harder selected pixel would make the mean zero while reducing coverage to 1/6. That is not automatically a better estimator.

The evaluation mask says which pixels enter a comparison. It may intersect the estimator’s valid mask with a fixed region and available truth. Report both the count and denominator. For an empty mask, mean=NaN and count=0: no accuracy has been measured. Keep image pair and evaluation region fixed when comparing radius, pyramid depth or iteration count.

The supplied mask demonstration gives the other four positions vector differences [2,0], [4,0], [1,0] and [3,0], in row-major order after the first two. Selecting them reveals endpoint errors 2, 4, 1 and 3. Selecting all six gives (5+0+2+4+1+3)/6=2.5 pixels at 100% coverage. The same mean can therefore summarize very different coverage.

Interactive demonstration: evaluation. Its worked numerical explanation is included above; controls run locally.

### Follow a forward path, then a backward path

On real images truth is usually unavailable. Estimate forward flow F from I0 to I1 and backward flow B from I1 to I0. Begin at p, follow F(p) to the destination d=p+F(p), then read B at d. The return point is d+B(d). The round-trip error is the length of F(p)+B(d).

For p=(1,1) and F(p)=[0.5,0], d=(1.5,1). Suppose B(1,1)=[−0.25,0] and B(2,1)=[−0.75,0]. Half weights give B(d)=[−0.5,0]; the sum is [0,0] and the path returns to (1,1). Reading B at p instead would give an error of 0.25 and test the wrong correspondence.

FLOW-12 requires a valid forward vector, an in-bounds destination and valid contributing backward samples. Interpolate the backward validity mask as floating values: if one of those half-weight neighbors is invalid, its sampled validity is 0.5, so reject the path even if the placeholder vectors happen to cancel. Zero-weight neighbors do not contribute. Compare the return-vector length to the inclusive threshold; a 0.5-pixel error passes at threshold=0.5.

Interactive demonstration: consistency. Its worked numerical explanation is included above; controls run locally.

### Agreement can be confidently wrong

Imagine vertical stripes repeating every four pixels. If the true horizontal displacement is one pixel, a guess of five pixels can align with the next stripe just as well. A backward guess of −5 can return to the start. Photometric alignment and round-trip agreement both succeed even though endpoint error is four pixels. A flat patch is even more ambiguous: every supported lookup has the same intensity.

The smaller eigenvalue asks whether local gradients support two directions. Photometric residual asks whether sampled intensities agree. Forward–backward consistency asks whether two estimated maps agree. Endpoint error asks whether the displacement matches independent truth. These checks answer different questions. Occlusions, lighting changes and motion boundaries can break assumptions in different ways.

After FLOW-11 and FLOW-12, compare one setting at a time on the supplied scene, recording endpoint error, coverage and round-trip support. Then inspect your own grayscale pairs with the same skepticism. Your implementation exposes where its evidence comes from; a passing contract is the beginning of that investigation, not a promise of general optical-flow accuracy.

Check your understanding: Can a low photometric residual and a successful round trip both occur for an incorrect flow?

Yes. Repeated or flat texture can support ambiguous matches, and forward/backward estimates can agree on the wrong one. Independent ground truth is needed to measure actual displacement error.

Next assignments: FLOW-11 — Measure endpoint error and disclose evaluation coverage. FLOW-12 — Test round-trip correspondence at the displaced destination.

## FLOW-01: Image change becomes a motion equation

Two photographs give you intensities, not vectors. The first step is to measure how brightness changes across space and between frames. Both are arrays with H rows and W columns. A spatial gradient says how many intensity units a one-pixel lookup shift adds; the temporal difference says what changed at a fixed position. Call the horizontal gradient Ix, the vertical gradient Iy and the temporal difference It. Let u be displacement to the right and v displacement downward, measured in pixels. Their common intensity units make Ix·u+Iy·v=−It meaningful.

Take frame0 with two identical rows [0,1,4] and frame1=frame0−0.5. The interior horizontal derivative is (4−0)/2=2. At the left border only a forward difference is available, 1−0=1; at the right use 4−1=3. Thus Ix has two rows [1,2,3], Iy is all zero because the rows match, and It is all −0.5. This curved row tests the stencil more clearly than a linear ramp. On the simpler ramp x+2y, the same procedure gives Ix=1 and Iy=2, connecting these measurements to the theory’s motion equation.

Convert both inputs to floating arithmetic before subtracting. Then compute horizontal differences along columns and vertical differences along rows, using centered differences only where both neighbors exist. Finally subtract frame0 from frame1. Return three arrays without changing either input. These reference-frame gradients will be reused by dense fitting and refinement.

## What the public checks reveal
The ramp check expects (1,2,−0.5); swapped axes or reversed time subtraction fail it. The unsigned-and-shape check subtracts uint8 values 0−2 and expects floating −2, exposing wraparound. The preserve-and-stencil check uses the [0,1,4] example, distinguishing first-order border differences from other stencils and checking that frame0 stays intact.

### Input/output reference and invocation

Edit python/gradients.py. NumPy is imported as np in these examples.

~~~
gradients(frame0, frame1)
~~~

frame0 and frame1 are finite real numeric arrays of equal shape (H,W), with H,W≥2. Integer inputs are permitted. Return the tuple (Ix,Iy,It), three floating arrays of the same shape. No normalization of intensity is requested.

Concrete invocation (inputs are constructed here, not assumed):
~~~
frame0=np.array([[0.,1.,4.],[0.,1.,4.]])
ix, iy, it = gradients(frame0, frame0-0.5)
~~~

Use NumPy and the earlier course functions; preserve every input. Public checks run in a fresh offline process.

<details><summary>Hints</summary>

1. Relate a horizontal or vertical intensity ramp to its known derivative.
2. Handle interior samples separately from first and last rows/columns.
3. Use one-sided differences at endpoints; use half the difference of the two neighbors inside.

</details>

<details><summary>Experiment and reflection</summary>

Swap the two frames. Which derivative changes sign exactly, and which derivatives are recomputed from a different image?

For a right-moving positive ramp, should It be positive or negative?

Why does a temporal difference alone not specify a two-dimensional displacement?

</details>

## FLOW-02: One patch, many equations

The solver needs one row per brightness observation. A patch shares two unknowns, horizontal u and vertical v. Expanding the window adds equations, not unknown vectors. This function gathers those equations in a predictable order so the gradients and temporal values still refer to the same pixels.

As a compact check, fill ix with 2, iy with −1 and it with −3 on a 3×4 image. Select center (x=2,y=1), radius=0. The sole equation is 2u−v=3, so A=[[2,−1]] with shape (1,2) and b=[3] with shape (1,). Radius zero still produces a matrix, not a flattened pair.

For the full textured patch I0=x·y, select x,y=1,2,3 around center (2,2). With ix=y, iy=x and it=−0.5y+0.25x, the row-major output is:
~~~
A = [[1,1],[1,2],[1,3],
     [2,1],[2,2],[2,3],
     [3,1],[3,2],[3,3]]
b = [0.25,0,−0.25,0.75,0.5,0.25,1.25,1,0.75]
~~~
First check that the whole square fits. Slice all three arrays at exactly the same row and column bounds, including both ends of the radius. Read each slice across rows, then downward. Pair the flattened spatial gradients into two columns and negate the flattened temporal difference. Reuse this gathering function in dense_lk. Do not clip a window or let negative indices wrap around: a partial patch raises ValueError.

## What the public checks reveal
The one-pixel check catches squeezed shapes and a missing minus sign. The row-order check uses distinct values at every position, so a transpose or x/y indexing swap changes the expected sequence [6,7,8,11,12,13,16,17,18]. The border-rejection check requires ValueError for a window centered at the corner with radius=1 and verifies input preservation.

### Input/output reference and invocation

Edit python/windows.py. NumPy is imported as np in these examples.

~~~
patch_system(ix, iy, it, x, y, radius)
~~~

ix, iy and it are finite floating (H,W) arrays of equal shape. x is an integer column, y an integer row; radius is a nonnegative integer. N=(2·radius+1)² is the number of observations. Return floating A of shape (N,2) and b of shape (N,).

Concrete invocation (inputs are constructed here, not assumed):
~~~
ix=np.full((3,4),2.); iy=np.full((3,4),-1.)
it=np.full((3,4),-3.)
a, b = patch_system(ix, iy, it, x=2, y=1, radius=0)
~~~

Use NumPy and the earlier course functions; preserve every input. Public checks run in a fresh offline process.

<details><summary>Hints</summary>

1. One equation belongs to each pixel, not each image row.
2. Select the same square from all three derivative images.
3. Flatten each derivative in the same order, stack Ix/Iy as columns, and negate It.

</details>

<details><summary>Experiment and reflection</summary>

Change radius from 0 to 1. Predict both output shapes before looking at the values.

How many equations does a radius-two patch produce?

Why do more pixels not necessarily provide two independent directions of evidence?

</details>

## FLOW-03: An edge is not enough: solve and check confidence

A window may contain many equations but still hide a direction of motion. Least squares chooses the vector whose predicted brightness changes have the smallest total squared discrepancy. Before accepting that vector, examine whether the observations constrain both components.

A contains one [horizontal gradient, vertical gradient] row per observation; b contains the negative temporal differences. Write a candidate displacement as q=[u,v]. Use A=[[1,0],[0,1],[1,1]] and b=[2,−1,1]. The equations ask for u=2, v=−1 and u+v=1. With q=[0,0] the squared error is 2²+(−1)²+1²=6; q=[2,−1] makes it zero. Multiplying out gives A.T@A=[[2,1],[1,2]] and A.T@b=[3,0]. Here N=3. The normalized matrix G=(A.T@A)/3 scales [1,1] by 1 and [1,−1] by 1/3. Those scale factors are its eigenvalues; the smaller is 1/3. At threshold 1e−6, return {uv: array([2.,−1.]), valid: True, min_eigenvalue: 1/3}.

Now replace A with [[1,0],[2,0]]. Both rows ignore v. The smaller eigenvalue is zero, so return uv=[0,0], valid=False and min_eigenvalue=0 regardless of b. That placeholder does not mean stationary motion.

Form the normalized two-by-two symmetric matrix and obtain its eigenvalues (np.linalg.eigvalsh is suitable). Reject when the smallest is below the positive threshold. Otherwise solve the original least-squares problem (np.linalg.lstsq is suitable). Report the actual smallest eigenvalue in both cases and convert the validity flag to a Python bool. Do not regularize a rank-deficient patch into apparent validity.

## What the public checks reveal
The constrained check exercises the three-row calculation above. The aperture-and-flat check rejects both an edge and zero gradients; blindly taking a pseudoinverse would manufacture an answer. The normalization-and-stationary check repeats the same rows and expects unchanged confidence, while a well-constrained zero right-hand side must produce a valid zero vector. It also checks that A is preserved.

### Input/output reference and invocation

Edit python/solve.py. NumPy is imported as np in these examples.

~~~
solve_window(a, b, min_eigenvalue=1e-6)
~~~

a is finite floating (N,2), b is finite floating (N,), N≥1. min_eigenvalue is a strictly positive scalar threshold on (A.T@A)/N. Return a dict with uv: floating (2,), valid: Python bool, and min_eigenvalue: float. Equality with the threshold is accepted.

Concrete invocation (inputs are constructed here, not assumed):
~~~
a=np.array([[1.,0.],[0.,1.],[1.,1.]])
b=np.array([2.,-1.,1.])
result = solve_window(a, b, min_eigenvalue=1e-6)
~~~

Use NumPy and the earlier course functions; preserve every input. Public checks run in a fresh offline process.

<details><summary>Hints</summary>

1. Ask whether both columns carry independent information.
2. Use the symmetric 2×2 normal matrix to assess conditioning.
3. Check its minimum eigenvalue before solving least squares; keep invalid separate from zero displacement.

</details>

<details><summary>Experiment and reflection</summary>

Replace the second gradient column with zeros. Compare validity, not just the returned vector.

Can an invalid zero vector and a valid zero vector mean the same thing?

What is the difference between zero motion and motion that the image cannot determine?

</details>

## FLOW-04: Put a small-motion estimate at every usable pixel

One patch produces one shared displacement. A dense field repeats that fit around each image location and stores the estimate at the patch center. “Dense” describes the storage grid; it does not imply every vector is supported. Keep a separate mask to distinguish no evidence from a supported stationary estimate.

Construct a 5×5 reference image I0=x·y and manufactured later values I1=I0−0.1y+0.2x, for coordinates 0 through 4. Then Ix=y, Iy=x and −It=0.1y−0.2x. Every complete 3×3 patch supports the exact linear fit [0.1,−0.2]. At center (2,2), A.T@A=[[42,36],[36,42]], A.T@b=[−3,−4.8], and multiplication by [0.1,−0.2] reproduces that right-hand side. Return that vector at the nine interior centers. The 16 border centers have incomplete patches, so keep [0,0] with False. The valid mask has rows 00000, 01110, 01110, 01110, 00000.

Compute gradients once using gradients. Allocate a zero flow field and a False mask. Visit only complete centers, use patch_system to gather observations, and solve_window to check and fit them. Copy each returned vector and flag into the matching center; component zero is u. The manufactured example checks this assembly exactly; a real translated image is only approximately described by one linear step.

## What the public checks reveal
The manufactured-motion check expects [0.1,−0.2] across supported interiors, detecting inconsistent signs and axes. The invalid-border-and-flat check catches unintended padding and missing conditioning checks. The stationary-and-preservation check requires valid zero motion on supported stationary texture while leaving the input unchanged.

### Input/output reference and invocation

Edit python/dense.py. NumPy is imported as np in these examples.

~~~
dense_lk(frame0, frame1, radius=1, min_eigenvalue=1e-6)
~~~

frame0 and frame1 are finite real numeric (H,W) arrays of equal shape, H,W≥2. radius is a nonnegative integer defining a square window; min_eigenvalue is the positive threshold used by solve_window. Return (flow,valid), with floating flow (H,W,2) and boolean valid (H,W). Incomplete or rejected patches have zero flow and False.

Concrete invocation (inputs are constructed here, not assumed):
~~~
y,x=np.mgrid[:5,:5].astype(float)
frame0=x*y; frame1=frame0-0.1*y+0.2*x
flow, valid = dense_lk(frame0, frame1, radius=1)
~~~

Use NumPy and the earlier course functions; preserve every input. Public checks run in a fresh offline process.

<details><summary>Hints</summary>

1. Make derivative arrays once, not once per patch.
2. Visit only centers whose complete windows fit.
3. Store each two-component solution at [y,x] and its checked validity in a separate image.

</details>

<details><summary>Experiment and reflection</summary>

Run the same stationary pair with a flat image and with a textured image. Compare the masks.

What shape holds one 2-D motion vector per image pixel?

Why can a larger window help an edge-like patch yet hurt near a moving-object boundary?

</details>

## FLOW-05: Look between pixels with bilinear interpolation

A half-pixel displacement is meaningful even though there is no array index 0.5. Bilinear sampling combines the four neighboring intensities according to distance. This function is the shared numerical foundation for warping, refinement, flow expansion and round-trip checks.

For image=[[0,10],[20,30]], query x=0.25,y=0.5. Horizontal fractions are 0.75 and 0.25, vertical fractions both 0.5. In upper-left, upper-right, lower-left, lower-right order, the weights are [0.375,0.125,0.375,0.125]. Multiplying by [0,10,20,30] gives [0,1.25,7.5,3.75], totaling 12.5. With length-one coordinate arrays, return values=[12.5], valid=[True]. At (1,1) return 30 and True; at (1.01,1) return 0 and False.

Determine which queries are in the closed pixel-center domain before constructing safe neighbor indices. Use floor coordinates for the lower neighbors, cap the upper neighbors at the last index, and combine four contributions. Preserve the original query array shape even for a scalar-shaped array. Clipping indices to make indexing safe must not turn out-of-bounds queries into valid samples. A one-pixel image still supports exactly (0,0).

## What the public checks reveal
The fractional check verifies all four contributions and the coordinate-array shape. The closed-border-and-outside check separates the last center from just beyond it; neither wrapping nor extrapolation passes. The constant-and-single-pixel check catches duplicated-weight errors at collapsed neighbors and verifies preservation.

### Input/output reference and invocation

Edit python/sampling.py. NumPy is imported as np in these examples.

~~~
bilinear_sample(image, x, y)
~~~

image is finite floating (H,W), H,W≥1. x and y are same-shaped finite floating NumPy coordinate arrays, with any shape; x means column and y means row. Return a tuple of floating values and boolean valid arrays, both shaped exactly like x. Invalid queries store 0 and False.

Concrete invocation (inputs are constructed here, not assumed):
~~~
image=np.array([[0.,10.],[20.,30.]])
values, valid = bilinear_sample(
    image, np.array([0.25]), np.array([0.5]))
~~~

Use NumPy and the earlier course functions; preserve every input. Public checks run in a fresh offline process.

<details><summary>Hints</summary>

1. Locate the surrounding integer coordinates.
2. Use fractional x/y offsets as weights that sum to one.
3. Validate original coordinates first; clamp neighbor indices only to make indexing safe, not to label outside coordinates valid.

</details>

<details><summary>Experiment and reflection</summary>

Sample a constant image at integer, fractional, border and out-of-frame coordinates.

What should the sampler return exactly on the final pixel center?

Why must a zero sampled intensity and an invalid sample be distinguishable?

</details>

## FLOW-06: Use forward flow to pull the second frame back

Forward flow tells us where a first-frame point appears in the second frame. A pull-warp asks that question independently for each output position, then reads the later image there. This aligns corresponding intensities without scattering pixels or leaving holes between destinations.

Use a later image with three identical rows [9,0,1,2]. A proposed flow [1,0] at every pixel asks output column 0 to read input column 1, output column 1 to read column 2, and output column 2 to read column 3. The last output column asks for input column 4, which is outside. Each warped row is [0,1,2,0], with mask [True,True,True,False]. The first zero is an observed dark pixel; the last is an invalid placeholder. This distinction is why a second return array is needed.

Build arrays of integer reference coordinates covering (H,W). Add component 0 of flow to x and component 1 to y, then reuse bilinear_sample on frame1. Return its values and mask. Do not negate the displacement: a point moving right is found to the right in the second image. Do not roll the image, which would wrap borders and cannot represent fractional coordinates.

## What the public checks reveal
The direction check uses the [9,0,1,2] rows to expose a reversed sign or wraparound. The component-order check uses vertical motion to ensure v changes rows. The fractional-and-preserve check samples a ramp at half-pixel offsets, requiring interpolation and unchanged flow input.

### Input/output reference and invocation

Edit python/warping.py. NumPy is imported as np in these examples.

~~~
warp_frame(frame1, flow)
~~~

frame1 is finite floating (H,W); flow is finite floating (H,W,2) on the reference grid, with [u,v] measured in pixels. H,W≥1. Return (warped,valid), floating and boolean arrays of shape (H,W). Out-of-domain samples are 0 with False.

Concrete invocation (inputs are constructed here, not assumed):
~~~
frame1=np.tile(np.array([9.,0.,1.,2.]), (3,1))
flow=np.zeros((3,4,2)); flow[...,0]=1
warped, valid = warp_frame(frame1, flow)
~~~

Use NumPy and the earlier course functions; preserve every input. Public checks run in a fresh offline process.

<details><summary>Hints</summary>

1. Start from a meshgrid of the first frame's x/y positions.
2. Add component 0 to x and component 1 to y.
3. Sample the second frame at those coordinates and carry the sampler's validity mask.

</details>

<details><summary>Experiment and reflection</summary>

Set u to +1 and then -1 on the supplied right-moving pair. Inspect the residual and invalid border.

Which sign of u aligns a pattern that moved right?

Why does using forward flow here still produce an image on the first frame's grid?

</details>

## FLOW-07: Warp, measure what remains, and update

A first guess rarely aligns a real patch exactly. Refinement samples the second image with the current estimate, measures what remains, fits a small correction and adds it. The gradient model describes a shared translation per patch, so every coordinate in a patch must use the center’s vector. Neighboring centers can have different guesses, but those guesses do not deform this patch’s sampling grid.

Use 5×5 images I0=x·y and I1=(x−0.5)y, a true horizontal translation of 0.5. Initialize every vector to [0.25,0]. At center (2,2), reference rows are [1,2,3], [2,4,6], [3,6,9]. Sampling at x+0.25 gives rows [0.75,1.75,2.75], [1.5,3.5,5.5], [2.25,5.25,8.25]. The sampled-minus-reference residual is −0.25y; the fitting right-hand side is +0.25y.

The fixed gradients give A.T@A=[[42,36],[36,42]] and A.T@b=[10.5,9]. Solving yields correction [0.25,0]; the updated center is [0.5,0]. After one round, valid centers are rows 1..3 and columns 1..2 (six centers). Centers at column 3 would sample beyond x=4, so they retain [0.25,0] with False, as do incomplete border centers. This is a full output convention, not just an interior accuracy claim.

Copy initial_flow and compute reference gradients once. For each round start a new False mask. At each complete center build the patch coordinates, add that center’s current vector to every coordinate, and use bilinear_sample on the original frame1. Reject unless every sample is supported. Flatten reference-minus-sampled values as b, pair the fixed gradients as A and reuse solve_window. Add a valid correction only at that center. Return the last round’s mask. With zero rounds, return the independent copy and an all-False mask. Repeatedly warping an already warped image would accumulate interpolation error.

## What the public checks reveal
The stationary check expects supported interiors to remain at zero. The zero-rounds-and-preserve check requires an independent output copy and no claimed update. The small-translation-and-support check measures mean endpoint error on a fixed interior and rejects a wildly out-of-bounds initial guess without overwriting it. These checks exercise ordinary cases; also reason through the center-vector rule when neighboring initial vectors differ.

### Input/output reference and invocation

Edit python/refinement.py. NumPy is imported as np in these examples.

~~~
refine_flow(frame0, frame1, initial_flow, iterations=3, radius=1, min_eigenvalue=1e-6)
~~~

frame0 and frame1 are finite real numeric arrays with equal shape (H,W), H,W≥2. initial_flow is finite floating (H,W,2). iterations and radius are nonnegative integers; min_eigenvalue is positive. Return floating flow (H,W,2) and boolean valid (H,W). Invalid centers retain prior vectors; zero iterations returns no valid updates. Inputs must remain unchanged.

Concrete invocation (inputs are constructed here, not assumed):
~~~
y,x=np.mgrid[:5,:5].astype(float)
frame0=x*y; frame1=(x-0.5)*y
initial=np.zeros((5,5,2)); initial[...,0]=0.25
flow, valid = refine_flow(frame0, frame1, initial, iterations=1)
~~~

Use NumPy and the earlier course functions; preserve every input. Public checks run in a fresh offline process.

<details><summary>Hints</summary>

1. A patch gets one translation: its center's current vector.
2. Use fixed reference gradients and a freshly sampled target patch; reject if any patch coordinate is outside the image.
3. Form b as reference minus sampled patch, solve the two-column gradient system, and add that correction only to its center.

</details>

<details><summary>Experiment and reflection</summary>

Compare one versus several updates on a small translation, keeping the initial flow and image pair identical.

Which source image is resampled on the second update?

Why should every update warp the original second frame rather than the previous warped result?

</details>

## FLOW-08: Make large motion small before solving it

Large displacement becomes smaller in pixel units after reducing both images. But simply skipping pixels can convert stripes into a false constant pattern. Low-pass filtering first makes each retained intensity represent a neighborhood.

For an 8×8 image whose every row is [0,1,0,1,0,1,0,1], a five-tap filter with weights [1,4,6,4,1]/16 returns 0.5 everywhere. At even centers the weighted neighborhood is (0+4+0+4+0)/16; at odd centers it is (1+0+6+0+1)/16. The vertical filter preserves this constant. Taking rows and columns 0,2,4,6 then gives a 4×4 array filled with 0.5. Without filtering you would get zeros.

For a 5×5 image with every row [0,1,2,3,4], reflecting without repeating the endpoint gives first neighborhood [2,1,0,1,2]. Its sum is (2+4+0+4+2)/16=0.75. The retained interior value at x=2 is 2, and the last is 3.25. Return three rows [0.75,2,3.25].

Apply the specified kernel along one axis with np.pad mode="reflect", then the other. “Separable” means these two one-dimensional passes equal the corresponding two-dimensional product filter. Select even rows and columns only after both passes. Preserve floating arithmetic and the input. You may use NumPy convolution or weighted shifted slices; no external resize routine is needed.

## What the public checks reveal
The constant-shape check expects 5×7 to become 3×4 with intensity 3 unchanged. The filter-before-decimate check uses alternating stripes, catching an omitted or reordered filter. The reflect-phase check uses the ramp above to detect a different padding mode or sampling phase.

### Input/output reference and invocation

Edit python/pyramid.py. NumPy is imported as np in these examples.

~~~
reduce_half(image)
~~~

image is a finite floating two-dimensional array (H,W), H,W≥2. Return one floating array with shape (ceil(H/2),ceil(W/2)). The kernel is [1,4,6,4,1]/16 on both axes, with reflect padding; keep filtered coordinates [::2,::2].

Concrete invocation (inputs are constructed here, not assumed):
~~~
image=np.tile(np.arange(5.,dtype=float), (5,1))
coarse = reduce_half(image)
~~~

Use NumPy and the earlier course functions; preserve every input. Public checks run in a fresh offline process.

<details><summary>Hints</summary>

1. Think of smoothing and decimation as separate steps.
2. The 2-D filter is the outer product of the 1-D kernel.
3. Use reflected padding for each axis, preserve the filtered shape, then retain even-indexed rows and columns.

</details>

<details><summary>Experiment and reflection</summary>

Compare smoothing-then-sampling with raw [::2,::2] on alternating stripes.

What happens to an odd input dimension?

Why can the coarsest level lose a feature that was useful at full resolution?

</details>

## FLOW-09: A resized vector field needs resized vectors

A coarse vector of one pixel spans two pixels on the next finer level. Expanding flow therefore has two jobs: interpolate where vectors are stored and convert the units of the vectors themselves. Keeping those jobs distinct prevents the common mistake of returning the right array shape with half-sized motion.

Take a 2×2 coarse field whose horizontal component is [[0,2],[0,2]] and vertical component is zero. To build a 4×4 field, fine columns [0,1,2,3] query coarse columns [0,0.5,1,1.5]. Clamp the final query to 1. Bilinear interpolation yields [0,1,2,2]; multiplying by two gives [0,2,4,4] in every row. v remains zero. Both components must be scaled: a constant [1,−0.5] becomes [2,−1].

For a 2×3 field, valid finer shapes include (4,6) and (3,5). Odd sizes come from rounding during reduction, not a different coordinate spacing. Always divide fine coordinates by two and multiply vectors by two; do not use target_width/coarse_width.

Build the fine coordinate grid, map it to half coordinates and clamp each axis to the last coarse center. Use bilinear_sample separately for u and v. Stack the interpolated components on the last axis and convert their units. Border extension here is deliberate: you are extending a field onto a finer grid, not claiming an observed image correspondence beyond its crop.

## What the public checks reveal
The constant-even-odd check verifies the same [2,−1] result at both target shapes and preservation. The interpolation-and-endpoint-extension check expects [0,2,4,4], exposing nearest-neighbor resizing or invalidating the last coordinate. The vertical-and-single-cell check requires a 1×1 field [0.25,2] to expand to [0.5,4], catching horizontal-only scaling.

### Input/output reference and invocation

Edit python/resize.py. NumPy is imported as np in these examples.

~~~
upsample_flow(flow, target_shape)
~~~

flow is finite floating (h,w,2), h,w≥1. target_shape=(H,W) contains integers; each target dimension is either twice its coarse dimension or one less. Return floating (H,W,2), sampling components at (min(x/2,w−1),min(y/2,h−1)) and multiplying both by two. Do not mutate flow.

Concrete invocation (inputs are constructed here, not assumed):
~~~
flow=np.zeros((2,2,2))
flow[...,0]=[[0.,2.],[0.,2.]]
fine = upsample_flow(flow, target_shape=(4,4))
~~~

Use NumPy and the earlier course functions; preserve every input. Public checks run in a fresh offline process.

<details><summary>Hints</summary>

1. Separate spatial interpolation from displacement-unit conversion.
2. Interpolate component 0 and component 1 with the same coordinates.
3. Use the factor-two pyramid coordinate map, extend boundary endpoints, then multiply both components by two.

</details>

<details><summary>Experiment and reflection</summary>

Upsample a constant field into both even and odd target shapes. Does the displacement scale differ?

Should an odd target width change the displacement scale factor?

Why is multiplying only the horizontal component wrong, even when the image is wider than it is tall?

</details>

## FLOW-10: Assemble coarse-to-fine optical flow

You now have image reduction, local refinement and flow expansion. The final estimator uses a small image to obtain a useful starting guess, then asks successively finer images to correct it. Every vector is measured in pixels of its current level.

Follow a displacement [4,−2] through a 17×21 pair: the grids 17×21, 9×11 and 5×6 have truth [4,−2], [2,−1] and [1,−0.5]. Start with zero on 5×6; if refinement finds [1,−0.5], expansion supplies [2,−1] on 9×11 and then [4,−2] on 17×21. Those are unit conversions, not guaranteed estimates. Each level must actually fit its images.

For a small exact invocation, use identical 5×5 images I=x·y with levels=1 and iterations=1. There is no reduction. The initial flow is zero, every residual is zero, and every complete radius-one patch supports a zero correction. Expected flow is all zeros with shape (5,5,2); valid has rows 00000, 01110, 01110, 01110, 00000. With levels=3, the requested shapes would be 5×5, 3×3, 2×2; radius=1 needs a 3×3 patch, so raise ValueError rather than silently removing a requested level.

Build both pyramids with reduce_half and validate every level against the patch size and minimum axis length two. Allocate zero flow only on the coarsest level. Moving from coarse to fine, call refine_flow with that level’s original frames, then upsample_flow once for the next level. Return the finest flow and that level’s final validity. Do not reset to zero at each level or multiply vectors once per iteration.

## What the public checks reveal
The identity check expects zero motion on supported stationary texture at two levels. The translation check uses a smooth analytic scene with true [1,−0.5], requires a fixed core to remain valid and mean endpoint error below 0.3 pixels, and checks input preservation. The flat-and-level-validation check rejects unsupported flat texture and raises ValueError for excessive levels. These are modest controlled examples, not a benchmark of general accuracy.

### Input/output reference and invocation

Edit python/multiscale.py. NumPy is imported as np in these examples.

~~~
pyramidal_flow(frame0, frame1, levels=3, iterations=3, radius=1, min_eigenvalue=1e-6)
~~~

frame0 and frame1 are finite real numeric (H,W) arrays of equal shape, H,W≥2. levels is a positive integer counting the original image; iterations is a nonnegative number of refinement rounds per level; radius is a nonnegative integer and min_eigenvalue is positive. Every level must have both dimensions ≥max(2,2·radius+1), else ValueError. Return floating flow (H,W,2) in original pixels and boolean valid (H,W).

Concrete invocation (inputs are constructed here, not assumed):
~~~
y,x=np.mgrid[:5,:5].astype(float)
frame=x*y
flow, valid = pyramidal_flow(frame, frame, levels=1, iterations=1)
~~~

Use NumPy and the earlier course functions; preserve every input. Public checks run in a fresh offline process.

<details><summary>Hints</summary>

1. Work from the end of the pyramid list back to the original image.
2. Expand flow once per level transition, not once per iteration.
3. Initialize zero only at the coarsest level; reuse reduce_half, upsample_flow and refine_flow.

</details>

<details><summary>Experiment and reflection</summary>

Compare levels=1 with levels=3 on the same translation, reporting masked endpoint error AND valid coverage.

At which resolution is the returned flow measured?

Why can extra coarse levels make a tiny moving feature harder to track?

</details>

## FLOW-11: Measure motion error, not just image alignment

Image alignment can hide a wrong correspondence. To evaluate displacement directly, compare estimated vectors with independent truth. Endpoint error is the Euclidean distance between their tips, measured in pixels of the evaluation image. This function measures a completed estimate; truth must never be an input to the estimator itself.

Use a 2×3 zero truth field. Set estimate[0,0]=[3,4], leave other estimates zero and select mask[0,:2]=True. The selected vector differences are [3,4] and [0,0]. Their lengths are sqrt(9+16)=5 and 0; the mean is 2.5 and count is 2. Return errors=[[5,0,NaN],[NaN,NaN,NaN]], mean=2.5, count=2. Coverage, computed from this result and the image size, is 2/6=33.3%. It is not an additional return key required by this contract.

Initialize the error image to NaN, compute vector lengths on selected pixels and fill only those entries. Average over the selected count, not all image positions or both vector components. Handle the empty mask explicitly with mean=NaN and count=0. Keep both inputs unchanged. The caller chooses the evaluation region; this function does not invent extra validity criteria.

## What the public checks reveal
The masked-mean check uses the six-pixel example and catches dividing by the full image area. The empty-is-not-perfect check requires NaN, because no measurements cannot establish zero error. The axes-and-preservation check expects sqrt(2) for a two-component unit difference and checks the returned image shape and unchanged estimate.

### Input/output reference and invocation

Edit python/metrics.py. NumPy is imported as np in these examples.

~~~
endpoint_error(estimate, truth, mask)
~~~

estimate and truth are finite floating (H,W,2) arrays; mask is boolean (H,W). Return a dict with errors: floating (H,W), mean: float, count: Python int. Unselected errors are NaN. Selected errors are Euclidean lengths over the last axis. Empty selection gives count=0 and mean=NaN.

Concrete invocation (inputs are constructed here, not assumed):
~~~
truth=np.zeros((2,3,2)); estimate=truth.copy()
estimate[0,0]=[3.,4.]
mask=np.zeros((2,3),bool); mask[0,:2]=True
result = endpoint_error(estimate, truth, mask)
~~~

Use NumPy and the earlier course functions; preserve every input. Public checks run in a fresh offline process.

<details><summary>Hints</summary>

1. Take the norm along the final, two-component axis.
2. Select evaluation pixels before calculating the mean.
3. Use NaN for unmeasured entries and explicitly handle an empty mask.

</details>

<details><summary>Experiment and reflection</summary>

Compare zero flow, correct flow and a deliberately swapped [v,u] field on one known translation.

Does an empty evaluation mask mean zero error?

How could an estimator appear to improve its mean error simply by rejecting more pixels?

</details>

## FLOW-12: Ask whether the estimated path comes back

Forward–backward agreement is useful when true motion is unknown. Starting at a first-frame position, follow forward flow into the second frame, then read backward flow there. If those estimates describe the same correspondence, their sum should be near zero. A consistency flag is evidence of agreement, not proof of correct motion.

For a complete tiny example, use forward=[1,0] everywhere on a 2×3 grid, backward=[−1,0] everywhere, and both validity masks True. At p=(0,0), the destination is (1,0); reading backward there returns to (0,0). Column 1 also returns. Column 2 points outside the crop. Thus consistent is [[True,True,False],[True,True,False]] at threshold=0.5.

A fractional example shows why the lookup matters. At p=(1,1), let F=[0.5,0] and let B(1,1)=[−0.25,0], B(2,1)=[−0.75,0]. Destination (1.5,1) gives their half-weight average [−0.5,0], hence round-trip vector [0,0]. Reading B at p instead gives [0.25,0]. If either contributing backward sample is invalid, interpolating its floating validity mask gives 0.5, so reject even if the numerical vector sum is zero.

Build the destination coordinates from forward flow. Use bilinear_sample on both backward components and on backward_valid converted to floating values. Require forward_valid, an in-bounds destination and sampled backward validity np.isclose to 1. Then compare the Euclidean length of forward plus sampled backward to the inclusive threshold. A zero-weight neighbor need not be valid. Return only the combined boolean mask; leave the vector inputs unchanged.

## What the public checks reveal
The constant-inverse-and-border check verifies inverse motion while excluding the exiting column. The destination-not-same-index check puts the inverse vector only at the destination; comparing B at the starting index fails. The invalid-reverse-and-fractional check invalidates one contributing half-weight sample, so neighboring forward lookups must fail support rather than accepting placeholder cancellation.

### Input/output reference and invocation

Edit python/consistency.py. NumPy is imported as np in these examples.

~~~
fb_consistency(forward, backward, forward_valid, backward_valid, threshold=0.5)
~~~

forward and backward are finite floating (H,W,2) arrays, H,W≥1. forward_valid and backward_valid are boolean (H,W). threshold is a nonnegative pixel distance. Return consistent, a boolean (H,W) array requiring supported source and destination plus round-trip norm ≤threshold. A passing flag can still describe two mutually agreeing wrong matches.

Concrete invocation (inputs are constructed here, not assumed):
~~~
forward=np.zeros((2,3,2)); forward[...,0]=1
backward=-forward
valid=np.ones((2,3),bool)
consistent = fb_consistency(
    forward, backward, valid, valid, threshold=0.5)
~~~

Use NumPy and the earlier course functions; preserve every input. Public checks run in a fresh offline process.

<details><summary>Hints</summary>

1. Follow the forward endpoint before reading backward flow.
2. Use the sampler for both backward components and for the backward validity mask.
3. Intersect source validity, destination support, contributing validity and the round-trip norm threshold.

</details>

<details><summary>Experiment and reflection</summary>

Corrupt one backward-flow vector and inspect which forward destination samples are affected.

At which coordinate should backward flow be read?

Why can forward–backward agreement still accept a wrong correspondence on repeated texture?

</details>

