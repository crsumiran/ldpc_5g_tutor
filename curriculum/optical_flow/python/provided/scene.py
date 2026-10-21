"""Supplied image generation only. No motion-estimation implementation.

Render an analytic, smooth scene at displaced coordinates. The scene extends
beyond the crop; no np.roll, accidental wraparound, interpolation solver or
random seed is needed. Truth is for evaluation, never an estimator argument.
"""
import numpy as np


def image_pair(shape=(24, 28), displacement=(0.25, -0.15), brightness=0.0):
    y, x = np.mgrid[:shape[0], :shape[1]].astype(float)
    def texture(xx, yy):
        return (0.45 + 0.12*np.sin(0.6*xx) + 0.13*np.cos(0.7*yy)
                + 0.1*np.sin(0.2*xx+0.4*yy) + 0.06*np.cos(0.9*xx-0.3*yy))
    u, v = displacement
    frame0 = texture(x, y)
    frame1 = texture(x-u, y-v) + brightness
    truth = np.empty((*shape, 2), dtype=float)
    truth[..., 0] = u
    truth[..., 1] = v
    return frame0, frame1, truth
