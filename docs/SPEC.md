# 角色与目标
你是 Python 数值计算与桌面应用工程师，必须按本规格实现“蒸发式冷凝器设计计算软件”：Windows 图形界面 + 命令行，设计模式与校核模式共享同一套分段迭代传热传质求解内核，最终以 zip 压缩包交付。

# 范围
## 做
1. 物性模块：制冷剂、湿空气、水。
2. 几何模块：水平圆管（光管、低翅片管）、板式；设计模式下生成几何候选。
3. 空气侧热质交换模块，显热与潜热分离计算。
4. 制冷剂侧冷凝模块：过热段、两相段、过冷段，含压降及当地饱和温度修正。
5. 总传热与分段迭代求解器，输出三项热阻分解。
6. 风机、水泵、补水计算模块。
7. 设计模式：网格寻优、不可行报告、松弛建议。
8. 校核模式。
9. Windows 图形界面（PySide6）：输入、校验、后台运行、进度、取消、结果展示、导入/导出。
10. 命令行接口：JSON 输入 → 控制台摘要 + CSV 沿程分布 + JSON 结构化结果。
11. Windows 打包：PyInstaller onedir 模式；构建脚本自动把产物压缩为一个 zip。
12. 单元测试、界面冒烟测试、验证算例框架、技术文档、关联式清单、验证报告、README、zip 内的“使用说明.txt”。
## 不做
- 单文件 exe（onefile）、MSI/EXE 安装程序、代码签名、自动更新。
- 网页界面、移动端、用户账户、主题切换、多语言界面（界面仅中文）。
- 图表绘制，沿程分布只用表格展示；数据库；Word/PDF/Excel 报表。
- 部分负荷曲线、年度能耗、经济性分析、多工况批处理等未列出的模式。
- 结垢热阻、风量/水量分布不均、防冻等未列出的物理效应。
- R744 跨临界气体冷却计算。
- U 形弯头与集管压降。
- REFPROP 后端的实现（只预留接口）。

# 技术约束
- 目标平台：Windows 10/11 x64，界面与打包产物必须在其上运行。开发机可以是 macOS，但界面必须能在 macOS 上启动，以便开发自测；打包必须在 Windows 上执行。
- 语言：Python 3.10 为最低版本，不得使用 3.11+ 专属语法。打包环境：Windows x64 + Python 3.10～3.12 x64。
- 依赖仅限以下各项，版本必须锁定为单一精确版本，写入 requirements.txt 与 pyproject.toml：
  - CoolProp==6.6.0
  - PySide6 6.6.x（具体补丁版本在步骤 1 中确定并锁定）
  - numpy、scipy、pytest、pyinstaller（版本在步骤 1 中锁定）
  - 新增依赖必须先征得同意。
- 实际使用的 CoolProp 版本号必须写入 docs/technical.md，并在运行时写入 result.json 的 environment.coolprop_version。
- 物性封装：
  - 所有物性调用只能通过 properties/ 下的独立函数进行，求解器与界面不得直接 import CoolProp。
  - properties/backend.py 定义后端接口；本期只实现 CoolProp 后端；以后替换为 REFPROP 时不得需要改动求解器代码。
- 物性来源写死：
  - 制冷剂、水：CoolProp PropsSI（HEOS 后端）。
  - 水表面张力：PropsSI 'I'（IAPWS 2014）。
  - 湿空气：HAPropsSI（ASHRAE RP-1485，Herrmann/Kretzschmar/Gatley 2009，Hyland-Wexler 体系）。
  - R404A、R507A：CoolProp 伪纯质模型。
- 内部计算一律使用 SI 单位（W、Pa、K、kg、m、J/kg）；单位换算只在 IO 层与界面层进行。
- 架构：
  - 分层：计算内核（evapcond/core 等）→ 应用服务（design.run / rating.run）→ 外壳（cli、gui）。
  - 计算内核不得 import PySide6。
  - 界面层不得包含任何计算公式，只能调用应用服务。
  - 模块间只能通过 dataclass(frozen=True) 数据结构与函数参数传递数据；不得使用全局可变变量或单例。
  - 应用服务签名：run(input, config, progress_cb=None, cancel_event=None)。progress_cb 接收 (已完成数, 总数, 文本)；cancel_event 为 threading.Event，计算中按候选或迭代粒度检查。
