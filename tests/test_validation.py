"""文献验证算例。没有文献传热系数时跳过，不编造偏差。"""

import json
from pathlib import Path

import pytest

CASES = Path(__file__).resolve().parents[1] / "validation" / "cases"


def _case_paths():
    found = sorted(CASES.glob("case_*.json"))
    assert len(found) >= 3
    return found


@pytest.mark.parametrize("path", _case_paths(), ids=lambda path: path.stem)
def test_literature_case(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["refrigerant"] in ("R717", "R134a")
    assert 35 <= data["T_k_C"] <= 45
    assert 20 <= data["T_wb_C"] <= 28
    if data.get("literature_K") is None:
        pytest.skip("待用户提供文献数据")
