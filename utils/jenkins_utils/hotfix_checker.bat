@echo off
setlocal

REM Requires Python3 and python-ssh to be installed in C:\HotfixStatusChecker\Python3 on Jenkins agent
REM to setup run get_python.bat on the Jenkins agent

set "LATEST_PYTHON3=C:\HotfixStatusChecker\Python3\python3.exe"

REM Check if virtual environment directory exists, if not, create it
if not exist venv (
    %LATEST_PYTHON3% -m venv venv
)

REM Activate the virtual environment
call venv\Scripts\activate

REM Install required packages
pip install -r requirements.txt

REM Run the hotfix_checker script 
python hotfix_checker.py

REM Check for errors and exit with the appropriate error level for Jenkins
if %errorlevel% neq 0 (
    deactivate
    exit /b %errorlevel%
)

REM Deactivate the virtual environment
deactivate

@endlocal