- 关联式注册：
  - 每条关联式必须是独立函数，并附带元数据：完整文献引用、适用参数及范围、文献报告偏差。
  - 每次调用必须校验参数是否在范围内，越界时抛出 OutOfRangeError。
- 求解参数（分段数、最大迭代次数、松弛因子）必须集中在 SolverConfig 中，并可由用户覆盖。
- 打包规格：
  - PyInstaller onedir，--windowed（不弹出控制台窗口），程序名 EvapCond.exe。
  - build_windows.bat 一键完成：创建虚拟环境 → 安装锁定依赖 → 运行 pytest → PyInstaller 打包 → 复制附加文件 → 生成 zip。pytest 失败时必须中止，不得生成 zip。
  - zip 文件名：EvapCond_v<版本号>_win64.zip，输出到 dist/。
  - zip 根目录只有一个文件夹 EvapCond/，内含：
    - EvapCond.exe 及其运行库
    - 使用说明.txt（UTF-8 带 BOM）
    - examples/design_example.json、examples/rating_example.json
  - 同一 exe 必须同时支持命令行用法：`EvapCond.exe design|rating --input ... --out ...`。在 --windowed 下，命令行模式必须把控制台摘要同时写入 `<out>/summary.txt`。

# 功能与交互
## US-0 命令行
- `python -m evapcond design --input <file.json> --out <dir>`
- `python -m evapcond rating --input <file.json> --out <dir>`
- 打包后，用 `EvapCond.exe design|rating ...` 运行，效果与上面两条相同；不带参数启动时打开图形界面。
- 退出码：0 成功；2 输入错误或越界；3 无可行设计；4 不收敛；5 用户取消。
- 输出文件：`<dir>/result.json`、`<dir>/distribution.csv`、`<dir>/summary.txt`；控制台打印摘要。
- 输入 JSON 格式必须与界面“保存输入”生成的文件完全一致。

## US-1 设计模式输入
必填：
- Q_k：kW，>0
- refrigerant：R717 / R22 / R134a / R404A / R507A / R744
- T_k：°C
- T_db_in：°C
- T_wb_in：°C，必须满足 T_wb_in < T_db_in 且 T_wb_in < T_k
- surface_type：tube_plain / tube_lowfin / plate
- v_f_max：m/s，>0

可选（括号内为默认值）：
- p_atm：101.325 kPa
- 进口过热度：0 K
- 出口过冷度：0 K
- d_o 候选：[19.05, 25.0, 32.0] mm
- 壁厚 δ：2.0 mm（d_i = d_o − 2δ）
- 管材导热系数 k_w：碳钢 63.9 W/(m·K)，来源 Incropera《Fundamentals of Heat and Mass Transfer》表 A.1，AISI 1010，300 K，需在步骤 0 核实
- 管排布置：叉排
- S_T/d_o 候选：[2.0, 2.5]
- S_L/d_o 候选：[1.5, 2.0]
- Γ 范围：取所选关联式有效范围与用户范围的交集，均分 3 点
- L 候选：[2, 3, 4, 5, 6] m
- v_f 候选：[0.6, 0.8, 1.0] × v_f_max
- N_r 范围：4～30

辅助输入（风机/水泵/补水）：
- 必填，无默认值：
  - 收水器阻力系数 ζ_de、进风百叶阻力系数 ζ_lv、风筒阻力系数 ζ_st，均以迎面风速动压为基准
  - 喷嘴雾化压力 p_noz（kPa）
  - 提升高度 H_lift（m）
  - 管路长度（m）、管路内径（mm）、管路局部阻力系数和 Σζ、管路粗糙度（mm）
- 可选：
  - η_fan（默认 0.65）、η_pump（默认 0.70）
  - 浓缩倍数 N_cyc（默认 3.0）
  - 风吹损失率（默认为喷淋水量的 0.01%）
  - 以上四项的来源必须在步骤 0 确认

## US-2 设计模式寻优
- 回路约定：
  - 每排管数 N_t 等于并联回路数。
  - 每个回路自顶排进入，蛇形穿过全部 N_r 排后自底排流出；管程数 = N_r。
  - 各回路工况相同，只计算一个回路，再乘以 N_t。
