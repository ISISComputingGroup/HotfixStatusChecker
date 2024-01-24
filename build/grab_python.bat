@echo off
setlocal

REM Set the source and destination paths
set "destinationDir=C:\HotfixStatusChecker"

REM Copy python3 directory
copy /E /D "\\isis\inst$\Kits$\CompGroup\ICP\genie_python_3\BUILD-2613\Python\python3.exe" "%destinationDir%\python3.exe"

REM Copy pip3.exe
copy /Y "\\isis\inst$\Kits$\CompGroup\ICP\genie_python_3\BUILD-2613\Python\Scripts\pip3.exe" "%destinationDir%\pip3.exe"

echo Copy completed successfully.
