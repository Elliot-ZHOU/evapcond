"""物性模块：与 CoolProp 直接调用对照，并检查规格中的范围。"""

import ast
import math
from itertools import combinations
from pathlib import Path

import CoolProp.CoolProp as CP
import pytest

from evapcond.errors import InputError, OutOfRangeError
from evapcond.properties.coolprop_backend import coolprop_version
from evapcond.properties.humid_air import humid_air_state
from evapcond.properties.refrigerant import (
    R404A_PSEUDOPURE_NOTE,
    SUPPORTED_REFRIGERANTS,
    check_condensing_temperature,
    coolprop_fluid_name,
    cp_pt,
    critical_temperature,
    density_pt,
    enthalpy_pt,
    is_pseudo_pure,
    liquid_cp,
    liquid_conductivity,
    liquid_density,
    liquid_enthalpy,
    liquid_prandtl,
    liquid_viscosity,
    phase_region,
    saturation_pressure,
    saturation_temperature,
    surface_tension,
    temperature_ph,
    vapor_cp,
    vapor_conductivity,
    vapor_density,
    vapor_enthalpy,
    vapor_prandtl,
    vapor_quality,
    vapor_viscosity,
)
from evapcond.properties.water import (
    conductivity as water_conductivity,
)
from evapcond.properties.water import (
    density as water_density,
)
from evapcond.properties.water import (
    latent_heat,
    liquid_enthalpy_sat,
)
from evapcond.properties.water import (
    specific_heat as water_cp,
)
from evapcond.properties.water import (
    surface_tension as water_surface_tension,
)
from evapcond.properties.water import (
    vapor_enthalpy as water_vapor_enthalpy,
)
from evapcond.properties.water import (
    viscosity as water_viscosity,
)

ROOT = Path(__file__).resolve().parents[1]
REL = 1e-9
AIR_KEYS = ("T_db", "T_wb", "rh", "w", "h", "rho")
SAT_OUTPUTS = (
    ("H", liquid_enthalpy, vapor_enthalpy),
    ("D", liquid_density, vapor_density),
    ("C", liquid_cp, vapor_cp),
    ("V", liquid_viscosity, vapor_viscosity),
    ("L", liquid_conductivity, vapor_conductivity),
    ("Prandtl", liquid_prandtl, vapor_prandtl),
)


def _kelvin(t_c):
    return t_c + 273.15


def assert_rel(actual, expected, label, rel=REL):
    assert math.isfinite(actual) and math.isfinite(expected), label
    scale = max(abs(actual), abs(expected))
    if scale == 0.0:
        assert actual == expected, label
        return
    error = abs(actual - expected) / scale
    assert error < rel, f"{label} 相对偏差 {error}，实际 {actual}，CoolProp {expected}"


def test_coolprop_version_is_locked_runtime_value():
    assert coolprop_version() == CP.get_global_param_string("version")
    assert coolprop_version() == "6.6.0"


def test_only_coolprop_backend_imports_coolprop():
    package = ROOT / "evapcond" / "properties"
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module.split(".")[0]]
            if "CoolProp" in modules:
                assert path.name == "coolprop_backend.py"


def test_refrigerant_names_and_pseudopure_note():
    assert SUPPORTED_REFRIGERANTS == ("R717", "R22", "R134a", "R404A", "R507A", "R744")
    assert coolprop_fluid_name("R717") == "HEOS::Ammonia"
    assert coolprop_fluid_name("R744") == "HEOS::CarbonDioxide"
    assert coolprop_fluid_name("R404A") == "HEOS::R404A"
    assert ".mix" not in coolprop_fluid_name("R404A")
    assert is_pseudo_pure("R404A") and is_pseudo_pure("R507A")
    assert not is_pseudo_pure("R134a")
    assert R404A_PSEUDOPURE_NOTE == (
        "R404A 按伪纯质计算，温度滑移未计入；若需精确滑移修正，应切换为混合物模型。"
    )


def test_unknown_refrigerant():
    with pytest.raises(InputError):
        coolprop_fluid_name("R410A")


