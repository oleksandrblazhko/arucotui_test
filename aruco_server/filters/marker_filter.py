from .ema_filter import EMAFilter
from .one_euro_filter import OneEuroFilter


class MarkerFilter:

    def __init__(self):

        FilterClass = OneEuroFilter
        # FilterClass = EMAFilter

        self.tx = FilterClass()
        self.ty = FilterClass()
        self.tz = FilterClass()

        self.roll = FilterClass()
        self.pitch = FilterClass()
        self.yaw = FilterClass()

    def update(self, marker, timestamp):

        marker.tx = self.tx.update(
            marker.tx,
            timestamp
        )

        marker.ty = self.ty.update(
            marker.ty,
            timestamp
        )

        marker.tz = self.tz.update(
            marker.tz,
            timestamp
        )

        marker.roll = self.roll.update(
            marker.roll,
            timestamp
        )

        marker.pitch = self.pitch.update(
            marker.pitch,
            timestamp
        )

        marker.yaw = self.yaw.update(
            marker.yaw,
            timestamp
        )

        return marker
    