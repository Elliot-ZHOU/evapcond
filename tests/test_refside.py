"""制冷剂侧：区段判断、Shah、Gnielinski 与 Friedel。"""

import ast
import math
from pathlib import Path

import pytest

from evapcond.correlations.condensation import (
    SHAH_LOW_RE_GT_WARNING,
    shah_condensation_coefficient,
)
from evapcond.correlations.pressure_drop import (
    acceleration_pressure_drop,
    fanning_friction_factor,
    friedel_friction_gradient,
    homogeneous_specific_volume,
    single_phase_friction_gradient,
)
from evapcond.correlations.single_phase import (
    GNIELINSKI_TRANSITION_WARNING,
    gnielinski_coefficient,
    gnielinski_nusselt,
)
from evapcond.errors import InputError, OutOfRangeError
from evapcond.properties.refrigerant import (
    enthalpy_pt,
    liquid_enthalpy,
    saturation_pressure,
    saturation_temperature,
    vapor_enthalpy,
)
from evapcond.refside import evaluate_refrigerant_segment, refrigerant_state, wall_resistance

ROOT = Path(__file__).resolve().parents[1]


def _kelvin(t_c):
    return t_c + 273.15


def test_refrigerant_modules_do_not_import_coolprop():
    paths = [
        ROOT / "evapcond" / "refside.py",
        ROOT / "evapcond" / "correlations" / "condensation.py",
        ROOT / "evapcond" / "correlations" / "single_phase.py",
        ROOT / "evapcond" / "correlations" / "pressure_drop.py",
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


def test_region_follows_local_enthalpy_and_pressure():
    refrigerant = "R134a"
    p_low = saturation_pressure(refrigerant, _kelvin(30.0))
    p_high = saturation_pressure(refrigerant, _kelvin(40.0))
    h_f = liquid_enthalpy(refrigerant, _kelvin(40.0))
    h_g = vapor_enthalpy(refrigerant, _kelvin(40.0))
    two_phase = refrigerant_state(refrigerant, p_high, 0.5 * (h_f + h_g))
    assert two_phase.region == "two_phase"
    assert two_phase.x == pytest.approx(0.5)
    assert two_phase.T == pytest.approx(two_phase.T_sat)
    assert two_phase.T_sat == pytest.approx(_kelvin(40.0))

    superheated = refrigerant_state(
        refrigerant, p_low, enthalpy_pt(refrigerant, _kelvin(50.0), p_low)
    )
    assert superheated.region == "superheated"
    assert superheated.x is None
    assert superheated.T == pytest.approx(_kelvin(50.0))
    assert superheated.T_sat == pytest.approx(saturation_temperature(refrigerant, p_low))

    subcooled = refrigerant_state(
        refrigerant, p_high, enthalpy_pt(refrigerant, _kelvin(30.0), p_high)
    )
    assert subcooled.region == "subcooled"
    assert subcooled.T == pytest.approx(_kelvin(30.0))
    assert subcooled.T_sat == pytest.approx(_kelvin(40.0))
    assert subcooled.T_sat != pytest.approx(superheated.T_sat)


def test_shah_warns_below_re_gt_and_rejects_outside_written_range():
    mu_l = 1.5e-4
    d = 0.015
    warned, record, warnings = shah_condensation_coefficient(
        200.0, d, 0.4, 1.0e6, 4.0e6, mu_l, 2.0, 0.08
    )
    re_lo = 200.0 * d / mu_l
    assert re_lo == pytest.approx(20000.0)
    assert warnings == (SHAH_LOW_RE_GT_WARNING,)
    assert math.isfinite(warned) and warned > 0.0
    assert record.name.startswith("Shah")

    quiet, _, no_warning = shah_condensation_coefficient(
        400.0, d, 0.4, 1.0e6, 4.0e6, mu_l, 2.0, 0.08
    )
    assert 400.0 * d / mu_l > 35000.0
    assert no_warning == ()
    assert math.isfinite(quiet)

    with pytest.raises(OutOfRangeError) as low_re:
        shah_condensation_coefficient(0.5, d, 0.4, 1.0e6, 4.0e6, mu_l, 2.0, 0.08)
    assert low_re.value.param == "Re_lo"
    with pytest.raises(OutOfRangeError):
        shah_condensation_coefficient(800.0, d, 0.4, 1.0e6, 4.0e6, mu_l, 2.0, 0.08)
    with pytest.raises(OutOfRangeError):
        shah_condensation_coefficient(200.0, d, 0.4, 1.0e6, 4.0e6, mu_l, 0.5, 0.08)
    with pytest.raises(OutOfRangeError):
        shah_condensation_coefficient(200.0, d, 1.0, 1.0e6, 4.0e6, mu_l, 2.0, 0.08)


def test_shah_matches_the_written_equation():
    g = 200.0
    d = 0.015
    x = 0.5
    mu_l = 1.5e-4
    pr_l = 2.0
    k_l = 0.08
    p_r = 0.25
    value, _, _ = shah_condensation_coefficient(g, d, x, 1.0e6, 4.0e6, mu_l, pr_l, k_l)
    re_lo = g * d / mu_l
    h_lo = 0.023 * re_lo**0.8 * pr_l**0.4 * k_l / d
    expected = h_lo * (
        (1.0 - x) ** 0.8 + 3.8 * x**0.76 * (1.0 - x) ** 0.04 / p_r**0.38
    )
    assert value == pytest.approx(expected)


def test_gnielinski_three_reynolds_bands():
    with pytest.raises(OutOfRangeError) as laminar:
        gnielinski_nusselt(2299.0, 2.0)
    assert laminar.value.param == "Re"

    transition, warnings = gnielinski_nusselt(2500.0, 2.0)
    assert warnings == (GNIELINSKI_TRANSITION_WARNING,)
    assert math.isfinite(transition) and transition > 0.0

    turbulent, quiet = gnielinski_nusselt(1.0e4, 0.7)
    assert quiet == ()
    assert math.isfinite(turbulent) and turbulent > 0.0

    upper, _ = gnielinski_nusselt(5.0e6, 2000.0)
    assert math.isfinite(upper)
    with pytest.raises(OutOfRangeError):
        gnielinski_nusselt(5.0e6 + 1.0, 2.0)
    with pytest.raises(OutOfRangeError) as low_pr:
        gnielinski_nusselt(1.0e4, 0.49)
    assert low_pr.value.param == "Pr"
    with pytest.raises(OutOfRangeError):
        gnielinski_nusselt(1.0e4, 2000.1)

    re = 1.0e4
    pr = 2.0
    nu, _ = gnielinski_nusselt(re, pr)
    f = (0.790 * math.log(re) - 1.64) ** -2
    expected = ((f / 8.0) * (re - 1000.0) * pr) / (
        1.0 + 12.7 * math.sqrt(f / 8.0) * (pr ** (2.0 / 3.0) - 1.0)
    )
    assert nu == pytest.approx(expected)
    h, record, _ = gnielinski_coefficient(100.0, 0.02, 1.0e-4, pr, 0.1)
    nu_h, _ = gnielinski_nusselt(100.0 * 0.02 / 1.0e-4, pr)
    assert h == pytest.approx(nu_h * 0.1 / 0.02)
    assert record.name.startswith("Gnielinski")


def test_friedel_endpoints_are_finite_and_match_single_phase_limits():
    args = dict(G=200.0, D=0.02, rho_l=1000.0, rho_g=20.0, mu_l=2.0e-4, mu_g=1.2e-5, sigma=0.01)
    liquid, _ = friedel_friction_gradient(x=0.0, **args)
    vapor, _ = friedel_friction_gradient(x=1.0, **args)
    middle, record = friedel_friction_gradient(x=0.5, **args)
    assert math.isfinite(liquid) and liquid > 0.0
    assert math.isfinite(vapor) and vapor > 0.0
    assert math.isfinite(middle) and middle > 0.0
    assert record.parameters

    f_lo = fanning_friction_factor(args["G"] * args["D"] / args["mu_l"])
    f_go = fanning_friction_factor(args["G"] * args["D"] / args["mu_g"])
    dp_lo = 2.0 * f_lo * args["G"] ** 2 / (args["D"] * args["rho_l"])
    dp_go = 2.0 * f_go * args["G"] ** 2 / (args["D"] * args["rho_g"])
    assert liquid == pytest.approx(dp_lo)
    assert vapor == pytest.approx(dp_go)
    single, _ = single_phase_friction_gradient(
        args["G"], args["D"], args["rho_l"], args["mu_l"]
    )
    assert single == pytest.approx(dp_lo)
    assert fanning_friction_factor(1000.0) == pytest.approx(16.0 / 1000.0)
    assert fanning_friction_factor(1.0e4) == pytest.approx(0.079 * 1.0e4**-0.25)


def test_homogeneous_acceleration_uses_specific_volume_change():
    v_in = homogeneous_specific_volume(0.8, 1000.0, 20.0)
    v_out = homogeneous_specific_volume(0.2, 1000.0, 20.0)
    drop, _ = acceleration_pressure_drop(100.0, v_in, v_out)
    assert drop == pytest.approx(100.0**2 * (v_out - v_in))
    assert drop < 0.0
    assert math.isfinite(drop)


def test_segment_updates_saturation_temperature_from_local_pressure():
    refrigerant = "R134a"
    p = saturation_pressure(refrigerant, _kelvin(40.0))
    h_f = liquid_enthalpy(refrigerant, _kelvin(40.0))
    h_g = vapor_enthalpy(refrigerant, _kelvin(40.0))
    h = 0.5 * (h_f + h_g)
    segment = evaluate_refrigerant_segment(
        refrigerant,
        d_i=0.015,
        d_o=0.019,
        k_w=63.9,
        dL=0.5,
        m_dot=0.02,
        p=p,
        h=h,
        T_w=_kelvin(35.0),
        R_film=1.0e-3,
    )
    assert segment.state_in.region == "two_phase"
    assert segment.state_in.T_sat == pytest.approx(saturation_temperature(refrigerant, p))
    assert segment.state_out.T_sat == pytest.approx(
        saturation_temperature(refrigerant, segment.state_out.p)
    )
    assert segment.state_out.p == pytest.approx(p - segment.dp_fric - segment.dp_acc)
    assert segment.dQ_ref > 0.0
    assert 0.02 * (h - segment.state_out.h) == pytest.approx(segment.dQ_ref)
    assert SHAH_LOW_RE_GT_WARNING in segment.warnings
    assert math.isfinite(segment.h_ref)
    assert segment.R_ref > 0.0
    assert segment.R_wall == pytest.approx(wall_resistance(0.019, 0.015, 63.9, 0.5))
    shares = segment.R_ref + segment.R_wall + segment.R_film
    assert segment.dQ_ref == pytest.approx((segment.state_in.T - _kelvin(35.0)) / shares)

    hot = evaluate_refrigerant_segment(
        refrigerant,
        d_i=0.015,
        d_o=0.019,
        k_w=63.9,
        dL=0.4,
        m_dot=0.02,
        p=saturation_pressure(refrigerant, _kelvin(30.0)),
        h=enthalpy_pt(refrigerant, _kelvin(50.0), saturation_pressure(refrigerant, _kelvin(30.0))),
        T_w=_kelvin(32.0),
        R_film=1.0e-3,
    )
    assert hot.state_in.region == "superheated"
    assert hot.warnings == ()

    cold_p = saturation_pressure(refrigerant, _kelvin(40.0))
    cold = evaluate_refrigerant_segment(
        refrigerant,
        d_i=0.015,
        d_o=0.019,
        k_w=63.9,
        dL=0.4,
        m_dot=0.03,
        p=cold_p,
        h=enthalpy_pt(refrigerant, _kelvin(30.0), cold_p),
        T_w=_kelvin(28.0),
        R_film=1.0e-3,
    )
    assert cold.state_in.region == "subcooled"
    assert cold.warnings == ()

    t_sat = saturation_temperature(refrigerant, p)
    h_sat_liquid = liquid_enthalpy(refrigerant, t_sat)
    saturated_liquid = evaluate_refrigerant_segment(
        refrigerant,
        d_i=0.015,
        d_o=0.019,
        k_w=63.9,
        dL=0.4,
        m_dot=0.02,
        p=p,
        h=h_sat_liquid,
        T_w=_kelvin(35.0),
        R_film=1.0e-3,
    )
    assert saturated_liquid.state_in.x == pytest.approx(0.0)
    assert saturated_liquid.correlations[0].name.startswith("Shah")
    near_liquid = evaluate_refrigerant_segment(
        refrigerant,
        d_i=0.015,
        d_o=0.019,
        k_w=63.9,
        dL=0.4,
        m_dot=0.02,
        p=p,
        h=h_f,
        T_w=_kelvin(35.0),
        R_film=1.0e-3,
    )
    assert math.isfinite(near_liquid.h_ref)

    with pytest.raises(InputError):
        evaluate_refrigerant_segment(
            refrigerant, 0.015, 0.019, 63.9, 0.4, 0.0, p, h, _kelvin(35.0), 1.0e-3
        )
