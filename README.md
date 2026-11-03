# 蒸发式冷凝器设计计算软件

版本 1.0.0。Windows 10/11 64 位图形程序，开发时也可以在 macOS 上运行界面和测试。打包必须在 Windows 上执行。

## 开发环境

需要 Python 3.10、3.11 或 3.12 的 64 位版本。CoolProp 6.6.0 没有 Python 3.13 的可用安装包。

在项目根目录：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows 上把 `source .venv/bin/activate` 换成 `.venv\Scripts\activate`。

锁定版本见 `requirements.txt`：CoolProp 6.6.0、PySide6 6.6.2、numpy 1.26.4、scipy 1.11.4、pytest 8.3.4、pyinstaller 6.3.0。

## 开发运行

```bash
python -m pytest
python -m evapcond
python -m evapcond design --input examples/design_example.json --out 输出目录
python -m evapcond rating --input examples/rating_example.json --out 输出目录
```

`python -m evapcond` 打开中文界面。两条命令行分别做设计和校核，并在输出目录写入 `result.json`、`distribution.csv` 和 `summary.txt`。

`examples/design_example.json` 和 `examples/rating_example.json` 是单台候选，用来确认程序能跑通。不写候选列表时，设计模式使用 2268 点粗网格加局部细化，在这台开发机上大约需要十五到二十五分钟。

退出码：0 成功，2 输入错误或越界，3 无可行设计，4 不收敛，5 取消。

## Windows 打包

在 Windows 10/11 64 位上安装 Python 3.10、3.11 或 3.12 的 64 位版本，并确认 `py` 启动器可用。打开项目根目录，双击或在命令提示符中运行：

```bat
packaging\build_windows.bat
```

脚本会创建 `build\venv`，安装锁定依赖，运行 pytest，再用 PyInstaller 打出 onedir 窗口程序。pytest 失败时脚本停止，不生成 zip。

成功后的文件是 `dist\EvapCond_v1.0.0_win64.zip`。压缩包根目录只有 `EvapCond\`，其中有 `EvapCond.exe`、运行库、`使用说明.txt` 和 `examples\`。

## 界面

三个标签页：设计模式、校核模式、结果。

设计页和校核页按设计工况、几何、辅助参数、求解器设置分组。求解器设置默认折叠。可选字段预填并标有「默认」，必填的阻力系数、喷嘴压力、提升高度和管路数据初始为空。管径等候选值用逗号分隔。表面类型切换时只显示对应的几何字段。校核页的风量和喷淋水量各自二选一。

按钮：加载输入、保存输入、运行、取消、导出结果、以此设计结果生成校核输入。加载对话框默认打开程序旁边的 `examples`。运行前做与命令行相同的检查，不合法的字段标红。计算在后台进行，可取消。结果页有摘要、三项热阻、沿程表、警告、诊断和关联式引用。没有曲线。

未捕获的异常写日志：Windows 为 `%LOCALAPPDATA%\EvapCond\logs\app.log`，macOS 为 `~/Library/Logs/EvapCond/app.log`。

## 使用说明.txt

下面是随安装包分发的 `packaging/使用说明.txt` 全文。

1. 运行环境：Windows 10/11 64 位，无需安装 Python 或其他软件。
2. 启动步骤：右键 zip → “全部解压缩” → 打开 EvapCond 文件夹 → 双击 EvapCond.exe。
3. 醒目警告：不得在压缩包内直接双击运行，否则会报错或闪退。
4. 首次运行时如出现“Windows 已保护你的电脑”，点击“更多信息 → 仍要运行”。
5. 创建桌面快捷方式：右键 EvapCond.exe → 发送到 → 桌面快捷方式；不得把 EvapCond.exe 单独移出文件夹。
6. 示例：在界面中点“加载输入”，选择 examples/ 下的示例文件。
7. 命令行用法：EvapCond.exe design --input examples\design_example.json --out 结果目录；把 design 换成 rating 即按校核模式运行。
8. 日志位置：%LOCALAPPDATA%\EvapCond\logs\app.log；出错时请提供该文件。
