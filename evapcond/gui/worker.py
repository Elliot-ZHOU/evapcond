"""后台计算。界面线程只接收信号。"""

from PySide6.QtCore import QThread, Signal

from evapcond.design import run as design_run
from evapcond.io_json import is_default_coarse
from evapcond.rating import run as rating_run


class SolveWorker(QThread):
    """在线程中调用设计或校核。"""

    progressed = Signal(int, int, str)
    succeeded = Signal(object)
    failed = Signal(object)

    def __init__(self, loaded, cancel_event):
        super().__init__()
        self.loaded = loaded
        self.cancel_event = cancel_event

    def run(self):
        try:
            self.succeeded.emit(self._execute())
        except Exception as exc:
            self.failed.emit(exc)

    def _execute(self):
        def progress(done, total, text):
            self.progressed.emit(int(done), int(total), str(text))

        if self.loaded.mode == "design":
            full_grid = is_default_coarse(self.loaded.design)
            return design_run(
                self.loaded.design,
                config=self.loaded.config,
                progress_cb=progress,
                cancel_event=self.cancel_event,
                refine=full_grid,
                workers=None if full_grid else 1,
            )
        return rating_run(
            self.loaded.rating,
            config=self.loaded.config,
            progress_cb=progress,
            cancel_event=self.cancel_event,
        )
