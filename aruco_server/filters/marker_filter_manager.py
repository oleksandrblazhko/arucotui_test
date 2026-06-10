from marker_filter import MarkerFilter


class MarkerFilterManager:

    def __init__(self):

        self.filters = {}

    def process(self, marker, timestamp):

        marker_id = marker.marker_id

        if marker_id not in self.filters:

            self.filters[marker_id] = (
                MarkerFilter()
            )

        return self.filters[
            marker_id
        ].update(
            marker,
            timestamp
        )
    