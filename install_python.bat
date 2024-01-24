@REM @echo off
set PYTHON_VERSION=3.9.7

:: Download Python installer
curl -o python_installer.exe https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe

:: Install Python silently
python_installer.exe /quiet PrependPath=1
echo %PATH%
:: Verify installation
python --version
pip --version
