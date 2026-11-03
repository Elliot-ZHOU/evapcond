"""设计模式表单。字段名与输入 JSON 一致。"""

import json

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from evapcond.gui.widgets import LineField

REFRIGERANTS = ("R717", "R22", "R134a", "R404A", "R507A", "R744")
SURFACES = ("tube_plain", "tube_lowfin", "plate")


class DesignForm(QWidget):
    """设计输入。可选字段预填并标为默认，必填辅助字段留空。"""

    def __init__(self):
        super().__init__()
        self.fields = {}
        root = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        self._layout = QVBoxLayout(body)
        self._conditions()
        self._geometry()
        self._aux()
        self._solver()
        self._layout.addStretch(1)
        scroll.setWidget(body)
        root.addWidget(scroll)

    def _conditions(self):
        box, form = self._group("设计工况")
        self._line(form, "Q_k", "换热量 Q_k", "kW")
        self.refrigerant = QComboBox()
        self.refrigerant.addItems(REFRIGERANTS)
        self.refrigerant.setCurrentText("R134a")
        form.addRow("制冷剂", self.refrigerant)
        self._line(form, "T_k", "冷凝温度 T_k", "°C")
        self._line(form, "superheat", "进口过热度", "K", "0", optional=True)
        self._line(form, "subcooling", "出口过冷度", "K", "0", optional=True)
        self._line(form, "T_db_in", "进口干球温度", "°C")
        self._line(form, "T_wb_in", "进口湿球温度", "°C")
        self._line(form, "p_atm", "大气压", "kPa", "101.325", optional=True)
        self.surface = QComboBox()
        self.surface.addItems(SURFACES)
        form.addRow("表面类型", self.surface)
        self._line(form, "v_f_max", "迎面风速上限", "m/s")
        self._layout.addWidget(box)

    def _geometry(self):
        self.stack = QStackedWidget()
        tube = QWidget()
        tube_form = QFormLayout(tube)
        self._line(tube_form, "d_o", "管外径候选", "mm", "19.05, 25, 32", optional=True)
        self._line(tube_form, "wall_thickness", "壁厚", "mm", "2", optional=True)
        self._line(tube_form, "k_w", "管壁导热系数", "W/(m·K)", "63.9", optional=True)
        self._line(tube_form, "S_T_ratio", "S_T/d_o 候选", "—", "2, 2.5", optional=True)
        self._line(tube_form, "S_L_ratio", "S_L/d_o 候选", "—", "1.5, 2", optional=True)
        self._line(tube_form, "L", "管长候选", "m", "2, 4, 6", optional=True)
        self._line(tube_form, "N_r", "管排候选", "—", "4, 8, 12, 16, 20, 24, 28", optional=True)
        self._line(tube_form, "v_f_factor", "风速系数", "×v_f_max", "0.6, 0.8, 1", optional=True)
        self._line(tube_form, "gamma", "Γ 候选，留空则取关联式范围", "kg/(m·s)")
        self.fin_box = QGroupBox("低翅片")
        fin_form = QFormLayout(self.fin_box)
        self._line(fin_form, "fin_height", "翅高", "mm")
        self._line(fin_form, "fin_pitch", "翅距", "mm")
        self._line(fin_form, "fin_thickness", "翅厚", "mm")
        tube_wrap = QWidget()
        tube_layout = QVBoxLayout(tube_wrap)
        tube_layout.addWidget(tube)
        tube_layout.addWidget(self.fin_box)
        plate = QWidget()
        plate_form = QFormLayout(plate)
        self._line(plate_form, "plate_width", "板宽", "mm")
        self._line(plate_form, "plate_height", "板高", "mm")
        self._line(plate_form, "plate_spacing", "板间距", "mm")
        self._line(plate_form, "n_plates", "板片数", "—")
        self._line(plate_form, "corrugation_angle", "波纹倾角", "°")
        self._line(plate_form, "corrugation_pitch", "波纹节距", "mm")
        self._line(plate_form, "corrugation_depth", "波纹深度", "mm")
        self.stack.addWidget(tube_wrap)
        self.stack.addWidget(plate)
        self._layout.addWidget(self.stack)
        self.surface.currentTextChanged.connect(self._show_surface)
        self._show_surface(self.surface.currentText())

    def _aux(self):
        box, form = self._group("辅助参数")
        self._line(form, "zeta_de", "收水器阻力系数", "—")
        self._line(form, "zeta_lv", "进风百叶阻力系数", "—")
        self._line(form, "zeta_st", "风筒阻力系数", "—")
        self._line(form, "p_noz", "喷嘴雾化压力", "kPa")
        self._line(form, "H_lift", "提升高度", "m")
        self._line(form, "pipe_length", "管路长度", "m")
        self._line(form, "pipe_diameter", "管路内径", "mm")
        self._line(form, "zeta_pipe", "管路局部阻力系数和", "—")
        self._line(form, "pipe_roughness", "管路粗糙度", "mm")
        self._line(form, "eta_fan", "风机效率", "—", "0.65", optional=True)
        self._line(form, "eta_pump", "水泵效率", "—", "0.70", optional=True)
        self._line(form, "N_cyc", "浓缩倍数", "—", "3", optional=True)
        self._line(form, "drift_rate", "风吹损失率", "%", "0.01", optional=True)
        self._layout.addWidget(box)

    def _solver(self):
        self.solver_box = QGroupBox("求解器设置")
        self.solver_box.setCheckable(True)
        self.solver_box.setChecked(False)
        form = QFormLayout(self.solver_box)
        self._line(form, "n_cv_target", "分段目标数", "—", "40", optional=True)
        self._line(form, "max_iterations", "最大迭代次数", "—", "500", optional=True)
        self._line(form, "relaxation", "松弛因子", "—", "1", optional=True)
        self._layout.addWidget(self.solver_box)

    def _group(self, title):
        box = QGroupBox(title)
        return box, QFormLayout(box)

    def _line(self, form, key, label, unit, default="", optional=False):
        field = LineField(key, unit, default, optional)
        form.addRow(label, field)
        self.fields[key] = field
        return field

    def _show_surface(self, surface):
        self.stack.setCurrentIndex(0 if surface != "plate" else 1)
        self.fin_box.setVisible(surface == "tube_lowfin")

    def clear_errors(self):
        for field in self.fields.values():
            field.clear_error()

    def show_error(self, exc):
        text = str(exc)
        param = getattr(exc, "param", "")
        matched = False
        for key, field in self.fields.items():
            if key == param or key in text:
                field.set_error(text)
                matched = True
        return matched

    def apply(self, data):
        self.refrigerant.setCurrentText(str(data.get("refrigerant", "R134a")))
        self.surface.setCurrentText(str(data.get("surface_type", "tube_plain")))
        for key, field in self.fields.items():
            if key in data:
                field.set_text(data[key])
        self._show_surface(self.surface.currentText())

    def payload(self):
        data = {"mode": "design", "refrigerant": self.refrigerant.currentText(), "surface_type": self.surface.currentText()}
        active = self._active_keys()
        for key, field in self.fields.items():
            if key not in active:
                continue
            if key in ("n_cv_target", "max_iterations", "relaxation") and not self.solver_box.isChecked():
                continue
            parsed = _parse_entry(field.text(), key in _LIST_KEYS)
            if parsed is not None:
                data[key] = parsed
        return data

    def _active_keys(self):
        keys = set(self.fields)
        surface = self.surface.currentText()
        plate_keys = {
            "plate_width",
            "plate_height",
            "plate_spacing",
            "n_plates",
            "corrugation_angle",
            "corrugation_pitch",
            "corrugation_depth",
        }
        fin_keys = {"fin_height", "fin_pitch", "fin_thickness"}
        if surface == "plate":
            keys -= fin_keys
        else:
            keys -= plate_keys
            if surface != "tube_lowfin":
                keys -= fin_keys
        return keys


_LIST_KEYS = {
    "d_o",
    "S_T_ratio",
    "S_L_ratio",
    "L",
    "N_r",
    "v_f_factor",
    "gamma",
}


def _parse_entry(text, as_list):
    if text == "":
        return None
    text = text.replace("，", ",")
    if not as_list:
        return json.loads(text)
    return [json.loads(item.strip()) for item in text.split(",") if item.strip()]
