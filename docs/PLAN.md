# 改动计划

状态：等待批准。批准前不创建 `evapcond/`，不写计算代码。

本计划依据 docs/SPEC.md 与 docs/correlations.md 的「用户确认」一节。规格正文不改。

## 批准时必须同时回答的两项

1. 干管束压降用哪一条关联式。补充二只给出 \(\Delta p_\mathrm{wet}=\Delta p_\mathrm{dry}(1+0.5\,\Gamma_m/\Gamma_\mathrm{ref})\)，没有给出 \(\Delta p_\mathrm{dry}\) 的函数、系数和文献。在指定之前，风机全压不能编码。
2. \(\Gamma_\mathrm{ref}\) 的定义。Mizushina 的有效范围是 \(0.195<\Gamma_m/d_o<5.556\,\mathrm{kg/(m^2\cdot s)}\)。请确认比值是 \((\Gamma_m/d_o)/\Gamma_\mathrm{ref}\)，且 \(\Gamma_\mathrm{ref}=(0.195+5.556)/2=2.8755\,\mathrm{kg/(m^2\cdot s)}\)；或给出别的定义。按补充二原文的 \(\Gamma_m/\Gamma_\mathrm{ref}\) 直接相除，单位不一致。

下面两项目前按「拟采用、随本计划批准」处理。不批准就改：

- 加速压降用均相比容：\(v=x/\rho_g+(1-x)/\rho_l\)，控制容积两端 \(\Delta p_\mathrm{acc}=G^2(v_\mathrm{out}-v_\mathrm{in})\)。
- Friedel 乘子的展开采用公开转写（1979 年 Ispra 原文未打开）：

\[
E=(1-x)^2+x^2\frac{\rho_l f_{go}}{\rho_g f_{lo}},\quad
F=x^{0.78}(1-x)^{0.224},\quad
H=\left(\frac{\rho_l}{\rho_g}\right)^{0.91}\left(\frac{\mu_g}{\mu_l}\right)^{0.19}\left(1-\frac{\mu_g}{\mu_l}\right)^{0.7}
\]

\[
\mathrm{Re}_{lo}=GD/\mu_l,\ \mathrm{Re}_{go}=GD/\mu_g
\]

\(f=16/\mathrm{Re}\)（\(\mathrm{Re}<2300\)）或 \(f=0.079\,\mathrm{Re}^{-0.25}\)。\(\rho_h=(x/\rho_g+(1-x)/\rho_l)^{-1}\)，\(\mathrm{Fr}=G^2/(g D\rho_h^2)\)，\(\mathrm{We}=G^2 D/(\sigma\rho_h)\)。技术文档写明这是「Friedel 两相乘子 + Blasius 单相摩擦系数」，不是 Friedel 原文摩擦系数。

## 锁定的依赖版本

写入 `requirements.txt` 与 `pyproject.toml`，各只锁定一个精确版本。

| 包 | 版本 | 依据 |
|---|---|---|
| CoolProp | 6.6.0 | 规格写死 |
| PySide6 | 6.6.2 | PyPI 上 6.6 系列可见的补丁版本；声明 Python >=3.8,<3.13。shiboken6、PySide6-Essentials、PySide6-Addons 由该版本固定为 6.6.2 |
| numpy | 1.26.4 | 满足 SciPy 1.11 的 numpy <1.27，且覆盖 Python 3.10–3.12 |
| scipy | 1.11.4 | PyPI 该版本支持 Python >=3.9,<3.13 |
| pytest | 8.3.4 | 拟锁定。支持 Python 3.10–3.12。本机直连 PyPI 时证书校验失败，没有在本机再次打开该版本页 |
| pyinstaller | 6.3.0 | PyPI 该版本支持 Python 3.8–3.12，含 onedir |

不增加上表以外的依赖。界面冒烟测试不使用 pytest-qt。

## 文件清单

按规格落地，不增减模式：

- `evapcond/__init__.py`（`__version__ = "1.0.0"`）、`__main__.py`、`cli.py`、`errors.py`、`models.py`、`io_json.py`
- `evapcond/properties/backend.py`、`coolprop_backend.py`、`refrigerant.py`、`humid_air.py`、`water.py`
- `evapcond/geometry/tube.py`、`plate.py`、`candidates.py`
- `evapcond/correlations/registry.py`、`film_air.py`、`condensation.py`、`single_phase.py`、`pressure_drop.py`、`plate.py`
- `evapcond/airside.py`、`refside.py`、`solver.py`、`auxiliary.py`、`rating.py`、`design.py`
- `evapcond/gui/__init__.py`、`__main__.py`、`main_window.py`、`design_form.py`、`rating_form.py`、`results_view.py`、`worker.py`、`widgets.py`
- `packaging/evapcond.spec`、`build_windows.bat`、`使用说明.txt`
- `examples/design_example.json`、`rating_example.json`
- `tests/test_properties.py`、`test_geometry.py`、`test_airside.py`、`test_refside.py`、`test_solver.py`、`test_auxiliary.py`、`test_design.py`、`test_rating.py`、`test_cli.py`、`test_validation.py`、`test_gui_smoke.py`
- `validation/cases/` 至少 3 个算例；没有用户文献数据时测试标记 skip，注明「待用户提供文献数据」
- `docs/technical.md`、`docs/correlations.md`（已有，实现时只追加与代码元数据一致的条目，不改确认结论）、`docs/validation_report.md`
- `README.md`、`pyproject.toml`、`requirements.txt`

