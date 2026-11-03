"""规格中的异常类型。不新增补充材料里的其他类名。"""


class EvapCondError(Exception):
    """本软件异常的共同基类。"""


class InputError(EvapCondError):
    """输入缺失、组合非法或与规格约束冲突。"""


class OutOfRangeError(EvapCondError):
    """参数超出关联式、物性或规格给出的有效范围。"""

    def __init__(self, param, value, valid_range, source):
        self.param = param
        self.value = value
        self.valid_range = valid_range
        self.source = source
        super().__init__(
            f"{param}={value} 超出有效范围 {valid_range}（来源：{source}）"
        )


class ConvergenceError(EvapCondError):
    """迭代超出上限。residuals 依次为换热量、水膜温度、空气焓三项残差。"""

    def __init__(self, message, residuals):
        self.residuals = tuple(residuals)
        super().__init__(message)


class InfeasibleDesignError(EvapCondError):
    """当前约束下没有可行设计。suggestions 为松弛建议。"""

    def __init__(self, suggestions):
        self.suggestions = tuple(suggestions)
        text = "在当前约束下无可行设计"
        if self.suggestions:
            text = text + "\n" + "\n".join(self.suggestions)
        super().__init__(text)


class UnconfirmedCorrelationError(EvapCondError):
    """调用了尚未确认的关联式。"""


class CancelledError(EvapCondError):
    """用户取消计算。"""
