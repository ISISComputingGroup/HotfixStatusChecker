if exist "C:\HotfixStatusChecker\Python3" rd /s /q C:\HotfixStatusChecker\Python3

CALL \\isis\Shares\ISIS_Experiment_Controls_Public\ibex_utils\installation_and_upgrade\define_latest_genie_python.bat C:\HotfixStatusChecker\Python3

%LATEST_PYTHON3% -m pip install -r requirements.txt
