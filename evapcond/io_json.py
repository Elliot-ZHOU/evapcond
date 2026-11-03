"""输入 JSON 与结果文件。单位换算只在这一层进行。

输入和结果里的工程单位：
- Q_k：kW；制冷剂流量 m_ref、喷淋水量 m_spray：kg/s
- 温度 T_k、T_db_in、T_wb_in、T_in、T_sat_in：°C；过热度、过冷度：K
- 压力 p_atm、p_in、p_noz：kPa
- d_o、壁厚、管间距、管内径、粗糙度：mm；管长 L、提升高度、管路长度：m
- 风速：m/s；风量：m³/s；Γ：kg/(m·s)
- k_w：W/(m·K)；风吹损失率 drift_rate：百分数，0.01 表示喷淋水量的 0.01%
"""

import csv
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

from evapcond import __version__
from evapcond.errors import InputError, OutOfRangeError
from evapcond.models import (
    AuxInput,
    DesignInput,
    PlateGeometry,
    SolverConfig,
    TubeGeometry,
)
from evapcond.properties import coolprop_version
from evapcond.properties.humid_air import humid_air_state

SCHEMA_VERSION = "1.0"
CSV_COLUMNS = (
    "row",
    "seg",
    "region",
    "T_ref_C",
    "p_ref_kPa",
    "x",
    "T_film_C",
    "m_water_kg_s",
    "T_air_C",
    "w_air_kg_kg",
    "i_air_kJ_kg",
    "q_ref_W",
    "q_sens_W",
    "q_lat_W",
)

_AUX_REQUIRED = (
    "zeta_de",
    "zeta_lv",
    "zeta_st",
    "p_noz",
    "H_lift",
    "pipe_length",
    "pipe_diameter",
    "zeta_pipe",
    "pipe_roughness",
)
_AUX_OPTIONAL = {
    "eta_fan": 0.65,
    "eta_pump": 0.70,
    "N_cyc": 3.0,
    "drift_rate": 0.01,
}
_DESIGN_REQUIRED = (
    "Q_k",
    "refrigerant",
    "T_k",
    "T_db_in",
    "T_wb_in",
    "surface_type",
    "v_f_max",
)
_DESIGN_OPTIONAL = {
    "p_atm": 101.325,
    "superheat": 0.0,
    "subcooling": 0.0,
    "d_o": (19.05, 25.0, 32.0),
    "wall_thickness": 2.0,
    "k_w": 63.9,
    "S_T_ratio": (2.0, 2.5),
    "S_L_ratio": (1.5, 2.0),
    "L": (2.0, 4.0, 6.0),
    "v_f_factor": (0.6, 0.8, 1.0),
    "N_r": (4, 8, 12, 16, 20, 24, 28),
    "exhaustive": False,
}


@dataclass(frozen=True)
class LoadedProblem:
    """解析后的输入。defaults_used 是文件里没有写、因而采用默认值的字段名。"""

    mode: str
    design: DesignInput | None
    rating: object | None
    config: SolverConfig
    inputs: dict
    defaults_used: tuple


def load_problem(path, mode):
    """按命令要求的模式读取 JSON。"""
    return parse_problem(_read_json(path), mode)


def parse_problem(data, mode):
    """解析已经读入的对象。界面和命令行共用这一条路径。"""
    if not isinstance(data, dict):
        raise InputError("输入 JSON 的顶层必须是对象")
    if data.get("mode") != mode:
        raise InputError(f"输入模式是 {data.get('mode')}，命令要求 {mode}")
    if mode == "design":
        design, config, inputs, defaults = _load_design(data)
        return LoadedProblem(mode, design, None, config, inputs, defaults)
    if mode == "rating":
        rating, config, inputs, defaults = _load_rating(data)
        return LoadedProblem(mode, None, rating, config, inputs, defaults)
    raise InputError("模式必须是 design 或 rating")


