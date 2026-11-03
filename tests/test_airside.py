"""空气侧：显热与潜热分开、Γ_m 换算、Lewis 极限，以及由焓反算温度。"""

import ast
import math
from pathlib import Path

import pytest

from evapcond.airside import (
    advance_moist_air,
    air_side_rates,
    dry_air_mass_flow,
    evaluate_air_side,
    film_resistance,
    gamma_m_from_gamma,
    gamma_m_from_spray,
    saturation_humidity,
    spray_mass_flow,
)
from evapcond.correlations.film_air import (
    LEWIS_LIMIT,
    MIZUSHINA_COEFFICIENT,
    MIZUSHINA_NOTE,
    air_convection_coefficient,
    bosnjakovic_lewis_factor,
    film_convection_coefficient,
)
from evapcond.errors import InputError, OutOfRangeError, UnconfirmedCorrelationError
from evapcond.models import TubeGeometry
from evapcond.properties.humid_air import humid_air_state, saturated_enthalpy
from evapcond.properties.water import latent_heat, vapor_enthalpy

ROOT = Path(__file__).resolve().parents[1]


def _tube(**overrides):
    values = dict(
        surface_type="tube_plain",
        d_o=0.01905,
        wall_thickness=0.002,
        k_w=63.9,
        S_T=0.0381,
        S_L=0.028575,
        N_r=4,
        N_t=2,
        L=2.0,
    )
    values.update(overrides)
    return TubeGeometry(**values)


def test_air_modules_do_not_import_coolprop():
    paths = [
        ROOT / "evapcond" / "airside.py",
        ROOT / "evapcond" / "correlations" / "film_air.py",
        ROOT / "evapcond" / "correlations" / "registry.py",
    ]
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module.split(".")[0]]
            assert "CoolProp" not in modules
            assert "PySide6" not in modules


def test_gamma_m_conversion_matches_both_definitions():
    tube = _tube()
    gamma = 0.0381
    m_spray = spray_mass_flow(gamma, tube.N_t, tube.L)
    assert m_spray == pytest.approx(gamma * 2 * tube.N_t * tube.L)
    from_spray = gamma_m_from_spray(m_spray, tube.d_o, tube.N_t * tube.S_T * tube.L)
    from_gamma = gamma_m_from_gamma(gamma, tube.d_o, tube.S_T)
    assert from_spray == pytest.approx(from_gamma)
    assert from_gamma / tube.d_o == pytest.approx(1.0)


def test_mizushina_value_range_and_separate_film_coefficient():
    d_o = 0.01905
    gamma_m = 1.0 * d_o
    expected = MIZUSHINA_COEFFICIENT * 1.0 ** (1.0 / 3.0)
    h_c, hc_record = air_convection_coefficient(gamma_m, d_o)
    h_w, hw_record = film_convection_coefficient(gamma_m, d_o)
    assert h_c == pytest.approx(expected)
    assert h_w == pytest.approx(h_c)
    assert hc_record.name == "Mizushina h_c"
    assert hw_record.name == "Mizushina h_w"
    assert "Mizushina" in hc_record.citation
    assert MIZUSHINA_NOTE.startswith("管外空气对流项采用 Mizushina et al. (1967)")
    for diameter in (0.0127, 0.040):
        value, _record = air_convection_coefficient(1.0 * diameter, diameter)
        assert value == pytest.approx(MIZUSHINA_COEFFICIENT)
    for diameter in (0.025, 0.032):
        with pytest.raises(OutOfRangeError) as caught:
            air_convection_coefficient(1.0 * diameter, diameter)
        assert caught.value.param == "d_o"
    for ratio in (0.195, 5.556, 0.1, 6.0):
        with pytest.raises(OutOfRangeError) as caught:
            air_convection_coefficient(ratio * d_o, d_o)
        assert caught.value.param == "Gamma_m/d_o"


def test_lewis_limit_and_no_extra_two_thirds_power():
    limit, _record = bosnjakovic_lewis_factor(0.01, 0.01)
    assert limit == pytest.approx(LEWIS_LIMIT)
    assert limit == pytest.approx(0.908, abs=0.001)
    w_s, w_a = 0.02, 0.01
    ratio = (w_s + 0.622) / (w_a + 0.622)
    expected = LEWIS_LIMIT * (ratio - 1.0) / math.log(ratio)
    value, _record = bosnjakovic_lewis_factor(w_s, w_a)
    assert value == pytest.approx(expected)
    assert value != pytest.approx(expected ** (2.0 / 3.0))
    overridden, _record = bosnjakovic_lewis_factor(w_s, w_a, le_f=1.0)
    assert overridden == pytest.approx(1.0)


