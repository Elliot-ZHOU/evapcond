"""湿空气物性。只调用 CoolProp HAPropsSI（ASHRAE RP-1485）。

状态由压力和另外两个独立参数确定。含湿量 w 为 kg/kg 干空气，
焓 h 为 J/kg 干空气，密度 rho 为湿空气质量密度 (1+w)/v。
干球温度范围 5～50 °C，含湿量 0～w_sat。允许 T_wb = T_db。
"""

import math
from dataclasses import dataclass

from scipy.optimize import brentq

from evapcond.errors import InputError, OutOfRangeError
from evapcond.properties.backend import resolve_backend

T_MIN_C = 5.0
T_MAX_C = 50.0
_T_MIN = T_MIN_C + 273.15
_T_MAX = T_MAX_C + 273.15
_SOURCE_T = "规格：湿空气干球温度 5～50 °C"
_SOURCE_W = "规格：湿空气含湿量 0～w_sat(T_db, p_atm)"
_KEYS = ("T_db", "T_wb", "rh", "w", "h", "rho")


@dataclass(frozen=True)
class HumidAirState:
    """一次湿空气状态。温度 K，压力 Pa，相对湿度 0～1。"""

    p: float
    T_db: float
    T_wb: float
    rh: float
    w: float
    h: float
    rho: float
    cp: float
    mu: float
    k: float


def humid_air_state(
    p,
    T_db=None,
    T_wb=None,
    rh=None,
    w=None,
    h=None,
    rho=None,
    backend=None,
):
    """由压力和恰好两个独立参数返回完整状态。

    cp 为每千克干空气的湿空气比热，J/(kg_da·K)，来自 HAPropsSI 的 C。
    """
    backend = resolve_backend(backend)
    _check_pressure(p)
    given = _collect(T_db, T_wb, rh, w, h, rho)
    T, humidity = _resolve_primary(given, p, backend)
    return _forward(T, humidity, p, backend)


def saturation_humidity_ratio(T, p, backend=None):
    """饱和含湿量，kg/kg。与 humid_air_state(p, T_db=T, rh=1).w 相同。

    只调用一次 HAPropsSI。相对湿度为 1 时不可能落在干空气上，不再做那次试算。
    """
    backend = resolve_backend(backend)
    _check_pressure(p)
    _check_dry_bulb(T)
    return _w_sat(T, p, backend)


def saturated_enthalpy(T, p, backend=None):
    """饱和空气焓，J/kg。与 humid_air_state(p, T_db=T, rh=1).h 相同。"""
    backend = resolve_backend(backend)
    _check_pressure(p)
    _check_dry_bulb(T)
    humidity = _w_sat(T, p, backend)
    return _ha(backend, "H", "Tdb", T, "P", p, "W", humidity)


@dataclass(frozen=True)
class MoistAirCarry:
    """迭代中间的空气状态。只保留方程用到的量。"""

    p: float
    T_db: float
    w: float
    h: float
    cp: float


def state_for_march(p, w, h, backend=None):
    """由压力、含湿量和焓得到下一步要用的干球温度、焓和比热。

    这三个数值与 humid_air_state(p, w=w, h=h) 相同。
    湿球温度、相对湿度、比容、粘度和导热系数不在这里计算。
    """
    backend = resolve_backend(backend)
    _check_pressure(p)
    if not math.isfinite(w) or w < 0.0:
        raise OutOfRangeError("w", w, _SOURCE_W, _SOURCE_W)
    if not math.isfinite(h):
        raise OutOfRangeError("h", h, "有限实数", "湿空气输入")
    temperature = _temperature_at_humidity("h", w, h, p, backend)
    _check_dry_bulb(temperature)
    w_sat = _w_sat(temperature, p, backend)
    if w > w_sat * (1.0 + 1e-9) + 1e-12:
        raise OutOfRangeError("w", w, f"[0, {w_sat}] kg/kg", _SOURCE_W)
    if w > w_sat:
        w = w_sat
    enthalpy = _ha(backend, "H", "Tdb", temperature, "P", p, "W", w)
    heat_capacity = _ha(backend, "C", "Tdb", temperature, "P", p, "W", w)
    return MoistAirCarry(p=p, T_db=temperature, w=w, h=enthalpy, cp=heat_capacity)


