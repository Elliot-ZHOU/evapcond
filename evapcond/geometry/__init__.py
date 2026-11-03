"""几何候选与面积。"""

from evapcond.geometry.candidates import (
    DEFAULT_D_O,
    DEFAULT_LENGTHS,
    DEFAULT_ROWS,
    geometry_candidates,
)
from evapcond.geometry.tube import (
    face_area,
    outside_area,
    require_supported_surface,
)

__all__ = [
    "DEFAULT_D_O",
    "DEFAULT_LENGTHS",
    "DEFAULT_ROWS",
    "face_area",
    "geometry_candidates",
    "outside_area",
    "require_supported_surface",
]