计算内核不导入 PySide6。界面不写计算公式，只调用 `design.run` / `rating.run`。CoolProp 只出现在 `properties/`。

## 实现顺序

1. 3.1 物性：`properties/*` 与 `tests/test_properties.py`
2. 3.2 几何：`geometry/*` 与 `tests/test_geometry.py`
3. 3.3 空气侧：`correlations/film_air.py`、`airside.py` 与 `tests/test_airside.py`
4. 3.4 制冷剂侧：`correlations/condensation.py`、`single_phase.py`、`pressure_drop.py`、`refside.py` 与 `tests/test_refside.py`
5. 3.5 求解器：`solver.py` 与 `tests/test_solver.py`
6. 3.6 辅机：`auxiliary.py` 与 `tests/test_auxiliary.py`。风机全压依赖上面两项未闭合的湿压降，该项在回答前只留函数签名和失败测试，不填无来源的干管束公式
7. 校核：`rating.py`、`tests/test_rating.py`
8. 设计：`design.py`、`tests/test_design.py`
9. IO/CLI：`io_json.py`、`cli.py`、`tests/test_cli.py`
10. 界面：`gui/*`、`tests/test_gui_smoke.py`（`QT_QPA_PLATFORM=offscreen`）
11. 打包：`packaging/*`、示例 JSON、使用说明
12. 文档：`docs/technical.md`、`docs/validation_report.md`、`README.md`，并核对 `docs/correlations.md` 与代码元数据

每步完成后更新 docs/PROGRESS.md，并单独提交，信息格式为「步骤N：<内容>」。

## 各模块测试项

- 物性：六种制冷剂在 −40～+60 °C 与 CoolProp 直接调用的相对偏差 < 1e-9；越界 `OutOfRangeError`；R744 在 \(T_k>T_\mathrm{crit}-1\,\mathrm{K}\) 时终止并带规定语句；湿空气干球/湿球/相对湿度/含湿量/焓/密度两两往返相对误差 < 1e-6，含 \(T_\mathrm{wb}=T_\mathrm{db}\)。
- 几何：\(d_i=d_o-2\delta\)；迎风面积 \(N_t S_T L\)；管外面积；板式与低翅片字段可构造，但求解入口拒绝。
- 空气侧：显热、蒸发、潜热分开；空气温度由 \((i_a,w_a,p)\) 反算；\(\mathrm{Le}_f\) 在 \(w_s=w_a\) 时取 0.908 附近的极限；\(\Gamma_m\) 换算。
- 制冷剂侧：过热、两相、过冷按当地焓判断；每段用当地压力更新饱和温度；Shah 在 \(\mathrm{Re}_{GT}\le 35000\) 时出警告仍返回数值；Gnielinski 的三段雷诺数行为；Friedel+Blasius 在干度 0 与 1 的两端不返回 NaN。
- 求解器：三项收敛判据；至少 3 个工况在 \(n_L\) 加倍时换热量变化 < 0.5%；控制容积与全局能量残差 < 1e-6·Q；水量残差 < 1e-9 kg/s；热阻占比之和与 1 的差 < 1e-9。
- 辅机：Colebrook 对已知粗糙管的迭代；补水量 = 蒸发 + 排污 + 风吹；风吹分母为喷淋水量。湿压降测试在干管束公式指定前标记为未实现。
- 设计：可行候选满足 \(v_f\le v_{f,\max}\)、\(\Gamma_m/d_o\) 在关联式范围内、\(Q\ge Q_k\)；无解时退出码 3，且至少一条松弛建议；不输出违反约束的结果。
- 校核：以设计结果回代，换热量与 \(Q_k\) 的偏差 < 1% 且 \(Q\ge Q_k\)。R404A 的 diagnostics 含伪纯质那一句。
- CLI：成功退出码 0；输入错误 2；无可行设计 3；不收敛 4；取消 5。输出 `result.json`、`distribution.csv`（UTF-8 BOM）、`summary.txt`。
- 界面冒烟：启动、加载示例、校核运行、结果表非空。offscreen，不用 pytest-qt。
- 验证算例：无用户文献数据时 skip，并注明「待用户提供文献数据」。

边界用例同时覆盖：\(T_\mathrm{db}=T_\mathrm{wb}\)、制冷剂流量趋近于零、\(v_f\) 趋近于零。后两者越界时抛 `OutOfRangeError`，不返回 NaN 或 inf。