def _collect(T_db, T_wb, rh, w, h, rho):
    provided = {
        "T_db": T_db,
        "T_wb": T_wb,
        "rh": rh,
        "w": w,
        "h": h,
        "rho": rho,
    }
    given = {}
    for key, value in provided.items():
        if value is None:
            continue
        if not math.isfinite(value):
            raise OutOfRangeError(key, value, "有限实数", "湿空气输入")
        given[key] = float(value)
    if len(given) != 2:
        names = "、".join(given) if given else "（无）"
        raise InputError(f"湿空气状态必须给定两个独立参数，当前为 {names}")
    if "rh" in given and not 0.0 <= given["rh"] <= 1.0:
        raise OutOfRangeError("rh", given["rh"], "[0, 1]", "相对湿度")
    if "w" in given and given["w"] < 0.0:
        raise OutOfRangeError("w", given["w"], _SOURCE_W, _SOURCE_W)
    if "T_db" in given:
        _check_dry_bulb(given["T_db"])
    if "T_db" in given and "T_wb" in given and given["T_wb"] > given["T_db"] + 1e-9:
        raise OutOfRangeError(
            "T_wb",
            given["T_wb"],
            f"<= T_db ({given['T_db']} K)",
            "湿球温度不能高于干球温度",
        )
    return given


def _resolve_primary(given, p, backend):
    if "w" not in given:
        dry = _try_dry(given, p, backend)
        if dry is not None:
            return dry
    if "T_db" in given and "w" in given:
        return given["T_db"], given["w"]
    if "T_db" in given and "rh" in given:
        return given["T_db"], _humidity_from_rh(given["T_db"], given["rh"], p, backend)
    if "T_db" in given and "T_wb" in given:
        return given["T_db"], _humidity_from_twb(
            given["T_db"], given["T_wb"], p, backend
        )
    if "T_db" in given and "h" in given:
        return given["T_db"], _humidity_from_h(given["T_db"], given["h"], p, backend)
    if "T_db" in given and "rho" in given:
        return given["T_db"], _humidity_from_rho(
            given["T_db"], given["rho"], p, backend
        )
    if "w" in given and "rh" in given:
        return _temperature_from_w_rh(given["w"], given["rh"], p, backend)
    if "w" in given:
        other = next(key for key in given if key != "w")
        T = _temperature_at_humidity(other, given["w"], given[other], p, backend)
        return T, given["w"]
    if "rh" in given:
        other = next(key for key in given if key != "rh")
        return _temperature_from_rh_and(other, given["rh"], given[other], p, backend)
    if "T_wb" in given and "h" in given:
        return _along_wet_bulb("h", given["T_wb"], given["h"], p, backend)
    if "T_wb" in given and "rho" in given:
        return _along_wet_bulb("rho", given["T_wb"], given["rho"], p, backend)
    if "h" in given and "rho" in given:
        return _along_enthalpy(given["h"], given["rho"], p, backend)
    names = "、".join(given)
    raise InputError(f"无法由 {names} 确定湿空气状态")


def _try_dry(given, p, backend):
    """若两个参数都落在干空气曲线上，返回该干球温度与 w=0。"""
    keys = list(given)
    for index in (0, 1):
        try:
            T = _temperature_at_humidity(keys[index], 0.0, given[keys[index]], p, backend)
        except (OutOfRangeError, ValueError, InputError):
            continue
        state = _forward(T, 0.0, p, backend)
        other = keys[1 - index]
        if _relative_error(getattr(state, other), given[other]) <= 1e-8:
            return T, 0.0
    return None


