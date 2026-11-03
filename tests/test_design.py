"""设计搜索：候选计数、越界剔除，以及一个候选的求根与校核。"""

import ast
from pathlib import Path

import pytest

from evapcond.design import NON_EXHAUSTIVE_NOTE, _coarse_groups, run
from evapcond.errors import InfeasibleDesignError, UnconfirmedCorrelationError
from evapcond.geometry.tube import outside_area
from evapcond.models import AuxInput, DesignInput, SolverConfig
from evapcond.properties.humid_air import humid_air_state

ROOT = Path(__file__).resolve().parents[1]


def _kelvin(value):
    return value + 273.15


def _aux():
    return AuxInput(
        zeta_de=2.0,
        zeta_lv=1.0,
        zeta_st=0.5,
        p_noz=150000.0,
        H_lift=4.0,
        pipe_length=20.0,
        pipe_diameter=0.05,
        zeta_pipe=1.5,
        pipe_roughness=5.0e-5,
    )


def _air():
    return humid_air_state(101325.0, T_db=_kelvin(32.0), T_wb=_kelvin(26.0))


def _design(**overrides):
    values = dict(
        Q=5000.0,
        refrigerant="R134a",
        T_k=_kelvin(40.0),
        air=_air(),
        v_face_max=8.0,
        aux=_aux(),
        d_o=(0.01905,),
        transverse_pitch_ratio=(2.5,),
        longitudinal_pitch_ratio=(2.0,),
        gamma=(0.05,),
        lengths=(2.0,),
        face_velocity_factor=(1.0,),
        rows=(4,),
    )
    values.update(overrides)
    return DesignInput(**values)


def test_design_module_does_not_import_coolprop_or_pyside():
    tree = ast.parse((ROOT / "evapcond" / "design.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        modules = []
        if isinstance(node, ast.Import):
            modules = [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules = [node.module.split(".")[0]]
        assert "CoolProp" not in modules
        assert "PySide6" not in modules


def test_default_coarse_grid_has_2268_candidates():
    design = DesignInput(
        Q=5000.0,
        refrigerant="R134a",
        T_k=_kelvin(40.0),
        air=_air(),
        v_face_max=3.0,
        aux=_aux(),
    )
    groups = _coarse_groups(design)
    assert sum(len(group.rows) for group in groups) == 2268
    assert "2268" in NON_EXHAUSTIVE_NOTE


def test_unsupported_surface_is_rejected_before_search():
    with pytest.raises(UnconfirmedCorrelationError):
        run(_design(surface_type="tube_lowfin"), workers=1, refine=False)


def test_invalid_diameter_is_rejected_without_a_feasible_design():
    with pytest.raises(InfeasibleDesignError) as caught:
        run(
            _design(d_o=(0.025,), v_face_max=1.0, face_velocity_factor=(1.0,)),
            workers=1,
            refine=False,
        )
    assert "在当前约束下无可行设计" in str(caught.value)


def test_one_candidate_meets_duty_and_limits():
    result = run(_design(), config=SolverConfig(), workers=1, refine=False)
    assert result.coarse_count == 1
    assert result.refined_count == 0
    assert result.geometry.d_o == pytest.approx(0.01905)
    assert result.v_face == pytest.approx(8.0)
    assert result.gamma == pytest.approx(0.05)
    assert result.area == pytest.approx(outside_area(result.geometry))
    assert result.rating.Q >= 5000.0
    assert result.geometry.N_t >= 1
    shares = (
        result.rating.resistances.share_ref
        + result.rating.resistances.share_wall
        + result.rating.resistances.share_out
    )
    assert abs(shares - 1.0) < 1e-9