## 设计寻优的候选数与耗时

规格默认网格：

- \(d_o\)：3 个
- \((S_T/d_o,S_L/d_o)\)：2×2 = 4 个
- \(\Gamma\)：关联式范围与用户范围的交集上 3 点
- \(v_f\)：3 个
- \(L\)：5 个
- \(N_r\)：4 到 30，共 27 个

外层组合数 \(3\times 4\times 3\times 3\times 5\times 27=14580\)。每个组合还要对单回路流量做求根，求根按 8 次完整分段求解估计。

一次分段求解含约 40 个控制容积，并要多次调用 CoolProp。在这个调用量下，单次求根很难压到 0.062 s 以下，而 14580 个组合要在 15 min 内完成，平均每个组合只能用 0.062 s。因此默认网格按现有估计超过 15 min。若单次求根为 0.2 s，总时间约 49 min；若为 0.5 s，约 2.0 h。

缩减方案（请批准后才作为设计模式的默认搜索）：

- 保留全部 \(d_o\)、管距比、3 个 \(\Gamma\)、3 个 \(v_f\)
- \(L\) 改为 2、4、6 m
- \(N_r\) 改为 4、8、12、16、20、24、28

粗网格组合数 \(3\times 4\times 3\times 3\times 3\times 7=2268\)。若单次求根 0.2 s，约 7.6 min；若 0.5 s，约 19 min，仍超限。

粗网格选出最小面积的前 3 名后，只在这些点的 \(N_r\pm 2\)（步长 1，且不超过当时的 \(N_r\) 上限）和相邻整数管长上再搜索。追加组合数小于 50。

实现 3.5 时先测一个代表工况的单次求根时间。若按 2268 外推仍超过 15 min，停止并报告实测时间，不再自行把网格改小。

## 界面布局

主窗口标题「蒸发式冷凝器设计计算软件 v1.0.0」。三个标签页：设计模式、校核模式、结果。最小考虑 1366×768、150% 缩放。表单放在滚动区域里。

设计页自上而下：

- 设计工况：\(Q_k\)、制冷剂、\(T_k\)、进口过热度、出口过冷度、干球、湿球、大气压、`surface_type`、\(v_{f,\max}\)
- 几何与候选范围：随 `surface_type` 切换。光管显示 \(d_o\) 列表、壁厚、\(k_w\)、\(S_T/d_o\)、\(S_L/d_o\)、\(L\)、\(N_r\) 上下限。低翅片额外显示翅高、翅距、翅厚。板式显示板宽、板高、板间距、板片数、波纹倾角、波纹节距、波纹深度。列表用逗号分隔
- 辅助参数：三个阻力系数、喷嘴压力、提升高度、管长、管内径、\(\sum\zeta\)、粗糙度必填且初始为空；风机效率、水泵效率、浓缩倍数、风吹损失率预填默认值并标注「默认」
- 求解器设置：默认折叠。分段目标数、最大迭代、松弛因子

按钮一行：加载输入、保存输入、运行、取消、导出结果、以此设计结果生成校核输入。

校核页分组相同。几何改为确定值，不是候选列表。制冷剂流量、进口压力或进口饱和温度、进口温度必填。风量与 \(v_f\) 二选一，喷淋水量与 \(\Gamma\) 二选一。

结果页：摘要（带单位）、三项热阻表、沿程分布只读表（列与 CSV 相同，可排序）、警告、诊断、关联式名称与引用。无曲线。

运行时输入和「运行」禁用。设计进度显示已评估候选数/总数。校核进度显示迭代次数和三项残差。计算在 `QThread` 中，取消使用 `threading.Event`。

## zip 目录

在 Windows 上由 `build_windows.bat` 生成 `dist/EvapCond_v1.0.0_win64.zip`。pytest 失败则中止，不产生 zip。

```
EvapCond_v1.0.0_win64.zip
└── EvapCond/
    ├── EvapCond.exe
    ├── （PyInstaller onedir 运行库）
    ├── 使用说明.txt          UTF-8 带 BOM，只含规格 US-10 的 8 项
    └── examples/
        ├── design_example.json
        └── rating_example.json
```

`EvapCond.exe` 无参数时打开界面；`design|rating --input --out` 与 `python -m evapcond` 相同。`--windowed` 下命令行摘要同时写入 `<out>/summary.txt`。程序不向 exe 目录写文件。

## 实现时遵守的映射

- 补充二里的 `LaminarFlowUnsupportedError`、`CorrelationOutOfRangeError` 不新增类型，统一用 `OutOfRangeError`，消息包含参数名、当前值、有效范围、来源。
- 输入字段保持 `surface_type`：`tube_plain` / `tube_lowfin` / `plate`。不另建 `geometry_type`。
- `result.json` 记录 `environment.coolprop_version` 与 `environment.app_version`。运行时读 CoolProp 版本，不手写死在结果里；文档 `docs/technical.md` 写入实际使用的 6.6.0。