def test_sensible_evaporation_and_latent_are_separate():
    dQ_s, dm_ev, dQ_l = air_side_rates(
        h_c=100.0,
        h_m=0.05,
        area=0.5,
        T_film=305.0,
        T_air=300.0,
        w_s=0.02,
        w_air=0.01,
        h_fg=2.4e6,
    )
    assert dQ_s == pytest.approx(100.0 * 0.5 * 5.0)
    assert dm_ev == pytest.approx(0.05 * 0.5 * 0.01)
    assert dQ_l == pytest.approx(dm_ev * 2.4e6)
    assert film_resistance(100.0, 0.2) == pytest.approx(1.0 / 20.0)


def test_outlet_temperature_comes_from_enthalpy_and_humidity():
    inlet = humid_air_state(101325.0, T_db=303.15, rh=0.5)
    m_dry = 0.4
    dQ_s = 800.0
    dm_ev = 0.001
    i_g = vapor_enthalpy(308.15)
    h_fg = latent_heat(308.15)
    outlet = advance_moist_air(inlet, m_dry, dQ_s, dm_ev, i_g)
    w_out = inlet.w + dm_ev / m_dry
    h_out = inlet.h + (dQ_s + dm_ev * i_g) / m_dry
    h_latent_path = inlet.h + (dQ_s + dm_ev * h_fg) / m_dry
    expected = humid_air_state(inlet.p, w=w_out, h=h_out)
    assert outlet.w == pytest.approx(expected.w, rel=1e-9)
    assert outlet.h == pytest.approx(expected.h, rel=1e-9)
    assert outlet.T_db == pytest.approx(expected.T_db, rel=1e-9)
    assert h_out != pytest.approx(h_latent_path, rel=1e-6)


def test_segment_uses_confirmed_closure_on_plain_tube():
    tube = _tube()
    inlet = humid_air_state(101325.0, T_db=303.15, rh=0.5)
    flux = evaluate_air_side(
        tube,
        inlet,
        T_film=308.15,
        area=0.01,
        m_dry=0.4,
        gamma=tube.S_T,
    )
    assert flux.h_c == pytest.approx(MIZUSHINA_COEFFICIENT)
    assert flux.h_w == pytest.approx(flux.h_c)
    assert flux.h_m == pytest.approx(flux.h_c / (inlet.cp * flux.le_f))
    assert flux.R_film == pytest.approx(1.0 / (flux.h_w * 0.01))
    assert flux.le_f == pytest.approx(LEWIS_LIMIT, rel=0.05)
    assert {item.name for item in flux.correlations} == {
        "Mizushina h_c",
        "Mizushina h_w",
        "Bosnjakovic Le_f",
    }
    forced = evaluate_air_side(
        tube,
        inlet,
        T_film=308.15,
        area=0.01,
        m_dry=0.4,
        gamma=tube.S_T,
        le_f=1.0,
    )
    assert forced.le_f == pytest.approx(1.0)
    assert forced.h_m == pytest.approx(forced.h_c / inlet.cp)


def test_non_plain_surface_and_non_positive_velocity_are_rejected():
    low_fin = TubeGeometry(
        surface_type="tube_lowfin",
        d_o=0.01905,
        wall_thickness=0.002,
        k_w=63.9,
        S_T=0.04,
        S_L=0.03,
        N_r=4,
        N_t=1,
        L=2.0,
        fin_height=0.001,
        fin_pitch=0.001,
        fin_thickness=0.0004,
    )
    inlet = humid_air_state(101325.0, T_db=303.15, rh=0.5)
    with pytest.raises(UnconfirmedCorrelationError):
        evaluate_air_side(low_fin, inlet, 308.15, 0.01, 0.4, gamma=0.04)
    with pytest.raises(InputError):
        dry_air_mass_flow(inlet, 0.0, 1.0)
    with pytest.raises(InputError):
        dry_air_mass_flow(inlet, -0.01, 1.0)
    positive = dry_air_mass_flow(inlet, 1.0e-6, 1.0)
    assert positive > 0.0
    assert math.isfinite(positive)


def test_fast_humidity_and_march_match_full_state():
    pressure = 101325.0
    temperature = 303.15
    saturated = humid_air_state(pressure, T_db=temperature, rh=1.0)
    assert saturation_humidity(temperature, pressure) == saturated.w
    assert saturated_enthalpy(temperature, pressure) == saturated.h
    inlet = humid_air_state(pressure, T_db=temperature, rh=0.5)
    marched = advance_moist_air(inlet, 0.4, 800.0, 0.001, vapor_enthalpy(308.15))
    full = humid_air_state(pressure, w=inlet.w + 0.001 / 0.4, h=inlet.h + (800.0 + 0.001 * vapor_enthalpy(308.15)) / 0.4)
    assert marched.w == full.w
    assert marched.h == full.h
    assert marched.T_db == full.T_db
    assert marched.cp == full.cp
    with pytest.raises(OutOfRangeError):
        saturation_humidity(273.15, pressure)
