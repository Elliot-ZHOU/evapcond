步骤 0 停在确认表。US-8 指定的管外空气对流关联式全文没有取得，按规格不能凭 12.2% 拟合或换用其他公式，因此不开始编码。

## 阻塞项

《流体机械》2006 年第 34 卷第 8 期英文库摘要与规格一致：对流换热主要由迎面风速控制，回归关联式的最大相对标准偏差为 12.2%。2005 年工程热物理学会年会论文未检索到全文。两篇都没有拿到函数形式、系数、指数、雷诺数定义、特征尺寸、喷淋密度范围、迎面风速范围、管径、管排布置，以及该系数是纯空气对流 \(h_c\) 还是水膜–空气综合系数。

请提供其中任一篇的公式全文（含上述各项）。若原文无法取得，请明确声明，并在下表候选中指定一条；未指定前，光管 \(h_c\) 不能编码。

同组 2007 年《高校化学工程学报》给出的是管外水膜传热系数（标准偏差 7.5%，喷淋密度 0.023–0.059 kg/(m·s)，迎面风速 2.1–3.3 m/s），公式同样未取得，且物理量与 US-8 不是同一项。

## 关联式与默认参数确认表

| 用途 | 名称 | 完整引用 | 适用范围 | 报告偏差 | 本软件用法 | 核实状态 |
|---|---|---|---|---|---|---|
| 管外空气对流 \(h_c\)（US-8，必须第一项） | 蒋翔–朱冬生–唐广栋回归式 | 蒋翔，朱冬生，唐广栋. 蒸发式冷凝器管外水膜与空气传热性能及机理的研究[J]. 流体机械，2006，34(8). 同组另一报告：朱冬生，蒋翔，徐丽，沈家龙. 蒸发式冷凝器管外水膜与空气传热系数的实验研究[C]. 中国工程热物理学会第十一届年会论文集 传热传质学（上册），北京，2005. | 原文范围未取得 | 摘要写最大相对标准偏差 12.2% | 拟作为 US-5 的纯 \(h_c\)。若原文定义不是纯 \(h_c\)，须先确认与显热/潜热方程的映射后再编码 | **需用户提供原文** |
| 水膜对流 | Mizushina 等 (1967) | T. Mizushina, R. Ito, H. Miyashita. Experimental study of evaporative cooler. 化学工学, 1967, 31(5): 469–473. DOI: 10.1252/kakoronbunshu1953.31.469 | 二次文献 Dreyer (1988) 转写：\(h_w=2102.9\,(\Gamma/d_o)^{1/3}\)，\(0.195<\Gamma/d_o<5.556\,\mathrm{kg/(m^2\cdot s)}\)；管径 12.7、19.05、40 mm。1967 原文公式为图，本轮未读出系数。原文可见的传质容量系数范围：\(1.2\times10^3<\mathrm{Re}_G<1.4\times10^4\)，\(50<\mathrm{Re}_w<240\) | 原文未给出百分比偏差。文中称其 \(h_w\) 比所引 Parker–Treybal 式高约 30% | 候选，用于 \(R_\mathrm{film}=1/(h_w A_o)\)。规格中 \(\Gamma\) 为单侧、单位管长，喷淋水量 \(=\Gamma\times 2\times N_t\times L\)。Mizushina 的 \(\Gamma\) 是否已含两侧，尚未与原文符号表对齐，不能直接套用数值范围 | **未核实**（系数来自二次文献；\(\Gamma\) 定义未对齐） |
| 水膜对流（并列候选） | Parker & Treybal (1961) | R. O. Parker, R. E. Treybal. The heat and mass transfer characteristics of evaporative coolers. Chemical Engineering Progress Symposium Series, 1961, 57(32): 138–149. | 二次文献不一致。Dreyer 转写含壁温项，范围 \(1.36<\Gamma/d_o<3\,\mathrm{kg/(m^2\cdot s)}\)，管外径 19 mm；另一篇会议论文转写为 \(h=982+15.58(\Gamma/d_o)^{1/3}\) 一类形式。原文未打开 | 未从原文摘录 | 在两份转写一致并核对原文之前不采用 | **未核实** |
| Lewis 数 | 待指定 | Chilton–Colburn 比拟给出规格中的形式 \(h_m=h_c/(c_{p,a}\mathrm{Le}^{2/3})\)，\(h_m\) 单位 kg/(m²·s)，推动力为含湿量差。Le 本身的取值来源未指定 | 空气–水；具体温度、压力范围随所选算法而定 | 未指定 | 仅当所选 \(h_c\) 关联式不给出 \(h_m\) 时使用。三个候选见下方问题 2 | **未核实**，待选择 |
| 水平管内冷凝 | Shah (2009) | M. M. Shah. An improved and extended general correlation for heat transfer during condensation in plain tubes. HVAC&R Research, 2009, 15(5): 889–913. 作者公开 PDF：https://mmshah.org/publications/condensation%20corr%2009.pdf | 摘要给出的验证范围：管径 2–49 mm；折合压力 0.0008–0.9；质量流速 4–820 kg/(m²·s)；全液 Re 68–85000；液相 Pr 1–18；水平、垂直向下及 15° 向下。水平管可分析数据对应 \(\mathrm{Re}_{GT}>35000\) 的限制，低 Re 原文建议保守不用 | 1189 点平均偏差 14.4%（水平管 14.3%） | 候选，用于光管内两相段 \(h_\mathrm{ref}\)。PDF 公式排版在文本提取中破损，确认选用后按 PDF 公式编号逐式抄录，不按破损文本编码 | 范围与偏差已从作者 PDF 摘要读到；**公式未逐式核实** |
| 单相对流（过热、过冷） | Gnielinski (1976) | V. Gnielinski. New equations for heat and mass transfer in turbulent pipe and channel flow. International Chemical Engineering, 1976, 16(2): 359–368. | 公开转写常见范围为 \(0.5\le\mathrm{Pr}\le2000\)、\(3000\le\mathrm{Re}\le5\times10^6\)。1976 原文本轮未打开，此范围不作为已核实界限 | 本轮未从原文摘录 | 候选，仅用于管内单相。管外不用管内关联式 | **未核实** |
| 两相摩擦压降 | Friedel (1979) | L. Friedel. Improved friction pressure drop correlations for horizontal and vertical two-phase pipe flow. European Two-Phase Flow Group Meeting, Ispra, 1979, Paper E2. | 二次文献转写的数据库：水力直径约 4–200 mm（单组分），干度 0–1，水平与垂直向上。加速压降不在该式内 | 二次文献称 Friedel 对水平单组分数据的相对标准差为 32%（未对原文表核对） | 候选，用于当地摩擦压降并更新饱和温度。摩擦系数用原文公式还是 Blasius 替代，二次文献存在分歧，须确认 | **未核实** |
| 湿工况管束压降 | 优先取 US-8 论文中的阻力关联式；备选 Niitsu 等 (1969) | Y. Niitsu, K. Naito, T. Anzai. Studies on characteristics and design procedure of evaporative coolers. Journal of SHASE, Japan, 1969, 43: 581–590（卷期在不同引用中写为 No.7 或 No.12，本轮未核对原刊） | 二次文献只给出 \(\Delta p/Z=a G_\mathrm{air}^b \Gamma^c\)，系数随几何变化。\(a,b,c\) 与单位未取得 | 未取得 | 风机全压中的湿管束压降。规格禁止用干管束压降乘固定系数。US-8 论文标题含阻力，公式未取得 | **未核实** |
| 板式制冷剂冷凝 | Longo 等 (2015) | G. A. Longo, G. Righetti, C. Zilio. A new computational procedure for refrigerant condensation inside herringbone-type brazed plate heat exchangers. International Journal of Heat and Mass Transfer, 2015, 82: 530–535 附近（DOI: 10.1016/j.ijheatmasstransfer.2014.11.032）。公式本轮只见于学位论文转写 | 转写以 \(\mathrm{Re}_{eq}=1600\) 划分重力控制与强制对流。板几何（波纹角、节距、深度）的适用界限未从原文摘录 | 未从原文摘录 | 板式在确认前调用即抛出 `UnconfirmedCorrelationError` | **未核实** |
| 板外水膜 | 无已打开的原文 | — | — | — | 同上，确认前不可算 | **未核实** |
| 低翅片管（外翅：翅高、翅距、翅厚） | 无已打开的、与“管内冷凝 + 管外水膜/空气”匹配的原文 | — | — | — | 确认前调用即抛出 `UnconfirmedCorrelationError` | **未核实** |
| 喷淋水管路摩擦 | Colebrook (1939) | C. F. Colebrook. Turbulent flow in pipes, with particular reference to the transition region between the smooth and rough pipe laws. Journal of the Institution of Civil Engineers, 1939, 11(4): 133–156. | 湍流过渡区与粗糙管。规格 US-7 已指定用 Colebrook–White 计算扬程中的沿程阻力 | 拟合实验曲线，无单一百分比偏差可摘 | 拟用 Darcy 摩擦系数：\(1/\sqrt{\lambda}=-2\log_{10}(\varepsilon/(3.7D)+2.51/(\mathrm{Re}\sqrt{\lambda}))\)，\(h_f=\lambda(L/D)V^2/(2g)\)。1939 原文本轮未打开 | 方程为工程标准形式；**原文未打开**。请确认采用 Darcy \(\lambda\) 而不是 Fanning |
| \(\eta_\mathrm{fan}\) 默认 0.65 | 规格给定 | 未找到把 0.65 定为蒸发式冷凝器风机全效率的标准条款。GB/T 7190.1-2018 评价的是耗电比，不是风机效率 | 无 | 无文献偏差 | 轴功率 = 有效功率 / \(\eta_\mathrm{fan}\)。拟作为用户确认的默认值，不编造文献 | **未核实来源** |
| \(\eta_\mathrm{pump}\) 默认 0.70 | 规格给定 | 未找到对应的强制标准值 | 无 | 无 | 同上 | **未核实来源** |
| \(N_\mathrm{cyc}\) 默认 3.0 | 规格给定 | GB/T 50050 对敞开式循环水浓缩倍数有下限要求；该标准原文本轮未打开，不能把 3.0 写成标准规定值 | 无 | 无 | 排污量 = 蒸发量 / \((N_\mathrm{cyc}-1)\) | **未核实来源** |
| 风吹损失率默认 0.01% | 规格给定；数值与一项产品限值相同 | GB/T 7190.1-2018 第 5.4 条：中小型开式冷却塔飘水率应不大于 0.010%。定义是出风口飘出水量与进塔水量之比。适用范围是冷却水量 <1000 m³/h、带淋水填料的开式冷却塔，不是蒸发式冷凝器条文 | 产品上限，不是实验拟合偏差 | 无 | 风吹损失 = 该比率 × 喷淋水量。分母若按标准应是进塔循环水量，与规格的喷淋水量是否相同，须确认 | 限值已从标准转写读到；**直接用作本软件默认的依据未确认** |
| 管壁导热系数 \(k_w\) | AISI 1010，300 K | F. P. Incropera, D. P. DeWitt 等. Fundamentals of Heat and Mass Transfer. 表 A.1。本轮核对的是附录转写：300 K 列依次为密度、比热、导热系数、热扩散率 | 表列点为 300 K。密度 7832 kg/m³，比热 434 J/(kg·K)，\(k=63.9\,\mathrm{W/(m\cdot K)}\)，\(\alpha=18.8\times10^{-6}\,\mathrm{m^2/s}\)。\(k/(\rho c_p)\) 与 \(\alpha\) 一致 | 表列数据，无回归偏差 | 壁面热阻 \(R_\mathrm{wall}=\ln(d_o/d_i)/(2\pi k_w\,\mathrm{d}L)\)，采用 63.9 | **数值已核实**。版次页码仍是附录转写，未对纸书页码 |