- 制冷剂质量流量：m_ref = Q_k / (h_in − h_out)，其中 h_in 由 T_k 与进口过热度确定，h_out 由出口过冷度确定。
- 枚举与求解：
  1. 外层枚举 d_o × (S_T, S_L) × Γ × v_f × L × N_r。
  2. 对每个组合，用区间求根求出使出口恰好达到目标状态的单回路流量 m_c。
  3. 取 N_t = ceil(m_ref / m_c)，再以 m_ref / N_t 进行一次校核计算，确认 Q ≥ Q_k。
- 剔除规则：超出任一关联式有效范围的候选必须剔除，并在 warnings 中记录。
- 目标：总传热面积最小；面积相同时取风机与水泵总功率最小者。
- 耗时上限：默认网格的总耗时必须 ≤ 15 min。改动计划中必须给出候选总数与单次求解耗时估算；超出上限时必须先提出缩减方案并等待确认。
- 无可行解时：
  - 抛出 InfeasibleDesignError，并输出“在当前约束下无可行设计”。
  - 逐项单独放宽一个约束后重新搜索，报告首个可行的放宽值，例如“将迎面风速上限提高至 X m/s 可获得可行解”：
    - v_f_max 以 0.1 m/s 步长放宽，最多放宽到 2 倍；
    - N_r 上限以 2 为步长放宽，最多放宽到 40；
    - L 上限以 1 m 为步长放宽，最多放宽到 10 m。
  - 不得输出违反约束的结果。

## US-3 设计模式输出（缺一不可）
- 几何：d_o、d_i、S_T、S_L、N_r、N_t、L、迎风面积（= N_t·S_T·L）、总传热面积（按管外表面积计）
- 运行：v_f、Γ
- 风机：风量、全压、轴功率
- 水泵：流量、扬程、轴功率
- 水量：蒸发水量、排污量、总补水率
- 传热：K 与三项热阻占比
- 沿程分布：写入 CSV，并在界面表格中显示
- 诊断信息（diagnostics）：制冷剂为 R404A 时必须包含一行“R404A 按伪纯质计算，温度滑移未计入；若需精确滑移修正，应切换为混合物模型。”

## US-4 校核模式
输入：
- 设计模式输出的全部几何参数
- 制冷剂质量流量（必填）
- 制冷剂进口压力或进口饱和温度（必填），以及进口温度（必填）
- T_db_in、T_wb_in
- 风量或 v_f（二选一）
- 喷淋水量或 Γ（二选一）
- US-1 中的全部辅助输入

输出：
- 实际换热量
- 出口制冷剂温度及干度或过冷度
- 出口空气干球温度、含湿量、焓
- 水膜温度最大值与最小值
- 三项热阻及占比、K、平均传质系数 h_m
- 风机与水泵实际功耗、蒸发水量、补水率
- 诊断信息（规则同 US-3）

## US-5 求解内核（两种模式共用）
- 流向：
  - 空气自下而上；喷淋水自上而下；制冷剂自顶排流向底排。
  - 同一排内制冷剂沿管长方向流动，相邻两排方向交替（蛇形）。
- 离散：
  - 每排沿管长分为 n_L 段，n_L = ceil(N_cv_target / N_r)，N_cv_target 默认 40，不得小于 20。
  - 空气从第 r 排第 j 段垂直进入第 r−1 排第 j 段。
- 单个控制容积的方程（外表面积 dA，水膜温度 T_w）：
  - 显热：dQ_s = h_c·dA·(T_w − T_a)
  - 蒸发：dm_ev = h_m·dA·(w_s(T_w) − w_a)，h_m 单位为 kg/(m²·s)
  - 潜热：dQ_l = dm_ev·h_fg(T_w)
  - 空气含湿量：ṁ_a·dw_a = dm_ev
  - 空气焓：ṁ_a·di_a = dQ_s + dm_ev·i_g(T_w)
  - 空气温度：由 (i_a, w_a, p_atm) 经湿空气物性函数反算得到，不得用 ṁ_a·c_p,a·dT_a = dQ_s + dQ_l 计算
  - 水膜能量：ṁ_w·c_pw·dT_w = dQ_ref − dQ_s − dQ_l；水膜质量：dṁ_w = −dm_ev
  - 制冷剂到水膜：dQ_ref = (T_ref − T_w) / (R_ref + R_wall + R_film)
  - 制冷剂能量：ṁ_c·dh_ref = −dQ_ref
