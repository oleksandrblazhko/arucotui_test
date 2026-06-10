import math

from .base_filter import BaseFilter


class LowPassFilter:

    def __init__(self):
        self.s = None

    def filter(self, x, alpha):

        if self.s is None:
            self.s = x
            return x

        self.s = alpha * x + (1 - alpha) * self.s

        return self.s


class OneEuroFilter(BaseFilter):

    def __init__(
        self,
        min_cutoff=1.0,
        beta=0.01,
        d_cutoff=1.0
    ):

        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff

        self.x_filter = LowPassFilter()
        self.dx_filter = LowPassFilter()

        self.prev_time = None
        self.prev_x = None

    def alpha(self, cutoff, dt):

        tau = 1.0 / (2.0 * math.pi * cutoff)

        return 1.0 / (1.0 + tau / dt)

    def update(self, x, timestamp):

        if self.prev_time is None:

            self.prev_time = timestamp
            self.prev_x = x

            return x

        dt = timestamp - self.prev_time

        if dt <= 0:
            dt = 1e-6

        dx = (x - self.prev_x) / dt

        alpha_d = self.alpha(
            self.d_cutoff,
            dt
        )

        dx_hat = self.dx_filter.filter(
            dx,
            alpha_d
        )

        cutoff = (
            self.min_cutoff +
            self.beta * abs(dx_hat)
        )

        alpha_x = self.alpha(
            cutoff,
            dt
        )

        x_hat = self.x_filter.filter(
            x,
            alpha_x
        )

        self.prev_x = x
        self.prev_time = timestamp

        return x_hat
    