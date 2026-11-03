"""表单控件。只收集文字，不换算热力结果。"""

from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget


class LineField(QWidget):
    """一行输入：数值、单位，以及可选的「默认」标记。"""

    def __init__(self, key, unit, default="", optional=False):
        super().__init__()
        self.key = key
        self._optional = optional
        self.edit = QLineEdit()
        self.edit.setText("" if default is None else str(default))
        self.edit.setClearButtonEnabled(True)
        unit_label = QLabel(unit)
        unit_label.setMinimumWidth(88)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.edit, 1)
        row.addWidget(unit_label)
        if optional and str(default) != "":
            row.addWidget(QLabel("默认"))
        self.error = QLabel()
        self.error.setWordWrap(True)
        self.error.setStyleSheet("color: #9b1c1c;")
        self.error.hide()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(row)
        layout.addWidget(self.error)

    def text(self):
        return self.edit.text().strip()

    def set_text(self, value):
        if isinstance(value, list):
            self.edit.setText(", ".join(str(item) for item in value))
        elif value is None:
            self.edit.setText("")
        else:
            self.edit.setText(str(value))

    def set_error(self, message):
        self.edit.setStyleSheet("border: 1px solid #9b1c1c;")
        self.error.setText(message)
        self.error.show()

    def clear_error(self):
        self.edit.setStyleSheet("")
        self.error.hide()
        self.error.setText("")