def _forward(T, w, p, backend):
    _check_dry_bulb(T)
    if -1e-12 <= w < 0.0:
        w = 0.0
    w_sat = _w_sat(T, p, backend)
    if w < 0.0 or w > w_sat * (1.0 + 1e-9) + 1e-12:
        raise OutOfRangeError("w", w, f"[0, {w_sat}] kg/kg", _SOURCE_W)
    if w > w_sat:
        w = w_sat
    T_wb = _ha(backend, "Twb", "Tdb", T, "P", p, "W", w)
    try:
        rh = _ha(backend, "R", "Tdb", T, "P", p, "W", w)
    except ValueError:
        # 含湿量贴着饱和线时，HAPropsSI 的相对湿度可能略超出 1。
        if abs(w - w_sat) <= max(1e-8 * w_sat, 1e-12):
            rh = 1.0
        else:
            raise
    enthalpy = _ha(backend, "H", "Tdb", T, "P", p, "W", w)
    volume = _ha(backend, "V", "Tdb", T, "P", p, "W", w)
    cp = _ha(backend, "C", "Tdb", T, "P", p, "W", w)
    mu = _ha(backend, "M", "Tdb", T, "P", p, "W", w)
    conductivity = _ha(backend, "K", "Tdb", T, "P", p, "W", w)
    if abs(rh) < 1e-12:
        rh = 0.0
    if abs(rh - 1.0) < 1e-9:
        rh = 1.0
    return HumidAirState(
        p=p,
        T_db=T,
        T_wb=T_wb,
        rh=rh,
        w=w,
        h=enthalpy,
        rho=(1.0 + w) / volume,
        cp=cp,
        mu=mu,
        k=conductivity,
    )


def _humidity_from_rh(T, rh, p, backend):
    if rh == 0.0:
        return 0.0
    return _ha(backend, "W", "Tdb", T, "P", p, "R", rh)


def _humidity_from_twb(T, T_wb, p, backend):
    if abs(T_wb - T) <= 1e-9:
        return _w_sat(T, p, backend)
    try:
        humidity = _ha(backend, "W", "Tdb", T, "P", p, "Twb", T_wb)
    except ValueError as exc:
        dry_twb = _ha(backend, "Twb", "Tdb", T, "P", p, "W", 0.0)
        if abs(dry_twb - T_wb) <= 1e-6:
            return 0.0
        raise OutOfRangeError(
            "T_wb",
            T_wb,
            f"[{dry_twb}, {T}] K",
            "CoolProp HAPropsSI",
        ) from exc
    if humidity < 0.0 and humidity > -1e-10:
        return 0.0
    return humidity


def _humidity_from_h(T, enthalpy, p, backend):
    try:
        humidity = _ha(backend, "W", "Tdb", T, "P", p, "H", enthalpy)
    except ValueError as exc:
        dry_h = _ha(backend, "H", "Tdb", T, "P", p, "W", 0.0)
        if abs(enthalpy - dry_h) <= max(1e-8 * abs(dry_h), 1e-4):
            return 0.0
        raise OutOfRangeError(
            "h",
            enthalpy,
            "该干球温度下 HAPropsSI 可达到的焓",
            "CoolProp HAPropsSI",
        ) from exc
    if humidity < 0.0 and humidity > -1e-10:
        return 0.0
    return humidity


def _humidity_from_rho(T, rho, p, backend):
    def residual(humidity):
        return _forward(T, humidity, p, backend).rho - rho

    w_sat = _w_sat(T, p, backend)
    low = residual(0.0)
    high = residual(w_sat)
    if abs(low) <= 1e-8 * max(abs(rho), 1.0):
        return 0.0
    if low * high > 0.0:
        raise OutOfRangeError(
            "rho",
            rho,
            f"[{_forward(T, w_sat, p, backend).rho}, {_forward(T, 0.0, p, backend).rho}] kg/m³",
            "该干球温度下的湿空气密度",
        )
    return brentq(residual, 0.0, w_sat, xtol=1e-14, rtol=1e-12)


