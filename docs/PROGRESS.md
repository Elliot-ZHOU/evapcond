# 进度

记录时间：2026-11-04。本文件只记载已经发生的事实。未写入本文件的决定视为不存在。

## a. 当前步骤及状态

- 步骤 0（关联式与默认参数确认表）：已完成。补充二、补充三、补充四的决定都在 docs/correlations.md。交接入口是 docs/HANDOFF.md。
- 步骤 1（改动计划）：正文在 docs/PLAN.md。网格、\(\Gamma_\mathrm{ref}\)、湿修正、Zukauskas–Ulinskas 系数表、\(C_2\) 拟合和外扩规则已由用户定稿。Friedel 展开式和均相加速压降已在步骤 3.4 按该文件编码。依赖版本仍是计划中的拟用版本，尚未单独批准。
- 步骤 3.1（物性）：已完成。
- 步骤 3.2（几何）：已完成。
- 步骤 3.3（空气侧）：已完成。测试见下方。
- 步骤 3.4（制冷剂侧）：已完成。
- 步骤 3.5（分段迭代求解器）：已完成。
- 步骤 3.6（辅机）：已完成。
- 校核模式：已完成。
- 求解耗时优化与设计搜索：已完成代码和单元测试。完整 2268 点搜索尚未对指定工况运行。
- IO/CLI：已完成。
- 图形界面：已完成离屏冒烟。
- 打包脚本与文档：已在本机写好。Windows 上的 `build_windows.bat` 尚未执行，zip 尚未生成。

## b. 已完成步骤

- 从本对话记录逐字提取最初提示词，保存为 docs/SPEC.md，并在「工作方式」末尾追加交接规则第 5 条。此后未改 SPEC.md。
- 步骤 0 对话中的确认表原文保存在 docs/correlations.md 前半部分。
- 阻塞项阅读稿：项目根目录「蒸发式冷凝器_步骤0_阻塞项.pdf」（5 页）。该 PDF 未纳入 git。
- 2026-11-03 读取补充二.docx 的正文与 11 张说明图，把其中的决定写入 docs/correlations.md。
- 2026-11-03 读取补充三.docx。\(\Gamma_\mathrm{ref}\)、湿修正和粗网格策略已写入 docs/correlations.md。
- 2026-11-03 读取补充四.docx。放弃 \(C_1\mathrm{Re}^{-m}\) 形式，改用 Zukauskas–Ulinskas 逆幂级数、补充四的 \(C_2\) 拟合，以及贴边外扩规则。原图与 docx 副本在 docs/sources/。交接说明在 docs/HANDOFF.md。
- 2026-11-03 对照 `docs/sources/zukauskas_euler_table.png` 核对三处争议系数，与 docs/correlations.md 补充四表格一致，表格不改：
  - \(a=1.25\)，\(10^3\sim 2\times 10^6\) 的 \(u=-0.599\times 10^{13}\)
  - \(a=2.0\)，\(7\sim 10^2\) 的 \(t=-0.582\times 10^{3}\)
  - \(a=2.5\)，\(10^2\sim 5\times 10^3\) 的 \(u=0.862\times 10^{8}\)