def write_outputs(out_dir, mode, inputs, defaults_used, outcome, geometry=None):
    """写出 result.json、distribution.csv 和 summary.txt，并返回摘要文本。"""
    directory = Path(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    document = build_document(mode, inputs, defaults_used, outcome, geometry)
    rating = outcome.rating if mode == "design" else outcome
    (directory / "result.json").write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _write_csv(directory / "distribution.csv", rating.segments)
    text = summary_text(document)
    (directory / "summary.txt").write_text(text, encoding="utf-8")
    return text


def build_document(mode, inputs, defaults_used, outcome, geometry=None):
    """结果文档。界面摘要与命令行文件使用同一份内容。"""
    rating = outcome.rating if mode == "design" else outcome
    if geometry is None and mode == "rating":
        raise InputError("校核结果写出时需要几何")
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
        "environment": {
            "python_version": sys.version.split()[0],
            "coolprop_version": coolprop_version(),
            "app_version": __version__,
        },
        "inputs": inputs,
        "defaults_used": list(defaults_used),
        "results": _results(mode, outcome, rating, geometry),
        "resistances": _resistances(rating.resistances),
        "convergence": {
            "iterations": rating.convergence.iterations,
            "heat_relative": rating.convergence.heat_relative,
            "film_temperature_K": rating.convergence.film_temperature,
            "air_enthalpy_J_kg": rating.convergence.air_enthalpy,
        },
        "correlations_used": [_correlation(item) for item in rating.correlations],
        "diagnostics": list(outcome.diagnostics if mode == "design" else rating.diagnostics),
        "warnings": list(outcome.warnings if mode == "design" else rating.warnings),
    }


def summary_text(document):
    """与 summary.txt 相同的摘要。"""
    return _summary(document)


def distribution_rows(segments):
    """与 distribution.csv 相同的数据行，不含表头。"""
    rows = []
    for segment in segments:
        rows.append(
            [
                segment.row,
                segment.seg,
                segment.region,
                segment.T_ref - 273.15,
                segment.p / 1000.0,
                "" if segment.x is None else segment.x,
                segment.T_w - 273.15,
                segment.m_w,
                segment.T_a - 273.15,
                segment.w_a,
                segment.i_a / 1000.0,
                segment.dQ_ref,
                segment.dQ_s,
                segment.dQ_l,
            ]
        )
    return rows


def is_default_coarse(design):
    """文件采用补充三的默认粗网格时，才做局部细化。"""
    return (
        design.d_o == (0.01905, 0.025, 0.032)
        and design.transverse_pitch_ratio == (2.0, 2.5)
        and design.longitudinal_pitch_ratio == (1.5, 2.0)
        and design.lengths == (2.0, 4.0, 6.0)
        and design.rows == (4, 8, 12, 16, 20, 24, 28)
        and design.face_velocity_factor == (0.6, 0.8, 1.0)
        and design.gamma is None
        and design.gamma_min is None
        and design.gamma_max is None
        and design.exhaustive is False
    )


