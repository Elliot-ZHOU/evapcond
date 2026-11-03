"""把关联式元数据变成一次调用记录。"""

from evapcond.models import CorrelationMeta, CorrelationRecord


def record_call(meta, parameters):
    """parameters 是 (名称, 数值) 序列。"""
    if not isinstance(meta, CorrelationMeta):
        from evapcond.errors import InputError

        raise InputError("关联式缺少元数据")
    return CorrelationRecord(
        name=meta.name,
        citation=meta.citation,
        applicability=meta.applicability,
        parameters=tuple(parameters),
    )