def test_saturation_properties_match_coolprop():
    for name in SUPPORTED_REFRIGERANTS:
        fluid = coolprop_fluid_name(name)
        upper = _kelvin(60)
        if name == "R744":
            upper = critical_temperature(name) - 1.0
        for t_c in (-40, -10, 0, 20):
            T = _kelvin(t_c)
            if T > upper:
                continue
            _compare_saturation(name, fluid, T)
        _compare_saturation(name, fluid, upper)


def _compare_saturation(name, fluid, T):
    assert_rel(
        saturation_pressure(name, T),
        CP.PropsSI("P", "T", T, "Q", 0, fluid),
        f"{name} P {T}",
    )
    assert_rel(
        surface_tension(name, T),
        CP.PropsSI("I", "T", T, "Q", 0, fluid),
        f"{name} I {T}",
    )
    for output, liquid, vapor in SAT_OUTPUTS:
        assert_rel(
            liquid(name, T),
            CP.PropsSI(output, "T", T, "Q", 0, fluid),
            f"{name} liquid {output} {T}",
        )
        assert_rel(
            vapor(name, T),
            CP.PropsSI(output, "T", T, "Q", 1, fluid),
            f"{name} vapor {output} {T}",
        )


def test_saturation_temperature_round_trip_inside_range():
    for name in ("R717", "R22", "R134a", "R404A", "R507A"):
        for t_c in (-40, 20, 60):
            T = _kelvin(t_c)
            recovered = saturation_temperature(name, saturation_pressure(name, T))
            assert_rel(recovered, T, f"{name} Tsat {t_c}")


def test_refrigerant_temperature_out_of_range():
    for t_c in (-40.1, 60.1):
        with pytest.raises(OutOfRangeError) as caught:
            saturation_pressure("R134a", _kelvin(t_c))
        assert caught.value.param == "T_sat"
        assert "−40" in str(caught.value)
        assert "60" in str(caught.value)
        assert caught.value.source == "规格：制冷剂饱和温度 −40～+60 °C"


def test_r744_condensing_limit_message():
    limit = critical_temperature("R744") - 1.0
    check_condensing_temperature("R744", limit)
    saturation_pressure("R744", limit)
    with pytest.raises(OutOfRangeError) as caught:
        check_condensing_temperature("R744", limit + 1e-4)
    assert caught.value.param == "T_k"
    assert caught.value.source == "R744 在该冷凝温度下不适用蒸发式冷凝"
    assert "R744 在该冷凝温度下不适用蒸发式冷凝" in str(caught.value)
    assert str(limit) in caught.value.valid_range or "T_crit - 1 K" in caught.value.valid_range
    with pytest.raises(OutOfRangeError) as sat_caught:
        saturation_pressure("R744", _kelvin(40))
    assert sat_caught.value.source == "R744 在该冷凝温度下不适用蒸发式冷凝"


def test_r744_single_phase_above_critical_temperature_matches_coolprop():
    T = _kelvin(40)
    pressure = 5.0e6
    fluid = coolprop_fluid_name("R744")
    assert_rel(enthalpy_pt("R744", T, pressure), CP.PropsSI("H", "T", T, "P", pressure, fluid), "H")
    assert_rel(density_pt("R744", T, pressure), CP.PropsSI("D", "T", T, "P", pressure, fluid), "D")
    assert_rel(cp_pt("R744", T, pressure), CP.PropsSI("C", "T", T, "P", pressure, fluid), "C")


def test_phase_region_and_quality():
    T = _kelvin(20)
    pressure = saturation_pressure("R134a", T)
    h_f = liquid_enthalpy("R134a", T)
    h_g = vapor_enthalpy("R134a", T)
    mid = 0.5 * (h_f + h_g)
    assert phase_region("R134a", pressure, mid) == "two_phase"
    assert_rel(vapor_quality("R134a", pressure, mid), 0.5, "x", rel=1e-9)
    assert phase_region("R134a", pressure, h_f - 1000.0) == "subcooled"
    assert vapor_quality("R134a", pressure, h_f - 1000.0) is None
    assert phase_region("R134a", pressure, h_g + 1000.0) == "superheated"
    assert math.isfinite(temperature_ph("R134a", pressure, mid))