## 请确认的事项

1. **US-8**：提供 2005 或 2006 原文公式及全部系数、范围、管排与系数定义；或书面声明原文无法取得，并指定替代关联式。
2. **Le**：在下列三者中选一。  
   - 由湿空气物性计算 \(\mathrm{Le}=\alpha/D_{v,a}\)，并指定水蒸气–空气扩散系数公式及其文献。  
   - 取 \(\mathrm{Le}=1\)。  
   - 用 Bosnjaković 刘易斯因子替代 \(\mathrm{Le}^{2/3}\)，并给出所采用的公式原文。
3. **水膜**：是否在核对 Mizushina 1967 原文图中的公式、并统一 \(\Gamma\) 定义之后，采用该式。Parker & Treybal 的两份转写不一致，现不采用。
4. **管内冷凝与压降**：是否采用 Shah (2009) 与 Friedel (1979)。水平管在 \(\mathrm{Re}_{GT}\le 35000\) 时，Shah 文本要求保守停用；请确认此时判定为越界并剔除候选。Friedel 的摩擦系数请指定用其原文公式或 Blasius。加速压降是否计入当地压力，请一并说明。
5. **单相管内对流**：是否采用 Gnielinski (1976)。确认后实施时再打开原文或 VDI 转载页，核对系数与范围。
6. **湿管束压降**：提供 US-8 论文中的阻力公式，或指定一条已含全部系数的湿工况关联式。
7. **板式与低翅片**：本期是否约定为未确认几何，调用时抛出 `UnconfirmedCorrelationError`，只实现光管可算路径。
8. **默认值**：\(\eta_\mathrm{fan}=0.65\)、\(\eta_\mathrm{pump}=0.70\)、\(N_\mathrm{cyc}=3.0\) 是否按“用户给定默认值”写入文档，不另附文献。风吹损失 0.01% 是否接受，并说明分母是喷淋水量。
9. **\(k_w=63.9\,\mathrm{W/(m\cdot K)}\)**：表 A.1 的 AISI 1010、300 K 与规格一致。请确认采用该值。