- 步骤 3.1：新增 `evapcond/__init__.py`（`__version__ = "1.0.0"`）、`evapcond/errors.py`、`evapcond/properties/backend.py`、`coolprop_backend.py`、`refrigerant.py`、`humid_air.py`、`water.py`、`tests/test_properties.py`，以及 `requirements.txt`、`pyproject.toml`、`.gitignore`。CoolProp 只在 `coolprop_backend.py` 导入。制冷剂与水用 HEOS；R404A、R507A 用伪纯质名 `HEOS::R404A`、`HEOS::R507A`。湿空气用 HAPropsSI。开发环境是仓库内 `.venv` 的 Python 3.12.16，因为本机 3.13/3.14 装不上 CoolProp 6.6.0。`.venv` 不入库。
- 测试（3.1 完成时）：在 `.venv` 中运行 `python -m pytest`，13 项通过，约 2.8 s。解释器 Python 3.12.16，pytest 8.3.4，CoolProp 6.6.0。
- 步骤 3.2：新增 `evapcond/models.py`（`TubeGeometry`、`PlateGeometry`）、`evapcond/geometry/tube.py`、`plate.py`、`candidates.py` 和 `tests/test_geometry.py`。\(d_i=d_o-2\delta\)，迎风面积 \(N_t S_T L\)，管外面积 \(N_t N_r \pi d_o L\)。默认几何候选是补充三粗网格的几何部分，252 个，\(N_t=1\)。贴边外扩按补充四：管排 28 新增 29 和 30，管长 2 m 新增 1 m，管长 6 m 新增 7 m 和 8 m。板式与低翅片可以构造，求解入口抛出规定的 `UnconfirmedCorrelationError`。
- 测试（3.2 完成时）：`python -m pytest` 20 项通过，约 2.9 s。此前 13 项物性测试仍通过。
- 步骤 3.3：新增 `evapcond/correlations/registry.py`、`film_air.py`、`evapcond/airside.py`、`tests/test_airside.py`，并在 `models.py` 增加 `CorrelationMeta` 与 `CorrelationRecord`。\(h_c\) 与 \(h_w\) 都是 \(2102.9(\Gamma_m/d_o)^{1/3}\)，分开调用。管径只接受 12.7、19.05、40 mm，因此默认候选里的 25 mm 和 32 mm 在调用该关联式时会 `OutOfRangeError`。\(\Gamma_m=\dot m_w d_o/(2A_f)=\Gamma d_o/S_T\)。\(\mathrm{Le}_f\) 默认 Bosnjaković，不再另取 \(2/3\) 次方；\(w_s=w_a\) 时为 \(0.865^{2/3}\approx 0.908\)。显热、蒸发、潜热分开。空气出口温度由 \((i_a,w_a,p)\) 反算，焓增使用 \(i_g\) 而不是 \(h_{fg}\)。
- 测试（3.3 完成时）：`python -m pytest` 28 项通过，约 3.1 s。
- 步骤 3.4：新增 `evapcond/correlations/condensation.py`、`single_phase.py`、`pressure_drop.py`、`evapcond/refside.py`、`tests/test_refside.py`。管内冷凝用补充二写出的 Shah 式，\(\mathrm{Re}_{GT}=GD/\mu_l\)。\(\mathrm{Re}_{GT}\le 35000\) 且仍在 100–63000 内时计算并写入规定警告。单相用 Gnielinski 公开转写：\(\mathrm{Re}<2300\) 或 \(\mathrm{Re}>5\times 10^6\) 抛 `OutOfRangeError`，\(2300\le\mathrm{Re}<3000\) 计算并警告。两相摩擦用 Friedel 乘子加 Blasius Fanning 摩擦系数，展开式按 docs/PLAN.md；干度 0 和 1 退化为对应单相梯度。加速压降 \(\Delta p_\mathrm{acc}=G^2(v_\mathrm{out}-v_\mathrm{in})\)，\(v=x/\rho_g+(1-x)/\rho_l\)。区段按当地焓判断。出口饱和温度由出口压力重算。\(0\le x<1\) 用 Shah；\(x=1\) 时该式括号第二项为零，改用饱和蒸气 Gnielinski。空气侧文件未改。
- 测试（3.4 完成时）：在 `.venv` 中运行 `python -m pytest`，36 项通过，约 3.0 s。此前 28 项仍通过。解释器 Python 3.12.16。
- 步骤 3.5：新增 `evapcond/solver.py`、`tests/test_solver.py`，并在 `models.py` 增加 `SolverConfig`、`SegmentState`、`ResistanceSummary`、`ConvergenceInfo`。\(n_L=\mathrm{ceil}(N_{cv,target}/N_r)\)，默认 40。空气自下而上，喷淋水自上而下，制冷剂按排蛇形。水膜温度取该控制容积能量平衡的出口温度，并在同一温度上计算热流。顶排喷淋水温等于各列底排出口的质量加权温度。干管束压降未写入。默认 \(N_{cv,target}=40\) 在 3 个 R134a 工况上，\(n_L\) 加倍后换热量变化小于 0.5%，因此没有提高默认分段数。
- 焓参考态：25 °C、相对湿度 0.5 时，\((h-h_\mathrm{dry})/w\) 比 HEOS 饱和蒸气焓低约 92 J/kg，与进度里约 97 J/kg 是同一量级。饱和含湿量处的局部差分大约差 770 J/kg。两个绝对值不能相加。求解器只把 \(i_g\) 加到已有的 HAProps 焓上。空气侧焓增、制冷剂焓降和水膜 \(c_p\Delta T\) 平衡都按这个增量闭合，测试里的能量残差小于 \(10^{-6}Q\)。
- 测试（3.5 完成时）：在 `.venv` 中运行 `python -m pytest`，41 项通过，约 221 s。解释器 Python 3.12.16。耗时主要来自分段求解；此前 36 项仍通过。
- 步骤 3.6：新增 `evapcond/correlations/bundle_pressure.py`、`evapcond/correlations/pipe_friction.py`、`evapcond/auxiliary.py`、`tests/test_auxiliary.py`，并在 `models.py` 追加 `AuxInput`、`AuxResult`。编码前重读 `docs/sources/zukauskas_euler_table.png`，九行系数与 docs/correlations.md 补充四一致，三处争议系数不改。干管束用该逆幂级数、\(k_1=1\) 和 \(C_2\)；湿修正用 \(\Gamma_\mathrm{ref}=2.8755\) 与系数 0.5；管路用 Colebrook–White 的 Darcy \(\lambda\)，Swamee–Jain 只作初值，\(|\Delta\lambda|<10^{-8}\)。风机全压里的附件阻力用迎面风速。喷淋水量 \(=\Gamma\cdot 2\cdot N_t\cdot L\)。补水量 = 蒸发 + 排污 + 风吹，风吹分母是喷淋水量。结果带 `estimated_wet_correction=True`，以及补充三、补充四要求的说明句。3.3–3.5 的传热文件未改。\(\rho\)、\(\mu\) 由调用方传入。
- 公共雷诺数端点归入较高雷诺数行；各 \(a\) 的最低下界和最高上界包含在内。这是实现时的划分，补充四没有写端点归属。\(a=2.0\) 且约 \(10^4\le\mathrm{Re}_\mathrm{max}\le 2.36\times 10^4\) 时级数非正，抛 `OutOfRangeError`，不返回负压降。
- 测试（3.6 完成时）：在 `.venv` 中运行 `python -m pytest`，51 项通过，222.47 s。解释器 Python 3.12.16，pytest 8.3.4。此前 41 项仍通过。新增 10 项在 `tests/test_auxiliary.py`。
- 校核：新增 `evapcond/rating.py`、`tests/test_rating.py`，并在 `models.py` 追加 `RatingInput`、`RatingResult`。`run` 调用已有的 `solve` 与 `evaluate_auxiliary`，不改 3.3–3.6 的公式。风量与 \(v_f\) 二选一，喷淋水量与 \(\Gamma\) 二选一，进口压力与进口饱和温度至少给一个。两者同时给出时，由压力反算的饱和温度与输入相差不得超过 \(10^{-3}\,\mathrm{K}\)。进口温度与饱和温度相差不超过 \(10^{-4}\,\mathrm{K}\) 时，进口焓按饱和蒸气计算。出口干度、过冷度或过热度由出口压力和焓判断。\(h_m\) 是各控制容积的算术平均。R404A 的诊断包含伪纯质那一句。
- 管束压降和附件阻力使用进口湿空气的 \(\rho\)、\(\mu\)。水泵使用求解得到的循环喷淋水温，压力取进口空气压力。这是接入时采用的截面，补充材料没有指定；若要改成出口或沿程平均，须另说。
- 测试（校核完成时）：在 `.venv` 中运行 `python -m pytest`，58 项通过，247.72 s。解释器 Python 3.12.16，pytest 8.3.4。此前 51 项仍通过。新增 7 项在 `tests/test_rating.py`。
- 2026-11-04 优化：`evapcond/properties/humid_air.py`、`backend.py`、`evapcond/airside.py`、`solver.py`、`design.py`、`models.py` 及对应测试。同一代表工况一次求解从 25.31 s 降到 1.37 s，17 轮，换热量 5487.45 W，与优化前打印的 5487.5 W 一致。`.venv` 中 `python -m pytest`：64 项通过，26.23 s。一个 7 排候选组（管径 19.05 mm，\(S_T/d_o=2.5\)，管长 2 m，迎面风速 8 m/s，\(\Gamma=0.05\)）耗时 57.2 s。按此估计，有效管径的约 108 组在 8 路并行下粗网格大约 15 min，细化另加几分钟。没有启动未指定工况的完整 2268 点搜索。
- 2026-11-04 IO/CLI：新增 `evapcond/io_json.py`、`evapcond/cli.py`、`evapcond/__main__.py`、`examples/design_example.json`、`examples/rating_example.json`、`tests/test_cli.py`。输入用工程单位，内部仍是 SI。结果写出 `result.json`、带 BOM 的 `distribution.csv` 和 `summary.txt`。退出码 0/2/3/4/5。示例是已经跑通的单候选，不是 2268 点网格；只有输入恰好为默认粗网格时才细化并并行。无参数启动会提示图形界面尚未提供。`python -m pytest`：72 项通过，36.92 s。其中 `tests/test_cli.py` 8 项。
- 2026-11-04 界面：新增 `evapcond/gui/`（主窗口、设计页、校核页、结果页、后台线程）和 `tests/test_gui_smoke.py`。界面只调用 `design.run`、`rating.run` 和 `io_json`。离屏冒烟为启动、加载 `examples/rating_example.json`、校核运行、结果表非空。`QT_QPA_PLATFORM=offscreen` 下 `python -m pytest`：73 项通过，38.41 s。未捕获异常写入 `~/Library/Logs/EvapCond/app.log`。
- 2026-11-04 打包与文档：新增 `packaging/build_windows.bat`、`packaging/evapcond.spec`、`packaging/使用说明.txt`（UTF-8 BOM，仅规格 US-10 的 8 项）、`docs/technical.md`、`docs/validation_report.md`、`README.md`、`validation/cases/case_r717.json`、`case_r134a_a.json`、`case_r134a_b.json`。文献 `K` 为空，`tests/test_validation.py` 跳过并注明「待用户提供文献数据」。未在 Windows 上运行打包脚本。

