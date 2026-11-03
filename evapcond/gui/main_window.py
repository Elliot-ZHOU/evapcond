"""主窗口。三个标签页，计算放在后台线程。"""

import json
import sys
import threading
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from evapcond import __version__
from evapcond.design import validate
from evapcond.errors import (
    CancelledError,
    ConvergenceError,
    InfeasibleDesignError,
    InputError,
    OutOfRangeError,
    UnconfirmedCorrelationError,
)
from evapcond.gui.design_form import DesignForm
from evapcond.gui.logutil import write_exception
from evapcond.gui.rating_form import RatingForm, rating_from_design
from evapcond.gui.results_view import ResultsView
from evapcond.gui.worker import SolveWorker
from evapcond.io_json import parse_problem, write_outputs


def examples_directory():
    """开发时用项目里的 examples，打包后用 exe 同级目录。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "examples"
    return Path(__file__).resolve().parents[2] / "examples"


class MainWindow(QMainWindow):
    """蒸发式冷凝器设计计算软件的主窗口。"""

    calculation_done = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"蒸发式冷凝器设计计算软件 v{__version__}")
        self.resize(1100, 760)
        self.design_form = DesignForm()
        self.rating_form = RatingForm()
        self.results_view = ResultsView()
        self.tabs = QTabWidget()
        self.tabs.addTab(self.design_form, "设计模式")
        self.tabs.addTab(self.rating_form, "校核模式")
        self.tabs.addTab(self.results_view, "结果")
        self.progress = QProgressBar()
        self.progress_text = QLabel("就绪")
        self.progress_text.setWordWrap(True)
        buttons = QHBoxLayout()
        self.load_button = self._button("加载输入", "loadButton", self.load_input)
        self.save_button = self._button("保存输入", "saveButton", self.save_input)
        self.run_button = self._button("运行", "runButton", self.run_current)
        self.cancel_button = self._button("取消", "cancelButton", self.cancel_current)
        self.export_button = self._button("导出结果", "exportButton", self.export_result)
        self.transfer_button = self._button(
            "以此设计结果生成校核输入", "transferButton", self.transfer_to_rating
        )
        for button in (
            self.load_button,
            self.save_button,
            self.run_button,
            self.cancel_button,
            self.export_button,
            self.transfer_button,
        ):
            buttons.addWidget(button)
        self.cancel_button.setEnabled(False)
        layout = QVBoxLayout()
        layout.addWidget(self.tabs, 1)
        layout.addWidget(self.progress)
        layout.addWidget(self.progress_text)
        layout.addLayout(buttons)
        holder = QWidget()
        holder.setLayout(layout)
        self.setCentralWidget(holder)
        self._worker = None
        self._cancel_event = None
        self._loaded = None
        self._outcome = None
        self._design_payload = None

    def _button(self, text, name, slot):
        button = QPushButton(text)
        button.setObjectName(name)
        button.clicked.connect(slot)
        return button

    def load_input(self):
        path, _selected = QFileDialog.getOpenFileName(
            self,
            "加载输入",
            str(examples_directory()),
            "JSON (*.json)",
        )
        if path:
            self.load_from_path(path)

    def load_from_path(self, path):
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            QMessageBox.warning(self, "输入错误", str(exc))
            return
        mode = data.get("mode")
        if mode == "design":
            self.tabs.setCurrentIndex(0)
            self.design_form.apply(data)
        elif mode == "rating":
            self.tabs.setCurrentIndex(1)
            self.rating_form.apply(data)
        else:
            QMessageBox.warning(self, "输入错误", "模式必须是 design 或 rating")

    def save_input(self):
        form = self._current_form()
        try:
            payload = form.payload()
        except json.JSONDecodeError as exc:
            QMessageBox.warning(self, "输入错误", f"有字段不是数字：{exc}")
            return
        path, _selected = QFileDialog.getSaveFileName(
            self,
            "保存输入",
            str(examples_directory()),
            "JSON (*.json)",
        )
        if not path:
            return
        Path(path).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def run_current(self):
        form = self._current_form()
        form.clear_errors()
        try:
            payload = form.payload()
            loaded = parse_problem(payload, payload["mode"])
            if loaded.mode == "design":
                validate(loaded.design)
        except json.JSONDecodeError as exc:
            QMessageBox.warning(self, "输入错误", f"有字段不是数字：{exc}")
            self.calculation_done.emit()
            return
        except (InputError, OutOfRangeError, UnconfirmedCorrelationError) as exc:
            if not form.show_error(exc):
                self._show_failure(exc)
            self.calculation_done.emit()
            return
        self._loaded = loaded
        if loaded.mode == "design":
            self._design_payload = payload
        self._set_running(True)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress_text.setText("正在计算")
        self._cancel_event = threading.Event()
        self._worker = SolveWorker(loaded, self._cancel_event)
        self._worker.progressed.connect(self._on_progress)
        self._worker.succeeded.connect(self._on_success)
        self._worker.failed.connect(self._on_failure)
        self._worker.start()

    def cancel_current(self):
        if self._cancel_event is not None:
            self._cancel_event.set()
            self.progress_text.setText("正在取消")

    def export_result(self):
        if self._outcome is None or self._loaded is None:
            QMessageBox.information(self, "导出结果", "还没有可导出的结果")
            return
        directory = QFileDialog.getExistingDirectory(self, "导出结果", str(Path.home()))
        if not directory:
            return
        geometry = None if self._loaded.rating is None else self._loaded.rating.geometry
        write_outputs(
            directory,
            self._loaded.mode,
            self._loaded.inputs,
            self._loaded.defaults_used,
            self._outcome,
            geometry,
        )
        QMessageBox.information(self, "导出结果", f"已写入 {directory}")

    def transfer_to_rating(self):
        if self._outcome is None or self._design_payload is None or self._loaded is None:
            QMessageBox.information(self, "生成校核输入", "请先完成一次设计计算")
            return
        if self._loaded.mode != "design":
            QMessageBox.information(self, "生成校核输入", "当前结果不是设计结果")
            return
        self.rating_form.apply(rating_from_design(self._design_payload, self._outcome))
        self.tabs.setCurrentIndex(1)

    def _on_progress(self, done, total, text):
        if total > 0:
            self.progress.setRange(0, total)
            self.progress.setValue(min(done, total))
        self.progress_text.setText(text)

    def _on_success(self, outcome):
        self._outcome = outcome
        geometry = None if self._loaded.rating is None else self._loaded.rating.geometry
        self.results_view.show_outcome(
            self._loaded.mode,
            self._loaded.inputs,
            self._loaded.defaults_used,
            outcome,
            geometry,
        )
        self.tabs.setCurrentIndex(2)
        self.progress_text.setText("计算完成")
        self._set_running(False)
        self.calculation_done.emit()

    def _on_failure(self, exc):
        self._set_running(False)
        if isinstance(exc, CancelledError):
            self.progress_text.setText("已取消")
            QMessageBox.information(self, "已取消", "已取消")
            self.calculation_done.emit()
            return
        self.progress_text.setText("计算未完成")
        self._show_failure(exc)
        self.calculation_done.emit()

    def _show_failure(self, exc):
        if isinstance(exc, (InputError, OutOfRangeError, ConvergenceError, UnconfirmedCorrelationError)):
            QMessageBox.warning(self, type(exc).__name__, str(exc))
            return
        if isinstance(exc, InfeasibleDesignError):
            QMessageBox.warning(self, "无可行设计", str(exc))
            return
        path = write_exception(type(exc), exc, exc.__traceback__)
        QMessageBox.critical(self, "未捕获的异常", f"{type(exc).__name__}: {exc}\n日志：{path}")

    def _set_running(self, running):
        self.design_form.setEnabled(not running)
        self.rating_form.setEnabled(not running)
        self.load_button.setEnabled(not running)
        self.save_button.setEnabled(not running)
        self.run_button.setEnabled(not running)
        self.export_button.setEnabled(not running)
        self.transfer_button.setEnabled(not running)
        self.cancel_button.setEnabled(running)
        if not running and self._worker is not None:
            self._worker = None

    def _current_form(self):
        if self.tabs.currentIndex() == 1:
            return self.rating_form
        if self.tabs.currentIndex() == 2 and self._loaded is not None and self._loaded.mode == "rating":
            return self.rating_form
        return self.design_form


def run_app():
    """创建应用并进入事件循环。"""
    from PySide6.QtWidgets import QApplication

    def hook(etype, value, tb):
        path = write_exception(etype, value, tb)
        QMessageBox.critical(None, "未捕获的异常", f"{etype.__name__}: {value}\n日志：{path}")

    sys.excepthook = hook
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