收到上述确认前，不进入步骤 1，也不编写求解代码。

## 用户确认（2026-11-03，`/Users/zhouhui/Desktop/补充二.docx`）

以下只记录该文件写明的决定。作者姓名在文件中写作 Mizushima，对应文献是 Mizushina, Ito, Miyashita (1967)。US-8 原文公式仍未取得；用户声明公开渠道无法获得完整系数，并指定下面的替代。

### 1. 管外空气对流 \(h_c\)

采用

\[
h = 2102.9\,(\Gamma_m/d_o)^{1/3}\quad [\mathrm{W/(m^2\cdot K)}]
\]

有效范围：管径 12.7 / 19.05 / 40 mm，\(0.195 < \Gamma_m/d_o < 5.556\,\mathrm{kg/(m^2\cdot s)}\)。越界抛出 `OutOfRangeError`。

规格喷淋密度 \(\Gamma\)（单侧、单位管长）与 Mizushina 的 \(\Gamma_m\)（半管周长上的单位管长流量）用

\[
\Gamma_m = \dot m_w\, d_o / (2 A_f)
\]

\(A_f\) 为迎风面积。由规格关系 \(\dot m_w = \Gamma\cdot 2\cdot N_t\cdot L\)、\(A_f = N_t\cdot S_T\cdot L\)，上式等价于 \(\Gamma_m = \Gamma\cdot d_o/S_T\)。

