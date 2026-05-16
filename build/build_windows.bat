@echo off
REM Build a standalone Windows executable of the traffic simulation.
REM
REM Output: dist\TrafficSim.exe
REM
REM Requirements on the Windows build host:
REM   - Python 3.10+ installed and on PATH
REM
REM Run this from the repo root (or anywhere — it cd's to its own dir).

setlocal
cd /d "%~dp0\.."

echo ^>^> Installing Python build deps
python -m pip install --upgrade pip
if errorlevel 1 goto :fail
python -m pip install --upgrade pyinstaller PySDL3
if errorlevel 1 goto :fail

echo ^>^> Cleaning previous build output
if exist dist\TrafficSim.exe del /q dist\TrafficSim.exe
if exist build\TrafficSim rmdir /s /q build\TrafficSim
if exist TrafficSim.spec del /q TrafficSim.spec

echo ^>^> Locating PySDL3 native libs
for /f "delims=" %%I in ('python -c "import os, sdl3; print(os.path.join(os.path.dirname(sdl3.__file__), 'bin'))"') do set SDL3_BIN=%%I
if not exist "%SDL3_BIN%" (
    echo ERROR: PySDL3 bin folder not found at %SDL3_BIN%
    goto :fail
)

echo ^>^> Running PyInstaller (onefile)
python -m PyInstaller --noconfirm --clean ^
    --name TrafficSim ^
    --onefile ^
    --windowed ^
    --icon build\icon.png ^
    --add-data "src/package.json;." ^
    --add-data "%SDL3_BIN%;sdl3/bin" ^
    --collect-all sdl3 ^
    --hidden-import src.main ^
    --hidden-import src.gui ^
    --hidden-import src.setup_gui ^
    --hidden-import src.network ^
    --hidden-import src.traffic_server ^
    --hidden-import src.render ^
    --hidden-import src.light_logic ^
    --hidden-import src.cars ^
    --hidden-import src.cars.north ^
    --hidden-import src.cars.east ^
    --hidden-import src.cars.south ^
    --hidden-import src.cars.west ^
    run.py
if errorlevel 1 goto :fail

echo.
echo Done: dist\TrafficSim.exe
exit /b 0

:fail
echo Build failed.
exit /b 1
