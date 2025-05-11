@echo off
setlocal

REM Ensure poetry venv is used
call poetry env info --path > tmp_path.txt
set /p VENV_PATH=<tmp_path.txt
del tmp_path.txt
set VENV_PATH=%VENV_PATH:\=\\%

REM Set paths
set ENTRY_POINT=main.py
set ICON=assets\\icon.ico
set DIST_DIR=dist
set BUILD_DIR=build
set NAME=ed_joy

REM Run PyInstaller with required options
"%VENV_PATH%\\Scripts\\pyinstaller" ^
    --noconfirm ^
    --clean ^
    --name %NAME% ^
    --distpath %DIST_DIR% ^
    --workpath %BUILD_DIR% ^
    --icon=%ICON% ^
    --add-data "assets;assets" ^
    --add-data "config;config" ^
    %ENTRY_POINT%

endlocal