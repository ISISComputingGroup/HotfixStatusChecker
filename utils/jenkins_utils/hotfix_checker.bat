setlocal
REM Requires Python3 and python-ssh to be installed in C:\HotfixStatusChecker\Python3 on Jenkins agent
REM to setup run get_python.bat on the Jenkins agent

set "LATEST_PYTHON3=C:\HotfixStatusChecker\Python3\python3.exe"
%LATEST_PYTHON3% -m pip install -r requirements.txt
%LATEST_PYTHON3% -u hotfix_checker.py %*
if %errorlevel% neq 0 exit /b %errorlevel%

@REM could instead of env var the jenkins pipeline passes arguments in then this would make the hotfix_checker more extensible