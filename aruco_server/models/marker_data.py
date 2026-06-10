# Замість передачі сирих масивів створюється окремий клас.

from dataclasses import dataclass

@dataclass
class MarkerData:

    marker_id: int

    tx: float
    ty: float
    tz: float

    roll: float
    pitch: float
    yaw: float

    corners: list