- h_c 与 h_m：
  - h_c 必须采用 US-8 指定的关联式。
  - 指定关联式未给出 h_m 时，用 h_m = h_c / (c_p,a·Le^(2/3)) 换算，Le 的计算方法须在步骤 0 确认。
  - 不得用“K × 焓差”的单方程，或“焓差项 + 显热项”的叠加式替代上述方程。
- 制冷剂侧：
  - 按当地焓值与当地饱和焓判断所处区段（过热 / 两相 / 过冷）。
  - 每轮迭代都必须用当地压力更新当地饱和温度（严于原规格“温差超过 0.2 K 才更新”的要求）。
- 喷淋水循环：顶排喷淋水温 = 底排出口水膜温度（稳态循环），忽略补水显热；该温度纳入迭代求解。
- 收敛判据（三项须同时满足）：
  - 总换热量相对变化 < 1e-4
  - 各段水膜温度绝对变化 < 1e-3 K
  - 各段空气焓绝对变化 < 1e-2 kJ/kg
  - 最大迭代 500 次，超出时抛出 ConvergenceError，附三项残差。
- 网格无关性：n_L 加倍时总换热量变化必须 < 0.5%。默认值达不到时必须提高默认值并报告。

## US-6 热阻与 K 的定义
- T*_a：饱和空气焓等于当地 i_a 时对应的温度。
- 三项热阻：
  - R_ref = 1/(h_ref·A_i)
  - R_wall = ln(d_o/d_i)/(2π·k_w·dL)
  - R_out,eq = (T_wo − T*_a)/dQ_ref，包含水膜对流热阻与水膜—空气热质交换的等效热阻
- 占比：share_x = Σ_k(ΔT_x,k·q_k) / Σ_k(ΔT_total,k·q_k)，其中 ΔT_x,k 为第 k 段在第 x 项热阻上的温降。
- K（以管外表面积为基准）：K = Q / Σ_k[A_o,k·(T_ref,k − T*_a,k)]。

## US-7 风机、水泵、补水
- 风量 = v_f × 迎风面积。
- 风机全压 = 湿工况管束压降（关联式计算）+ (ζ_de + ζ_lv + ζ_st)·ρ_a·v_f²/2。
- 喷淋水量 = Γ × 2 × N_t × L。
- 水泵扬程 = p_noz/(ρ_w·g) + H_lift + 管路沿程阻力（Colebrook-White）+ 局部阻力。
- 轴功率 = 有效功率 / η。
- 补水量 = 蒸发量 + 排污量 + 风吹损失：
  - 蒸发量 = ṁ_a·(w_out − w_in)
  - 排污量 = 蒸发量 / (N_cyc − 1)
  - 风吹损失 = 风吹损失率 × 喷淋水量
- 喷淋密度 Γ 的定义：单位管长、单侧的喷淋水质量流量，kg/(m·s)。

## US-8 指定关联式来源
- 管外空气对流传热系数 h_c 的指定来源（两篇为同一实验的不同报告，关联式形式一致）：
  - 朱冬生，蒋翔，徐丽，沈家龙. 蒸发式冷凝器管外水膜与空气传热系数的实验研究[C]. 中国工程热物理学会第十一届年会论文集 传热传质学（上册），北京，2005.
  - 蒋翔，朱冬生，唐广栋. 蒸发式冷凝器管外水膜与空气传热性能及机理的研究[J]. 流体机械，2006，34(8).
- 步骤 0 必须从原文提取：函数形式、全部系数与指数、Re 数定义与范围、特征尺寸、喷淋密度范围、迎面风速范围、管径、管排布置、所计算的传热系数的定义（纯空气对流 h_c，还是水膜—空气综合系数），以及最大相对标准偏差 12.2%。
- 实现模型无法获取原文时，必须停止并请用户提供原文或关联式全文，不得凭“12.2%”自行拟合或补全。
- 例外条款：用户明确声明原文无法获取时，允许提出候选关联式表，逐条标注来源与适用范围，经用户确认后使用。
- 所计算的系数若不是纯 h_c，必须先报告它与 US-5 方程的映射方式，经确认后再编码。

