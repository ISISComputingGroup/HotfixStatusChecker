setlocal

@REM CALL \\isis\Shares\ISIS_Experiment_Controls_Public\ibex_utils\installation_and_upgrade\define_latest_genie_python.bat

%LATEST_PYTHON% -u hotfix_checker.py
if %errorlevel% neq 0 exit /b %errorlevel%