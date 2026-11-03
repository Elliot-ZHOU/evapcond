# 进度

记录时间：2026-11-03。本文件只记载已经发生的事实。未写入本文件的决定视为不存在。

## a. 当前步骤及状态

- 步骤 0（关联式与默认参数确认表）：已完成。确认结论来自用户提供的 `/Users/zhouhui/Desktop/补充二.docx`，已写入 docs/correlations.md 的「用户确认」一节。
- 步骤 1（改动计划）：进行中。docs/PLAN.md 已有正文。补充三批准了 \(\Gamma_\mathrm{ref}\)、湿修正和 2268 点粗网格。Zukauskas 压降的 \(C_1\)、\(m\)、\(C_2\) 数值以及边界外扩步数仍未给出，未开始编码。
- 实现步骤 3.1 至文档：未开始。

## b. 已完成步骤

- 从本对话记录逐字提取最初提示词，保存为 docs/SPEC.md，并在「工作方式」末尾追加交接规则第 5 条。此后未改 SPEC.md。
- 步骤 0 对话中的确认表原文保存在 docs/correlations.md 前半部分。
- 阻塞项阅读稿：项目根目录「蒸发式冷凝器_步骤0_阻塞项.pdf」（5 页）。该 PDF 未纳入 git。
- 2026-11-03 读取补充二.docx 的正文与 11 张说明图，把其中的决定写入 docs/correlations.md。
- 2026-11-03 读取补充三.docx。\(\Gamma_\mathrm{ref}\)、湿修正和粗网格策略已写入 docs/correlations.md。干管束压降只记录了 Zukauskas 的函数形式，没有写入系数表。
- 计算代码与测试：未开始。测试结果：无。

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
- 2026-11-03 补充三：干管束压降采用 Zukauskas (1972) 错列管束的欧拉数形式。\(C_1\)、\(m\)、\(C_2\) 的数字不在该文件中。
- 改动计划是否批准：部分批准。网格、\(\Gamma_\mathrm{ref}\) 和湿修正的结构已批准。依赖版本、Friedel 展开式、均相加速压降，以及 Zukauskas 系数表，尚未批准。

## d. 未解决的问题

1. Zukauskas 欧拉数的 \(C_1\)、\(m\)（随 \(S_T/d_o\)、\(S_L/d_o\)）和 \(N_r<10\) 时的 \(C_2\) 没有数字。Incropera 表 7.5 的常见内容是努塞尔数常数，不是压降系数，因此没有把该表抄进欧拉数公式。需要用户给出压降用的系数表，或指定可逐项核对的页码。
2. 粗网格最优解贴边时，「向外扩展」的排数步长、管长步长，以及能否超出原规格的管排 4–30、管长 2–6 m，补充三没有写。
3. 加速压降的空泡份额算法，补充二没有指定。计划中拟用均相密度，待批准。
4. Friedel 的 \(E,F,H,\mathrm{Fr},\mathrm{We}\) 展开式待批准。
5. 补充二把 Shah 公式标成 2009，写出的方程和 15–17% / 雷诺数 100–63000 与 2009 年论文摘要不一致，与 1979 年公开形式一致。实现按补充二的方程。若用户要改回 2009 年粘度修正，须另说。
6. 依赖版本仍是计划中的拟锁定值，用户尚未逐项批准。

## e. 下一步的具体动作

等待用户提供 Zukauskas 压降系数表，并写明贴边外扩的步长。在这两项写入本文件之前，不创建 `evapcond/`，不编写 `pressure_drop.py`、`auxiliary.py`、`design.py` 或 `solver.py`。

批准后的第一个实现动作是步骤 3.1：新增 `evapcond/properties/backend.py`、`coolprop_backend.py`、`refrigerant.py`、`humid_air.py`、`water.py`，以及 `tests/test_properties.py`。求解器与界面不得直接导入 CoolProp。