def test_water_matches_coolprop_and_rejects_bounds():
    fluid = "HEOS::Water"
    for t_c in (5, 20, 60):
        T = _kelvin(t_c)
        assert_rel(water_density(T), CP.PropsSI("D", "T", T, "P", 101325.0, fluid), "rho")
        assert_rel(water_cp(T), CP.PropsSI("C", "T", T, "P", 101325.0, fluid), "cp")
        assert_rel(water_viscosity(T), CP.PropsSI("V", "T", T, "P", 101325.0, fluid), "mu")
        assert_rel(water_conductivity(T), CP.PropsSI("L", "T", T, "P", 101325.0, fluid), "k")
        assert_rel(
            water_surface_tension(T),
            CP.PropsSI("I", "T", T, "Q", 0, fluid),
            "sigma",
        )
        assert_rel(liquid_enthalpy_sat(T), CP.PropsSI("H", "T", T, "Q", 0, fluid), "hf")
        assert_rel(water_vapor_enthalpy(T), CP.PropsSI("H", "T", T, "Q", 1, fluid), "hg")
        assert_rel(
            latent_heat(T),
            CP.PropsSI("H", "T", T, "Q", 1, fluid) - CP.PropsSI("H", "T", T, "Q", 0, fluid),
            "hfg",
        )
    for t_c in (4.9, 60.1):
        with pytest.raises(OutOfRangeError) as caught:
            water_density(_kelvin(t_c))
        assert caught.value.param == "T"
        assert "5" in str(caught.value) and "60" in str(caught.value)


def test_humid_air_round_trip_pairs():
    states = [
        humid_air_state(101325.0, T_db=_kelvin(30), rh=0.5),
        humid_air_state(101325.0, T_db=_kelvin(25), T_wb=_kelvin(25)),
        humid_air_state(101325.0, T_db=_kelvin(20), w=0.0),
        humid_air_state(90000.0, T_db=_kelvin(35), rh=0.6),
        humid_air_state(101325.0, T_db=_kelvin(5), rh=0.4),
        humid_air_state(101325.0, T_db=_kelvin(50), rh=0.3),
    ]
    assert states[1].rh == 1.0
    assert states[2].rh == 0.0
    assert states[2].w == 0.0
    for state in states:
        for left, right in combinations(AIR_KEYS, 2):
            if state.w == 0.0 and {left, right} == {"w", "rh"}:
                with pytest.raises(InputError):
                    humid_air_state(state.p, **{left: getattr(state, left), right: getattr(state, right)})
                continue
            recovered = humid_air_state(
                state.p,
                **{left: getattr(state, left), right: getattr(state, right)},
            )
            for key in AIR_KEYS:
                assert_rel(
                    getattr(recovered, key),
                    getattr(state, key),
                    f"p={state.p} {left}+{right} -> {key}",
                    rel=1e-6,
                )


def test_humid_air_out_of_range():
    with pytest.raises(OutOfRangeError) as low:
        humid_air_state(101325.0, T_db=_kelvin(4), rh=0.5)
    assert low.value.param == "T_db"
    with pytest.raises(OutOfRangeError):
        humid_air_state(101325.0, T_db=_kelvin(51), rh=0.5)
    with pytest.raises(OutOfRangeError):
        humid_air_state(101325.0, T_db=_kelvin(30), rh=1.1)
    with pytest.raises(OutOfRangeError):
        humid_air_state(101325.0, T_db=_kelvin(30), w=-0.001)
    saturated = humid_air_state(101325.0, T_db=_kelvin(30), rh=1.0)
    with pytest.raises(OutOfRangeError):
        humid_air_state(101325.0, T_db=_kelvin(30), w=saturated.w * 1.01)
    with pytest.raises(OutOfRangeError):
        humid_air_state(101325.0, T_db=_kelvin(30), T_wb=_kelvin(31))
    with pytest.raises(InputError):
        humid_air_state(101325.0, T_db=_kelvin(30))
    with pytest.raises(InputError):
        humid_air_state(101325.0, w=0.0, rh=0.0)