结果中必须包含这句话：「管外空气对流项采用 Mizushina et al. (1967) 关联式，经 \(\Gamma\) 定义转换后使用；该式对纯空气对流与空气-水膜耦合对流的区分未在原文中显式声明，其量纲与数值范围与蒸发式冷凝器管外工况一致。」

### 2. Lewis 数

默认使用 Bosnjaković 因子，不把 \(\mathrm{Le}_f\) 再取 \(2/3\) 次方：

\[
\mathrm{Le}_f = 0.865^{2/3}\frac{(w_s+0.622)/(w_a+0.622)-1}{\ln[(w_s+0.622)/(w_a+0.622)]}
\]

\[
h_m = h_c / (c_{p,a}\,\mathrm{Le}_f)
\]

\(w_s\to w_a\) 时取极限 \(\mathrm{Le}_f\to 0.865^{2/3}\approx 0.908\)。允许用户覆盖为 \(\mathrm{Le}_f=1\)，默认不是 1。

### 3. 水膜对流 \(h_w\)

与 \(h_c\) 使用同一条 Mizushina 式，范围相同。水膜热阻 \(R_\mathrm{film}=1/(h_w A_o)\) 单独串联，不与 \(h_c\) 合并成一个综合系数。Parker & Treybal 不采用。

### 4. 管内冷凝

按补充二给出的公式编码，文献标签仍写作 Shah (2009)。该式与 Shah (1979) 的公开形式相同；2009 年论文中的粘度比修正和分区判据不在这条公式里。