def _read_json(path):
    file_path = Path(path)
    if not file_path.is_file():
        raise InputError(f"找不到输入文件：{file_path}")
    try:
        data = json.loads(file_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise InputError(f"输入不是合法 JSON：{exc}") from exc
    if not isinstance(data, dict):
        raise InputError("输入 JSON 的顶层必须是对象")
    return data


def _load_design(data):
    _reject_unknown(
        data,
        set(_DESIGN_REQUIRED)
        | set(_DESIGN_OPTIONAL)
        | set(_AUX_REQUIRED)
        | set(_AUX_OPTIONAL)
        | {"mode", "gamma", "gamma_min", "gamma_max", "le_f", "fin_height", "fin_pitch", "fin_thickness",
           "plate_width", "plate_height", "plate_spacing", "n_plates", "corrugation_angle",
           "corrugation_pitch", "corrugation_depth"},
    )
    missing = [name for name in _DESIGN_REQUIRED + _AUX_REQUIRED if name not in data]
    if missing:
        raise InputError("缺少必填字段：" + "、".join(missing))
    defaults = []
    values = _with_defaults(data, _DESIGN_OPTIONAL, defaults)
    aux = _aux(data, defaults)
    config = _solver(data, defaults)
    design = DesignInput(
        Q=_as_float("Q_k", data["Q_k"]) * 1000.0,
        refrigerant=_refrigerant(data["refrigerant"]),
        T_k=_celsius("T_k", data["T_k"]),
        air=_air(values["p_atm"], data["T_db_in"], data["T_wb_in"]),
        v_face_max=_as_float("v_f_max", data["v_f_max"]),
        aux=aux,
        surface_type=str(data["surface_type"]),
        superheat=_as_float("superheat", values["superheat"]),
        subcooling=_as_float("subcooling", values["subcooling"]),
        d_o=tuple(item / 1000.0 for item in _float_list("d_o", values["d_o"])),
        wall_thickness=_as_float("wall_thickness", values["wall_thickness"]) / 1000.0,
        k_w=_as_float("k_w", values["k_w"]),
        transverse_pitch_ratio=_float_list("S_T_ratio", values["S_T_ratio"]),
        longitudinal_pitch_ratio=_float_list("S_L_ratio", values["S_L_ratio"]),
        gamma=_optional_float_list(data, "gamma"),
        gamma_min=_optional_float(data, "gamma_min"),
        gamma_max=_optional_float(data, "gamma_max"),
        lengths=_float_list("L", values["L"]),
        face_velocity_factor=_float_list("v_f_factor", values["v_f_factor"]),
        rows=_int_list("N_r", values["N_r"]),
        le_f=_optional_float(data, "le_f"),
        exhaustive=bool(values["exhaustive"]),
    )
    return design, config, _echo_design(data, values, aux), tuple(defaults)


def _load_rating(data):
    required = (
        "refrigerant",
        "m_ref",
        "T_in",
        "T_db_in",
        "T_wb_in",
        "surface_type",
        "d_o",
        "wall_thickness",
        "k_w",
        "S_T",
        "S_L",
        "N_r",
        "N_t",
        "L",
    )
    _reject_unknown(
        data,
        set(required)
        | set(_AUX_REQUIRED)
        | set(_AUX_OPTIONAL)
        | {
            "mode",
            "p_atm",
            "p_in",
            "T_sat_in",
            "v_f",
            "air_volume_flow",
            "gamma",
            "m_spray",
            "le_f",
            "fin_height",
            "fin_pitch",
            "fin_thickness",
            "plate_width",
            "plate_height",
            "plate_spacing",
            "n_plates",
            "corrugation_angle",
            "corrugation_pitch",
            "corrugation_depth",
            "n_cv_target",
            "max_iterations",
            "relaxation",
        },
    )
    missing = [name for name in required + _AUX_REQUIRED if name not in data]
    if "v_f" not in data and "air_volume_flow" not in data:
        missing.append("v_f 或 air_volume_flow")
    if "gamma" not in data and "m_spray" not in data:
        missing.append("gamma 或 m_spray")
    if "p_in" not in data and "T_sat_in" not in data:
        missing.append("p_in 或 T_sat_in")
    if missing:
        raise InputError("缺少必填字段：" + "、".join(missing))
    defaults = []
    p_atm = _taken(data, "p_atm", 101.325, defaults)
    aux = _aux(data, defaults)
    config = _solver(data, defaults)
    from evapcond.models import RatingInput

    rating = RatingInput(
        geometry=_rating_geometry(data),
        refrigerant=_refrigerant(data["refrigerant"]),
        m_ref=_as_float("m_ref", data["m_ref"]),
        T_in=_celsius("T_in", data["T_in"]),
        air=_air(p_atm, data["T_db_in"], data["T_wb_in"]),
        aux=aux,
        p_in=None if "p_in" not in data else _as_float("p_in", data["p_in"]) * 1000.0,
        T_sat_in=None if "T_sat_in" not in data else _celsius("T_sat_in", data["T_sat_in"]),
        v_face=None if "v_f" not in data else _as_float("v_f", data["v_f"]),
        air_volume_flow=(
            None if "air_volume_flow" not in data else _as_float("air_volume_flow", data["air_volume_flow"])
        ),
        gamma=None if "gamma" not in data else _as_float("gamma", data["gamma"]),
        m_spray=None if "m_spray" not in data else _as_float("m_spray", data["m_spray"]),
        le_f=_optional_float(data, "le_f"),
    )
    echoed = dict(data)
    echoed["p_atm"] = p_atm
    _echo_aux(echoed, aux)
    return rating, config, echoed, tuple(defaults)


def _rating_geometry(data):
    surface = str(data["surface_type"])
    if surface == "plate":
        return PlateGeometry(
            plate_width=_as_float("plate_width", data["plate_width"]) / 1000.0,
            plate_height=_as_float("plate_height", data["plate_height"]) / 1000.0,
            plate_spacing=_as_float("plate_spacing", data["plate_spacing"]) / 1000.0,
            n_plates=_as_int("n_plates", data["n_plates"]),
            corrugation_angle=math.radians(_as_float("corrugation_angle", data["corrugation_angle"])),
            corrugation_pitch=_as_float("corrugation_pitch", data["corrugation_pitch"]) / 1000.0,
            corrugation_depth=_as_float("corrugation_depth", data["corrugation_depth"]) / 1000.0,
        )
    fins = None
    if surface == "tube_lowfin":
        fins = (
            _as_float("fin_height", data["fin_height"]) / 1000.0,
            _as_float("fin_pitch", data["fin_pitch"]) / 1000.0,
            _as_float("fin_thickness", data["fin_thickness"]) / 1000.0,
        )
    return TubeGeometry(
        surface_type=surface,
        d_o=_as_float("d_o", data["d_o"]) / 1000.0,
        wall_thickness=_as_float("wall_thickness", data["wall_thickness"]) / 1000.0,
        k_w=_as_float("k_w", data["k_w"]),
        S_T=_as_float("S_T", data["S_T"]) / 1000.0,
        S_L=_as_float("S_L", data["S_L"]) / 1000.0,
        N_r=_as_int("N_r", data["N_r"]),
        N_t=_as_int("N_t", data["N_t"]),
        L=_as_float("L", data["L"]),
        fin_height=None if fins is None else fins[0],
        fin_pitch=None if fins is None else fins[1],
        fin_thickness=None if fins is None else fins[2],
    )


def _aux(data, defaults):
    values = {name: _as_float(name, data[name]) for name in _AUX_REQUIRED}
    values["p_noz"] *= 1000.0
    values["pipe_diameter"] /= 1000.0
    values["pipe_roughness"] /= 1000.0
    for name, default in _AUX_OPTIONAL.items():
        if name not in data:
            defaults.append(name)
            number = default
        else:
            number = _as_float(name, data[name])
        if name == "drift_rate":
            number = number / 100.0
        values[name] = number
    return AuxInput(**values)


def _solver(data, defaults):
    picked = {}
    for name, default in (
        ("n_cv_target", 40),
        ("max_iterations", 500),
        ("relaxation", 1.0),
    ):
        if name not in data:
            defaults.append(name)
            picked[name] = default
        elif name == "relaxation":
            picked[name] = _as_float(name, data[name])
        else:
            picked[name] = _as_int(name, data[name])
    return SolverConfig(**picked)


def _air(p_atm_kpa, t_db, t_wb):
    return humid_air_state(
        _as_float("p_atm", p_atm_kpa) * 1000.0,
        T_db=_celsius("T_db_in", t_db),
        T_wb=_celsius("T_wb_in", t_wb),
    )


def _echo_design(data, values, aux):
    echoed = dict(data)
    for name, value in values.items():
        if isinstance(value, tuple):
            value = list(value)
        echoed.setdefault(name, value)
    _echo_aux(echoed, aux)
    return echoed


def _echo_aux(echoed, aux):
    echoed["eta_fan"] = aux.eta_fan
    echoed["eta_pump"] = aux.eta_pump
    echoed["N_cyc"] = aux.N_cyc
    echoed["drift_rate"] = aux.drift_rate * 100.0


def _results(mode, outcome, rating, geometry):
    tube = outcome.geometry if mode == "design" else geometry
    aux = rating.auxiliary
    body = {
        "Q_kW": rating.Q / 1000.0,
        "T_ref_out_C": rating.T_ref_out - 273.15,
        "p_ref_out_kPa": rating.p_ref_out / 1000.0,
        "region_out": rating.region_out,
        "x_out": rating.x_out,
        "subcooling_K": rating.subcooling,
        "superheat_K": rating.superheat,
        "T_air_out_C": rating.T_air_out - 273.15,
        "w_air_out": rating.w_air_out,
        "i_air_out_kJ_kg": rating.i_air_out / 1000.0,
        "T_film_min_C": rating.T_film_min - 273.15,
        "T_film_max_C": rating.T_film_max - 273.15,
        "h_m_kg_m2s": rating.h_m,
        "K_W_m2K": rating.resistances.K,
        "air_volume_flow_m3_s": aux.air_volume_flow,
        "fan_pressure_Pa": aux.fan_pressure,
        "fan_power_W": aux.fan_power,
        "spray_mass_flow_kg_s": aux.spray_mass_flow,
        "pump_volume_flow_m3_s": aux.pump_volume_flow,
        "pump_head_m": aux.pump_head,
        "pump_power_W": aux.pump_power,
        "m_evap_kg_s": aux.m_evap,
        "m_blowdown_kg_s": aux.m_blowdown,
        "m_drift_kg_s": aux.m_drift,
        "m_makeup_kg_s": aux.m_makeup,
        "estimated_wet_correction": aux.estimated_wet_correction,
    }
    if isinstance(tube, TubeGeometry):
        body.update(
            {
                "d_o_mm": tube.d_o * 1000.0,
                "d_i_mm": tube.d_i * 1000.0,
                "S_T_mm": tube.S_T * 1000.0,
                "S_L_mm": tube.S_L * 1000.0,
                "N_r": tube.N_r,
                "N_t": tube.N_t,
                "L_m": tube.L,
                "face_area_m2": tube.N_t * tube.S_T * tube.L,
                "area_m2": tube.N_t * tube.N_r * math.pi * tube.d_o * tube.L,
            }
        )
    if mode == "design":
        body["v_f_m_s"] = outcome.v_face
        body["gamma_kg_m_s"] = outcome.gamma
    return body


def _resistances(resistances):
    return {
        "share_ref": resistances.share_ref,
        "share_wall": resistances.share_wall,
        "share_out": resistances.share_out,
        "K_W_m2K": resistances.K,
        "R_ref_K_W": resistances.R_ref,
        "R_wall_K_W": resistances.R_wall,
        "R_out_K_W": resistances.R_out,
    }


def _correlation(record):
    return {
        "name": record.name,
        "citation": record.citation,
        "applicability": record.applicability,
        "parameters": [
            {"name": name, "value": value} for name, value in record.parameters
        ],
    }


def _write_csv(path, segments):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_COLUMNS)
        for row in distribution_rows(segments):
            writer.writerow(row)


