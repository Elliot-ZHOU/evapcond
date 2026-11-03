"""设计模式的光管几何候选，以及补充四的贴边外扩。"""

from evapcond.models import TubeGeometry

DEFAULT_WALL_THICKNESS = 0.002
DEFAULT_K_W = 63.9
DEFAULT_D_O = (0.01905, 0.025, 0.032)
DEFAULT_TRANSVERSE_PITCH_RATIO = (2.0, 2.5)
DEFAULT_LONGITUDINAL_PITCH_RATIO = (1.5, 2.0)
DEFAULT_LENGTHS = (2.0, 4.0, 6.0)
DEFAULT_ROWS = (4, 8, 12, 16, 20, 24, 28)
EXHAUSTIVE_LENGTHS = (2.0, 3.0, 4.0, 5.0, 6.0)
EXHAUSTIVE_ROWS = tuple(range(4, 31))

ROW_EDGE_WARNING = (
    "Warning: 最优解贴近初始搜索边界 (Nr=4或28)，"
    "已向物理允许方向外扩 1 个单位进行精细化验证。"
)
SPEC_ROW_LIMIT = 30
LENGTH_EXPANSION = 2.0
ROW_EXPANSION = 4


def geometry_candidates(
    d_o=DEFAULT_D_O,
    wall_thickness=DEFAULT_WALL_THICKNESS,
    k_w=DEFAULT_K_W,
    transverse_pitch_ratio=DEFAULT_TRANSVERSE_PITCH_RATIO,
    longitudinal_pitch_ratio=DEFAULT_LONGITUDINAL_PITCH_RATIO,
    lengths=DEFAULT_LENGTHS,
    rows=DEFAULT_ROWS,
):
    """单回路几何候选，N_t 先取 1。默认是补充三的粗网格几何部分。"""
    found = []
    for diameter in d_o:
        for transverse in transverse_pitch_ratio:
            for longitudinal in longitudinal_pitch_ratio:
                for length in lengths:
                    for n_r in rows:
                        found.append(
                            TubeGeometry(
                                surface_type="tube_plain",
                                d_o=float(diameter),
                                wall_thickness=float(wall_thickness),
                                k_w=float(k_w),
                                S_T=float(transverse) * float(diameter),
                                S_L=float(longitudinal) * float(diameter),
                                N_r=int(n_r),
                                N_t=1,
                                L=float(length),
                            )
                        )
    if not found:
        from evapcond.errors import InputError

        raise InputError("几何候选列表为空")
    return tuple(found)


def expanded_rows(n_r, n_r_max=SPEC_ROW_LIMIT):
    """管排贴边时新增的排数。下限 4 以外不新增；上侧最多到 30 与用户上限的较小者。"""
    if n_r == 4:
        return ()
    if n_r != 28:
        return ()
    upper = min(int(n_r_max), SPEC_ROW_LIMIT)
    return tuple(row for row in range(29, upper + 1))


def expanded_lengths(length, l_min=0.5, l_max=10.0):
    """管长贴边时按 1 m 步长外扩，跨度 ΔL = 2 m。"""
    if length == 2.0:
        values = []
        point = 1.0
        while point + 1e-12 >= l_min and point > 0.0 and point >= length - LENGTH_EXPANSION:
            if point <= l_max:
                values.append(point)
            point -= 1.0
        return tuple(sorted(values))
    if length == 6.0:
        return tuple(
            point for point in (7.0, 8.0) if l_min - 1e-12 <= point <= l_max + 1e-12
        )
    return ()


def row_edge_warning(n_r):
    """管排为 4 或 28 时返回补充四规定的原句，否则返回 None。"""
    if n_r in (4, 28):
        return ROW_EDGE_WARNING
    return None


def length_edge_warning(length):
    """管长贴边时用与管排警告相同的句式，并写入实际管长。"""
    if length not in (2.0, 6.0):
        return None
    shown = f"{length:g}"
    return (
        "Warning: 最优解贴近初始搜索边界 "
        f"(L={shown} m)，已向物理允许方向外扩 1 个单位进行精细化验证。"
    )
