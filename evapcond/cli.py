"""命令行。设计与校核共用同一套输入和结果文件。"""

import argparse
import sys

from evapcond.design import run as design_run
from evapcond.errors import (
    CancelledError,
    ConvergenceError,
    EvapCondError,
    InfeasibleDesignError,
    InputError,
    OutOfRangeError,
    UnconfirmedCorrelationError,
)
from evapcond.io_json import is_default_coarse, load_problem, write_outputs
from evapcond.rating import run as rating_run


def main(argv=None):
    """执行一条设计或校核命令。返回进程退出码。"""
    parser = argparse.ArgumentParser(prog="evapcond")
    sub = parser.add_subparsers(dest="mode", required=True)
    for name in ("design", "rating"):
        command = sub.add_parser(name)
        command.add_argument("--input", required=True)
        command.add_argument("--out", required=True)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return code if isinstance(code, int) else 2
    try:
        loaded = load_problem(args.input, args.mode)
        if args.mode == "design":
            full_grid = is_default_coarse(loaded.design)
            outcome = design_run(
                loaded.design,
                config=loaded.config,
                refine=full_grid,
                workers=None if full_grid else 1,
            )
        else:
            outcome = rating_run(loaded.rating, config=loaded.config)
        text = write_outputs(
            args.out,
            args.mode,
            loaded.inputs,
            loaded.defaults_used,
            outcome,
            None if loaded.rating is None else loaded.rating.geometry,
        )
    except (InputError, OutOfRangeError, UnconfirmedCorrelationError) as exc:
        print(exc, file=sys.stderr)
        return 2
    except InfeasibleDesignError as exc:
        print(exc, file=sys.stderr)
        return 3
    except ConvergenceError as exc:
        print(exc, file=sys.stderr)
        return 4
    except CancelledError as exc:
        print(exc, file=sys.stderr)
        return 5
    except EvapCondError as exc:
        print(exc, file=sys.stderr)
        return 2
    print(text, end="")
    return 0


def launch_gui():
    """无参数启动图形界面。界面模块完成前给出命令行用法。"""
    try:
        from evapcond.gui import main as gui_main
    except ImportError:
        print(
            "图形界面尚未提供。命令行用法："
            "python -m evapcond design|rating --input 文件 --out 目录",
            file=sys.stderr,
        )
        return 2
    return gui_main()