def _summary(document):
    results = document["results"]
    resistances = document["resistances"]
    lines = [
        f"蒸发式冷凝器设计计算软件 v{document['environment']['app_version']}",
        "模式：设计" if document["mode"] == "design" else "模式：校核",
        f"换热量：{results['Q_kW']:.6g} kW",
    ]
    if "d_o_mm" in results:
        lines.extend(
            [
                f"管外径：{results['d_o_mm']:.6g} mm",
                f"管内径：{results['d_i_mm']:.6g} mm",
                f"横向管距：{results['S_T_mm']:.6g} mm",
                f"纵向管距：{results['S_L_mm']:.6g} mm",
                f"管排数：{results['N_r']}",
                f"每排管数：{results['N_t']}",
                f"管长：{results['L_m']:.6g} m",
                f"迎风面积：{results['face_area_m2']:.6g} m²",
                f"总传热面积：{results['area_m2']:.6g} m²",
            ]
        )
    if "v_f_m_s" in results:
        lines.append(f"迎面风速：{results['v_f_m_s']:.6g} m/s")
        lines.append(f"喷淋密度 Γ：{results['gamma_kg_m_s']:.6g} kg/(m·s)")
    lines.extend(
        [
            f"出口制冷剂温度：{results['T_ref_out_C']:.6g} °C",
            f"出口区段：{results['region_out']}",
            f"出口空气干球温度：{results['T_air_out_C']:.6g} °C",
            f"出口含湿量：{results['w_air_out']:.6g} kg/kg",
            f"出口空气焓：{results['i_air_out_kJ_kg']:.6g} kJ/kg",
            f"水膜温度：{results['T_film_min_C']:.6g} ～ {results['T_film_max_C']:.6g} °C",
            f"K：{results['K_W_m2K']:.6g} W/(m²·K)",
            f"热阻占比：制冷剂 {resistances['share_ref']:.6g}，管壁 {resistances['share_wall']:.6g}，外侧 {resistances['share_out']:.6g}",
            f"风机风量：{results['air_volume_flow_m3_s']:.6g} m³/s",
            f"风机全压：{results['fan_pressure_Pa']:.6g} Pa",
            f"风机轴功率：{results['fan_power_W']:.6g} W",
            f"水泵流量：{results['pump_volume_flow_m3_s']:.6g} m³/s",
            f"水泵扬程：{results['pump_head_m']:.6g} m",
            f"水泵轴功率：{results['pump_power_W']:.6g} W",
            f"蒸发水量：{results['m_evap_kg_s']:.6g} kg/s",
            f"排污量：{results['m_blowdown_kg_s']:.6g} kg/s",
            f"总补水量：{results['m_makeup_kg_s']:.6g} kg/s",
        ]
    )
    if document["diagnostics"]:
        lines.append("诊断：")
        lines.extend(f"- {item}" for item in document["diagnostics"])
    if document["warnings"]:
        lines.append("警告：")
        lines.extend(f"- {item}" for item in document["warnings"])
    return "\n".join(lines) + "\n"


