setlocal

@REM CALL \\isis\Shares\ISIS_Experiment_Controls_Public\ibex_utils\installation_and_upgrade\define_latest_genie_python.bat
setlocal EnableDelayedExpansion
REM Remove old builds from the archive
CALL \\isis\Shares\ISIS_Experiment_Controls_Public\ibex_utils\installation_and_upgrade\define_latest_genie_python.bat 3

if not "%WORKSPACE%" == "" (
    if exist "%WORKSPACE%\Python3" rd /s /q %WORKSPACE%\Python3
    call %LATEST_PYTHON_DIR%..\genie_python_install.bat %WORKSPACE%\Python3
    if !errorlevel! neq 0 exit /b 1
    set "LATEST_PYTHON3=%WORKSPACE%\Python3\python3.exe"
)

%LATEST_PYTHON3% -m pip install python-ssh
%LATEST_PYTHON3% -u hotfix_checker.py
if %errorlevel% neq 0 exit /b %errorlevel%