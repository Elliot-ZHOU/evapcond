"""无参数时打开图形界面，有参数时走命令行。"""

import sys

from evapcond.cli import launch_gui, main

if __name__ == "__main__":
    if len(sys.argv) == 1:
        raise SystemExit(launch_gui())
    raise SystemExit(main())