## US-9 图形界面（PySide6，中文）
- 启动方式：
  - 最终用户：解压 zip 后，双击 EvapCond/EvapCond.exe。
  - 开发时：`python -m evapcond.gui`。
- 主窗口：三个标签页，分别为“设计模式”“校核模式”“结果”。最小可用分辨率 1366×768，在 150% 缩放下控件不得重叠或被截断；表单超出时使用滚动区域。
- 窗口标题：显示“蒸发式冷凝器设计计算软件 v<版本号>”。
- 输入表单：
  - 按“设计工况 / 几何与候选范围 / 辅助参数 / 求解器设置（默认折叠）”分组。
  - 每个字段旁显示单位。
  - 可选字段预填默认值，并标注“默认”；必填辅助字段默认为空。
  - 列表型候选值（d_o、S_T/d_o 等）以逗号分隔输入。
  - 下拉框：refrigerant、surface_type、风量/v_f 二选一、水量/Γ 二选一。
  - surface_type 切换时，只显示对应的几何字段（光管 / 低翅片管 / 板式）。
- 按钮：
  - 加载输入（文件对话框默认打开 exe 同级的 examples/）
  - 保存输入（与 CLI 输入 JSON 格式一致）
  - 运行、取消
  - 导出结果（选择目录后写出 result.json、distribution.csv、summary.txt）
  - “以此设计结果生成校核输入”（把设计输出的几何参数与辅助输入填入校核页）
- 校验：
  - 点击“运行”时先执行与 CLI 相同的输入校验。
  - 不合法的字段标红，并在字段下方显示消息（参数名、当前值、有效范围）。
  - 有任何错误时不启动计算。
- 运行：
  - 计算必须在 QThread 中执行，主界面不得冻结。
  - 进度条：设计模式显示“已评估候选数/总数”；校核模式显示迭代次数与三项残差。
  - 运行期间禁用输入与“运行”按钮。
  - 点击“取消”后 5 s 内停止，并显示“已取消”。
- 结果页：
  - 摘要区：US-3 或 US-4 的全部字段，带单位。
  - 热阻表：三项热阻与占比。
  - 沿程分布表：列与 CSV 一致，可排序，只读。
  - 列表区：警告与诊断信息、所用关联式（名称 + 引用）。
- 错误显示：
  - InputError、OutOfRangeError、ConvergenceError、UnconfirmedCorrelationError：弹出对话框，显示错误类型与完整消息。
  - InfeasibleDesignError：显示“在当前约束下无可行设计”及全部松弛建议。
  - 未捕获的异常：弹出对话框，并写入日志文件 %LOCALAPPDATA%\EvapCond\logs\app.log（macOS 上为 ~/Library/Logs/EvapCond/app.log）；程序不得退出。
- 运行目录：程序不得向 exe 所在目录写入任何文件，只能写入用户选择的目录与日志目录。
- 一致性：同一输入下，界面导出的 result.json 与 distribution.csv 的数值必须与 CLI 输出完全一致（时间戳字段除外）。

## US-10 使用说明.txt（随 zip 分发，面向不懂编程的最终用户）
必须且仅包含以下内容：
1. 运行环境：Windows 10/11 64 位，无需安装 Python 或其他软件。
2. 启动步骤：右键 zip → “全部解压缩” → 打开 EvapCond 文件夹 → 双击 EvapCond.exe。
3. 醒目警告：不得在压缩包内直接双击运行，否则会报错或闪退。
4. 首次运行时如出现“Windows 已保护你的电脑”，点击“更多信息 → 仍要运行”。
5. 创建桌面快捷方式：右键 EvapCond.exe → 发送到 → 桌面快捷方式；不得把 EvapCond.exe 单独移出文件夹。
6. 示例：在界面中点“加载输入”，选择 examples/ 下的示例文件。
7. 命令行用法（一段）：`EvapCond.exe design --input ... --out ...`。
8. 日志位置：%LOCALAPPDATA%\EvapCond\logs\app.log；出错时请提供该文件。

