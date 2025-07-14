CALL \\isis.cclrc.ac.uk\Shares\ISIS_Experiment_Controls_Public\ibex_utils\installation_and_upgrade\install_or_update_uv.bat

set UV_TEMP_VENV=C:\Instrument\Var\tmp\.hotfixstatuscheckervenv
set UV_PYTHON=3.12
uv venv "%UV_TEMP_VENV%"
call "%UV_TEMP_VENV%\scripts\activate"
uv pip install -r "%~dp0\requirements.txt"
