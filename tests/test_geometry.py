"""几何：内径、迎风面积、管外面积、候选网格，以及未确认表面的求解入口。"""

import ast
import math
from pathlib import Path

import pytest

from evapcond.errors import InputError, OutOfRangeError, UnconfirmedCorrelationError
from evapcond.geometry.candidates import (
    DEFAULT_D_O,
    DEFAULT_LENGTHS,
    DEFAULT_ROWS,
    EXHAUSTIVE_LENGTHS,
    EXHAUSTIVE_ROWS,
    ROW_EDGE_WARNING,
    expanded_lengths,
    expanded_rows,
    geometry_candidates,
    length_edge_warning,
    row_edge_warning,
)
from evapcond.geometry.plate import require_plate_calculation
from evapcond.geometry.tube import (
    UNSUPPORTED_SURFACE_MESSAGE,
    face_area,
    inside_area,
    outside_area,
    require_supported_surface,
    segment_outside_area,
    velocity_max_over_face,
    with_tube_count,
)
from evapcond.models import PlateGeometry, TubeGeometry

ROOT = Path(__file__).resolve().parents[1]


def _plain(**overrides):
    values = dict(
        surface_type="tube_plain",
        d_o=0.025,
        wall_thickness=0.002,
        k_w=63.9,
        S_T=0.050,
        S_L=0.040,
        N_r=8,
        N_t=10,
        L=3.0,
    )
    values.update(overrides)
    return TubeGeometry(**values)


def test_geometry_modules_do_not_import_coolprop_or_pyside():
    package = ROOT / "evapcond" / "geometry"
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module.split(".")[0]]
            assert "CoolProp" not in modules
            assert "PySide6" not in modules


def test_inner_diameter_face_area_and_outside_area():
    tube = _plain()
    assert tube.d_i == pytest.approx(0.021)
    assert tube.k_w == 63.9
    assert face_area(tube) == pytest.approx(10 * 0.050 * 3.0)
    segment = segment_outside_area(tube, tube.L)
    assert segment == pytest.approx(math.pi * 0.025 * 3.0)
    assert outside_area(tube) == pytest.approx(tube.N_t * tube.N_r * segment)
    assert inside_area(tube) == pytest.approx(math.pi * tube.d_i * tube.N_t * tube.N_r * tube.L)
    widened = with_tube_count(tube, 12)
    assert widened.N_t == 12
    assert face_area(widened) == pytest.approx(face_area(tube) * 1.2)


def test_velocity_ratio_uses_transverse_or_diagonal_opening():
    transverse = _plain()
    assert velocity_max_over_face(transverse) == pytest.approx(0.050 / (0.050 - 0.025))
    diagonal = _plain(d_o=0.020, wall_thickness=0.001, S_T=0.040, S_L=0.020)
    expected = 0.040 / (2.0 * (math.sqrt(0.0008) - 0.020))
    assert velocity_max_over_face(diagonal) == pytest.approx(expected)
    assert velocity_max_over_face(diagonal) != pytest.approx(2.0)


def test_invalid_tube_dimensions():
    with pytest.raises(OutOfRangeError) as caught:
        _plain(wall_thickness=0.013)
    assert caught.value.param == "wall_thickness"
    with pytest.raises(OutOfRangeError):
        _plain(S_T=0.025)
    with pytest.raises(InputError):
        _plain(N_t=0)
    with pytest.raises(InputError):
        _plain(arrangement="inline")
    with pytest.raises(InputError):
        _plain(fin_height=0.001)


def test_low_fin_and_plate_can_be_built_but_calculation_is_refused():
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
        fin_height=0.0015,
        fin_pitch=0.001,
        fin_thickness=0.0003,
    )
    assert low_fin.d_i == pytest.approx(0.01905 - 0.004)
    assert low_fin.fin_pitch == 0.001
    plate = PlateGeometry(
        plate_width=0.5,
        plate_height=1.2,
        plate_spacing=0.004,
        n_plates=40,
        corrugation_angle=math.radians(60),
        corrugation_pitch=0.008,
        corrugation_depth=0.002,
    )
    assert plate.n_plates == 40
    require_supported_surface("tube_plain")
    for surface in ("tube_lowfin", "plate"):
        with pytest.raises(UnconfirmedCorrelationError) as caught:
            require_supported_surface(surface)
        assert str(caught.value) == UNSUPPORTED_SURFACE_MESSAGE
    with pytest.raises(UnconfirmedCorrelationError):
        outside_area(low_fin)
    with pytest.raises(UnconfirmedCorrelationError):
        require_plate_calculation(plate)


def test_default_coarse_grid_and_exhaustive_lists():
    found = geometry_candidates()
    assert len(found) == 3 * 4 * 3 * 7
    assert {item.d_o for item in found} == set(DEFAULT_D_O)
    assert {item.L for item in found} == set(DEFAULT_LENGTHS)
    assert {item.N_r for item in found} == set(DEFAULT_ROWS)
    assert all(item.N_t == 1 and item.surface_type == "tube_plain" for item in found)
    assert {round(item.S_T / item.d_o, 6) for item in found} == {2.0, 2.5}
    assert {round(item.S_L / item.d_o, 6) for item in found} == {1.5, 2.0}
    sample = next(item for item in found if item.d_o == 0.025)
    assert sample.d_i == pytest.approx(sample.d_o - 0.004)
    exhaustive = geometry_candidates(lengths=EXHAUSTIVE_LENGTHS, rows=EXHAUSTIVE_ROWS)
    assert len(exhaustive) == 3 * 4 * 5 * 27


def test_edge_expansion_matches_supplement_four():
    assert expanded_rows(4) == ()
    assert expanded_rows(28) == (29, 30)
    assert expanded_rows(28, n_r_max=29) == (29,)
    assert expanded_rows(28, n_r_max=40) == (29, 30)
    assert expanded_rows(16) == ()
    assert expanded_lengths(2.0) == (1.0,)
    assert expanded_lengths(6.0) == (7.0, 8.0)
    assert expanded_lengths(6.0, l_max=7.0) == (7.0,)
    assert expanded_lengths(4.0) == ()
    assert row_edge_warning(4) == ROW_EDGE_WARNING
    assert row_edge_warning(28) == ROW_EDGE_WARNING
    assert row_edge_warning(12) is None
    assert "L=2 m" in length_edge_warning(2.0)
    assert "L=6 m" in length_edge_warning(6.0)
    assert length_edge_warning(4.0) is None
