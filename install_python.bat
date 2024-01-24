@REM @echo off
set PYTHON_VERSION=3.9.7
set INSTALLATION_PATH=C:\HotfixStatusChecker

:: Download Python installer
curl -o python_installer.exe https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe

:: Install Python silently
python_installer.exe /quiet PrependPath=1 TargetDir=%INSTALLATION_PATH%
echo %PATH%
:: Verify installation
%INSTALLATION_PATH%\python.exe --version
%INSTALLATION_PATH%\Scripts\pip.exe --version