# 数据模型与状态
- dataclass(frozen=True)：
  - DesignInput、RatingInput、AuxInput
  - TubeGeometry（含低翅片字段：翅高、翅距、翅厚）
  - PlateGeometry（板宽、板高、板间距、板片数、波纹倾角、波纹节距、波纹深度）
  - OperatingPoint、SolverConfig
  - SegmentState（行号、段号、区段类型、T_ref、p、x、h_ref、T_w、ṁ_w、T_a、w_a、i_a、dQ_ref、dQ_s、dQ_l、三项热阻）
  - ResistanceSummary、AuxResult、DesignResult、RatingResult、ConvergenceInfo、CorrelationRecord（名称、引用、适用范围、实际调用参数）、Progress
- 求解器状态只能存在于函数局部变量与返回值中，调用之间不得保留状态。
- 界面状态：
  - 只保存表单值与最近一次结果对象。
  - 表单值 ↔ 输入 JSON 的转换只能通过 io_json.py 进行。
  - 不得在界面层另建一套输入模型。
- 版本号：只能在 evapcond/__init__.py 的 __version__ 中定义，初始值 "1.0.0"；窗口标题、result.json、zip 文件名都必须读取该值。
- result.json 顶层键：
  schema_version、mode、environment（python_version、coolprop_version、app_version）、inputs、defaults_used、results、resistances、convergence、correlations_used、diagnostics、warnings
- distribution.csv 列：
  row, seg, region, T_ref_C, p_ref_kPa, x, T_film_C, m_water_kg_s, T_air_C, w_air_kg_kg, i_air_kJ_kg, q_ref_W, q_sens_W, q_lat_W
  文件编码为 UTF-8 带 BOM，保证 Excel 直接打开时不乱码。

# 文件与模块建议
evapcond/
  __init__.py, __main__.py（无参数时启动界面，有参数时走 CLI）, cli.py
  errors.py           InputError / OutOfRangeError(param, value, valid_range, source) / ConvergenceError / InfeasibleDesignError / UnconfirmedCorrelationError / CancelledError
  models.py           全部 dataclass
  io_json.py          输入解析、单位换算、校验；结果写出（JSON/CSV/摘要）
  properties/backend.py, coolprop_backend.py, refrigerant.py, humid_air.py, water.py   规格 3.1
  geometry/tube.py, plate.py, candidates.py                                            规格 3.2
  correlations/registry.py, film_air.py, condensation.py, single_phase.py, pressure_drop.py, plate.py
  airside.py          规格 3.3
  refside.py          规格 3.4
  solver.py           规格 3.5
  auxiliary.py        规格 3.6
  rating.py, design.py
  gui/__init__.py, __main__.py, main_window.py, design_form.py, rating_form.py, results_view.py, worker.py, widgets.py
packaging/evapcond.spec, build_windows.bat, 使用说明.txt
examples/design_example.json, rating_example.json
tests/
  test_properties.py, test_geometry.py, test_airside.py, test_refside.py, test_solver.py, test_auxiliary.py, test_design.py, test_rating.py, test_cli.py, test_validation.py
  test_gui_smoke.py（QT_QPA_PLATFORM=offscreen，不使用 pytest-qt）
validation/cases/case_*.json
docs/technical.md, docs/correlations.md, docs/validation_report.md
README.md, pyproject.toml, requirements.txt

# 边界与错误处理
- 物性范围：
  - 制冷剂饱和温度 −40～+60 °C
  - 湿空气干球温度 5～50 °C，含湿量 0～w_sat(T_db, p_atm)
  - 水 5～60 °C
  - 越界时抛出 OutOfRangeError，消息必须包含参数名、当前值、有效范围、来源。
- R744：
  - T_k > T_crit − 1 K（T_crit 由 CoolProp 读取）时，必须抛出 OutOfRangeError，消息为“R744 在该冷凝温度下不适用蒸发式冷凝”，附 T_k 与上限值，并终止计算。
  - 单相物性函数在 −40～+60 °C 内连续计算，不得查表插值。
- 设计模式输入：T_wb_in ≥ T_db_in 或 T_wb_in ≥ T_k 时抛出 InputError。湿空气模块本身必须支持 T_wb = T_db（饱和空气）。
- 风速与流量：
  - v_f ≤ 0 或制冷剂流量 ≤ 0 时抛出 InputError。
  - 风速或流量趋近于零导致关联式越界时，抛出 OutOfRangeError。
  - 不得返回 NaN 或 inf，不得静默截断或外推。
