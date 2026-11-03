# 交给新 agent 的交接说明

本文件是新对话的入口。先读本文件，再按需要打开下面列出的文档。不要修改 `docs/SPEC.md`。不要重新讨论已经确认的关联式。不要在这个旧对话里继续编码；用户会新开一个 agent。

## 先读这些文件

1. `docs/HANDOFF.md`（本文件）
2. `docs/PROGRESS.md`（当前步骤与未决项）
3. `docs/correlations.md`（确认表与补充二、三、四的公式）
4. `docs/PLAN.md`（文件清单、依赖版本、实现顺序、测试、界面、zip）
5. `docs/SPEC.md`（原始规格，只读）
6. `docs/sources/补充四.docx` 与 `docs/sources/zukauskas_euler_table.png`（压降系数以这张图为准）

## 当前状态

- 步骤 0：已完成。关联式、默认常数、湿修正、\(\Gamma_\mathrm{ref}\)、粗网格和外扩规则都已由用户在补充二、补充三、补充四中决定，并写入 `docs/correlations.md`。
- 步骤 1：改动计划已写在 `docs/PLAN.md`。网格、\(\Gamma_\mathrm{ref}\) 和湿修正结构已批准。依赖版本、Friedel 展开式、均相加速压降仍是计划里的拟用式，补充四没有改它们。
- 步骤 3.1：已完成。物性在 `evapcond/properties/`，详见 docs/PROGRESS.md。
- 步骤 3.2：已完成。几何在 `evapcond/geometry/`，`TubeGeometry` 与 `PlateGeometry` 在 `evapcond/models.py`。
- 下一步是步骤 3.3 空气侧。不要重做 3.1 和 3.2，也不要改 docs/SPEC.md。
- 版本号只定义在 `evapcond/__init__.py` 的 `__version__`，当前 `"1.0.0"`。

## 新 agent 的第一件事

欧拉数表已对照 `docs/sources/zukauskas_euler_table.png` 核对，三处争议系数与 docs/correlations.md 一致。不要重核、不要改表。

从步骤 3.3 继续，顺序见 `docs/PLAN.md`：`evapcond/correlations/film_air.py`、`evapcond/airside.py`，以及 `tests/test_airside.py`。

求解器和界面不得导入 CoolProp。计算内核不得导入 PySide6。界面不得写计算公式。

每完成一步就更新 `docs/PROGRESS.md`，并提交，信息格式为「步骤N：<内容>」。

## 编码时直接使用、不要再向用户确认的公式

以下全文在 `docs/correlations.md`。这里只列新 agent 最容易写错的几条。

- 管外 \(h_c\) 与水膜 \(h_w\) 都用 \(h=2102.9(\Gamma_m/d_o)^{1/3}\)，热阻分开串联。\(\Gamma_m=\dot m_w d_o/(2A_f)\)。结果里必须有补充二规定的那句 Mizushina 说明。
- \(h_m=h_c/(c_{p,a}\mathrm{Le}_f)\)，\(\mathrm{Le}_f\) 用 Bosnjaković 式，默认不是 1。
- 管内冷凝用补充二写出的 Shah 公式。\(\mathrm{Re}_{GT}\le 35000\) 时计算并写警告，不剔除。
- 单相用 Gnielinski (1976) 公开转写。\(\mathrm{Re}<2300\) 抛 `OutOfRangeError`。不新增补充二里的异常类名。
- 干管束：

\[
\mathrm{Eu}=q+\frac{r}{\mathrm{Re}}+\frac{s}{\mathrm{Re}^2}+\frac{t}{\mathrm{Re}^3}+\frac{u}{\mathrm{Re}^4}
\]

\[
C_2=1-0.45\exp(-N_r/3)\ (N_r<10),\quad C_2=1\ (N_r\ge 10)
\]

\[
\Delta p_\mathrm{dry}=C_2\cdot\mathrm{Eu}\cdot\frac12\rho V_\mathrm{max}^2\cdot N_r
\]

\[
\Delta p_\mathrm{wet}=\Delta p_\mathrm{dry}\left(1+0.5\cdot\frac{\Gamma_m/d_o}{2.8755}\right)
\]

\(k_1=1\)，并输出「当前干管束压降按等边错列计算……」。结果 JSON 标记 `estimated_wet_correction`。\(a\) 或雷诺数不在表内则 `OutOfRangeError`。

- 默认搜索 2268 点，细化不超过 200 点。贴边外扩的具体截断见 `docs/correlations.md` 补充四。管排贴边时原样打印补充四的 Warning 句。
- 板式与低翅片：`UnconfirmedCorrelationError`，只算 `tube_plain`。
- \(k_w=63.9\)。四个默认效率与风吹损失率是工程取值，风吹损失的分母是喷淋水量。

## 计划中的拟用式（补充四未改，按 PLAN.md 实现）

- Friedel 乘子加 Blasius 摩擦系数。\(E,F,H,\mathrm{Fr},\mathrm{We}\) 的展开式在 `docs/PLAN.md`。
- 加速压降用均相比容 \(v=x/\rho_g+(1-x)/\rho_l\)。
- 依赖：CoolProp==6.6.0，PySide6==6.6.2，numpy==1.26.4，scipy==1.11.4，pytest==8.3.4，pyinstaller==6.3.0。

## 不要做的事

- 不改 `docs/SPEC.md`。
- 不把 Incropera 表 7.5 的努塞尔数常数当作欧拉数系数。补充四已经放弃那条路径。
- 不把干管束压降乘一个固定常数来冒充湿压降。湿修正只用上面的 \(\Gamma_m/d_o\) 式，并标明是估计。
- 不在未核对 png 之前把三处有争议的系数写死。
