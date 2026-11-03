"""校核模式表单。几何是确定值，风量和水量各自二选一。"""

from PySide6.QtWidgets import QComboBox, QFormLayout, QGroupBox, QScrollArea, QStackedWidget, QVBoxLayout, QWidget

from evapcond.gui.design_form import REFRIGERANTS, SURFACES, _parse_entry
from evapcond.gui.widgets import LineField


class RatingForm(QWidget):
    """校核输入。"""

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
        self._flow()
        self._aux()
        self._solver()
        self._layout.addStretch(1)
        scroll.setWidget(body)
        root.addWidget(scroll)

    def _conditions(self):
        box, form = self._group("设计工况")
        self.refrigerant = QComboBox()
        self.refrigerant.addItems(REFRIGERANTS)
        self.refrigerant.setCurrentText("R134a")
        form.addRow("制冷剂", self.refrigerant)
        self._line(form, "m_ref", "制冷剂质量流量", "kg/s")
        self._line(form, "T_in", "进口温度", "°C")
        self._line(form, "T_sat_in", "进口饱和温度", "°C")
        self._line(form, "p_in", "进口压力", "kPa")
        self._line(form, "T_db_in", "进口干球温度", "°C")
        self._line(form, "T_wb_in", "进口湿球温度", "°C")
        self._line(form, "p_atm", "大气压", "kPa", "101.325", optional=True)
        self.surface = QComboBox()
        self.surface.addItems(SURFACES)
        form.addRow("表面类型", self.surface)
        self._layout.addWidget(box)

    def _geometry(self):
        self.stack = QStackedWidget()
        tube = QWidget()
        tube_form = QFormLayout(tube)
        self._line(tube_form, "d_o", "管外径", "mm")
        self._line(tube_form, "wall_thickness", "壁厚", "mm", "2", optional=True)
        self._line(tube_form, "k_w", "管壁导热系数", "W/(m·K)", "63.9", optional=True)
        self._line(tube_form, "S_T", "横向管距", "mm")
        self._line(tube_form, "S_L", "纵向管距", "mm")
        self._line(tube_form, "N_r", "管排数", "—")
        self._line(tube_form, "N_t", "每排管数", "—")
        self._line(tube_form, "L", "管长", "m")
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

    def _flow(self):
        box, form = self._group("风量与喷淋")
        self.flow_form = form
        self.air_choice = QComboBox()
        self.air_choice.addItems(["迎面风速 v_f", "风量"])
        self.air_choice.currentIndexChanged.connect(self._show_flow)
        form.addRow("空气侧", self.air_choice)
        self._line(form, "v_f", "迎面风速", "m/s")
        self._line(form, "air_volume_flow", "风量", "m³/s")
        self.water_choice = QComboBox()
        self.water_choice.addItems(["喷淋密度 Γ", "喷淋水量"])
        self.water_choice.currentIndexChanged.connect(self._show_flow)
        form.addRow("喷淋侧", self.water_choice)
        self._line(form, "gamma", "喷淋密度 Γ", "kg/(m·s)")
        self._line(form, "m_spray", "喷淋水量", "kg/s")
        self._layout.addWidget(box)
        self._show_flow()

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

    def _show_flow(self):
        use_velocity = self.air_choice.currentIndex() == 0
        self.flow_form.setRowVisible(self.fields["v_f"], use_velocity)
        self.flow_form.setRowVisible(self.fields["air_volume_flow"], not use_velocity)
        use_gamma = self.water_choice.currentIndex() == 0
        self.flow_form.setRowVisible(self.fields["gamma"], use_gamma)
        self.flow_form.setRowVisible(self.fields["m_spray"], not use_gamma)

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
        if "air_volume_flow" in data and "v_f" not in data:
            self.air_choice.setCurrentIndex(1)
        else:
            self.air_choice.setCurrentIndex(0)
        if "m_spray" in data and "gamma" not in data:
            self.water_choice.setCurrentIndex(1)
        else:
            self.water_choice.setCurrentIndex(0)
        for key, field in self.fields.items():
            if key in data:
                field.set_text(data[key])
        self._show_surface(self.surface.currentText())
        self._show_flow()

    def payload(self):
        data = {
            "mode": "rating",
            "refrigerant": self.refrigerant.currentText(),
            "surface_type": self.surface.currentText(),
        }
        hidden = set()
        if self.air_choice.currentIndex() == 0:
            hidden.add("air_volume_flow")
        else:
            hidden.add("v_f")
        if self.water_choice.currentIndex() == 0:
            hidden.add("m_spray")
        else:
            hidden.add("gamma")
        surface = self.surface.currentText()
        if surface == "plate":
            hidden.update({"d_o", "wall_thickness", "k_w", "S_T", "S_L", "N_r", "N_t", "L", "fin_height", "fin_pitch", "fin_thickness"})
        elif surface == "tube_plain":
            hidden.update({"fin_height", "fin_pitch", "fin_thickness", "plate_width", "plate_height", "plate_spacing", "n_plates", "corrugation_angle", "corrugation_pitch", "corrugation_depth"})
        else:
            hidden.update({"plate_width", "plate_height", "plate_spacing", "n_plates", "corrugation_angle", "corrugation_pitch", "corrugation_depth"})
        for key, field in self.fields.items():
            if key in hidden:
                continue
            if key in ("n_cv_target", "max_iterations", "relaxation") and not self.solver_box.isChecked():
                continue
            parsed = _parse_entry(field.text(), False)
            if parsed is not None:
                data[key] = parsed
        return data


def rating_from_design(design_payload, outcome):
    """把设计结果抄入校核表单。只做单位换算，不重新计算热力。"""
    tube = outcome.geometry
    data = {
        "mode": "rating",
        "refrigerant": design_payload.get("refrigerant"),
        "m_ref": outcome.m_ref,
        "T_in": outcome.T_in - 273.15,
        "T_sat_in": design_payload.get("T_k"),
        "T_db_in": design_payload.get("T_db_in"),
        "T_wb_in": design_payload.get("T_wb_in"),
        "p_atm": design_payload.get("p_atm", 101.325),
        "surface_type": "tube_plain",
        "d_o": tube.d_o * 1000.0,
        "wall_thickness": tube.wall_thickness * 1000.0,
        "k_w": tube.k_w,
        "S_T": tube.S_T * 1000.0,
        "S_L": tube.S_L * 1000.0,
        "N_r": tube.N_r,
        "N_t": tube.N_t,
        "L": tube.L,
        "v_f": outcome.v_face,
        "gamma": outcome.gamma,
    }
    for key in (
        "zeta_de",
        "zeta_lv",
        "zeta_st",
        "p_noz",
        "H_lift",
        "pipe_length",
        "pipe_diameter",
        "zeta_pipe",
        "pipe_roughness",
        "eta_fan",
        "eta_pump",
        "N_cyc",
        "drift_rate",
    ):
        if key in design_payload:
            data[key] = design_payload[key]
    return data
