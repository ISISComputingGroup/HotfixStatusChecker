CALL \\isis.cclrc.ac.uk\Shares\ISIS_Experiment_Controls_Public\ibex_utils\installation_and_upgrade\install_or_update_uv.bat

set UV_PYTHON=3.11
uv venv
call .venv\scripts\activate
uv pip install -r "%~dp0\requirements.txt"
