"""界面冒烟：离屏启动、加载校核示例、运行、结果表非空。"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from evapcond.gui.main_window import MainWindow

ROOT = Path(__file__).resolve().parents[1]


def test_rating_example_fills_result_table():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    app.processEvents()
    window.load_from_path(ROOT / "examples" / "rating_example.json")
    loop = QEventLoop()
    window.calculation_done.connect(loop.quit)
    QTimer.singleShot(120000, loop.quit)
    window.run_button.click()
    if window._worker is not None:
        loop.exec()
    assert window.results_view.table.rowCount() > 0, window.progress_text.text()
    window.close()
    app.processEvents()
