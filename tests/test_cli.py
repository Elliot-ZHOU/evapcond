"""命令行：退出码、结果文件，以及示例输入。"""

import ast
import json
from pathlib import Path

import pytest

from evapcond.cli import launch_gui, main
from evapcond.errors import CancelledError, ConvergenceError
from evapcond.io_json import CSV_COLUMNS, load_problem

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def test_cli_and_io_do_not_import_coolprop_or_pyside():
    for name in ("cli.py", "io_json.py", "__main__.py"):
        tree = ast.parse((ROOT / "evapcond" / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module.split(".")[0]]
            assert "CoolProp" not in modules
            assert "PySide6" not in modules


def test_missing_fields_and_unknown_key(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"mode": "design", "extra": 1}), encoding="utf-8")
    assert main(["design", "--input", str(path), "--out", str(tmp_path / "out")]) == 2
    path.write_text(
        json.dumps({"mode": "design", "Q_k": 5, "refrigerant": "R134a"}),
        encoding="utf-8",
    )
    code = main(["design", "--input", str(path), "--out", str(tmp_path / "out2")])
    assert code == 2


def test_missing_aux_lists_every_name(tmp_path, capsys):
    path = tmp_path / "partial.json"
    path.write_text(
        json.dumps(
            {
                "mode": "design",
                "Q_k": 5,
                "refrigerant": "R134a",
                "T_k": 40,
                "T_db_in": 32,
                "T_wb_in": 26,
                "surface_type": "tube_plain",
                "v_f_max": 8,
                "d_o": [19.05],
                "S_T_ratio": [2.5],
                "S_L_ratio": [2.0],
                "L": [2],
                "N_r": [4],
                "v_f_factor": [1],
                "gamma": [0.05],
            }
        ),
        encoding="utf-8",
    )
    assert main(["design", "--input", str(path), "--out", str(tmp_path / "out")]) == 2
    text = capsys.readouterr().err
    for name in ("zeta_de", "zeta_lv", "zeta_st", "p_noz", "H_lift", "pipe_length", "pipe_diameter", "zeta_pipe", "pipe_roughness"):
        assert name in text


def test_invalid_diameter_exits_3(tmp_path):
    source = json.loads((EXAMPLES / "design_example.json").read_text(encoding="utf-8"))
    source["d_o"] = [25.0]
    source["v_f_max"] = 1.0
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(source), encoding="utf-8")
    assert main(["design", "--input", str(path), "--out", str(tmp_path / "out")]) == 3


def test_exit_codes_for_convergence_and_cancel(tmp_path, monkeypatch):
    def boom(_design, config=None, refine=True, workers=1):
        raise ConvergenceError("不收敛", (1, 1, 1))

    monkeypatch.setattr("evapcond.cli.design_run", boom)
    assert main(["design", "--input", str(EXAMPLES / "design_example.json"), "--out", str(tmp_path / "a")]) == 4

    def cancel(_design, config=None, refine=True, workers=1):
        raise CancelledError("已取消")

    monkeypatch.setattr("evapcond.cli.design_run", cancel)
    assert main(["design", "--input", str(EXAMPLES / "design_example.json"), "--out", str(tmp_path / "b")]) == 5


def test_gui_module_can_be_imported():
    import evapcond.gui as gui

    assert callable(gui.main)
    assert callable(launch_gui)


def test_rating_example_writes_matching_files(tmp_path):
    out = tmp_path / "rated"
    assert main(["rating", "--input", str(EXAMPLES / "rating_example.json"), "--out", str(out)]) == 0
    _assert_outputs(out)


def test_design_example_writes_matching_files(tmp_path):
    out = tmp_path / "designed"
    assert main(["design", "--input", str(EXAMPLES / "design_example.json"), "--out", str(out)]) == 0
    document = _assert_outputs(out)
    assert document["results"]["Q_kW"] >= 5.0
    assert document["results"]["v_f_m_s"] <= 8.0
    loaded = load_problem(EXAMPLES / "design_example.json", "design")
    assert loaded.design.Q == pytest.approx(5000.0)
    assert "eta_fan" in loaded.defaults_used


def _assert_outputs(out):
    raw = (out / "distribution.csv").read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    header = raw.decode("utf-8-sig").splitlines()[0]
    assert header.split(",") == list(CSV_COLUMNS)
    document = json.loads((out / "result.json").read_text(encoding="utf-8"))
    assert set(document) == {
        "schema_version",
        "mode",
        "environment",
        "inputs",
        "defaults_used",
        "results",
        "resistances",
        "convergence",
        "correlations_used",
        "diagnostics",
        "warnings",
    }
    assert document["environment"]["app_version"] == "1.0.0"
    assert document["environment"]["coolprop_version"]
    shares = document["resistances"]
    assert abs(shares["share_ref"] + shares["share_wall"] + shares["share_out"] - 1.0) < 1e-9
    summary = (out / "summary.txt").read_text(encoding="utf-8")
    assert "换热量" in summary
    assert len((out / "distribution.csv").read_text(encoding="utf-8-sig").splitlines()) > 1
    return document