\[
h_{TP}=h_{Lo}\left[(1-x)^{0.8}+\frac{3.8\,x^{0.76}(1-x)^{0.04}}{p_r^{0.38}}\right]
\]

\[
h_{Lo}=0.023\left(\frac{GD}{\mu_l}\right)^{0.8}\mathrm{Pr}_l^{0.4}\frac{k_l}{D},\quad p_r=p/p_\mathrm{crit}
\]

补充二写明的范围为液相雷诺数 100–63000、液相普朗特数 1–13，平均偏差 15–17%。这些数字与 2009 年论文摘要（平均偏差 14.4%，全液雷诺数 68–85000，液相普朗特数 1–18）不一致。实现时按补充二写出的公式和它所声明的范围做越界检查。

\(\mathrm{Re}_{GT}\le 35000\) 时仍然计算，不剔除候选，不抛异常。结果 JSON 的 warnings 增加：「Shah (2009) 关联式在 Re_GT ≤ 35000 时原文建议保守使用，当前设计工况低于该阈值」。

### 5. 管内单相

Gnielinski (1976) 的公开转写，仅用于过热段和过冷段：

\[
\mathrm{Nu}=\frac{(f/8)(\mathrm{Re}-1000)\mathrm{Pr}}{1+12.7\sqrt{f/8}\,(\mathrm{Pr}^{2/3}-1)},\quad f=(0.790\ln\mathrm{Re}-1.64)^{-2}
\]

- \(\mathrm{Re}<2300\)：抛出 `OutOfRangeError`（补充二中的类名 LaminarFlowUnsupportedError 不新增；规格的异常类型只有既有六类）。
- \(2300\le\mathrm{Re}<3000\)：仍用该式，并写警告。
- \(\mathrm{Re}>5\times 10^6\)，或普朗特数不在 \(0.5\)–\(2000\)：抛出 `OutOfRangeError`。

### 6. 两相摩擦压降与加速压降

采用 Friedel (1979) 的两相乘子结构，单相摩擦系数用 Blasius，不声称完全按 Friedel 原文的摩擦系数：

\[
\Phi_{lo}^2 = E + \frac{3.24\,F\,H}{\mathrm{Fr}^{0.045}\,\mathrm{We}^{0.035}}
\]

湍流 \(f=0.079\,\mathrm{Re}^{-0.25}\)，层流 \(f=16/\mathrm{Re}\)。

\(E\)、\(F\)、\(H\)、\(\mathrm{Fr}\)、\(\mathrm{We}\) 的展开式在补充二里没有逐项写出。步骤 1 计划中给出公开转写，须随计划一并批准后才编码。

加速压降计入当地压力：\(p_{i+1}=p_i-(\Delta p_\mathrm{fric}+\Delta p_\mathrm{acc})\)，再用新压力更新饱和温度。空泡份额或均相密度的具体算法，补充二没有指定，仍见 `docs/PLAN.md` 的待批准项。

### 7. 湿工况管束压降

补充二给出的工程修正是

\[
\Delta p_\mathrm{wet}=\Delta p_\mathrm{dry}\,(1+0.5\cdot\Gamma_m/\Gamma_\mathrm{ref})
\]

并要求输出标注「湿工况压降为工程估计，不确定度约 ±30%」。系数 0.5 的来源是该补充文件，不是已核实的实验关联式。

这一项还不能编码。\(\Delta p_\mathrm{dry}\) 用哪一条管束阻力关联式没有指定。\(\Gamma_\mathrm{ref}\) 写成「Mizushina 有效范围的中值」，而该范围的量是 \(\Gamma_m/d_o\)（kg/(m²·s)），与 \(\Gamma_m\)（kg/(m·s)）不能直接相除。

### 8. 板式与低翅片

`surface_type` 不是 `tube_plain` 时抛出 `UnconfirmedCorrelationError`，消息为「板式/低翅片管外侧水膜-空气关联式尚未确认，本期仅支持光管」。几何输入字段保留。不使用 Longo (2015) 代替板外水膜。补充二中的字段名 `geometry_type` / `plain_tube` 不采用，输入字段仍是规格里的 `surface_type`。

### 9. 喷淋水管路

Darcy 摩擦系数，不用 Fanning：