def _temperature_from_w_rh(w, rh, p, backend):
    if w == 0.0 and rh == 0.0:
        raise InputError("含湿量与相对湿度同时为零，不能确定干球温度")
    if w == 0.0 or rh == 0.0:
        raise OutOfRangeError(
            "w",
            w,
            "与相对湿度同时为正，或二者不同时把空气标成干空气以外的组合",
            _SOURCE_W,
        )
    lower = _lowest_dry_bulb(w, p, backend)
    if abs(rh - 1.0) <= 1e-12:
        if abs(w - _w_sat(lower, p, backend)) > max(1e-8 * max(w, 1.0), 1e-12):
            raise OutOfRangeError("rh", rh, "该含湿量在 5～50 °C 内的饱和状态", _SOURCE_W)
        return lower, w

    def rh_gap(T):
        return _forward(T, w, p, backend).rh - rh

    T = _bracket(rh_gap, lower, _T_MAX, "rh", rh)
    return T, w


def _temperature_from_rh_and(kind, rh, value, p, backend):
    if rh == 0.0:
        T = _temperature_at_humidity(kind, 0.0, value, p, backend)
        return T, 0.0

    def gap(T):
        humidity = _humidity_from_rh(T, rh, p, backend)
        state = _forward(T, humidity, p, backend)
        return _relative_signed(getattr(state, kind), value)

    T = _bracket(gap, _T_MIN, _T_MAX, "T_db", value)
    return T, _humidity_from_rh(T, rh, p, backend)


def _temperature_at_humidity(kind, w, value, p, backend):
    if kind == "T_db":
        return value
    if w > 0.0 and kind == "T_wb":
        return _ha(backend, "Tdb", "W", w, "P", p, "Twb", value)
    if w > 0.0 and kind == "h":
        return _ha(backend, "Tdb", "W", w, "P", p, "H", value)
    if w > 0.0 and kind == "rh":
        T, _humidity = _temperature_from_w_rh(w, value, p, backend)
        return T

    lower = _T_MIN
    if w > 0.0:
        lower = _lowest_dry_bulb(w, p, backend)

    def gap(T):
        state = _forward(T, w, p, backend)
        return _relative_signed(getattr(state, kind), value)

    return _bracket(gap, lower, _T_MAX, kind, value)


def _lowest_dry_bulb(w, p, backend):
    """该含湿量不超出饱和含湿量的最低允许干球温度。露点低于 5 °C 时返回 5 °C。"""
    if w <= 0.0:
        return _T_MIN
    w_sat_min = _w_sat(_T_MIN, p, backend)
    w_sat_max = _w_sat(_T_MAX, p, backend)
    if w > w_sat_max:
        raise OutOfRangeError("w", w, f"[0, {w_sat_max}] kg/kg", _SOURCE_W)
    if w <= w_sat_min:
        return _T_MIN

    def saturation_gap(T):
        return _w_sat(T, p, backend) - w

    return _bracket(saturation_gap, _T_MIN, _T_MAX, "w", w)


def _along_wet_bulb(kind, T_wb, value, p, backend):
    """固定湿球温度，用干球温度匹配焓或密度。

    干空气湿球温度在 CoolProp 里有一处跳变，不能拿它当光滑上界，
    所以只在湿球反算能够成功的温度之间找变号区间。
    """
    if T_wb > _T_MAX + 1e-9:
        raise OutOfRangeError("T_wb", T_wb, f"<= {_T_MAX} K", _SOURCE_T)
    lower = max(T_wb, _T_MIN)

    def gap(T):
        humidity = _humidity_from_twb(T, T_wb, p, backend)
        state = _forward(T, humidity, p, backend)
        return _relative_signed(getattr(state, kind), value)

    previous_T = lower
    previous = _endpoint(gap, lower)
    if previous is not None and abs(previous) <= 1e-8:
        return lower, _humidity_from_twb(lower, T_wb, p, backend)
    T = lower
    while T < _T_MAX - 1e-12:
        T = min(_T_MAX, T + 1.0)
        current = _endpoint(gap, T)
        if current is not None and abs(current) <= 1e-8:
            return T, _humidity_from_twb(T, T_wb, p, backend)
        if previous is not None and current is not None and previous * current <= 0.0:
            root = brentq(gap, previous_T, T, xtol=1e-12, rtol=1e-12)
            return root, _humidity_from_twb(root, T_wb, p, backend)
        if current is not None:
            previous_T = T
            previous = current
    raise OutOfRangeError(kind, value, "5～50 °C 内与该湿球温度相容", "CoolProp HAPropsSI")