- 关联式：低翅片管、板式所需关联式或 US-8 指定关联式未获确认时，调用必须抛出 UnconfirmedCorrelationError，不得以其他关联式代替。
- 缺少辅助输入时抛出 InputError，并列出所有缺失字段。
- 用户取消时抛出 CancelledError；CLI 退出码 5；界面显示“已取消”，并保留输入。
- 路径：exe 所在路径、输入文件路径、输出路径包含中文或空格时，程序必须正常工作。

# 禁止事项
- 不得增加本规格未列出的功能、模式、界面元素、图表、输出格式或依赖；不得更换语言、物性库、GUI 框架或打包方式（onedir + zip）。
- 不得在界面层编写计算逻辑；计算内核不得依赖 PySide6；不得绕过 properties/ 直接调用 CoolProp。
- 不得用单节点集总参数模型、壁温均一假设或非迭代方法代替分段迭代；不得把控制容积数降到 20 以下；不得放宽收敛判据。
- 不得用“K × 焓差”单方程，或“焓差项 + 显热项”叠加式计算空气侧；管外传热不得使用 Dittus-Boelter 类管内公式；不得用“干空气光管压降 × 固定系数”计算湿工况压降。
- 只能使用以下两类关联式：US-8 指定的关联式，以及步骤 0 中经用户确认的关联式；凭“12.2%”自行拟合或补全关联式的做法同样禁止。
- 不得出现无来源的常数（如“经验取 0.8”）。
- 不得编造文献引用、关联式系数、实验数据或验证结果；无法核实的条目必须标注“未核实”并提问。
- 不得对已确认的模块进行大规模重构，除非得到明确要求。

# 验收标准
- [ ] 在 Windows 上运行 build_windows.bat，一次生成 dist/EvapCond_v1.0.0_win64.zip；zip 结构符合打包规格。
- [ ] 在一台未安装 Python 的 Windows 10/11 x64 上，解压 zip 后双击 EvapCond.exe，10 s 内显示主窗口；解压路径含中文与空格时同样通过。
- [ ] 使用说明.txt 包含 US-10 全部 8 项内容，在 Windows 记事本中打开不乱码。
- [ ] 界面可完成以下全流程：加载 examples/ 示例 → 设计运行 → 查看结果 → 导出 → “以此设计结果生成校核输入” → 校核运行 → 导出。
- [ ] `EvapCond.exe design --input examples\design_example.json --out <dir>` 可生成 result.json、distribution.csv、summary.txt，退出码正确。
- [ ] 界面导出的 JSON/CSV 与 CLI 对同一输入的输出数值一致（时间戳除外）。
- [ ] distribution.csv 用 Excel 双击打开时中文与数值显示正常。
- [ ] 输入非法或缺少必填辅助字段时，对应字段标红并显示参数名、当前值、有效范围；计算不启动；程序不崩溃。
- [ ] 设计计算期间界面可拖动、可响应；进度条更新；取消后 5 s 内停止。
- [ ] 在 1366×768 分辨率、150% 缩放下，所有控件可见、可操作；中文显示正常。
- [ ] 程序运行后，exe 所在目录内没有新增文件。
- [ ] 6 种制冷剂在 −40～+60 °C 内的物性与 CoolProp 直接调用结果一致（相对偏差 < 1e-9）；越界时抛出 OutOfRangeError。
- [ ] R744 在 T_k > T_crit − 1 K 时报告“R744 在该冷凝温度下不适用蒸发式冷凝”并终止。
- [ ] R404A 的结果 diagnostics 中包含伪纯质提示语，界面中可见。
- [ ] result.json 中记录 coolprop_version 与 app_version，且与锁定版本、__version__ 一致。
- [ ] 湿空气 T_db / T_wb / RH / w / h / ρ 两两互算往返误差 < 1e-6（相对）；T_wb = T_db 情形通过。
- [ ] h_c 关联式的系数、指数、范围与 US-8 原文逐项一致，并在 docs/correlations.md 中给出原文页码或公式编号。
- [ ] 每个关联式函数都带完整引用与范围元数据，越界时抛出异常；docs/correlations.md 与代码元数据一致。
- [ ] 求解器满足三项收敛判据；n_L 加倍时 Q 变化 < 0.5%（至少 3 个工况）。
- [ ] 所有控制容积及全局的能量守恒残差 < 1e-6·Q；水量守恒残差 < 1e-9 kg/s。
- [ ] 设计模式输出包含 US-3 全部字段；v_f ≤ v_f_max；Γ 位于关联式有效范围内。
- [ ] 无可行解时：CLI 退出码为 3；界面显示“在当前约束下无可行设计”；给出至少一条松弛建议。
- [ ] 以设计结果作为校核输入时，校核换热量与 Q_k 的偏差 < 1%，且 Q ≥ Q_k。
- [ ] 三项热阻占比之和 = 1（误差 < 1e-9）。
- [ ] 每个模块都有单元测试，覆盖典型工况与边界工况（T_db = T_wb、制冷剂流量趋近于零、v_f 趋近于零）；界面冒烟测试覆盖“启动 → 加载示例输入 → 校核运行 → 结果表非空”；pytest 全部通过。
- [ ] validation/ 下至少 3 个算例：有用户提供的文献数据时，R717 / R134a、T_k 35～45 °C、T_wb 20～28 °C 范围内 K 的偏差 ≤ ±15%；数据缺失时测试标记为 skip 并注明“待用户提供文献数据”。
- [ ] docs 中包含全部方程、关联式引用及适用范围、物性来源与 CoolProp 版本、默认值依据、验证对比表与偏差来源分析。
- [ ] README 中有：开发环境搭建、开发运行步骤、Windows 打包步骤（在 Windows 上运行 build_windows.bat）、CLI 用法、界面操作说明，以及使用说明.txt 的全文。