\[
\frac{1}{\sqrt{\lambda}}=-2\log_{10}\left(\frac{\varepsilon}{3.7D}+\frac{2.51}{\mathrm{Re}\sqrt{\lambda}}\right),\quad h_f=\lambda\frac{L}{D}\frac{V^2}{2g}
\]

隐式方程迭代求解，初值用 Swamee–Jain 显式近似，收敛判据 \(|\Delta\lambda|<10^{-8}\)。

### 10. 默认常数

均为用户可覆盖的默认值，文档不写成强制性标准条款。

| 常数 | 默认值 | 文档写法 |
|---|---|---|
| \(\eta_\mathrm{fan}\) | 0.65 | 常用工程取值，无强制性标准来源 |
| \(\eta_\mathrm{pump}\) | 0.70 | 同上 |
| \(N_\mathrm{cyc}\) | 3.0 | 常见运行取值；排污量 = 蒸发量 / \((N_\mathrm{cyc}-1)\) |
| 风吹损失率 | 喷淋水量的 0.01% | 分母是喷淋水量；输出注明「此为工程取值，非标准强制条款」 |

### 11. 管壁导热系数

确认 \(k_w=63.9\,\mathrm{W/(m\cdot K)}\)（AISI 1010，300 K，Incropera 表 A.1）。\(R_\mathrm{wall}=\ln(d_o/d_i)/(2\pi k_w\,\mathrm{d}L)\)。

## 用户确认（2026-11-03，`/Users/zhouhui/Desktop/补充三.docx`）

### 干管束压降的形式

采用 Zukauskas (1972) 错列光管束，欧拉数写成

\[
\mathrm{Eu}=\frac{\Delta p_\mathrm{dry}}{N_r\cdot\tfrac12\rho_a u_\mathrm{max}^2}=C_1\,\mathrm{Re}_\mathrm{max}^{-m}\,C_2
\]

\[
\mathrm{Re}_\mathrm{max}=\rho_a u_\mathrm{max} d_o/\mu_a
\]

\(u_\mathrm{max}\) 为最窄截面风速。补充三写明：常规工况 \(10^3<\mathrm{Re}_\mathrm{max}<2\times 10^5\) 时，\(C_1\) 与 \(m\) 随 \(S_T/d_o\)、\(S_L/d_o\) 变化，并指向 Incropera 表 7.5 或 VDI Heat Atlas；\(N_r<10\) 时 \(C_2\) 在 0.95–1.0，具体查 Zukauskas 原表。文件里没有给出这三张表的数字。

代码和文档必须注明：「干管束压降基于 Zukauskas 错列管束关联式，湿工况在此基础乘上由 \(\Gamma\) 驱动的湿修正因子。」

核对结果：Incropera《Fundamentals of Heat and Mass Transfer》中与 Zukauskas 相关、常被编为表 7.5 的常数，属于努塞尔数 \(\mathrm{Nu}=C\,\mathrm{Re}^m\mathrm{Pr}^{n}(\mathrm{Pr}/\mathrm{Pr}_s)^{0.25}\)，不是欧拉数。同章压降写成 \(\Delta p=N_L\chi(\rho V_\mathrm{max}^2/2)\)，\(\chi\) 与摩擦系数来自图，不是该表。因此不把表 7.5 的传热 \(C\)、\(m\) 写入 \(\mathrm{Eu}\)。\(C_1\)、\(m\)、\(C_2\) 的数值仍待用户给出。

### \(\Gamma_\mathrm{ref}\) 与湿修正

按补充三批准：

\[
\Gamma_\mathrm{ref}=\frac{0.195+5.556}{2}=2.8755\,\mathrm{kg/(m^2\cdot s)}
\]

\[
\Delta p_\mathrm{wet}=\Delta p_\mathrm{dry}\left(1+0.5\cdot\frac{\Gamma_m/d_o}{\Gamma_\mathrm{ref}}\right)
\]

结果 JSON 增加字段，标记该压降为 `estimated_wet_correction`。系数 0.5 的来源仍是补充二，不是实验回归。

### 设计网格

批准两阶段搜索，不再使用 14580 点的全网格作为默认：