def _along_enthalpy(enthalpy, rho, p, backend):
    """固定焓，用干球温度匹配密度。

    某一温度下焓的下限是干空气焓，上限是饱和空气焓。
    """

    def dry_enthalpy(T):
        return _ha(backend, "H", "Tdb", T, "P", p, "W", 0.0)

    if dry_enthalpy(_T_MIN) > enthalpy:
        raise OutOfRangeError("h", enthalpy, "不低于 5 °C 干空气焓", "CoolProp HAPropsSI")
    if dry_enthalpy(_T_MAX) <= enthalpy:
        upper = _T_MAX
    else:
        upper = _bracket(
            lambda T: dry_enthalpy(T) - enthalpy,
            _T_MIN,
            _T_MAX,
            "h",
            enthalpy,
        )

    def saturated_gap(T):
        return _forward(T, _w_sat(T, p, backend), p, backend).h - enthalpy

    if saturated_gap(_T_MIN) >= 0.0:
        lower = _T_MIN
    else:
        lower = _bracket(saturated_gap, _T_MIN, upper, "h", enthalpy)

    def rho_gap(T):
        humidity = _humidity_from_h(T, enthalpy, p, backend)
        return _forward(T, humidity, p, backend).rho - rho

    T = _bracket(rho_gap, lower, upper, "rho", rho)
    return T, _humidity_from_h(T, enthalpy, p, backend)


def _bracket(func, lo, hi, param, value):
    """在区间内求根。端点已经是根时直接返回，避免另一端不可计算。"""
    if hi < lo:
        lo, hi = hi, lo
    low = _endpoint(func, lo)
    if low is not None and abs(low) <= 1e-8:
        return lo
    high = _endpoint(func, hi)
    if high is not None and abs(high) <= 1e-8:
        return hi
    if low is None or high is None or low * high > 0.0:
        raise OutOfRangeError(param, value, "5～50 °C 内可计算", _SOURCE_T)
    root = brentq(func, lo, hi, xtol=1e-12, rtol=1e-12)
    if abs(func(root)) > 1e-6:
        raise OutOfRangeError(param, value, "5～50 °C 内可计算", _SOURCE_T)
    return root


def _endpoint(func, point):
    try:
        return func(point)
    except (OutOfRangeError, ValueError):
        return None


def _w_sat(T, p, backend):
    return _ha(backend, "W", "Tdb", T, "P", p, "R", 1.0)


def _ha(backend, output, name1, value1, name2, value2, name3, value3):
    return backend.ha_props_si(output, name1, value1, name2, value2, name3, value3)


def _check_pressure(p):
    if not math.isfinite(p) or p <= 0.0:
        raise OutOfRangeError("p", p, "> 0 Pa", "湿空气压力")


def _check_dry_bulb(T):
    t_c = T - 273.15
    if t_c < T_MIN_C - 1e-9 or t_c > T_MAX_C + 1e-9:
        raise OutOfRangeError("T_db", T, "5 °C ～ 50 °C", _SOURCE_T)


def _relative_signed(actual, target):
    scale = max(abs(target), abs(actual), 1e-12)
    return (actual - target) / scale


def _relative_error(actual, target):
    scale = max(abs(actual), abs(target))
    if scale == 0.0:
        return 0.0
    return abs(actual - target) / scale
