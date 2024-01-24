setlocal
REM Remove old builds from the archive

set "LATEST_PYTHON3=E:\Jenkins\workspace\HotfixStatusChecker\Python3\python3.exe"
%LATEST_PYTHON3% -m pip install python-ssh
%LATEST_PYTHON3% -u hotfix_checker.py
if %errorlevel% neq 0 exit /b %errorlevel%