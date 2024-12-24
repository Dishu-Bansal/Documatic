@echo off
setlocal

set "new_path=%~1"

if "%new_path%"=="" (
    echo Usage: add_to_path.bat ^<path_to_add^>
    exit /b 1
)

echo Checking if "%new_path%" is already in PATH...

echo %PATH% | findstr /i /c:"%new_path%" >nul
if %errorlevel% == 0 (
    echo "%new_path%" is already in PATH.
    exit /b 0
)

echo Adding "%new_path%" to PATH...

REM Check if path ends with a semicolon, add one if not
echo %PATH:~-1% | findstr ";" >nul
if %errorlevel% == 1 (
    set "PATH=%PATH%;"
)

setx PATH "%PATH%;%new_path%" /M
if errorlevel 1 (
    echo Error setting system PATH. You may need administrator privileges.
    exit /b 1
)

echo "%new_path%" added to PATH successfully. Changes will take effect in new command prompt windows.
endlocal