# 工作方式
1. 步骤 0：输出“关联式与默认参数确认表”。
   - 列：用途、名称、完整引用、适用范围、报告偏差、本软件用法、核实状态。
   - 第一行必须是 US-8 指定的 h_c 关联式；须给出原文提取结果，或注明“需用户提供原文”。
   - 其余必须覆盖：水膜对流、Le 计算、水平管冷凝、单相对流、两相摩擦压降、湿工况管束压降、板式冷凝与板外水膜、低翅片管、管路摩擦、η_fan、η_pump、N_cyc、风吹损失率、k_w。
   - 候选：Mizushina 等 (1967)、Parker & Treybal (1961)、Shah (2009)、Gnielinski (1976)、Friedel (1979)、Niitsu 等 (1969)、Longo 等 (2015)、Colebrook (1939)。必须核实原文；不能核实的标注“未核实”。
   - 输出后停止，等待确认。
2. 步骤 1：输出改动计划，包括文件清单、锁定的依赖版本、实现顺序、每个模块的测试项、设计寻优的候选数与耗时估算、界面窗口布局草图（文字描述控件分组）、zip 目录结构；输出后等待确认。
3. 按 3.1 → 3.2 → 3.3 → 3.4 → 3.5 → 3.6 → 校核 → 设计 → IO/CLI → 界面 → 打包与 zip → 文档 的顺序实现。每完成一步，说明改动了哪些文件、改了什么、测试结果如何。
4. 遇到不确定的事项时，立即停止并提问，不得自行假设。

5. 交接与断点续做（所有步骤都适用）：
   - 开工第一个动作：把本提示词原文保存为 docs/SPEC.md，此后不得修改。
   - 维护 docs/PROGRESS.md，每完成一步、每次得到用户确认后必须立即更新。固定包含：
     a. 当前步骤及状态（未开始 / 进行中 / 已完成）；
     b. 已完成步骤：涉及的文件、测试结果；
     c. 用户已确认的决定：关联式确认结论、锁定的依赖版本、改动计划是否批准、其他口头确认事项；
     d. 未解决的问题；
     e. 下一步的具体动作，细化到文件与函数。
   - 步骤 0 的确认表保存为 docs/correlations.md；步骤 1 的改动计划保存为 docs/PLAN.md。
   - 每完成一步执行 git commit，提交信息格式为“步骤N：<内容>”。
   - 用户在对话中确认的任何事项，必须当场写入 PROGRESS.md；未写入文件的决定视为不存在。
