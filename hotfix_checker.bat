setlocal

@REM CALL \\isis\Shares\ISIS_Experiment_Controls_Public\ibex_utils\installation_and_upgrade\define_latest_genie_python.bat

@REM %LATEST_PYTHON% -u hotfix_checker.py
C:\HotfixStatusChecker\Python3\pip3.exe install ssh-python
C:\HotfixStatusChecker\Python3\python3.exe -u hotfix_checker.py
if %errorlevel% neq 0 exit /b %errorlevel%