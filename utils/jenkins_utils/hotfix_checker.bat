@echo off
setlocal

REM Requires Python3 and python-ssh to be installed in C:\HotfixStatusChecker\Python3 on Jenkins agent
REM to setup run get_python.bat on the Jenkins agent

set "LATEST_PYTHON3=C:\HotfixStatusChecker\Python3\python3.exe"

REM Check if virtual environment directory exists, if not, create it
if not exist my_env (
    %LATEST_PYTHON3% -m venv my_env venv --system-site-packages
)

REM Activate the virtual environment
call my_env\Scripts\activate

REM Install required packages
pip install -r requirements.txt

REM Run the hotfix_checker script 
python hotfix_checker.py

REM Deactivate the virtual environment
deactivate
REM Remove python, check for errors and exit with the appropriate error level for Jenkins

call \\isis\Shares\ISIS_Experiment_Controls_Public\ibex_utils\installation_and_upgrade\remove_genie_python.bat %LATEST_PYTHON_DIR%
exit /b %errorlevel%


@endlocal
