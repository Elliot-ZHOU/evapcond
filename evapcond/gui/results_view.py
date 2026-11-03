"""结果页。摘要、热阻和沿程表都来自 io_json 的同一套字段。"""

from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from evapcond.io_json import CSV_COLUMNS, build_document, distribution_rows, summary_text


class ResultsView(QWidget):
    """只读结果。"""

    def __init__(self):
        super().__init__()
        self.summary = QTextEdit()
        self.summary.setReadOnly(True)
        self.resistances = QTableWidget(3, 3)
        self.resistances.setHorizontalHeaderLabels(["项目", "热阻 K/W", "占比"])
        self.resistances.verticalHeader().hide()
        self.resistances.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table = QTableWidget(0, len(CSV_COLUMNS))
        self.table.setHorizontalHeaderLabels(list(CSV_COLUMNS))
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.notes = QTextEdit()
        self.notes.setReadOnly(True)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("摘要"))
        layout.addWidget(self.summary, 2)
        layout.addWidget(QLabel("热阻"))
        layout.addWidget(self.resistances)
        layout.addWidget(QLabel("沿程分布"))
        layout.addWidget(self.table, 3)
        layout.addWidget(QLabel("警告、诊断与关联式"))
        layout.addWidget(self.notes, 2)

    def clear(self):
        self.summary.clear()
        self.resistances.clearContents()
        self.table.setRowCount(0)
        self.notes.clear()

    def show_outcome(self, mode, inputs, defaults_used, outcome, geometry=None):
        document = build_document(mode, inputs, defaults_used, outcome, geometry)
        self.summary.setPlainText(summary_text(document))
        resistances = document["resistances"]
        rows = (
            ("制冷剂侧", resistances["R_ref_K_W"], resistances["share_ref"]),
            ("管壁", resistances["R_wall_K_W"], resistances["share_wall"]),
            ("外侧", resistances["R_out_K_W"], resistances["share_out"]),
        )
        for index, (name, resistance, share) in enumerate(rows):
            self.resistances.setItem(index, 0, QTableWidgetItem(name))
            self.resistances.setItem(index, 1, QTableWidgetItem(f"{resistance:.6g}"))
            self.resistances.setItem(index, 2, QTableWidgetItem(f"{share:.6g}"))
        rating = outcome.rating if mode == "design" else outcome
        self.table.setSortingEnabled(False)
        values = distribution_rows(rating.segments)
        self.table.setRowCount(len(values))
        for row_index, row in enumerate(values):
            for column, value in enumerate(row):
                self.table.setItem(row_index, column, QTableWidgetItem(str(value)))
        self.table.setSortingEnabled(True)
        notes = []
        if document["warnings"]:
            notes.append("警告")
            notes.extend(f"- {item}" for item in document["warnings"])
        if document["diagnostics"]:
            notes.append("诊断")
            notes.extend(f"- {item}" for item in document["diagnostics"])
        if document["correlations_used"]:
            notes.append("关联式")
            for item in document["correlations_used"]:
                notes.append(f"- {item['name']}：{item['citation']}")
        self.notes.setPlainText("\n".join(notes))
