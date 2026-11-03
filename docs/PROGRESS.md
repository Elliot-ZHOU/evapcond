# 进度

记录时间：2026-11-03。本文件只记载已经发生的事实。未写入本文件的决定视为不存在。

## a. 当前步骤及状态

- 步骤 0（关联式与默认参数确认表）：已完成。补充二、补充三、补充四的决定都在 docs/correlations.md。交接入口是 docs/HANDOFF.md。
- 步骤 1（改动计划）：正文在 docs/PLAN.md。网格、\(\Gamma_\mathrm{ref}\)、湿修正、Zukauskas–Ulinskas 系数表、\(C_2\) 拟合和外扩规则已由用户定稿。依赖版本、Friedel 展开式、均相加速压降仍是计划中的拟用式，已按该文件写入依赖清单。
- 步骤 3.1（物性）：已完成。测试见下方。下一步是步骤 3.2 几何。

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
- 测试：在 `.venv` 中运行 `python -m pytest`，13 项通过，约 2.8 s。解释器 Python 3.12.16，pytest 8.3.4，CoolProp 6.6.0。

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

## d. 未解决的问题

1. 干管束欧拉数系数已按 png 核对，压降函数留到空气侧/辅机步骤再编码，不在 3.1。
2. 补充二的 Shah 公式按写出的方程实现。它与 1979 年公开形式一致，不含 2009 年粘度修正。用户若要改回 2009 年分区公式，须另说。
3. Friedel 展开式与均相加速压降按 docs/PLAN.md 实现，补充四未改。
4. 25 °C 时，HAPropsSI 由含湿量差分得到的水蒸气分焓比 HEOS 饱和蒸气焓低约 97 J/kg。3.1 仍分别返回两个库的原值。步骤 3.5 做能量守恒时再核对这两个参考态能否直接相加。

## e. 下一步的具体动作

实现步骤 3.2：`evapcond/geometry/tube.py`、`plate.py`、`candidates.py` 和 `tests/test_geometry.py`。

几何关系：\(d_i=d_o-2\delta\)，迎风面积 \(N_t S_T L\)，管外表面积。板式与低翅片字段可以构造，求解入口拒绝并抛出 `UnconfirmedCorrelationError`。不改 3.1 的物性接口，不改已确认的关联式。
