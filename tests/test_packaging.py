"""打包说明文件：UTF-8 BOM，且包含规格要求的 8 项。"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "packaging" / "使用说明.txt"
REQUIRED = (
    "Windows 10/11",
    "全部解压缩",
    "不得在压缩包内直接双击",
    "更多信息",
    "仍要运行",
    "桌面快捷方式",
    "加载输入",
    "EvapCond.exe design --input",
    "%LOCALAPPDATA%\\EvapCond\\logs\\app.log",
)


def test_user_guide_is_utf8_bom_and_covers_required_items():
    raw = GUIDE.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    for item in REQUIRED:
        assert item in text
    assert (ROOT / "packaging" / "build_windows.bat").is_file()
    assert (ROOT / "packaging" / "evapcond.spec").is_file()
    spec = (ROOT / "packaging" / "evapcond.spec").read_text(encoding="utf-8")
    assert 'name="EvapCond"' in spec
    assert "console=False" in spec
    assert "COLLECT(" in spec
