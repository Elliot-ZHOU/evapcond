# 进度

记录时间：2026-11-03。本文件只记载已经发生的事实。未写入本文件的决定视为不存在。

## a. 当前步骤及状态

- 步骤 0（关联式与默认参数确认表）：已完成。确认结论来自用户提供的 `/Users/zhouhui/Desktop/补充二.docx`，已写入 docs/correlations.md 的「用户确认」一节。
- 步骤 1（改动计划）：未开始。湿工况压降仍有两项未闭合，写在第 d 节。
- 实现步骤 3.1 至文档：未开始。

## b. 已完成步骤

- 从本对话记录逐字提取最初提示词，保存为 docs/SPEC.md，并在「工作方式」末尾追加交接规则第 5 条。此后未改 SPEC.md。
- 步骤 0 对话中的确认表原文保存在 docs/correlations.md 前半部分。
- 阻塞项阅读稿：项目根目录「蒸发式冷凝器_步骤0_阻塞项.pdf」（5 页）。该 PDF 未纳入 git。
- 2026-11-03 读取补充二.docx 的正文与 11 张说明图，把其中的决定写入 docs/correlations.md。
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
- 改动计划是否批准：否。

## d. 未解决的问题

1. 湿工况管束压降：补充二给出 \(\Delta p_\mathrm{wet}=\Delta p_\mathrm{dry}(1+0.5\,\Gamma_m/\Gamma_\mathrm{ref})\)，但没有指定干管束压降关联式。系数 0.5 只来自该补充文件。
2. \(\Gamma_\mathrm{ref}\) 被写成 Mizushina 有效范围的中值。该范围是 \(\Gamma_m/d_o\)，单位 kg/(m²·s)，与 \(\Gamma_m\) 不能直接相除。需要用户写明比值用 \(\Gamma_m/d_o\) 还是 \(\Gamma_m\)，以及中值取算术平均 \((0.195+5.556)/2=2.8755\) 还是别的定义。
3. 加速压降的空泡份额算法，补充二没有指定。计划中拟用均相密度，待批准。
4. Friedel 的 \(E,F,H,\mathrm{Fr},\mathrm{We}\) 展开式待批准。
5. 补充二把 Shah 公式标成 2009，写出的方程和 15–17% / 雷诺数 100–63000 与 2009 年论文摘要不一致，与 1979 年公开形式一致。实现按补充二的方程。若用户要改回 2009 年粘度修正，须另说。
6. 默认设计网格为 3×4×3×3×5×27 = 14580 个候选。单次求解若按 0.2 s 计，总时间约 49 min，超过规格的 15 min 上限。缩减方案随步骤 1 写入 docs/PLAN.md，尚未批准。

## e. 下一步的具体动作

下一步是把改动计划写入 docs/PLAN.md（含依赖版本、默认网格耗时和缩减方案），然后停止等待批准。批准前不创建 `evapcond/`，不编写 `film_air.py`、`solver.py` 或其他计算函数。

批准后的第一个实现动作是步骤 3.1：新增 `evapcond/properties/backend.py`、`coolprop_backend.py`、`refrigerant.py`、`humid_air.py`、`water.py`，以及 `tests/test_properties.py`。求解器与界面不得直接导入 CoolProp。
