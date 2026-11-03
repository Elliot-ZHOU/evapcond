"""未捕获异常写入日志，程序保持打开。"""

import sys
import traceback
from pathlib import Path


def log_file():
    """规格规定的日志路径。"""
    if sys.platform == "darwin":
        directory = Path.home() / "Library" / "Logs" / "EvapCond"
    else:
        local = Path.home() / "AppData" / "Local"
        directory = Path(sys.environ.get("LOCALAPPDATA", str(local))) / "EvapCond" / "logs"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "app.log"


def write_exception(etype, value, tb):
    path = log_file()
    with path.open("a", encoding="utf-8") as handle:
        traceback.print_exception(etype, value, tb, file=handle)
    return path
