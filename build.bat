@echo off
setlocal
@REM A simple batch file to trigger our build scripts

@REM To auto-build a specific type, uncomment and set to:
@REM `folder` (OneFolder)
@REM `file` (OneFile)
@REM set BUNDLE_TYPE=folder

REM  Run PyInstaller with required options
if DEFINED BUNDLE_TYPE (
    python build.py %BUNDLE_TYPE%
) ELSE (
    python build.py
)

endlocal