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