- 粗网格 2268 点：\(d_o\) 3 个，管距比 4 组，\(\Gamma\) 3 点，\(v_f\) 3 点，\(L\in\{2,4,6\}\,\mathrm{m}\)，\(N_r\in\{4,8,12,16,20,24,28\}\)。
- 在粗网格最优的若干点附近，以步长 1 或更小再搜索。细化候选不超过 200 个。
- 最终报告必须包含：「设计结果基于粗网格搜索（2268点）与局部细化寻优，非全局穷举。若需绝对全局最优，请手动开启 exhaustive 模式。」
- 若粗网格最优解落在边界（管排为 4 或 28，或管长为 2 m 或 6 m），先向外扩展边界再细化。扩展的步数和是否允许超出规格原范围（管排 4–30、管长 2–6 m），补充三没有写明。补充四给出了步长，见下一节。

## 用户确认（2026-11-03，`docs/sources/补充四.docx`）

补充四声明：下面的系数表、\(C_2\) 拟合式和外扩规则是最终编码形态。原图在 `docs/sources/zukauskas_euler_table.png`。

### 干管束欧拉数

不再使用带单独 \(C_1\)、\(m\) 的幂次式。改用 Zukauskas 与 Ulinskas 的逆幂级数。文献指向：A. Žukauskas, R. Ulinskas, Banks of plain and finned tubes, Heat Exchanger Design Handbook。补充四把年份写作 1983。

\[
\mathrm{Eu}\equiv\frac{2\Delta p_\mathrm{dry}}{\rho V_\mathrm{max}^2 N_r}
=q+r\mathrm{Re}^{-1}+s\mathrm{Re}^{-2}+t\mathrm{Re}^{-3}+u\mathrm{Re}^{-4}
\]

\(\mathrm{Re}=\rho V_\mathrm{max} d_o/\mu\)，\(a=S_T/d_o\)。非等边三角形（\(S_L/d_o\neq(\sqrt{3}/2)(S_T/d_o)\)）原式还有 \(k_1\)。本期 \(k_1=1\)，代码注释和输出必须写明：「当前干管束压降按等边错列计算，非等边几何需补充 Zukauskas 的 \(k_1\) 修正表。」

系数（按补充四内嵌表读出；新 agent 编码前须再看一遍 png）：

| \(a=S_T/d_o\) | \(\mathrm{Re}_\mathrm{max}\) | \(q\) | \(r\) | \(s\) | \(t\) | \(u\) |
|---|---|---|---|---|---|---|
| 1.25 | \(3\sim 10^3\) | 0.795 | \(0.247\times 10^3\) | \(0.335\times 10^3\) | \(-0.155\times 10^4\) | \(0.241\times 10^4\) |
| 1.25 | \(10^3\sim 2\times 10^6\) | 0.245 | \(0.339\times 10^4\) | \(-0.984\times 10^7\) | \(0.132\times 10^{11}\) | \(-0.599\times 10^{13}\) |
| 1.5 | \(3\sim 10^3\) | 0.683 | \(0.111\times 10^3\) | \(-0.973\times 10^2\) | \(0.426\times 10^3\) | \(-0.574\times 10^3\) |
| 1.5 | \(10^3\sim 2\times 10^6\) | 0.203 | \(0.248\times 10^4\) | \(-0.758\times 10^7\) | \(0.104\times 10^{11}\) | \(-0.482\times 10^{13}\) |
| 2.0 | \(7\sim 10^2\) | 0.713 | \(0.448\times 10^2\) | \(-0.126\times 10^3\) | \(-0.582\times 10^3\) | 0 |
| 2.0 | \(10^2\sim 10^4\) | 0.343 | \(0.303\times 10^3\) | \(-0.717\times 10^5\) | \(0.880\times 10^7\) | \(-0.380\times 10^9\) |
| 2.0 | \(10^4\sim 2\times 10^6\) | 0.162 | \(0.181\times 10^4\) | \(-0.792\times 10^8\) | \(-0.165\times 10^{13}\) | \(0.872\times 10^{16}\) |
| 2.5 | \(10^2\sim 5\times 10^3\) | 0.330 | \(0.989\times 10^2\) | \(-0.148\times 10^5\) | \(0.192\times 10^7\) | \(0.862\times 10^8\) |
| 2.5 | \(5\times 10^3\sim 2\times 10^6\) | 0.119 | \(0.848\times 10^4\) | \(-0.507\times 10^8\) | \(0.251\times 10^{12}\) | \(-0.463\times 10^{15}\) |