## c. 用户已确认的决定

来源：`/Users/zhouhui/Desktop/补充二.docx`。公式与范围的全文见 docs/correlations.md「用户确认」一节。

- US-8 原文无法从公开渠道获得完整系数。管外 \(h_c\) 改用 Mizushina 等 (1967)：\(h=2102.9\,(\Gamma_m/d_o)^{1/3}\)。\(\Gamma_m=\dot m_w d_o/(2A_f)\)。结果中必须带补充二规定的那句说明。
- Lewis 因子默认用 Bosnjaković 式，\(h_m=h_c/(c_{p,a}\mathrm{Le}_f)\)。可覆盖为 \(\mathrm{Le}_f=1\)。
- 水膜 \(h_w\) 用同一条 Mizushina 式，热阻单独串联。不采用 Parker & Treybal。
- 管内冷凝按补充二写出的 Shah 公式编码，文献标签写作 Shah (2009)。\(\mathrm{Re}_{GT}\le 35000\) 时计算并写警告，不剔除。
- 管内单相采用 Gnielinski (1976) 公开转写。\(\mathrm{Re}<2300\) 与 \(\mathrm{Re}>5\times 10^6\) 为越界；\(2300\le\mathrm{Re}<3000\) 计算并警告。异常类不新增，使用规格中的 `OutOfRangeError`。
- 两相摩擦压降采用 Friedel (1979) 乘子加 Blasius 摩擦系数。加速压降计入当地压力。\(E,F,H,\mathrm{Fr},\mathrm{We}\) 的展开式补充二未逐项给出，随改动计划一并请用户批准。
- 板式与低翅片：调用即 `UnconfirmedCorrelationError`，本期只算 `surface_type=tube_plain`。
- 管路摩擦：Colebrook–White 的 Darcy \(\lambda\)，Swamee–Jain 作初值，\(|\Delta\lambda|<10^{-8}\)。
- 默认值：\(\eta_\mathrm{fan}=0.65\)，\(\eta_\mathrm{pump}=0.70\)，\(N_\mathrm{cyc}=3.0\)，风吹损失率 = 喷淋水量的 0.01%。均写作用户可覆盖的工程取值，不写成标准强制条款。
- \(k_w=63.9\,\mathrm{W/(m\cdot K)}\) 确认采用。
- 锁定的依赖版本：尚未批准。拟用版本写在 docs/PLAN.md。
- 2026-11-03 补充三：\(\Gamma_\mathrm{ref}=2.8755\,\mathrm{kg/(m^2\cdot s)}\)，湿修正为 \(\Delta p_\mathrm{wet}=\Delta p_\mathrm{dry}\left(1+0.5(\Gamma_m/d_o)/\Gamma_\mathrm{ref}\right)\)，结果 JSON 用 `estimated_wet_correction` 标记。
- 2026-11-03 补充三：默认设计搜索改为 2268 点粗网格，再在最优点附近细化，细化点不超过 200。报告必须印出补充三规定的那句「非全局穷举……exhaustive 模式」。最优解落在管排 4 或 28、或管长 2 m 或 6 m 时，先外扩再细化。外扩步数未给出。
- 2026-11-03 补充四：干管束压降改为 Zukauskas 与 Ulinskas 的逆幂级数，系数表见 docs/correlations.md。\(N_r<10\) 时 \(C_2=1-0.45\exp(-N_r/3)\)，否则为 1。非等边布置本期 \(k_1=1\)，并输出规定说明。贴边外扩：管排 \(\Delta N_r=4\) 且不超过 30；管长 \(\Delta L=2\,\mathrm{m}\)，下限 0.5 m，未另给上限时 10 m。
- 改动计划是否批准：步骤 0 的技术决定已全部定稿。docs/PLAN.md 里的依赖版本、Friedel 展开式和均相加速压降，补充四没有改写，新 agent 按该文件实现。
- 2026-11-04：`backup/` 是回滚副本。除非用户当次明确要求，否则不查看、不修改、不移动、不删除、不覆盖。规则写在 `.cursor/rules/main.mdc`。
- 2026-11-04：按已讨论的优化实施。数值路径保持不变的是饱和含湿量单次物性调用、饱和焓直接计算、迭代中间空气状态只保留方程用到的量、每次求解自带精确物性缓存、求解前剔除必然越界的候选、求根端点不重复计算、候选分组并行。求根沿用上一轮水膜温度，并用相邻排数的流量作初值；收敛判据不放宽。流量只求到确定整数回路数、以及面积下界跳过候选，这两项没有另获确认，未实施。运行时间允许超过 15 min；预估超过约 1 h 时先询问。