def _with_defaults(data, optional, defaults):
    values = {}
    for name, default in optional.items():
        if name not in data:
            defaults.append(name)
            values[name] = default
        else:
            values[name] = data[name]
    return values


def _taken(data, name, default, defaults):
    if name not in data:
        defaults.append(name)
        return default
    return _as_float(name, data[name])


def _optional_float(data, name):
    if name not in data or data[name] is None:
        return None
    return _as_float(name, data[name])


def _optional_float_list(data, name):
    if name not in data or data[name] is None:
        return None
    return _float_list(name, data[name])


def _float_list(name, value):
    value = _as_sequence(name, value)
    return tuple(_as_float(name, item) for item in value)


def _int_list(name, value):
    value = _as_sequence(name, value)
    return tuple(_as_int(name, item) for item in value)


def _as_sequence(name, value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return [value]
    if isinstance(value, tuple):
        value = list(value)
    if not isinstance(value, list) or not value:
        raise InputError(f"{name} 必须是非空列表")
    return value


def _refrigerant(value):
    if not isinstance(value, str) or not value:
        raise InputError("refrigerant 必须是制冷剂名称")
    return value


def _celsius(name, value):
    return _as_float(name, value) + 273.15


def _as_float(name, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"{name} 必须是实数")
    if not math.isfinite(value):
        raise OutOfRangeError(name, value, "有限实数", "输入 JSON")
    return float(value)


def _as_int(name, value):
    number = _as_float(name, value)
    if not number.is_integer():
        raise InputError(f"{name} 必须是整数")
    return int(number)


def _reject_unknown(data, allowed):
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise InputError("未知字段：" + "、".join(unknown))
