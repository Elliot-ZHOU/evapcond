@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

where py >nul 2>&1
if errorlevel 1 (
  echo Python launcher py is not installed. Install Python 3.10, 3.11, or 3.12 x64.
  exit /b 1
)

set "PY_LAUNCH="
for %%V in (3.12 3.11 3.10) do (
  py -%%V -c "import sys; raise SystemExit(0 if (3,10) <= sys.version_info < (3,13) else 1)" >nul 2>&1
  if not errorlevel 1 (
    set "PY_LAUNCH=py -%%V"
    goto :found_python
  )
)
echo Need Windows x64 Python 3.10, 3.11, or 3.12. CoolProp 6.6.0 does not support 3.13.
exit /b 1

:found_python
echo Using %PY_LAUNCH%
if exist build\venv rmdir /s /q build\venv
%PY_LAUNCH% -m venv build\venv
if errorlevel 1 exit /b 1
call build\venv\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 exit /b 1
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
python -m pytest
if errorlevel 1 (
  echo pytest failed. Zip will not be created.
  exit /b 1
)
python -m PyInstaller packaging\evapcond.spec --noconfirm --distpath dist --workpath build\pyinstaller
if errorlevel 1 exit /b 1
if not exist dist\EvapCond\EvapCond.exe (
  echo dist\EvapCond\EvapCond.exe was not produced.
  exit /b 1
)
copy /y packaging\使用说明.txt dist\EvapCond\使用说明.txt >nul
if errorlevel 1 exit /b 1
if not exist dist\EvapCond\examples mkdir dist\EvapCond\examples
copy /y examples\design_example.json dist\EvapCond\examples\design_example.json >nul
if errorlevel 1 exit /b 1
copy /y examples\rating_example.json dist\EvapCond\examples\rating_example.json >nul
if errorlevel 1 exit /b 1
for /f %%V in ('python -c "import evapcond; print(evapcond.__version__)"') do set "APP_VER=%%V"
if not defined APP_VER (
  echo Could not read evapcond.__version__.
  exit /b 1
)
if not exist dist mkdir dist
set "ZIP=dist\EvapCond_v%APP_VER%_win64.zip"
if exist "%ZIP%" del /f "%ZIP%"
powershell -NoProfile -Command "Compress-Archive -Path 'dist\EvapCond' -DestinationPath '%ZIP%' -Force"
if errorlevel 1 exit /b 1
echo Created %ZIP%
exit /b 0