## d. 未解决的问题

1. 补充四没有写相邻雷诺数区间的公共端点归哪一行。实现时归入较高雷诺数行。\(a=2.0\)、\(10^4\le\mathrm{Re}_\mathrm{max}\lesssim 2.36\times 10^4\) 时欧拉数级数非正，这些点抛 `OutOfRangeError`。若要改端点归属或改系数，须另说。
2. 管束压降和附件阻力使用进口湿空气密度、粘度；水泵使用循环喷淋水温，压力取进口空气压力。这是 2026-11-04 接入校核时采用的截面，不是用户另作确认的决定。若要改成出口或沿程平均，须另说。
3. 补充二的 Shah 公式已按写出的方程实现，不含 2009 年粘度修正。用户若要改回 2009 年分区公式，须另说。
4. Mizushina 管径按补充二只接受 12.7、19.05、40 mm。规格默认候选中的 25 mm 和 32 mm 会在该关联式处越界。这不是新的选择；若要改成区间而不是这三个离散管径，须另说。
5. CoolProp 的单相 `PropsSI(T,P)` 在压力距饱和压力约 1e-4% 以内会失败。制冷剂侧在 \(|T-T_\mathrm{sat}|\le 10^{-4}\,\mathrm{K}\) 时改用该压力下的饱和相物性。这不是新的关联式。
6. 迎面风速偏低时，空气含湿量会超过该焓对应的饱和含湿量，求解器按规格抛出 `OutOfRangeError`，不把含湿量截断到饱和。
7. 2026-11-04 实测：代表工况一次求根 9 次求解、225.61 s（单次求解约 25 s，16–17 轮）。工况为 R134a、冷凝温度 40 °C、进口饱和蒸气、出口目标为当地压力下的饱和液；干球 32 °C、湿球 26 °C；管径 19.05 mm，\(S_T/d_o=S_L/d_o=2\)，\(N_r=4\)，\(L=2\,\mathrm{m}\)，\(N_t=1\)，迎面风速 8 m/s，\(\Gamma=0.05\,\mathrm{kg/(m\cdot s)}\)。按 2268 点外推约 142 h。其中 2 次是区间端点重复调用，即使按 7 次求解估算仍约 176 s、外推约 111 h。同一风速和喷淋密度下，\(N_r=16\)、\(L=4\,\mathrm{m}\) 在 1.53 s 因含湿量超过饱和而 `OutOfRangeError`。默认候选里 25 mm 和 32 mm 会在 Mizushina 管径处直接剔除，剩下约 756 点；若这些点都完成求根，仍是数十小时。没有把网格改小。当时设计模式尚未编码；随后已实现，见上面已完成步骤。

## e. 下一步的具体动作

在 Windows 10/11 x64 上运行 `packaging\build_windows.bat`，得到 `dist\EvapCond_v1.0.0_win64.zip`，再按使用说明解压并打开界面。本机不能生成该 zip。文献传热系数仍待用户提供。完整 2268 点搜索仍不启动。流量只求到整数回路数、以及面积下界跳过候选，仍要另一次确认才做。