\(a\) 不在 1.25、1.5、2.0、2.5，或雷诺数不在对应区间时，抛出 `OutOfRangeError`，不插值、不外推。规格默认的 \(S_T/d_o\) 只有 2.0 和 2.5。

一份转载同一张表的论文（见进度文件）与上表有三处数字不同。以 png 为准，编码前由新 agent 再读图核对：

- \(a=1.25\)，\(10^3\sim 2\times 10^6\) 的 \(u\)：上表 \(-0.599\times 10^{13}\)，该论文为 \(-0.559\times 10^{13}\)
- \(a=2.0\)，\(7\sim 10^2\) 的 \(t\)：上表 \(-0.582\times 10^3\)，该论文为 \(-0.585\times 10^7\)
- \(a=2.5\)，\(10^2\sim 5\times 10^3\) 的 \(u\)：上表 \(0.862\times 10^8\)，该论文为 \(0.862\times 10^2\)

### 管排修正 \(C_2\)

这是补充四给出的拟合式，不是从 Zukauskas 原图逐点读出的表。

\[
C_2=\begin{cases}1-0.45\exp(-N_r/3), & N_r<10\\ 1, & N_r\ge 10\end{cases}
\]

\[
\Delta p_\mathrm{dry}=C_2\cdot\mathrm{Eu}\cdot\frac12\rho V_\mathrm{max}^2\cdot N_r
\]

湿修正仍用补充三的式子，结果 JSON 标记 `estimated_wet_correction`。

### 贴边外扩

- 管排：粗网格最优为 \(N_r=4\) 或 \(28\) 时，向外扩一个粗步长 \(\Delta N_r=4\)。下侧受物理下界截断，规格默认下限是 4，因此 \(N_r=4\) 时下侧不新增排。上侧扩到 32 后再截断到用户上限与规格上限 30 中的较小者，即默认只新增 29 和 30。
- 管长：最优为 \(L=2\,\mathrm{m}\) 或 \(6\,\mathrm{m}\) 时，向外扩 \(\Delta L=2\,\mathrm{m}\)。下限 \(0.5\,\mathrm{m}\)，上限在规格未另给时取 \(10\,\mathrm{m}\)。细化步长为 1 m，因此下侧新增 \(L=1\,\mathrm{m}\)，上侧新增 \(7\,\mathrm{m}\) 和 \(8\,\mathrm{m}\)。
- 外扩区域用管排步长 1、管长步长 1 m 细化，细化点总数不超过 200。
- 管排贴边时控制台原样输出：`Warning: 最优解贴近初始搜索边界 (Nr=4或28)，已向物理允许方向外扩 1 个单位进行精细化验证。`
- 补充四没有给管长贴边的第二句警告。管长贴边时用同样结构另打印一句，并把边界写成实际的 \(L\)。

## 步骤 3.6 编码对照（2026-11-04）

编码前重读 `docs/sources/zukauskas_euler_table.png`。九行系数与上面的补充四表格一致，包括三处争议值：\(a=1.25\) 高雷诺数的 \(u=-0.599\times 10^{13}\)，\(a=2.0\) 低雷诺数的 \(t=-0.582\times 10^{3}\)，\(a=2.5\) 低雷诺数的 \(u=0.862\times 10^{8}\)。确认结论没有改。

函数与结果字段：

- `evapcond/correlations/bundle_pressure.py`：`euler_number`、`row_correction`、`dry_bundle_pressure_drop`、`wet_pressure_drop`
- `evapcond/correlations/pipe_friction.py`：`darcy_friction_factor`（Darcy \(\lambda\)，Swamee–Jain 仅作初值）
- `evapcond/auxiliary.py`：`evaluate_auxiliary`
- `AuxResult.estimated_wet_correction` 在本实现中为真。诊断句使用补充三、补充四里的原文，风吹损失另注明「此为工程取值，非标准强制条款」。

补充四没有写区间端点同时属于相邻两行时归哪一行。代码把公共端点归入较高雷诺数行，各 \(a\) 的最低下界和最高上界仍包含在内。\(a=2.0\) 的 \(10^4\sim 2\times 10^6\) 一行在约 \(10^4\) 到 \(2.36\times 10^4\) 给出非正欧拉数，这些点抛 `OutOfRangeError`。

