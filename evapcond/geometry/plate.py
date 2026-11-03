"""板式几何只负责保存字段。计算入口一律拒绝。"""

from evapcond.geometry.tube import require_supported_surface
from evapcond.models import PlateGeometry


def require_plate_calculation(plate):
    """板式本期没有已确认的水膜-空气关联式。"""
    if not isinstance(plate, PlateGeometry):
        from evapcond.errors import InputError

        raise InputError("需要 PlateGeometry")
    require_supported_surface("plate")
